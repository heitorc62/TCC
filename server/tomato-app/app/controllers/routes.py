from flask_smorest import Blueprint, abort
from sqlalchemy import desc
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from app import db
from PIL import Image
from app.models import ImageModel, ImageStatus, ReviewerModel, InvitationModel, AdminModel, TaskStatusModel, \
                        TaskStatus, process_ml_pipeline, save_image_to_db, send_invite_email, \
                        update_S3_dataset, create_task_in_label_studio, generate_presigned_url, \
                        generate_image_metadata, update_s3_label, query_llm, create_llm_prompt, load_new_weights
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, jwt_required
from datetime import timedelta
import io, secrets, requests
from flask_login import login_user, login_required

blp = Blueprint("Routes", "routes", description="Routes for the application")

@blp.route('/update_dataset', methods=['POST'])
@jwt_required()
def update_dataset():
    # get all reviewed images from the database
    reviewed_images = ImageModel.query.filter_by(status=ImageStatus.REVIEWED).all()
    result = update_S3_dataset(reviewed_images)
    return jsonify(result)


@blp.route('/update_weights', methods=['POST'])
@jwt_required()
def update_weights():
    try:
        # Extract the weights URL from the request
        request_data = request.get_json()
        weights_url = request_data.get('weights_url')
        weights_key = request_data.get('weights_key')
        
        if not weights_url or not weights_key:
            return jsonify({"error": "weights_url or weights_key is missing in the request."}), 400

        # Local path where the weights will be saved
        local_weights_path = f"app/config/weights/{weights_key}"

        # Download the file from the presigned URL
        response = requests.get(weights_url)
        if response.status_code == 200:
            with open(local_weights_path, 'wb') as f:
                f.write(response.content)
            print(f"New weights downloaded and saved at: {local_weights_path}")
        else:
            return jsonify({"error": "Failed to download the weights file from the presigned URL."}), 400

        # Reload the model with the new weights
        current_app.models["object_detection"] = load_new_weights(local_weights_path)  # Custom function to load the new weights
        print(f"Model reloaded with the new weights from {local_weights_path}")
        
        return jsonify({"message": "Weights updated and model reloaded successfully."}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    


@blp.route('/invite_reviewer', methods=['POST'])
@jwt_required()
def invite_reviewer():
    request_data = request.get_json()
    email = request_data.get('email')
    print("Vamos enviar o email para: ", email)
    token = secrets.token_urlsafe(32)  # Generate a unique token
    
    # Check if the invitation already exists
    existing_invite = InvitationModel.query.filter_by(email=email).first()
    if existing_invite:
        return jsonify({'message': 'An invitation for this email already exists.'}), 409

    # Send the invite via email (assume you have email setup)
    try:
        if send_invite_email(email, token): print("Email sent successfully.")
        else: raise Exception("Failed to send email")
        # Store the invitation in the database after the email is sent
        invite = InvitationModel(email=email, token=token)
        db.session.add(invite)
        db.session.commit()

        return jsonify({'message': 'Invitation sent and stored successfully'}), 201
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({'message': 'Failed to send invitation email'}), 500

@blp.route('/register_reviewer/<token>', methods=['GET', 'POST'])
def register_reviewer(token):
    # Check if the token exists and is valid
    invite = InvitationModel.query.filter_by(token=token, is_used=False).first()
    if not invite:
        flash('Invalid or expired invite token', 'danger')
        return redirect(url_for('Routes.login'))

    if request.method == 'POST':
        # Process the registration
        username = request.form['username']
        password = request.form['password']
        
        # Hash the password before storing it
        hashed_password = pbkdf2_sha256.hash(password)

        # Create the reviewer user
        reviewer = ReviewerModel(username=username, password=hashed_password)
        db.session.add(reviewer)

        # Mark the invitation as used
        invite.is_used = True
        db.session.commit()

        flash('Reviewer registered successfully', 'success')
        return redirect(url_for('Routes.login'))

    # Render registration form
    return render_template('register_reviewer.html', token=token)


@blp.route('/admin_login', methods=['POST'])
def admin_login():
    request_data = request.get_json()
    username = request_data.get('username')
    password = request_data.get('password')
    
    admin = AdminModel.query.filter(
            AdminModel.username == username
        ).first()

    if admin and pbkdf2_sha256.verify(password, admin.password):
        access_token = create_access_token(identity=admin.id, fresh=True, expires_delta=timedelta(days=1))
        return jsonify({ "access_token": access_token }), 200

    abort(401, message="Invalid credentials.")


@blp.route('/register_admin', methods=['POST'])
def register_admin():
    request_data = request.get_json()
    username = request_data.get('username')
    password = request_data.get('password')
    if AdminModel.query.filter(AdminModel.username == username).first():
        abort(409, message="An admin with that user already exists.")

    admin = AdminModel(
        username=username,
        password=pbkdf2_sha256.hash(password)
    )
    db.session.add(admin)
    db.session.commit()

    return jsonify({"message": "Admin created successfully."}), 201


@blp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Process the login form submission
        username = request.form['username']
        password = request.form['password']

        # Query the user from the database
        reviewer = ReviewerModel.query.filter_by(username=username).first()

        # Check if the user exists and if the password is correct
        if reviewer is None or not pbkdf2_sha256.verify(password, reviewer.password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

        # Log the user in
        login_user(reviewer)
        # On successful login, redirect to the labelling tool page
        flash('Login successful', 'success')
        # use flask login to log the user in
        return redirect(url_for('Routes.labelling_tool'))

    # For GET request, render the login form
    return render_template('login.html')


@blp.route('/process_image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    
    result = process_ml_pipeline(image, current_app.models, current_app.config, current_app.device)
    save_image_to_db(image_bytes, result, current_app.config)
    
    # Extract relevant data for LLM prompt
    prompt = create_llm_prompt(result)
    
    # Generate response from LLM
    llm_response = query_llm(prompt)

    return jsonify({
        "ml_result": result,
        "llm_response": llm_response
    })

#require flask login
@blp.route('/labelling_tool')
@login_required
def labelling_tool():
    # Step 1: Query an unreviewed image from the database
    unreviewed_image = db.session.query(ImageModel).filter_by(status=ImageStatus.PENDING).first()
    if not unreviewed_image:
        return redirect(url_for('Routes.no_images'))
    # Step 2: Create a task in Label Studio for the unreviewed image
    presigned_url = generate_presigned_url(current_app.config["S3_BUCKET"], unreviewed_image.s3_key)
    task_id = create_task_in_label_studio(presigned_url, unreviewed_image.image_metadata, current_app.LABEL_STUDIO_PROJECT_ID, image_id=unreviewed_image.id)
    # Step 3: Redirect the user to the Label Studio task page
    task_status = TaskStatusModel(task_id=task_id)
    db.session.add(task_status)
    db.session.commit()
    label_studio_task_url = f"http://localhost:8080/projects/{current_app.LABEL_STUDIO_PROJECT_ID}/data?tab=2&task={task_id}"
    return redirect(label_studio_task_url)

def mark_task_as_completed(task_id):
    task_status = TaskStatusModel.query.filter_by(task_id=task_id).order_by(desc(TaskStatusModel.id)).first()
    task_status.status = TaskStatus.COMPLETED
    db.session.commit()

@blp.route('/labelling_tool/webhook', methods=['POST'])
def labelling_callback():
    label_data = request.json
    # Extract the relevant information from the payload
    action = label_data['action']
    if action in ["ANNOTATION_CREATED", "ANNOTATION_UPDATED"]:
        # Step 1: Update the image metadata in the database
        annotations = label_data['annotation']['result']
        task_data = label_data['task']['data']
        image_id = task_data['image_id']
        current_task_id = label_data['task']['id']
        
        # Save the labels to your DB
        image = db.session.query(ImageModel).filter_by(id=image_id).first()
        metadata = generate_image_metadata(annotations)
        image.image_metadata = metadata
        
        # Mark the image as reviewed
        image.status = ImageStatus.REVIEWED
        db.session.commit()
        
        # Step 2: Update the image's YOLO label in S3
        update_s3_label(image.label_s3_key, metadata)
        
        # Step 3: Start a new review by selecting another unreviewed image
        new_image = db.session.query(ImageModel).filter_by(status=ImageStatus.PENDING).first()
        if new_image:
            # Create a new task in Label Studio for the new image
            print(f"Starting a new review for image {new_image.id}")
            presigned_url = generate_presigned_url(current_app.config["S3_BUCKET"], new_image.s3_key)
            new_task_id = create_task_in_label_studio(presigned_url, new_image.image_metadata, current_app.LABEL_STUDIO_PROJECT_ID, image_id=new_image.id)
            print(f"New task created with ID {new_task_id}")
            new_task_status = TaskStatusModel(task_id=new_task_id)
            db.session.add(new_task_status)
            
            # Mark the current task as completed
            mark_task_as_completed(current_task_id)
            
            return jsonify({'message': 'Review completed successfully. Starting a new review.'}), 200
        else:
            print("No more images to review")
            
            # Mark the current task as completed
            mark_task_as_completed(current_task_id)
            
            return jsonify({'message': 'Review completed successfully. No more images to review.'}), 200
    else:
        return jsonify({'message': 'No action required'}), 200
    
    

@blp.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task_status = TaskStatusModel.query.filter_by(task_id=task_id).order_by(desc(TaskStatusModel.id)).first().status.name
    next_task = TaskStatusModel.query.filter_by(status=TaskStatus.PENDING).first()
    if next_task:
        next_task_id = next_task.task_id
        label_studio_task_url = f"http://localhost:8080/projects/{current_app.LABEL_STUDIO_PROJECT_ID}/data?tab=2&task={next_task_id}"
        response_data = {"task_status": task_status, "next_task": label_studio_task_url}
    else:
        response_data = {"task_status": task_status, "next_task": f"http://localhost:5000{url_for('Routes.no_images')}"}
        
    response = jsonify(response_data)
    # Add CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@blp.route('/no_images')
def no_images():
    return '''
    <h1>No more images to review! Please come back later.</h1>
    '''
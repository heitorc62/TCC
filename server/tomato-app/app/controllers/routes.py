from flask_smorest import Blueprint, abort
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from app import db
from PIL import Image
from app.models import ImageModel, ImageStatus, ReviewerModel, InvitationModel, AdminModel, \
                        process_ml_pipeline, save_image_to_db, send_invite_email, \
                        update_S3_dataset, create_task_in_label_studio, generate_presigned_url
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, jwt_required
from datetime import timedelta
import io, secrets


blp = Blueprint("Routes", "routes", description="Routes for the application")

@blp.route('/update_dataset', methods=['POST'])
@jwt_required()
def update_dataset():
    # get all reviewed images from the database
    reviewed_images = ImageModel.query.filter_by(status=ImageStatus.REVIEWED).all()
    result = update_S3_dataset(reviewed_images)
    return jsonify(result)


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

        # On successful login, redirect to the labelling tool page
        flash('Login successful', 'success')
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

    return jsonify(result)

@blp.route('/labelling_tool')
def labelling_tool():
    # Step 1: Query an unreviewed image from the database
    unreviewed_image = db.session.query(ImageModel).filter_by(status=ImageStatus.PENDING).first()
    if not unreviewed_image:
        return "No unreviewed images available", 404
    # Step 2: Create a task in Label Studio for the unreviewed image
    presigned_url = generate_presigned_url(current_app.config["S3_BUCKET"], unreviewed_image.s3_key)
    print(f"presigned_url={presigned_url}")
    task_id = create_task_in_label_studio(presigned_url, unreviewed_image.image_metadata, current_app.LABEL_STUDIO_PROJECT_ID)
    # Step 3: Redirect the user to the Label Studio task page
    label_studio_task_url = f"http://localhost:8080/projects/{current_app.LABEL_STUDIO_PROJECT_ID}/data?tab=2&task={task_id}"
    return redirect(label_studio_task_url)

@blp.route('/labelling_tool/webhook', methods=['POST'])
def labelling_callback():
    label_data = request.json
    # Extract the relevant information from the payload
    task_id = label_data['id']
    project_id = label_data['project']
    action = label_data['action']
    
    if action in ["ANNOTATION_CREATED", "ANNOTATION_UPDATED"]:
        # Get the task information (such as image URL) from the payload
        task_data = label_data['data']  # This will contain your image data
        annotations = label_data['annotations'][0]['result']  # Extract labels
        # Step 1: Update the image metadata in the database
        # Save the labels to your DB
        # Mark the image as reviewed
        # Step 2: Update the image's YOLO label in S3
        # Step 3: Start a new review by selecting another unreviewed image
        new_image = db.session.query(ImageModel).filter_by(reviewed=False).first()
        if new_image:
            create_task_in_label_studio(new_image.url, project_id)  # Create a new task in Label Studio

    return jsonify({'status': 'success'}), 200
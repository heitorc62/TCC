from flask_smorest import Blueprint, abort
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from app import db
from PIL import Image
from app.models import ImageModel, ImageStatus, ReviewerModel, InvitationModel, AdminModel, \
                        process_ml_pipeline, save_image_to_db, send_invite_email, \
                        update_S3_dataset
from werkzeug.security import generate_password_hash, check_password_hash
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
    email = request.form['email']
    token = secrets.token_urlsafe(32)  # Generate a unique token
    
    # Store the invitation in the database
    invite = InvitationModel(email=email, token=token)
    db.session.add(invite)
    db.session.commit()

    # Send the invite via email (assume you have email setup)
    send_invite_email(email, token)  # Placeholder for email sending logic
    return jsonify({'message': 'Invitation sent successfully'})


@blp.route('/register_reviewer/<token>', methods=['GET', 'POST'])
def register_reviewer(token):
    # Check if the token exists and is valid
    invite = InvitationModel.query.filter_by(token=token, is_used=False).first()
    if not invite:
        flash('Invalid or expired invite token', 'danger')
        return redirect(url_for('routes.login'))

    if request.method == 'POST':
        # Process the registration
        username = request.form['username']
        password = request.form['password']
        
        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Create the reviewer user
        reviewer = ReviewerModel(username=username, password=hashed_password)
        db.session.add(reviewer)

        # Mark the invitation as used
        invite.is_used = True
        db.session.commit()

        flash('Reviewer registered successfully', 'success')
        return redirect(url_for('routes.login'))

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
    if AdminModel.query.filter(AdminModel.email == username).first():
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
        if reviewer is None or not check_password_hash(reviewer.password, password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

        # On successful login, redirect to the labelling tool page
        flash('Login successful', 'success')
        return redirect(url_for('labelling_tool'))

    # For GET request, render the login form
    return render_template('login.html')



@blp.route('/labelling_tool')
def labelling_tool():
    return "Welcome to the labelling tool"


@blp.route('/process_image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

    ml_config = current_app.config['ML_CONFIG']
    
    result = process_ml_pipeline(image, current_app.models, ml_config, current_app.device)
    save_image_to_db(image_bytes, result)

    return jsonify(result)
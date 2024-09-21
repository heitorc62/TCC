from server.app.models.models import ImageModel, ImageStatus
from app import db, mail
from flask_mail import Message
from flask import current_app, render_template, url_for
import boto3, io

def save_image_to_db(image_bytes, result, config):
    id_path = f'{ImageModel.get_last_image_id() + 1}.jpg'
    image = ImageModel(path=id_path, status=ImageStatus.PENDING, metadata=result)
    db.session.add(image)
    db.session.commit()
    
    # Store the image in S3 bucket
    s3 = boto3.client('s3', region_name=config['AWS_REGION'])
    s3.upload_fileobj(io.BytesIO(image_bytes), config['S3_BUCKET'], id_path)
    
def send_invite_email(email, token):
    subject = "You're Invited to Join the Reviewer Platform"
    recipient = [email]
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    
    # Construct the registration URL
    registration_url = url_for('routes.register_reviewer', token=token, _external=True)
    
    # Render email template
    html_body = render_template('email_invite.html', registration_url=registration_url)
    
    msg = Message(subject=subject, recipients=recipient, sender=sender, html=html_body)
    mail.send(msg)
from app.models.models import ImageModel, ImageStatus
from app import db
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app, render_template, url_for
import boto3, io, os, smtplib

def update_db_image_status(image, status):
    db_image = ImageModel.query.filter_by(id=image.id)
    db_image.status = status
    db.session.commit()
    

def move_image_and_label(image, target_prefix, s3, bucket_name):
        """
        Move both the image file and its label file to the target folder.
        
        Parameters:
            image (ImageModel): The image object containing metadata.
            target_prefix (str): The S3 folder (either for training or validation).
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Original file keys in the bucket
            image_key = image.s3_key
            label_key = image.label_s3_key

            # Define new keys for image and label in the destination folder
            new_image_key = f"{target_prefix}/images/{os.path.basename(image_key)}"
            new_label_key = f"{target_prefix}/labels/{os.path.basename(label_key)}"

            # Move image
            s3.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': image_key},
                Key=new_image_key
            )

            # Move label file
            s3.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': label_key},
                Key=new_label_key
            )
            return True
        
        except Exception as e:
            print(f"Error moving image {image_key}: {str(e)}")
            return False



def update_S3_dataset(reviewed_images, config):    
    # Config values
    bucket_name = config['S3_BUCKET']
    dataset_path = config['S3_DATASET_PATH']
    training_split = config['TRAIN_PERCENTAGE']
    region = config['AWS_REGION']
    
    s3 = boto3.client('s3', region=region)
    
    # Split reviewed images into training and validation sets
    total_images = len(reviewed_images)
    training_count = int(total_images * training_split)
        
    # Separate images for training and validation
    training_images = reviewed_images[:training_count]
    validation_images = reviewed_images[training_count:]
        
    # Initialize counters for success and failures
    training_moved = 0
    validation_moved = 0
    errors = []

    # Process training images
    training_prefix = f"{dataset_path}/train"
    for image in training_images:
        if move_image_and_label(image, training_prefix, s3, bucket_name):
            training_moved += 1
            update_db_image_status(image, ImageStatus.INCORPORATED)
        else:
            errors.append(image.s3_key)

    # Process validation images
    validation_prefix = f"{dataset_path}/val"
    for image in validation_images:
        if move_image_and_label(image, validation_prefix, s3, bucket_name):
            validation_moved += 1
            update_db_image_status(image, ImageStatus.INCORPORATED)
        else:
            errors.append(image.s3_key)

    # Return the results
    result = {
        "training_moved": training_moved,
        "validation_moved": validation_moved,
        "errors": errors
    }
    
    return result
    

def get_label_content(image):
    # Get yolo label content
    pass


def save_image_to_db(image_bytes, result, config):
    image = ImageModel(metadata=result, new_images_path=config['S3_NEW_IMAGES_PATH'])
    db.session.add(image)
    db.session.commit()
    
    # Generate yolo label file
    label_content = get_label_content(image)
    
    # Store the image and label to S3 bucket
    s3 = boto3.client('s3', region_name=config['AWS_REGION'])
    s3.upload_fileobj(io.BytesIO(image_bytes), config['S3_BUCKET'], image.s3_key)
    s3.upload_fileObj(label_content, config['S3_BUCKET'], image.label_s3_key)
    
def send_invite_email(email, token):
    subject = "You're Invited to Join the Reviewer Platform"
    recipient = email
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    
    # Construct the registration URL
    registration_url = url_for('Routes.register_reviewer', token=token, _external=True)
    
    # Render email template
    html_body = render_template('email_invite.html', registration_url=registration_url)
    
    # Create the message
    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        html_content=html_body)
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.send(message)
        return True
    except Exception as e:
        print(e.message)
        return False
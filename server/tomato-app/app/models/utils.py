from app.models.models import ImageModel, ImageStatus
from app import db
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app, render_template, url_for, abort
import boto3, io, os, requests, json
from datetime import datetime
from PIL import Image
from openai import OpenAI
import openai

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
    
    s3 = boto3.client('s3', region_name=region)
    
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
    

def get_label_content(metadata):
    image_width = metadata['image_width']  # Assuming the image width is stored in metadata
    image_height = metadata['image_height']  # Assuming the image height is stored in metadata

    detected_objects = metadata.get('detected_objects', [])
    
    label_content = []
    
    for obj in detected_objects:
        class_index = obj['class_index']
        box = obj['box']  # [xmin, ymin, xmax, ymax]
        
        # Calculate center, width, and height
        xmin, ymin, xmax, ymax = box
        x_center = (xmin + xmax) / 2 / image_width
        y_center = (ymin + ymax) / 2 / image_height
        width = (xmax - xmin) / image_width
        height = (ymax - ymin) / image_height
        
        # Format the YOLO label string
        label_content.append(f"{class_index} {x_center} {y_center} {width} {height}")
    
    # Join the list into a string with newline characters
    return "\n".join(label_content)


def save_image_to_db(image_bytes, result, config):
    # Open the image to get dimensions
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    image_width, image_height = image.size  # Get image width and height

    # Add the image dimensions to the result (metadata)
    result['image_width'] = image_width
    result['image_height'] = image_height

    # Create an ImageModel instance with the updated metadata
    image_record = ImageModel(new_images_path=config['S3_NEW_IMAGES_PATH'], metadata=result)
    db.session.add(image_record)
    db.session.commit()
    
    # Generate YOLO label file content
    label_content = get_label_content(image_record.image_metadata)
    
    # Store the image and label to S3 bucket
    s3 = boto3.client('s3', region_name=config['AWS_REGION'])
    s3.upload_fileobj(io.BytesIO(image_bytes), config['S3_BUCKET'], image_record.s3_key)
    
    # For the label, convert the label content to bytes and upload to S3
    label_content_bytes = io.BytesIO(label_content.encode('utf-8'))
    s3.upload_fileobj(label_content_bytes, config['S3_BUCKET'], image_record.label_s3_key)

    
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

def generate_annotations(label_info):
    """
    Generates the 'results' object containing annotations from the label_info.
    
    Args:
        label_info (dict): A dictionary containing detected objects and image dimensions.
    
    Returns:
        list: A list of annotation results to be included in the task.
    """
    results = []
    detected_objects = label_info.get('detected_objects', None)
    if detected_objects is None: return results
    image_width = label_info['image_width']
    image_height = label_info['image_height']

    for obj in detected_objects:
        box = obj['box']
        x_min, y_min, x_max, y_max = box
        class_name = obj['class_name']
        score = obj['score']

        # Calculate coordinates in percentages
        x = (x_min / image_width) * 100
        y = (y_min / image_height) * 100
        width = ((x_max - x_min) / image_width) * 100
        height = ((y_max - y_min) / image_height) * 100

        # Construct the annotation result
        result = {
            "from_name": "label",
            "to_name": "image",
            "type": "rectanglelabels",
            "value": {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "rotation": 0,
                "rectanglelabels": [class_name]
            },
            "score": score  # Optional: Include confidence score
        }
        results.append(result)

    return results

def retrieve_task_id(image_url, project_id):
    """
    Retrieves the task ID for a task by matching the image URL after the task is created.
    
    Args:
        image_url (str): The URL of the image used in the task.
        project_id (int): The ID of the project.
    
    Returns:
        task_id (int): The ID of the matching task or None if not found.
    """
    headers = {
        'Authorization': f"Token {current_app.config['LABEL_STUDIO_API_KEY']}",
        'Content-Type': 'application/json'
    }
    
    # API endpoint to get tasks
    endpoint = f"{current_app.config['LABEL_STUDIO_URL']}/api/projects/{project_id}/tasks"
    
    try:
        # Query the task list to find the task by image_url
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            tasks = response.json()
            # Loop through tasks to find the one with matching image_url
            for task in tasks:
                if task['data']['image'] == image_url:
                    return task['id']
            print(f"Task with image {image_url} not found.")
            return None
        else:
            print(f"Failed to retrieve tasks. Status code: {response.status_code}")
            print("Response:", response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def create_task_in_label_studio(image_url, label_info, project_id, image_id=None):
    """
    Creates a task in Label Studio with the given annotations by making an API call.
    
    Args:
        api_url (str): The base URL of the Label Studio instance.
        api_token (str): The API token for authentication.
        project_id (int): The ID of the project where the task will be created.
        image_url (str): The URL of the image to annotate.
        results (list): The list of annotation results generated by generate_annotations.
    """
    # Prepare the headers
    headers = {
        'Authorization': f"Token {current_app.config['LABEL_STUDIO_API_KEY']}",
        'Content-Type': 'application/json'
    }
    
    results = generate_annotations(label_info)

    # Prepare the task data
    task_data = {
        "data": {
            "image": image_url,
            "image_id": image_id
        },
        "annotations": [
            {
                "completed_by": 1,  # Update with the correct user ID
                "result": results,
                "was_cancelled": False,
                "ground_truth": False,
                "lead_time": 0,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
        ]
    }

    # API endpoint
    endpoint = f"{current_app.config['LABEL_STUDIO_URL']}/api/projects/{project_id}/import"

    try:
        # Send the POST request
        response = requests.post(
            endpoint,
            headers=headers,
            data=json.dumps([task_data])  # The API expects a list of tasks
        )

        if response.status_code == 201:
            print(f"Task created successfully! Now retrieving task ID...")
            # After the task is created, retrieve the task ID.
            task_id = retrieve_task_id(image_url, project_id)
            if task_id:
                print(f"Task ID: {task_id}")
                return task_id
            else:
                print("Task ID not found.")
                return None
        else:
            print(f"Failed to create task. Status code: {response.status_code}")
            print("Response:", response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """
    Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_key: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3', region_name=current_app.config['AWS_REGION'])
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                    'Bucket': bucket_name,
                    'Key': object_key,
                    'ResponseContentDisposition': 'inline',
                    'ResponseContentType': 'image/jpeg'
                },
            ExpiresIn=expiration
        )
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None

    # The response contains the presigned URL
    return response

def generate_image_metadata(annotations):
    # Initialize the image metadata dictionary
    image_metadata = {'detected_objects': []}
    original_width = 0
    original_height = 0
    # Iterate through each annotation to convert and add to the metadata
    for annotation in annotations:
        # Extract the original image dimensions
        original_width = annotation['original_width']
        original_height = annotation['original_height']
        
        # Extract bounding box details from annotation
        x = annotation['value']['x'] / 100.0 * original_width
        y = annotation['value']['y'] / 100.0 * original_height
        width = annotation['value']['width'] / 100.0 * original_width
        height = annotation['value']['height'] / 100.0 * original_height
        
        # Create the bounding box in the format [x1, y1, x2, y2]
        box = [x, y, x + width, y + height]

        # Extract other details like class name and score
        class_name = annotation['value']['rectanglelabels'][0]  # Assumes one label per annotation
        score = annotation.get('score', None)  # Get the score if it exists
        
        # Add to the detected_objects list in the desired format
        image_metadata['detected_objects'].append({
            'box': box,
            'class_index': '5',  # Based on your example, class index for 'Tomato leaf yellow virus'
            'class_name': class_name,
            'score': score
        })
    
    image_metadata['image_width'] = original_width
    image_metadata['image_height'] = original_height
    
    return image_metadata
    
def update_s3_label(label_s3_key, metadata):
    # Update YOLO label file content
    try:
        s3 = boto3.client('s3', region_name=current_app.config['AWS_REGION'])
        label_content = get_label_content(metadata)
        label_content_bytes = io.BytesIO(label_content.encode('utf-8'))
        s3.upload_fileobj(label_content_bytes, current_app.config['S3_BUCKET'], label_s3_key)
    except Exception as e:
        print(f"Error updating label in S3: {e}")
        

def create_llm_prompt(result):
    detected_objects = result.get('detected_objects', [])
    
    if not detected_objects:
        return "No objects detected in the image."

    image_width = result['image_width']
    image_height = result['image_height']

    prompt = (
        f"The image of size {image_width}x{image_height} pixels contains the following detected diseases:\n"
    )

    for idx, obj in enumerate(detected_objects):
        class_name = obj['class_name']
        score = obj['score']
        box = obj['box']
        x1, y1, x2, y2 = box

        location = f"from ({x1}, {y1}) to ({x2}, {y2})"
        prompt += (
            f"{idx + 1}. Disease: {class_name}\n"
            f"   Confidence: {score:.2f}\n"
            f"   Location: {location}\n\n"
        )
    
    # Add a request for advice at the end of the prompt
    prompt += (
        "Please provide advice on how to manage or treat the detected diseases and suggestions for improving the growth "
        "and health of the tomato plant overall."
    )
    
    return prompt



def query_llm(prompt):
    if prompt == "No objects detected in the image.":
        return "Our model did not detect any relevant information about tomatoes in the image. Have in mind that this is an app in development and we are constantly improving our models."
    try:
        # Access OpenAI API
        response = current_app.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # You can use "gpt-4" or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,  # Adjust response length as needed
            temperature=0.7  # Adjust creativity level
        )
        print(response.choices[0].message.content)
        # Extract the model's response
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error querying LLM: {str(e)}"

import os
import boto3
import argparse
import logging
import requests
from ultralytics import YOLO
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fetch the dataset from S3
def fetch_dataset(s3_bucket, s3_prefix, local_dir):
    s3 = boto3.client('s3')
    try:
        # List objects in the bucket under the prefix (folder)
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)

        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Extract the file's key and define the local file path
                    s3_key = obj['Key']

                    # Skip "folders" (i.e., keys ending with '/')
                    if not s3_key.endswith('/'):
                        # Derive the relative path in the local directory
                        relative_path = os.path.relpath(s3_key, s3_prefix)
                        local_file_path = os.path.join(local_dir, relative_path)

                        # Ensure the local directory structure exists
                        local_folder = os.path.dirname(local_file_path)
                        if not os.path.exists(local_folder):
                            os.makedirs(local_folder)

                        logging.info(f"Downloading {s3_key} to {local_file_path}")
                        s3.download_file(s3_bucket, s3_key, local_file_path)
                        logging.info(f"File saved to {local_file_path}")

    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except NoCredentialsError:
        logging.error("S3 credentials not available.")
        raise
    except ClientError as e:
        logging.error(f"S3 client error: {e}")
        raise

# Train YOLO using this dataset
def train_yolo(data_yaml, epochs=100, img_size=640, device=0):
    logging.info(f"Starting YOLO training with {epochs} epochs and image size {img_size}.")
    try:
        model = YOLO("yolov8n.pt")  # Build from YAML and transfer weights
        results = model.train(task="detect", data=data_yaml, epochs=epochs, imgsz=img_size, device=device)
        logging.info("YOLO training completed.")
        logging.info(f"results saved in: {results.save_dir}")
        return results
    except Exception as e:
        logging.error(f"Error during YOLO training: {e}")
        raise

# Upload the final weights file to the S3 bucket
def upload_to_s3(file_path, bucket_name, object_name=None):
    s3 = boto3.client('s3')
    
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    try:
        logging.info(f"Uploading {file_path} to S3: s3://{bucket_name}/{object_name}")
        s3.upload_file(file_path, bucket_name, object_name)
        logging.info(f"File uploaded to S3 successfully: s3://{bucket_name}/{object_name}")
    except FileNotFoundError:
        logging.error(f"The file {file_path} was not found.")
        raise
    except NoCredentialsError:
        logging.error("S3 credentials not available.")
        raise
    except ClientError as e:
        logging.error(f"S3 client error: {e}")
        raise

# Check if the weights should be updated based on the performance
def should_update_weights(current_performance, new_performance, threshold=0.05):
    """Returns True if new performance is significantly better than the current one."""
    logging.info(f"Comparing current performance: {current_performance} with new performance: {new_performance}")
    if new_performance - current_performance > threshold:
        logging.info("New weights perform better. Proceeding with the update.")
        return True
    else:
        logging.info("No significant improvement in the model performance. Skipping update.")
        #return False
        logging.info("Let's update anyway")
        return True

# Make a call to the server to update the weights file
def call_server_to_update_weights(weights_url, server_endpoint, weights_key):
    try:
        logging.info(f"Requesting server to update weights from: {weights_url} and with weights_key: {weights_key}")
        response = requests.post(server_endpoint, json={"weights_url": weights_url, "weights_key": weights_key})
        if response.status_code == 200:
            logging.info("Server successfully updated the weights.")
        else:
            logging.error(f"Server responded with error: {response.status_code}")
    except Exception as e:
        logging.error(f"Error while requesting server to update weights: {e}")
        raise
    
def update_current_performance_file(new_performance, current_performance_file):
    with open(current_performance_file, 'w') as f:
        f.write(str(new_performance))

def create_presigned_url(bucket_name, object_name, expiration=3600):
    s3 = boto3.client('s3')
    try:
        response = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)
        logging.info(f"Presigned URL generated for s3://{bucket_name}/{object_name}")
        return response
    except ClientError as e:
        logging.error(f"Error generating presigned URL: {e}")
        raise


# Main function to coordinate the workflow
def main():
    parser = argparse.ArgumentParser(description="Train YOLO model and manage weights.")
    parser.add_argument("--save_path", type=str, default="../datasets/tomato-dataset.zip", help="Path to save the dataset")
    parser.add_argument("--s3_bucket", type=str, required=True, help="S3 bucket containing the dataset")
    parser.add_argument("--s3_key", type=str, required=True, help="S3 key for the dataset file")
    parser.add_argument("--img_size", type=int, default=640, help="Image size for YOLO training")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--data_yaml", type=str, required=True, help="YAML file for YOLO training configuration")
    parser.add_argument("--s3_weights_key", type=str, required=True, help="S3 bucket to upload the trained weights")
    parser.add_argument("--server_endpoint", type=str, required=True, help="Server endpoint to notify for weights update")
    parser.add_argument("--current_performance", type=float, default=0.85, help="Current model performance")
    parser.add_argument("--current_performance_file", type=str, default="../best_metrics.csv", help="File to store current performance")
    
    args = parser.parse_args()

    # Fetch dataset from S3
    #fetch_dataset(args.s3_bucket, args.s3_key, args.save_path)
    
    # Train YOLO model
    results = train_yolo(data_yaml=args.data_yaml, epochs=args.epochs, img_size=args.img_size)
    new_performance = results.results_dict["metrics/mAP50(B)"]  # Example metric from YOLO training results

    # Decide if we should update the weights
    if should_update_weights(args.current_performance, new_performance):
        # Upload the new weights to S3
        upload_to_s3(f"{results.save_dir}/weights/best.pt", args.s3_bucket, args.s3_weights_key)
        # Call the server to update the weights
        weights_url = create_presigned_url(args.s3_bucket, args.s3_weights_key)
        print(f"weights_url = {weights_url}")
        call_server_to_update_weights(weights_url, args.server_endpoint, os.path.basename(args.s3_weights_key))
        update_current_performance_file(new_performance, args.current_performance_file)

if __name__ == "__main__":
    main()

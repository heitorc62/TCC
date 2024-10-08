import os
import boto3
import argparse
import logging
import requests
from ultralytics import YOLO
from botocore.exceptions import NoCredentialsError, ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fetch the dataset from S3
def fetch_dataset(s3_bucket, s3_key, save_path):
    s3 = boto3.client('s3')
    try:
        logging.info(f"Downloading dataset from S3: s3://{s3_bucket}/{s3_key} to {save_path}")
        s3.download_file(s3_bucket, s3_key, save_path)
        logging.info(f"Dataset saved to {save_path}")
    except FileNotFoundError:
        logging.error(f"File {save_path} not found.")
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
        return False

# Make a call to the server to update the weights file
def call_server_to_update_weights(weights_url, server_endpoint):
    try:
        logging.info(f"Requesting server to update weights from: {weights_url}")
        response = requests.post(server_endpoint, json={"weights_url": weights_url})
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

# Main function to coordinate the workflow
def main():
    parser = argparse.ArgumentParser(description="Train YOLO model and manage weights.")
    parser.add_argument("--save_path", type=str, default="../datasets/tomato-dataset.zip", help="Path to save the dataset")
    parser.add_argument("--s3_bucket", type=str, required=True, help="S3 bucket containing the dataset")
    parser.add_argument("--s3_key", type=str, required=True, help="S3 key for the dataset file")
    parser.add_argument("--img_size", type=int, default=640, help="Image size for YOLO training")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--data_yaml", type=str, required=True, help="YAML file for YOLO training configuration")
    parser.add_argument("--weights_output", type=str, default="./runs/train/weights/best.pt", help="Path to the output weights file")
    parser.add_argument("--s3_output_bucket", type=str, required=True, help="S3 bucket to upload the trained weights")
    parser.add_argument("--server_endpoint", type=str, required=True, help="Server endpoint to notify for weights update")
    parser.add_argument("--current_performance", type=float, default=0.85, help="Current model performance")
    parser.add_argument("--current_performance_file", type=str, default="../best_metrics.csv", help="File to store current performance")
    
    args = parser.parse_args()

    # Fetch dataset from S3
    fetch_dataset(args.s3_bucket, args.s3_key, args.save_path)
    
    # Train YOLO model
    results = train_yolo(data_yaml=args.data_yaml, epochs=args.epochs, img_size=args.img_size)
    
    new_performance = results["metrics"]["mAP_50"]  # Example metric from YOLO training results

    # Decide if we should update the weights
    if should_update_weights(parser.current_performance, new_performance):
        # Upload the new weights to S3
        upload_to_s3(args.weights_output, args.s3_output_bucket)
        # Call the server to update the weights
        weights_url = f"s3://{args.s3_output_bucket}/{os.path.basename(args.weights_output)}"
        call_server_to_update_weights(weights_url, args.server_endpoint)
        update_current_performance_file(new_performance, args.current_performance_file)

if __name__ == "__main__":
    main()

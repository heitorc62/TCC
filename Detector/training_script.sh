#!/bin/bash

# Exit immediately if any command exits with a non-zero status
set -e

# Check if a dataset path is provided
if [ -z "$1" ]; then
  echo "Error: No dataset path provided."
  echo "Usage: ./remote_script.sh <dataset_path> <s3_weights_key> <server_endpoint> <s3_url> <s3_access_key> <s3_secret_access_key>"
  exit 1
fi

# Check if an S3 weights key is provided
if [ -z "$2" ]; then
  echo "Error: No S3 weights key provided."
  echo "Usage: ./remote_script.sh <dataset_path> <s3_weights_key> <server_endpoint> <s3_url> <s3_access_key> <s3_secret_access_key>"
  exit 1
fi

# Check if an Ngrok URL is provided; if so, use it, otherwise default to localhost
if [ -z "$3" ]; then
  echo "Error: No server endpoint provided."
  echo "Usage: ./remote_script.sh <dataset_path> <s3_weights_key> <server_endpoint> <s3_url> <s3_access_key> <s3_secret_access_key>"
  exit 1
fi

# Check if and Ngrok URL for S3 is provided; if so, use it, otherwise default to localhost
if [-z "$4"]; then
  echo "Error: No S3 url provided."
  echo "Usage: ./remote_script.sh <dataset_path> <s3_weights_key> <server_endpoint> <s3_url> <s3_access_key> <s3_secret_access_key>"
  exit 1
else

if [ -z "$5"]; then
  echo "Error: No S3 access key provided."
  echo "Usage: ./remote_script.sh <dataset_path> <s3_weights_key> <server_endpoint> <s3_url> <s3_access_key> <s3_secret_access_key>"
  exit 1
fi

if [ -z "$6"]; then
  echo "Error: No SECRET_ACCESS_KEY provided."
  echo "Usage: ./remote_script.sh <dataset_path> <s3_weights_key> <server_endpoint> <s3_url> <s3_access_key> <s3_secret_access_key>"
  exit 1
fi

DATASET_PATH=$1
S3_WEIGHTS_KEY="weights/${2}.pt"
YAML_FILE="/home/heitorc62/PlantsConv/TCC/Detector/tomato.yaml"
METRICS_FILE="/home/heitorc62/PlantsConv/TCC/Detector/best_metrics.csv"
TRAIN_SCRIPT="/home/heitorc62/PlantsConv/TCC/Detector/src/s3_dataset_train.py"
S3_BUCKET="tomato-dataset"
S3_KEY="dataset/"
SERVER_ENDPOINT="$3/update_weights"
S3_ENDPOINT=$4
S3_ACCESS_KEY=$5
S3_SECRET_ACCESS_KEY=$6

. /home/heitorc62/PlantsConv/TCC/Detector/.yolo_env/bin/activate

# Step 1: Update the tomato.yaml file with the dataset path
echo "Updating $YAML_FILE with dataset path: $DATASET_PATH"
sed -i "s|path:.*|path: $DATASET_PATH|" $YAML_FILE

# Step 2: Get the current performance from best_metrics.csv
if [ ! -f "$METRICS_FILE" ]; then
  echo "Error: Metrics file $METRICS_FILE not found."
  exit 1
fi

# Extract current performance values from the best_metrics.csv
mAP50=$(head -n 1 "$METRICS_FILE" | xargs)

echo "Current Performance:"
echo "mAP50: $mAP50"

# Step 3: Run the src/s3_dataset_train.py script with the dataset path
echo "Running training script with dataset path: $DATASET_PATH"
nohup python $TRAIN_SCRIPT \
        --save_path datasets/$DATASET_PATH \
        --s3_endpoint $S3_ENDPOINT \
        --access_key_id $S3_ACCESS_KEY \
        --secret_access_key $S3_SECRET_ACCESS_KEY \
        --s3_bucket $S3_BUCKET \
        --s3_key $S3_KEY \
        --data_yaml $YAML_FILE \
        --s3_weights_key $S3_WEIGHTS_KEY \
	      --server_endpoint $SERVER_ENDPOINT \
        --current_performance $mAP50 > "${TRAIN_SCRIPT%/*}/train.log" 2>&1 &


# End of script

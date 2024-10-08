#!/bin/bash

# Exit immediately if any command exits with a non-zero status
set -e

# Check if a dataset path is provided
if [ -z "$1" ]; then
  echo "Error: No dataset path provided."
  echo "Usage: ./run_training.sh <dataset_path>"
  exit 1
fi

DATASET_PATH=$1
YAML_FILE="tomato.yaml"
METRICS_FILE="best_metrics.csv"
TRAIN_SCRIPT="src/s3_dataset_train.py"

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
python $TRAIN_SCRIPT --data $DATASET_PATH

# End of script

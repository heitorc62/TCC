import argparse
import torch
from torchvision import datasets, transforms
from torchvision import models
import torch.nn as nn
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import json
import os


# Pass all images of IPM dataset into the loaded network and access performance metrics.
def load_data(data_dir, input_size=224, batch_size=8):
    # Define your transform
    transform = transforms.Compose([
        transforms.RandomResizedCrop(input_size),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    # Load the dataset
    dataset = datasets.ImageFolder(data_dir, transform=transform)
    # Create the dataloaders
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    return dataloader

def get_model(weights_path, device='cuda', num_classes=39):
    model = models.vgg16_bn()
    print(f"num_classes = {num_classes}")
    num_ftrs = model.classifier[6].in_features
    print(f"num_ftrs = {num_ftrs}")
    model.classifier[6] = nn.Linear(num_ftrs,num_classes)
        
    # Load model weights if a path is provided
    checkpoint = torch.load(weights_path, map_location=lambda storage, loc: storage.cuda(device))
    model.load_state_dict(checkpoint)
    
    return model

def inference(model, dataloader, device):
    model.eval()
    model.to(device)
    predictions = []
    true_labels = []
    
    with torch.no_grad():
        for data, labels in dataloader:
            data = data.to(device)
            labels = labels.to(device)
            outputs = model(data)
            
            # Process predictions
            _, preds = torch.max(outputs, 1)
            predictions.extend(preds.cpu().numpy())
            true_labels.extend(labels.cpu().numpy())
            
    # Calculate accuracy
    #print("\n\n\n###########################################################\n\n\n")
    #print(f"true_labels:{true_labels}")
    #print("\n\n\n###########################################################\n\n\n")
    #print(f"predictions:{predictions}")
    #print("\n\n\n###########################################################\n\n\n")
    correct_predictions = sum(p == t for p, t in zip(predictions, true_labels))
    accuracy = correct_predictions / len(true_labels)
    print(f"Accuracy: {accuracy:.4f}")
    
    return predictions, true_labels

def calculate_metrics(predictions, true_labels):
    accuracy = accuracy_score(true_labels, predictions)
    precision = precision_score(true_labels, predictions, average='weighted')
    recall = recall_score(true_labels, predictions, average='weighted')
    f1 = f1_score(true_labels, predictions, average='weighted')
    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1
    }
    return metrics

def save_results(results, output_dir, name):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"results_{name}.json")
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=4)


def main(dataset_dir, output_dir, model_path, model_name, cuda_device):
    device=torch.device(f"cuda:{cuda_device}" if torch.cuda.is_available() else "cpu")
    print("The selected device is:", device)
    # Initialize the model for this run
    model = get_model(model_path, cuda_device)
    # Load the data
    dataloader = load_data(dataset_dir)
    # Evaluate
    predictions, true_labels = inference(model, dataloader, cuda_device)
    metrics = calculate_metrics(predictions, true_labels)
    save_results(metrics, output_dir, model_name)
    




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Access the performance of different models in a standardad dataset.")
    parser.add_argument('--dataset_dir', type=str, default='/home/heitorc62/PlantsConv/Plants-ConvNets-ViT/TCC/test_datasets/IPM_dataset')
    parser.add_argument('--output_dir', type=str, default='/home/heitorc62/PlantsConv/Plants-ConvNets-ViT/TCC/generalization/results')
    parser.add_argument('--cuda_device', type=int, default=1)
    parser.add_argument('--model_path', type=str)
    
    args = parser.parse_args()
    
    parts = args.model_path.split('/')
    model_name = parts[7]
    
    print(f"The selected model is: {args.model_path}")
    
    main(args.dataset_dir, args.output_dir, args.model_path, model_name, args.cuda_device)
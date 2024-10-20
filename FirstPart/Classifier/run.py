from __future__ import print_function 
from __future__ import division
import torch
print("PyTorch Version: ",torch.__version__)
import torchvision
print("Torchvision Version: ",torchvision.__version__)
import argparse
from src.save import *
from src.data import load_data
from src.train import train_model
from src.model import *
    
    


def main(epochs, dataset_dir, testset_dir, output_dir, device):
    print("The selected device is:", device)
    # Initialize the model for this run
    model_ft, input_size = initialize_model()
    
    # Print the model we just instantiated
    print(model_ft)
    
    # Load the data
    dataloaders_dict = load_data(dataset_dir, testset_dir, input_size)
    
    # Define the optimizer
    optimizer_ft, scheduler = define_optimizer(model_ft, device)
    
    # Define the loss function
    criterion = nn.CrossEntropyLoss()
    
    # Train and evaluate
    model, stats = train_model(model_ft, dataloaders_dict, criterion, optimizer_ft, scheduler, device, num_epochs=epochs)
    
    # Save the model
    save_model(model, output_dir)
    # Save stats
    save_stats(stats, output_dir)




if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser()

    # Add the arguments
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--device', type=str, default='cuda:1')
    parser.add_argument('--testset_dir', type=str)
    parser.add_argument('--dataset_dir', type=str)
    parser.add_argument('--output_dir', type=str)

    # Parse the arguments
    args = parser.parse_args()
    print("The selected epochs is:", args.epochs)

    main(args.epochs, args.dataset_dir, args.testset_dir, args.output_dir, args.device)

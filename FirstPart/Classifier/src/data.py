from torch.utils.data import random_split
from torchvision import datasets, transforms
import torch



class PlantVillageDataset(torch.utils.data.Dataset):
    def __init__(self, dataset, transform=None):
        self.dataset = dataset
        self.transform = transform

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        image, label = self.dataset[idx]
        if self.transform:
            image = self.transform(image)
            
        return image, label



def load_data(dataset_dir, testset_dir, input_size, batch_size=24, train_percent=0.8):
    # Define the transformations
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(input_size),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val_test': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(input_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    # Load the full training dataset
    full_train_dataset = datasets.ImageFolder(dataset_dir)

    # Determine the sizes for train and validation sets
    train_size = int(train_percent * len(full_train_dataset))
    val_size = len(full_train_dataset) - train_size
    # Split the dataset into training and validation sets
    train_dataset, val_dataset = random_split(full_train_dataset, [train_size, val_size])

    
    # Create the datasets with respective transformations
    train_dataset = PlantVillageDataset(train_dataset, transform=data_transforms['train'])
    val_dataset = PlantVillageDataset(val_dataset, transform=data_transforms['val_test'])

    # Load the test dataset
    test_dataset = datasets.ImageFolder(testset_dir, data_transforms['val_test'])

    # Create dataloaders
    dataloaders = {
        'train': torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4),
        'val': torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4),
        'test': torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    }
    
    return dataloaders
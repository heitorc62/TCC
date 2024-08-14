import torch
from torchvision import models
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler

    
def initialize_model(num_classes=39, input_size = 224):
    model_ft = None
    # Defining the model as GoogLeNet:
    print("Using pretrained model!!")
    model_ft = models.googlenet(weights='IMAGENET1K_V1')
    
    in_features = model_ft.fc.in_features
    model_ft.fc = nn.Linear(in_features, num_classes)
    
    if model_ft.aux_logits:
        in_features_aux1 = model_ft.aux1.fc2.in_features
        model_ft.aux1 = nn.Linear(in_features_aux1, num_classes)
        in_features_aux2 = model_ft.aux2.fc2.in_features
        model_ft.aux2 = nn.Linear(in_features_aux2, num_classes)
    return model_ft, input_size


def define_optimizer(model_ft, device):
    # Send the model to GPU
    model_ft = model_ft.to(device)
    params_to_update = model_ft.parameters()
    print("Params to learn:")
    for name,param in model_ft.named_parameters():
        if param.requires_grad == True:
            print("\t",name)

    # Observe that all parameters are being optimized
    optimizer_ft = optim.SGD(params_to_update, lr=0.005, momentum=0.9, weight_decay=0.0005)
    exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=10, gamma=0.1)
    return optimizer_ft, exp_lr_scheduler




"""
Paper optmization settings:
    - Solver type: Stochastic Gradient Descent,
    - Base learning rate: 0.005,
    - Learning rate policy: Step (decreases by a factor of 10 every 30/3 epochs),
    - Momentum: 0.9,
    - Weight decay: 0.0005,
    - Gamma: 0.1,
"""
from torchvision import models
from torchvision.models.vgg import VGG16_BN_Weights
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler

    
def initialize_model(num_classes=39, input_size = 224):
    model_ft = None
    # Defining the model as VGG:
    print("Using pretrained model!!")
    model_ft = models.vgg16_bn(weights=VGG16_BN_Weights.IMAGENET1K_V1)
    
    num_ftrs = model_ft.classifier[6].in_features
    model_ft.classifier[6] = nn.Linear(num_ftrs, num_classes)
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
    optimizer_ft = optim.SGD(params_to_update, lr=0.001, momentum=0.9)
    exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)
    return optimizer_ft, exp_lr_scheduler
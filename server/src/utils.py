from PIL import Image
import torch, torchvision, sys
from ultralytics import YOLO

def crop_image(image, box):
    left, top, right, bottom = box
    return image.crop((left, top, right, bottom))

def load_model(model_config, device):
    architecture = model_config['architecture']
    model_path = model_config['path']
    num_classes = model_config.get('num_classes', None)
    model = None

    if architecture in torchvision.models.__dict__:
        # Classification models
        model_class = getattr(torchvision.models, architecture)
        model = model_class(pretrained=False)
        if num_classes is not None:
            if hasattr(model, 'fc'):
                in_features = model.fc.in_features
                model.fc = torch.nn.Linear(in_features, num_classes)
            elif hasattr(model, 'classifier'):
                in_features = model.classifier[-1].in_features
                model.classifier[-1] = torch.nn.Linear(in_features, num_classes)
    elif architecture in torchvision.models.detection.__dict__:
        # Object detection models
        model_class = getattr(torchvision.models.detection, architecture)
        num_classes = model_config['num_classes']
        if architecture.startswith('retinanet'):
            model = model_class(pretrained=False, num_classes=num_classes)
        else:
            model = model_class(pretrained=False)
            if hasattr(model, 'roi_heads'):
                in_features = model.roi_heads.box_predictor.cls_score.in_features
                model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(in_features, num_classes)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.to(device)
        model.eval()
    elif architecture == 'yolov8':
        # Load YOLOv8 model
        model = YOLO(model_path)
        # No need to call model.to(device) or model.eval(), handled internally
    else:
        raise ValueError(f"Unknown architecture '{architecture}'")

    return model


def load_models(config, device):
    models = {}
    for task in config.tasks:
        model_info = config.get_model_config(task)
        models[task] = load_model(model_info, device)
    return models

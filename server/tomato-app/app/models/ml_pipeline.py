import torch, torchvision
from ultralytics import YOLO
from app.config.config import Config

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
    for task in config['tasks']:
        model_info = config['models'][task]
        models[task] = load_model(model_info, device)
    return models


def extract_yolov8_boxes(detections, class_names):
    boxes = []
    # Detections is a list; we take the first element for a single image
    detection = detections[0]
    for bbox in detection.boxes:
        score = bbox.conf.item()
        class_idx = int(bbox.cls.item())
        class_name = class_names.get(str(class_idx), 'Unknown')
        box = bbox.xyxy[0].tolist()  # [xmin, ymin, xmax, ymax]
        boxes.append({
            'box': box,
            'class_index': str(class_idx),
            'class_name': class_name,
            'score': score
        })
    return boxes

def classify_region(region, model, class_names, device, preprocess_params):
    resize_size = preprocess_params.get('resize', [224, 224])
    mean = preprocess_params.get('mean', [0.485, 0.456, 0.406])
    std = preprocess_params.get('std', [0.229, 0.224, 0.225])

    preprocess = torchvision.transforms.Compose([
        torchvision.transforms.Resize(resize_size),
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Normalize(mean=mean, std=std)
    ])
    input_tensor = preprocess(region).unsqueeze(0).to(device)
    outputs = model(input_tensor)
    _, predicted = torch.max(outputs, 1)
    class_idx = str(predicted.item())
    class_name = class_names.get(class_idx, 'Unknown')
    return {
        'class_index': class_idx,
        'class_name': class_name
    }

def process_ml_pipeline(image, models, config, device):
    result = {}
    detection_model = models['object_detection']
    detection_class_names = Config.get_class_names('object_detection')
    detection_threshold = config.get('models', {})['object_detection']['detection_threshold']

    # Run detection using YOLOv8
    detections = detection_model.predict(image, imgsz=640, conf=detection_threshold, device=device, verbose=False)

    # Extract boxes and class names from detections
    detected_objects = extract_yolov8_boxes(detections, detection_class_names)

    if not detected_objects:
        result['message'] = 'No regions detected'
    else:
        result['detected_objects'] = detected_objects

    return result


def load_new_weights(local_weights_path):
    model = YOLO(local_weights_path)  # YOLO handles reloading internally
    print(f"New YOLOv8 weights loaded from: {local_weights_path}")
    return model


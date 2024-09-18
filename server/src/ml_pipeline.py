import torch
from torchvision import transforms

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

    preprocess = transforms.Compose([
        transforms.Resize(resize_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
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
    detection_class_names = config.get_class_names('object_detection')
    detection_threshold = config.detection_threshold

    # Run detection using YOLOv8
    detections = detection_model.predict(image, imgsz=640, conf=detection_threshold, device=device, verbose=False)

    # Extract boxes and class names from detections
    detected_objects = extract_yolov8_boxes(detections, detection_class_names)

    if not detected_objects:
        result['message'] = 'No regions detected'
    else:
        result['detected_objects'] = detected_objects

    return result


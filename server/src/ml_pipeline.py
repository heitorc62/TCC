import torch
from torchvision import transforms
from src import crop_image

def extract_boxes(detections, detection_threshold, detection_class_names):
    boxes = []
    detection = detections[0]
    scores = detection['scores'].detach().cpu().numpy()
    boxes_tensor = detection['boxes'].detach().cpu()
    labels = detection['labels'].detach().cpu().numpy()
    for score, box, label in zip(scores, boxes_tensor, labels):
        if score >= detection_threshold:
            box = box.numpy().tolist()
            class_idx = str(label)
            class_name = detection_class_names.get(class_idx, 'Unknown')
            boxes.append({
                'box': box,
                'class_index': class_idx,
                'class_name': class_name,
                'score': float(score)
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
    tasks = config.tasks
    classifications = []

    if 'object_detection' in tasks:
        detection_model = models['object_detection']
        detection_class_names = config.get_class_names('object_detection')
        detection_threshold = config.detection_threshold
        input_tensor = transforms.ToTensor()(image).to(device)
        detections = detection_model([input_tensor])
        detected_objects = extract_boxes(detections, detection_threshold, detection_class_names)
        if not detected_objects:
            result['message'] = 'No regions detected'
            return result

        classification_model = models['classification']
        classification_class_names = config.get_class_names('classification')
        preprocess_params = config.get_preprocessing_params('classification')
        for idx, obj in enumerate(detected_objects):
            box = obj['box']
            region = crop_image(image, box)
            class_result = classify_region(region, classification_model, classification_class_names, device, preprocess_params)
            classifications.append({
                'region_id': idx,
                'detection': obj,
                'classification': class_result
            })
        result['classifications'] = classifications
    else:
        classification_model = models['classification']
        classification_class_names = config.get_class_names('classification')
        preprocess_params = config.get_preprocessing_params('classification')
        class_result = classify_region(image, classification_model, classification_class_names, device, preprocess_params)
        result['classification'] = class_result

    return result

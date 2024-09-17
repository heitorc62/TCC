# app.py

from flask import Flask, request, jsonify
from PIL import Image
import io, torch
from src import load_models, process_ml_pipeline, Config

app = Flask(__name__)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load configuration
config = Config('config/pipeline_config.json')

# Load models
models = load_models(config, device)

@app.route('/process_image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

    result = process_ml_pipeline(image, models, config, device)

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

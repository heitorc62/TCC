import os, json

class Config:
    SECRET_KEY = os.environ.get('SECRET')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AWS_REGION = os.environ.get('AWS_REGION')
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_DATASET_BUCKET = os.environ.get('S3_DATASET_BUCKET')
    S3_NEW_IMAGES_PATH = os.environ.get('S3_NEW_IMAGES_PATH')
    S3_DATASET_PATH = os.environ.get('S3_DATASET_PATH')
    TRAIN_PERCENTAGE = os.environ.get('TRAIN_PERCENTAGE')
    
    @staticmethod
    def init_app(app):
        # Load additional config from JSON file using from_json
        current_directory = os.path.dirname(os.path.abspath(__file__))
        config_json_path = os.path.join(current_directory, 'ml_config.json')
        if os.path.exists(config_json_path):
            with open(config_json_path) as f:
                config = json.load(f)
            app.config.update(config)
            print("Loaded additional configuration from ml_config.json")
        else:
            raise FileNotFoundError(f"Configuration file {config_json_path} not found.")


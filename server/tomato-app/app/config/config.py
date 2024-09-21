import os

class Config:
    SECRET_KEY = os.environ.get('SECRET')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AWS_REGION = os.environ.get('AWS_REGION')
    S3_BUCKET = os.environ.get('S3_BUCKET')
    
    @staticmethod
    def init_app(app):
        # Load additional config from JSON file using from_json
        config_json_path = os.path.join(app.instance_path, 'ml_config.json')
        if os.path.exists(config_json_path):
            app.config.from_json(config_json_path)
        else:
            raise FileNotFoundError(f"Configuration file {config_json_path} not found.")


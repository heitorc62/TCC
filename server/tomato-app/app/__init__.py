import torch
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_migrate import Migrate
from app.config.config import Config
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config='app.config.config.Config'):
    app = Flask(__name__, template_folder='view')
    app.config.from_object(config)
    Config.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from app.models import load_models
    # Load the device and models after the app is configured
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    app.device = device
    app.models = load_models(app.config, device)
    
    from app.controllers import routes_bp
    app.register_blueprint(routes_bp)
    
    return app





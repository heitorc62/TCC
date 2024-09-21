import torch
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_migrate import Migrate
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app(config='app.config.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    from models import load_models
    # Load the device and models after the app is configured
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    app.device = device
    app.models = load_models(app.config, device)  # Pass app.config
    
    from controllers import routes_bp
    app.register_blueprint(routes_bp)
    
    return app





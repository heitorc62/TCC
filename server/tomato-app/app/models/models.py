from app import db
from sqlalchemy import Enum
from datetime import datetime
import enum
from flask_login import UserMixin

class ImageStatus(enum.Enum):
    PENDING = 0
    IN_REVIEW = 1
    REVIEWED = 2
    INCORPORATED = 3
    
class ImageModel(db.Model):
    __tablename__ = "images"
    
    id = db.Column(db.Integer, primary_key=True)
    last_id = db.Column(db.Integer, nullable=False)
    s3_key = db.Column(db.String(80), nullable=False)
    label_s3_key = db.Column(db.String(80), nullable=False)
    status = db.Column(db.Enum(ImageStatus), nullable=False, default=ImageStatus.PENDING)
    image_metadata = db.Column(db.JSON, nullable=False, default={})
    new_images_path = db.Column(db.String(80), nullable=False)
    
    def __init__(self, new_images_path, metadata):
        self.last_id = ImageModel.get_last_image_id()
        self.new_images_path = new_images_path
        self.s3_key = self.get_image_s3_key()
        self.label_s3_key = self.get_label_s3_key()
        self.image_metadata = metadata  # Initialize the image metadata
    
    @staticmethod
    def get_last_image_id():
        last_image = ImageModel.query.order_by(ImageModel.id.desc()).first()
        return last_image.id if last_image else 0
    
    def get_image_s3_key(self):
        return f'{self.new_images_path}/images/uploaded_image_{self.last_id}.jpg'
        
    def get_label_s3_key(self):
        return f'{self.new_images_path}/labels/uploaded_image_{self.last_id}.txt'
    
    
class ReviewerModel(db.Model, UserMixin):
    __tablename__ = "reviewers"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
class AdminModel(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    

class InvitationModel(db.Model):
    __tablename__ = 'invitations'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
class TaskStatus(enum.Enum):
    PENDING = 0
    COMPLETED = 1
class TaskStatusModel(db.Model):
    __tablename__ = 'task_status'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
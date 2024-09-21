from app import db
from sqlalchemy import Enum
from datetime import datetime
import enum

class ImageStatus(enum.Enum):
    PENDING = 0
    IN_REVIEW = 1
    REVIEWED = 2
    
class ImageModel(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(80), nullable=False)
    status = db.Column(Enum(ImageStatus), nullable=False, default=ImageStatus.PENDING)
    image_metadata = db.Column(db.JSON, nullable=False, default={})
    
    @staticmethod
    def get_last_image_id():
        return ImageModel.query.order_by(ImageModel.id.desc()).first().id
    
class ReviewerModel(db.Model):
    __tablename__ = "reviewers"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    

class InvitationModel(db.Model):
    __tablename__ = 'invitations'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
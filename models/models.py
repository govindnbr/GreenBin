from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    total_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    plastic_drops = db.relationship('PlasticDrop', backref='user', lazy=True)
    redemptions = db.relationship('Redemption', backref='user', lazy=True)

class TrashBin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.String(50), unique=True, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, default=100)  # in percentage
    current_load = db.Column(db.Integer, default=0)  # in percentage
    status = db.Column(db.String(20), default='active')  # active, full, maintenance
    last_emptied = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    plastic_drops = db.relationship('PlasticDrop', backref='trash_bin', lazy=True)

class PlasticDrop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trash_bin_id = db.Column(db.Integer, db.ForeignKey('trash_bin.id'), nullable=False)
    qr_code = db.Column(db.String(100), unique=True, nullable=False)
    plastic_type = db.Column(db.String(50), default='bottle')  # bottle, container, bag
    points_earned = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=True)

class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    redemption_type = db.Column(db.String(50), nullable=False)  # coupon, gift_card, bank_transfer
    points_used = db.Column(db.Integer, nullable=False)
    value = db.Column(db.Float, nullable=False)  # monetary value
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    coupon_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    trash_bin_id = db.Column(db.Integer, db.ForeignKey('trash_bin.id'), nullable=False)
    plastic_type = db.Column(db.String(50), default='bottle')
    points_value = db.Column(db.Integer, default=10)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime)
    used_by = db.Column(db.Integer, db.ForeignKey('user.id'))

def generate_qr_code():
    """Generate a unique QR code"""
    return str(uuid.uuid4())[:8].upper()

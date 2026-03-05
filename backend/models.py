from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    activation_code = db.Column(db.String(20), unique=True)  # For initial passkey enrollment
    activated = db.Column(db.Boolean, default=False)  # True once user sets up passkey
    pwa_install_dismissed = db.Column(db.Boolean, default=False)  # True if user dismissed PWA install prompt
    email = db.Column(db.String(255))  # Optional email address for notifications
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(6))
    email_verification_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    items = db.relationship('Item', backref='added_by', lazy=True, foreign_keys='Item.added_by_user_id')
    categories = db.relationship('Category', backref='creator', lazy=True)
    settings = db.relationship('Setting', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'activated': self.activated,
            'pwa_install_dismissed': self.pwa_install_dismissed,
            'email': self.email,
            'email_verified': bool(self.email_verified),
            'created_at': self.created_at.isoformat()
        }


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    default_expiration_days = db.Column(db.Integer, default=180)  # 6 months default
    image_url = db.Column(db.String(500))  # Optional custom image URL for category
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_system = db.Column(db.Boolean, default=False)  # System categories can't be deleted

    # Relationships
    items = db.relationship('Item', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'default_expiration_days': self.default_expiration_days,
            'image_url': self.image_url,
            'created_by_user_id': self.created_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_system': self.is_system
        }


class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    qr_code = db.Column(db.String(255), unique=True, nullable=False)
    upc = db.Column(db.String(50))  # Universal Product Code (barcode)
    image_url = db.Column(db.String(500))  # URL to product image
    name = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(200))  # e.g., "Costco"
    weight = db.Column(db.Float)
    weight_unit = db.Column(db.String(20), default='lb')  # lb, oz, kg, g

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime)

    status = db.Column(db.String(20), nullable=False, default='in_freezer')  # in_freezer, consumed, thrown_out
    removed_date = db.Column(db.DateTime)

    notes = db.Column(db.Text)

    added_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'qr_code': self.qr_code,
            'upc': self.upc,
            'image_url': self.image_url,
            'name': self.name,
            'source': self.source,
            'weight': self.weight,
            'weight_unit': self.weight_unit,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'added_date': self.added_date.isoformat(),
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'status': self.status,
            'removed_date': self.removed_date.isoformat() if self.removed_date else None,
            'notes': self.notes,
            'added_by_user_id': self.added_by_user_id,
            'added_by_username': self.added_by.username if self.added_by else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    setting_name = db.Column(db.String(100), nullable=False)
    setting_value = db.Column(db.String(500))

    __table_args__ = (db.UniqueConstraint('user_id', 'setting_name', name='_user_setting_uc'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'setting_name': self.setting_name,
            'setting_value': self.setting_value
        }


class LowStockAlert(db.Model):
    __tablename__ = 'low_stock_alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    threshold = db.Column(db.Integer, nullable=False, default=2)
    enabled = db.Column(db.Boolean, default=True)
    last_sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='low_stock_alerts')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'item_name', name='_user_item_alert_uc'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'item_name': self.item_name,
            'threshold': self.threshold,
            'enabled': self.enabled,
            'last_sent_at': self.last_sent_at.isoformat() if self.last_sent_at else None,
            'created_at': self.created_at.isoformat(),
        }


def generate_qr_code():
    """Generate a unique alphanumeric code identifier (e.g., ABC123)"""
    import random
    import string

    # Generate 3 random uppercase letters + 3 random digits
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=3))
    return f"{letters}{digits}"

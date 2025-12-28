"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, User, Category, Item, Setting


@pytest.fixture
def app():
    """Create application for testing"""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'SECRET_KEY': 'test-secret-key',
    }
    flask_app = create_app(test_config=test_config)

    # Create tables
    with flask_app.app_context():
        db.create_all()

        # Create default admin user
        admin = User(
            username='admin',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Create default regular user
        user = User(
            username='testuser',
            role='user'
        )
        user.set_password('test123')
        db.session.add(user)

        # Create default categories
        categories = [
            Category(name='Beef', default_expiration_days=365),
            Category(name='Chicken', default_expiration_days=270),
            Category(name='Pork', default_expiration_days=180),
            Category(name='Fish', default_expiration_days=180),
        ]
        for category in categories:
            db.session.add(category)

        db.session.commit()

        yield flask_app

        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def admin_token(client):
    """Get JWT token for admin user"""
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    return response.json['access_token']


@pytest.fixture
def user_token(client):
    """Get JWT token for regular user"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'test123'
    })
    return response.json['access_token']


@pytest.fixture
def auth_headers_admin(admin_token):
    """Get authorization headers for admin"""
    return {'Authorization': f'Bearer {admin_token}'}


@pytest.fixture
def auth_headers_user(user_token):
    """Get authorization headers for regular user"""
    return {'Authorization': f'Bearer {user_token}'}


@pytest.fixture
def sample_item(app, auth_headers_admin, client):
    """Create a sample item for testing"""
    with app.app_context():
        response = client.post('/api/items/',
            json={
                'name': 'Test Ribeye Steak',
                'source': 'Test Store',
                'weight': 2.5,
                'weight_unit': 'lb',
                'category_id': 1,
                'notes': 'Test notes'
            },
            headers=auth_headers_admin
        )
        return response.json

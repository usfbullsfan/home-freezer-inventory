"""
Tests for authentication endpoints
"""
import pytest


def test_login_success(client):
    """Test successful login"""
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })

    assert response.status_code == 200
    assert 'access_token' in response.json
    assert 'user' in response.json
    assert response.json['user']['username'] == 'admin'
    assert response.json['user']['role'] == 'admin'


def test_login_invalid_username(client):
    """Test login with invalid username"""
    response = client.post('/api/auth/login', json={
        'username': 'nonexistent',
        'password': 'password123'
    })

    assert response.status_code == 401
    assert 'error' in response.json


def test_login_invalid_password(client):
    """Test login with invalid password"""
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'wrongpassword'
    })

    assert response.status_code == 401
    assert 'error' in response.json


def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.post('/api/auth/login', json={
        'username': 'admin'
    })

    assert response.status_code == 400


def test_protected_route_without_token(client):
    """Test accessing protected route without token"""
    response = client.get('/api/items/')

    assert response.status_code == 401


def test_protected_route_with_token(client, auth_headers_admin):
    """Test accessing protected route with valid token"""
    response = client.get('/api/items/', headers=auth_headers_admin)

    assert response.status_code == 200


def test_change_password_success(client, auth_headers_admin):
    """Test successful password change"""
    response = client.post('/api/auth/change-password',
        json={
            'current_password': 'admin123',
            'new_password': 'newpassword123'
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 200
    assert 'message' in response.json

    # Try logging in with new password
    login_response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'newpassword123'
    })

    assert login_response.status_code == 200


def test_change_password_wrong_current(client, auth_headers_admin):
    """Test password change with wrong current password"""
    response = client.post('/api/auth/change-password',
        json={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 401
    assert 'error' in response.json

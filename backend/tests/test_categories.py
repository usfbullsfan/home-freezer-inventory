"""
Tests for categories endpoints
"""
import pytest


def test_get_categories(client, auth_headers_admin):
    """Test getting all categories"""
    response = client.get('/api/categories/', headers=auth_headers_admin)

    assert response.status_code == 200
    assert len(response.json) == 4  # Default categories from fixture
    assert response.json[0]['name'] == 'Beef'
    assert response.json[0]['default_expiration_days'] == 365


def test_create_category(client, auth_headers_admin):
    """Test creating a new category"""
    response = client.post('/api/categories/',
        json={
            'name': 'Seafood',
            'default_expiration_days': 120
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 201
    assert response.json['name'] == 'Seafood'
    assert response.json['default_expiration_days'] == 120


def test_create_category_missing_name(client, auth_headers_admin):
    """Test creating category without name"""
    response = client.post('/api/categories/',
        json={
            'default_expiration_days': 180
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 400


def test_update_category(client, auth_headers_admin):
    """Test updating a category"""
    response = client.put('/api/categories/1',
        json={
            'name': 'Grass-Fed Beef',
            'default_expiration_days': 400
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 200
    assert response.json['name'] == 'Grass-Fed Beef'
    assert response.json['default_expiration_days'] == 400


def test_delete_category_as_admin(client, auth_headers_admin):
    """Test deleting category as admin"""
    response = client.delete('/api/categories/1', headers=auth_headers_admin)

    assert response.status_code == 200


def test_delete_category_as_user(client, auth_headers_user):
    """Test deleting category as regular user (should fail)"""
    response = client.delete('/api/categories/1', headers=auth_headers_user)

    assert response.status_code == 403

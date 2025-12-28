"""
Tests for items endpoints
"""
import pytest
from datetime import datetime, timedelta


def test_get_items_empty(client, auth_headers_admin):
    """Test getting items when database is empty"""
    response = client.get('/api/items/', headers=auth_headers_admin)

    assert response.status_code == 200
    assert response.json == []


def test_create_item_success(client, auth_headers_admin):
    """Test successful item creation"""
    response = client.post('/api/items/',
        json={
            'name': 'Prime Ribeye Steak',
            'source': 'Costco',
            'weight': 2.5,
            'weight_unit': 'lb',
            'category_id': 1,
            'notes': 'Premium cut'
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 201
    assert response.json['name'] == 'Prime Ribeye Steak'
    assert response.json['source'] == 'Costco'
    assert response.json['weight'] == 2.5
    assert response.json['status'] == 'in_freezer'
    assert 'qr_code' in response.json
    # Verify new format: 3 letters + 3 digits (e.g., ABC123)
    qr_code = response.json['qr_code']
    assert len(qr_code) == 6
    assert qr_code[:3].isalpha() and qr_code[:3].isupper()
    assert qr_code[3:].isdigit()


def test_create_item_with_custom_qr_code(client, auth_headers_admin):
    """Test creating item with custom QR code"""
    response = client.post('/api/items/',
        json={
            'name': 'Test Item',
            'qr_code': 'CUSTOM-123'
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 201
    assert response.json['qr_code'] == 'CUSTOM-123'


def test_create_item_duplicate_qr_code(client, auth_headers_admin):
    """Test creating item with duplicate QR code"""
    # Create first item
    client.post('/api/items/',
        json={
            'name': 'Item 1',
            'qr_code': 'DUPLICATE-123'
        },
        headers=auth_headers_admin
    )

    # Try to create second item with same QR code
    response = client.post('/api/items/',
        json={
            'name': 'Item 2',
            'qr_code': 'DUPLICATE-123'
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 400
    assert 'error' in response.json


def test_create_item_with_custom_added_date(client, auth_headers_admin):
    """Test creating item with custom added date"""
    custom_date = (datetime.utcnow() - timedelta(days=30)).date().isoformat()

    response = client.post('/api/items/',
        json={
            'name': 'Old Item',
            'added_date': custom_date
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 201
    assert custom_date in response.json['added_date']


def test_create_item_missing_name(client, auth_headers_admin):
    """Test creating item without name"""
    response = client.post('/api/items/',
        json={
            'source': 'Test Store'
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 400


def test_get_items_after_creation(client, auth_headers_admin, sample_item):
    """Test getting items after creating one"""
    response = client.get('/api/items/', headers=auth_headers_admin)

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['name'] == 'Test Ribeye Steak'


def test_get_item_by_id(client, auth_headers_admin, sample_item):
    """Test getting a specific item by ID"""
    item_id = sample_item['id']
    response = client.get(f'/api/items/{item_id}', headers=auth_headers_admin)

    assert response.status_code == 200
    assert response.json['id'] == item_id
    assert response.json['name'] == 'Test Ribeye Steak'


def test_get_item_by_qr_code(client, auth_headers_admin, sample_item):
    """Test getting item by QR code"""
    qr_code = sample_item['qr_code']
    response = client.get(f'/api/items/qr/{qr_code}', headers=auth_headers_admin)

    assert response.status_code == 200
    assert response.json['qr_code'] == qr_code


def test_get_item_not_found(client, auth_headers_admin):
    """Test getting non-existent item"""
    response = client.get('/api/items/9999', headers=auth_headers_admin)

    assert response.status_code == 404


def test_update_item(client, auth_headers_admin, sample_item):
    """Test updating an item"""
    item_id = sample_item['id']
    response = client.put(f'/api/items/{item_id}',
        json={
            'name': 'Updated Ribeye Steak',
            'weight': 3.0
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 200
    assert response.json['name'] == 'Updated Ribeye Steak'
    assert response.json['weight'] == 3.0


def test_update_item_status_consumed(client, auth_headers_admin, sample_item):
    """Test marking item as consumed"""
    item_id = sample_item['id']
    response = client.put(f'/api/items/{item_id}/status',
        json={'status': 'consumed'},
        headers=auth_headers_admin
    )

    assert response.status_code == 200
    assert response.json['status'] == 'consumed'
    assert response.json['removed_date'] is not None


def test_update_item_status_invalid(client, auth_headers_admin, sample_item):
    """Test updating item with invalid status"""
    item_id = sample_item['id']
    response = client.put(f'/api/items/{item_id}/status',
        json={'status': 'invalid_status'},
        headers=auth_headers_admin
    )

    assert response.status_code == 400


def test_delete_item_as_admin(client, auth_headers_admin, sample_item):
    """Test deleting item as admin"""
    item_id = sample_item['id']
    response = client.delete(f'/api/items/{item_id}', headers=auth_headers_admin)

    assert response.status_code == 200

    # Verify item is deleted
    get_response = client.get(f'/api/items/{item_id}', headers=auth_headers_admin)
    assert get_response.status_code == 404


def test_delete_item_as_user(client, auth_headers_user, sample_item):
    """Test deleting item as regular user (should fail)"""
    item_id = sample_item['id']
    response = client.delete(f'/api/items/{item_id}', headers=auth_headers_user)

    assert response.status_code == 403


def test_search_items(client, auth_headers_admin):
    """Test searching items"""
    # Create multiple items
    client.post('/api/items/',
        json={'name': 'Ribeye Steak', 'source': 'Costco'},
        headers=auth_headers_admin
    )
    client.post('/api/items/',
        json={'name': 'Chicken Breast', 'source': 'Walmart'},
        headers=auth_headers_admin
    )

    # Search for "ribeye"
    response = client.get('/api/items/?search=ribeye', headers=auth_headers_admin)

    assert response.status_code == 200
    assert len(response.json) == 1
    assert 'Ribeye' in response.json[0]['name']


def test_filter_items_by_category(client, auth_headers_admin):
    """Test filtering items by category"""
    # Create items in different categories
    client.post('/api/items/',
        json={'name': 'Ribeye', 'category_id': 1},
        headers=auth_headers_admin
    )
    client.post('/api/items/',
        json={'name': 'Chicken', 'category_id': 2},
        headers=auth_headers_admin
    )

    # Filter by category 1 (Beef)
    response = client.get('/api/items/?category_id=1', headers=auth_headers_admin)

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['category_id'] == 1


def test_filter_items_by_status(client, auth_headers_admin):
    """Test filtering items by status"""
    # Create item and mark as consumed
    item_response = client.post('/api/items/',
        json={'name': 'Test Item'},
        headers=auth_headers_admin
    )
    item_id = item_response.json['id']

    client.put(f'/api/items/{item_id}/status',
        json={'status': 'consumed'},
        headers=auth_headers_admin
    )

    # Filter for consumed items
    response = client.get('/api/items/?status=consumed', headers=auth_headers_admin)

    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['status'] == 'consumed'

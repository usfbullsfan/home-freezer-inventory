"""
Tests for settings endpoints
"""
import pytest


def test_get_user_settings(client, auth_headers_admin):
    """Test getting user settings"""
    response = client.get('/api/settings/', headers=auth_headers_admin)

    assert response.status_code == 200
    assert isinstance(response.json, dict)
    # Should have default track_history setting
    assert 'track_history' in response.json
    assert response.json['track_history'] == 'true'


def test_update_user_settings(client, auth_headers_admin):
    """Test updating user settings"""
    response = client.put('/api/settings/',
        json={
            'track_history': 'false'
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 200
    assert 'message' in response.json

    # Verify settings were updated
    get_response = client.get('/api/settings/', headers=auth_headers_admin)
    assert get_response.json['track_history'] == 'false'


def test_get_system_settings_as_admin(client, auth_headers_admin):
    """Test getting system settings as admin"""
    response = client.get('/api/settings/system', headers=auth_headers_admin)

    assert response.status_code == 200
    assert isinstance(response.json, dict)
    # Should have default enable_image_fetching setting
    assert 'enable_image_fetching' in response.json
    assert response.json['enable_image_fetching'] == 'true'


def test_get_system_settings_as_user(client, auth_headers_user):
    """Test getting system settings as regular user (should fail)"""
    response = client.get('/api/settings/system', headers=auth_headers_user)

    assert response.status_code == 403
    assert 'error' in response.json


def test_update_system_settings_as_admin(client, auth_headers_admin):
    """Test updating system settings as admin"""
    response = client.put('/api/settings/system',
        json={
            'enable_image_fetching': 'false'
        },
        headers=auth_headers_admin
    )

    assert response.status_code == 200
    assert 'message' in response.json

    # Verify settings were updated
    get_response = client.get('/api/settings/system', headers=auth_headers_admin)
    assert get_response.json['enable_image_fetching'] == 'false'


def test_update_system_settings_as_user(client, auth_headers_user):
    """Test updating system settings as regular user (should fail)"""
    response = client.put('/api/settings/system',
        json={
            'enable_image_fetching': 'false'
        },
        headers=auth_headers_user
    )

    assert response.status_code == 403
    assert 'error' in response.json


def test_update_settings_no_data(client, auth_headers_admin):
    """Test updating settings with no data"""
    response = client.put('/api/settings/',
        json={},
        headers=auth_headers_admin
    )

    assert response.status_code == 400
    assert 'error' in response.json


def test_purge_history_as_admin(client, auth_headers_admin):
    """Test purging history as admin"""
    # Create and consume an item
    item_response = client.post('/api/items/',
        json={'name': 'Test Item'},
        headers=auth_headers_admin
    )
    item_id = item_response.json['id']

    client.put(f'/api/items/{item_id}/status',
        json={'status': 'consumed'},
        headers=auth_headers_admin
    )

    # Purge history
    response = client.post('/api/settings/purge-history', headers=auth_headers_admin)

    assert response.status_code == 200
    assert 'message' in response.json
    assert '1' in response.json['message']  # Should have purged 1 item


def test_purge_history_as_user(client, auth_headers_user):
    """Test purging history as regular user (should fail)"""
    response = client.post('/api/settings/purge-history', headers=auth_headers_user)

    assert response.status_code == 403
    assert 'error' in response.json


def test_get_backup_info_as_admin(client, auth_headers_admin):
    """Test getting backup info as admin"""
    response = client.get('/api/settings/backup/info', headers=auth_headers_admin)

    assert response.status_code == 200
    assert 'file_size' in response.json
    assert 'last_modified' in response.json
    assert 'total_items' in response.json
    assert 'active_items' in response.json
    assert 'total_categories' in response.json
    assert 'total_users' in response.json


def test_get_backup_info_as_user(client, auth_headers_user):
    """Test getting backup info as regular user (should fail)"""
    response = client.get('/api/settings/backup/info', headers=auth_headers_user)

    assert response.status_code == 403
    assert 'error' in response.json


def test_download_backup_as_admin(client, auth_headers_admin):
    """Test downloading backup as admin"""
    response = client.get('/api/settings/backup/download', headers=auth_headers_admin)

    # Should return a file
    assert response.status_code == 200
    assert response.content_type == 'application/x-sqlite3'


def test_download_backup_as_user(client, auth_headers_user):
    """Test downloading backup as regular user (should fail)"""
    response = client.get('/api/settings/backup/download', headers=auth_headers_user)

    assert response.status_code == 403

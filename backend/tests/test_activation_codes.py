"""
Tests for activation code generation and normalized lookup.

These build their own admin token with create_access_token rather than going
through the shared login fixtures in conftest.py.
"""
import sqlite3
from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from models import db, User
from utils.activation_codes import (
    ACTIVATION_CODE_ALPHABET,
    ACTIVATION_CODE_LENGTH,
    generate_activation_code,
    normalize_activation_code,
    codes_match,
)

AMBIGUOUS = set('0O1IL')
NOT_RECOGNISED = "That code wasn't recognised"


@pytest.fixture
def admin_headers(app):
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        token = create_access_token(
            identity=str(admin.id),
            expires_delta=timedelta(hours=1),
            additional_claims={'role': 'admin', 'username': 'admin'},
        )
    return {'Authorization': f'Bearer {token}'}


def _add_pending_user(app, username, code):
    with app.app_context():
        user = User(username=username, role='user', activation_code=code, activated=False)
        user.set_password('unused-placeholder')
        db.session.add(user)
        db.session.commit()
        return user.id


# --- Generation -----------------------------------------------------------

class TestGeneration:
    def test_alphabet_has_no_ambiguous_characters(self):
        assert not AMBIGUOUS & set(ACTIVATION_CODE_ALPHABET)
        assert len(set(ACTIVATION_CODE_ALPHABET)) == len(ACTIVATION_CODE_ALPHABET)

    def test_generated_codes_use_alphabet_and_length(self):
        for _ in range(500):
            code = generate_activation_code()
            assert len(code) == ACTIVATION_CODE_LENGTH == 8
            assert set(code) <= set(ACTIVATION_CODE_ALPHABET)

    def test_register_returns_unambiguous_code(self, app, client, admin_headers):
        response = client.post('/api/auth/register', json={'username': 'newbie'},
                               headers=admin_headers)
        assert response.status_code == 201
        code = response.json['activation_code']
        assert len(code) == 8
        assert set(code) <= set(ACTIVATION_CODE_ALPHABET)

    def test_regenerate_returns_unambiguous_code(self, app, client, admin_headers, monkeypatch):
        # The endpoint deletes passkeys through its own raw sqlite3 connection,
        # which for an in-memory test DB is a separate, empty database. Give it
        # one with the tables it expects.
        real_connect = sqlite3.connect

        def connect_with_tables(*args, **kwargs):
            conn = real_connect(':memory:')
            conn.execute('CREATE TABLE passkey_credentials (user_id INTEGER)')
            conn.execute('CREATE TABLE recovery_codes (user_id INTEGER)')
            return conn

        monkeypatch.setattr(sqlite3, 'connect', connect_with_tables)
        user_id = _add_pending_user(app, 'regen', 'OLDCODE1')
        response = client.post(f'/api/auth/users/{user_id}/regenerate-activation',
                               headers=admin_headers)
        assert response.status_code == 200
        code = response.json['activation_code']
        assert len(code) == 8
        assert set(code) <= set(ACTIVATION_CODE_ALPHABET)


# --- Normalization helpers ------------------------------------------------

class TestNormalization:
    @pytest.mark.parametrize('raw', ['abcd-efgh', ' ABCD EFGH ', 'abcdefgh', 'AbCd - eFgH', 'ABCD\tEFGH'])
    def test_normalize(self, raw):
        assert normalize_activation_code(raw) == 'ABCDEFGH'

    def test_normalize_non_string(self):
        assert normalize_activation_code(None) == ''
        assert normalize_activation_code(12345678) == ''

    def test_codes_match_tolerates_lookalikes(self):
        assert codes_match('9F0GVQ2M', '9FOGVQ2M')
        assert codes_match('A1B2C3D4', 'AIB2C3D4')
        assert codes_match('ALB2C3D4', 'A1B2C3D4')
        assert not codes_match('9F0GVQ2N', '9FOGVQ2M')
        assert not codes_match('', 'ABCDEFGH')


# --- /api/auth/activate ---------------------------------------------------

class TestActivateLookup:
    CODE = 'HJKM2345'

    @pytest.mark.parametrize('entered', [
        'hjkm2345',       # lowercase
        'HJKM-2345',      # hyphen, as displayed
        'hjkm-2345',
        'HJKM 2345',      # space
        '  HJKM2345  ',   # surrounding whitespace
    ])
    def test_normalized_input_activates(self, app, client, entered):
        _add_pending_user(app, 'pending', self.CODE)
        response = client.post('/api/auth/activate', json={'activation_code': entered})
        assert response.status_code == 200, response.json
        assert response.json['user']['username'] == 'pending'
        with app.app_context():
            user = User.query.filter_by(username='pending').first()
            assert user.activated is True
            assert user.activation_code is None

    def test_legacy_code_with_letter_o_accepts_zero(self, app, client):
        # The code from the migration incident: O easily read as zero.
        _add_pending_user(app, 'legacy', '9FOGVQ2M')
        response = client.post('/api/auth/activate', json={'activation_code': '9f0g-vq2m'})
        assert response.status_code == 200, response.json

    def test_legacy_code_exact_still_works(self, app, client):
        _add_pending_user(app, 'legacy', 'A1B0CILD')
        response = client.post('/api/auth/activate', json={'activation_code': 'a1b0cild'})
        assert response.status_code == 200, response.json

    def test_wrong_code_gets_helpful_message(self, app, client):
        _add_pending_user(app, 'pending', self.CODE)
        response = client.post('/api/auth/activate', json={'activation_code': 'ZZZZ-ZZZZ'})
        assert response.status_code == 401
        assert NOT_RECOGNISED in response.json['error']

    def test_used_code_gets_same_message(self, app, client):
        _add_pending_user(app, 'pending', self.CODE)
        first = client.post('/api/auth/activate', json={'activation_code': self.CODE})
        assert first.status_code == 200
        again = client.post('/api/auth/activate', json={'activation_code': self.CODE})
        wrong = client.post('/api/auth/activate', json={'activation_code': 'ZZZZZZZZ'})
        assert again.status_code == wrong.status_code == 401
        assert again.json['error'] == wrong.json['error']

    def test_separators_only_is_rejected(self, app, client):
        response = client.post('/api/auth/activate', json={'activation_code': ' - - '})
        assert response.status_code == 401
        assert NOT_RECOGNISED in response.json['error']

    def test_missing_code_is_400(self, client):
        response = client.post('/api/auth/activate', json={})
        assert response.status_code == 400

    def test_ambiguous_fallback_with_two_candidates_is_rejected(self, app, client):
        # Two legacy codes that differ only in look-alike characters: an
        # input matching neither exactly must not pick one arbitrarily.
        _add_pending_user(app, 'one', 'ABCDOOO1')
        _add_pending_user(app, 'two', 'ABCD000I')
        response = client.post('/api/auth/activate', json={'activation_code': 'ABCD0O0L'})
        assert response.status_code == 401
        # Exact matches still resolve to the right user.
        response = client.post('/api/auth/activate', json={'activation_code': 'abcd000i'})
        assert response.status_code == 200
        assert response.json['user']['username'] == 'two'

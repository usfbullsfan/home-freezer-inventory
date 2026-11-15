"""
Tests for the passkey (WebAuthn) routes' database handling.

The WebAuthn verification functions are monkeypatched: these tests cover how
challenges, credentials and recovery codes are stored and consumed, not the
cryptography. Tokens are built with create_access_token rather than the shared
login fixtures in conftest.py.
"""
import base64
import hashlib
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from flask_jwt_extended import create_access_token

import routes.passkey as passkey_routes
from models import db, User, PasskeyChallenge, PasskeyCredential, RecoveryCode


def _user_id(app, username='testuser'):
    with app.app_context():
        return User.query.filter_by(username=username).first().id


def _headers(app, username='testuser'):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1),
            additional_claims={'role': user.role, 'username': user.username},
        )
    return {'Authorization': f'Bearer {token}'}


def _add_credential(app, user_id, cred_bytes=b'cred-1', sign_count=0, name='Laptop'):
    with app.app_context():
        db.session.add(PasskeyCredential(
            user_id=user_id, credential_id=cred_bytes.hex(), public_key=b'pk'.hex(),
            sign_count=sign_count, name=name,
        ))
        db.session.commit()


def _b64url(raw):
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def test_create_all_creates_passkey_tables(app):
    with app.app_context():
        tables = set(db.inspect(db.engine).get_table_names())
    assert {'passkey_challenges', 'passkey_credentials', 'recovery_codes'} <= tables


# --- Registration ---------------------------------------------------------

class TestRegistration:
    def test_begin_stores_challenge_and_excludes_existing(self, app, client):
        uid = _user_id(app)
        _add_credential(app, uid, b'existing')

        response = client.post('/api/passkey/register/begin', json={'username': 'testuser'})
        assert response.status_code == 200
        assert _b64url(b'existing') in response.json['options']

        with app.app_context():
            row = db.session.get(PasskeyChallenge, response.json['challengeId'])
            assert row.user_id == uid
            assert row.expires_at > datetime.now()

    def test_begin_unknown_user(self, client):
        response = client.post('/api/passkey/register/begin', json={'username': 'nobody'})
        assert response.status_code == 404

    def test_complete_stores_credential_and_consumes_challenge(self, app, client, monkeypatch):
        seen = {}

        def fake_verify(**kwargs):
            seen.update(kwargs)
            return SimpleNamespace(credential_id=b'new-cred', credential_public_key=b'new-pk',
                                   sign_count=3)

        monkeypatch.setattr(passkey_routes, 'verify_registration_response', fake_verify)
        begin = client.post('/api/passkey/register/begin', json={'username': 'testuser'})
        challenge_id = begin.json['challengeId']

        response = client.post('/api/passkey/register/complete', json={
            'credential': {'id': 'x'}, 'challengeId': challenge_id, 'name': 'Phone'})
        assert response.status_code == 200
        assert response.json['credentialId'] == b'new-cred'.hex()

        with app.app_context():
            assert db.session.get(PasskeyChallenge, challenge_id) is None
            stored = PasskeyCredential.query.filter_by(credential_id=b'new-cred'.hex()).one()
            assert stored.user_id == _user_id(app)
            assert stored.public_key == b'new-pk'.hex()
            assert stored.sign_count == 3
            assert stored.name == 'Phone'
            assert stored.created_at is not None
        assert len(seen['expected_challenge']) == 32

        # Challenge is single-use
        again = client.post('/api/passkey/register/complete', json={
            'credential': {'id': 'x'}, 'challengeId': challenge_id})
        assert again.status_code == 400
        assert again.json['error'] == 'Invalid challenge'

    def test_complete_rejects_expired_challenge(self, app, client):
        with app.app_context():
            row = PasskeyChallenge(challenge='00' * 32, user_id=_user_id(app),
                                   expires_at=datetime.now() - timedelta(seconds=1))
            db.session.add(row)
            db.session.commit()
            challenge_id = row.id

        response = client.post('/api/passkey/register/complete', json={
            'credential': {'id': 'x'}, 'challengeId': challenge_id})
        assert response.status_code == 400
        assert response.json['error'] == 'Challenge expired'
        with app.app_context():
            assert db.session.get(PasskeyChallenge, challenge_id) is None

    def test_complete_verification_failure_stores_nothing(self, app, client, monkeypatch):
        def fail(**kwargs):
            raise ValueError('bad attestation')

        monkeypatch.setattr(passkey_routes, 'verify_registration_response', fail)
        begin = client.post('/api/passkey/register/begin', json={'username': 'testuser'})
        response = client.post('/api/passkey/register/complete', json={
            'credential': {'id': 'x'}, 'challengeId': begin.json['challengeId']})
        assert response.status_code == 400
        with app.app_context():
            assert PasskeyCredential.query.count() == 0


# --- Login ----------------------------------------------------------------

class TestLogin:
    def test_begin_allows_users_credentials(self, app, client):
        _add_credential(app, _user_id(app), b'mine')
        response = client.post('/api/passkey/login/begin', json={'username': 'testuser'})
        assert response.status_code == 200
        assert _b64url(b'mine') in response.json['options']
        with app.app_context():
            row = db.session.get(PasskeyChallenge, response.json['challengeId'])
            assert row.username == 'testuser'
            assert row.user_id is None

    def test_begin_without_username(self, client):
        response = client.post('/api/passkey/login/begin', json={})
        assert response.status_code == 200
        assert 'challengeId' in response.json

    def test_complete_issues_token_and_updates_sign_count(self, app, client, monkeypatch):
        uid = _user_id(app)
        _add_credential(app, uid, b'cred-1', sign_count=5)
        seen = {}

        def fake_verify(**kwargs):
            seen.update(kwargs)
            return SimpleNamespace(new_sign_count=6)

        monkeypatch.setattr(passkey_routes, 'verify_authentication_response', fake_verify)
        begin = client.post('/api/passkey/login/begin', json={'username': 'testuser'})

        response = client.post('/api/passkey/login/complete', json={
            'credential': {'id': _b64url(b'cred-1')}, 'challengeId': begin.json['challengeId']})
        assert response.status_code == 200
        assert response.json['user'] == {'id': uid, 'username': 'testuser', 'role': 'user'}
        assert response.json['token']
        assert seen['credential_public_key'] == b'pk'
        assert seen['credential_current_sign_count'] == 5

        with app.app_context():
            stored = PasskeyCredential.query.filter_by(credential_id=b'cred-1'.hex()).one()
            assert stored.sign_count == 6
            assert stored.last_used_at is not None

    def test_complete_unknown_credential(self, client):
        begin = client.post('/api/passkey/login/begin', json={})
        response = client.post('/api/passkey/login/complete', json={
            'credential': {'id': _b64url(b'nope')}, 'challengeId': begin.json['challengeId']})
        assert response.status_code == 404

    def test_reads_legacy_iso_text_timestamps(self, app, client, monkeypatch):
        # Rows written by the old raw-sqlite3 code stored datetime.isoformat()
        # strings ('T' separator) in these columns.
        uid = _user_id(app)
        _add_credential(app, uid, b'legacy')
        expires = (datetime.now() + timedelta(minutes=5)).isoformat()
        with app.app_context():
            db.session.execute(db.text(
                "INSERT INTO passkey_challenges (id, challenge, username, expires_at) "
                "VALUES (999, :c, 'testuser', :e)"), {'c': '00' * 32, 'e': expires})
            db.session.commit()

        monkeypatch.setattr(passkey_routes, 'verify_authentication_response',
                            lambda **kw: SimpleNamespace(new_sign_count=1))
        response = client.post('/api/passkey/login/complete', json={
            'credential': {'id': _b64url(b'legacy')}, 'challengeId': 999})
        assert response.status_code == 200


# --- Recovery codes -------------------------------------------------------

class TestRecoveryCodes:
    def test_generate_and_use_once(self, app, client):
        response = client.post('/api/passkey/recovery/generate', headers=_headers(app))
        assert response.status_code == 200
        codes = response.json['codes']
        assert len(codes) == 8

        with app.app_context():
            rows = RecoveryCode.query.filter_by(user_id=_user_id(app)).all()
            assert len(rows) == 8
            assert {r.code_hash for r in rows} == {
                hashlib.sha256(c.encode()).hexdigest() for c in codes}
            assert not any(r.used for r in rows)

        use = client.post('/api/passkey/recovery/use',
                          json={'username': 'testuser', 'code': codes[0]})
        assert use.status_code == 200
        assert use.json['temporaryToken']

        with app.app_context():
            row = RecoveryCode.query.filter_by(
                code_hash=hashlib.sha256(codes[0].encode()).hexdigest()).one()
            assert row.used is True
            assert row.used_at is not None

        reuse = client.post('/api/passkey/recovery/use',
                            json={'username': 'testuser', 'code': codes[0]})
        assert reuse.status_code == 401

    def test_code_for_other_user_rejected(self, app, client):
        codes = client.post('/api/passkey/recovery/generate', headers=_headers(app)).json['codes']
        response = client.post('/api/passkey/recovery/use',
                               json={'username': 'admin', 'code': codes[0]})
        assert response.status_code == 401


# --- Management -----------------------------------------------------------

class TestManagement:
    def test_list_only_own_passkeys(self, app, client):
        _add_credential(app, _user_id(app), b'mine', name=None)
        _add_credential(app, _user_id(app, 'admin'), b'theirs')

        response = client.get('/api/passkey/list', headers=_headers(app))
        assert response.status_code == 200
        passkeys = response.json['passkeys']
        assert len(passkeys) == 1
        assert passkeys[0]['name'] == 'Passkey'
        datetime.fromisoformat(passkeys[0]['created_at'])
        assert passkeys[0]['last_used_at'] is None

    def test_delete_own_passkey(self, app, client):
        _add_credential(app, _user_id(app), b'mine')
        with app.app_context():
            pk_id = PasskeyCredential.query.one().id
        response = client.delete(f'/api/passkey/delete/{pk_id}', headers=_headers(app))
        assert response.status_code == 200
        with app.app_context():
            assert PasskeyCredential.query.count() == 0

    def test_cannot_delete_other_users_passkey(self, app, client):
        _add_credential(app, _user_id(app, 'admin'), b'theirs')
        with app.app_context():
            pk_id = PasskeyCredential.query.one().id
        response = client.delete(f'/api/passkey/delete/{pk_id}', headers=_headers(app))
        assert response.status_code == 404
        with app.app_context():
            assert PasskeyCredential.query.count() == 1

    def test_deleting_user_removes_passkey_data(self, app, client):
        uid = _user_id(app)
        _add_credential(app, uid, b'mine')
        with app.app_context():
            db.session.add(RecoveryCode(user_id=uid, code_hash='h'))
            db.session.add(PasskeyChallenge(challenge='00', user_id=uid,
                                            expires_at=datetime.now()))
            db.session.commit()

        response = client.delete(f'/api/auth/users/{uid}', headers=_headers(app, 'admin'))
        assert response.status_code == 200
        with app.app_context():
            assert PasskeyCredential.query.count() == 0
            assert RecoveryCode.query.count() == 0
            assert PasskeyChallenge.query.count() == 0

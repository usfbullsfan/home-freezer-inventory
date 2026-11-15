"""
Passkey Authentication Routes
WebAuthn-based passwordless authentication
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json
)
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from models import db, User, PasskeyChallenge, PasskeyCredential, RecoveryCode
import os
from utils.domains import get_rp_id, origin_for_request_url

passkey_bp = Blueprint('passkey', __name__)

# Configuration (hostnames come from utils/domains.py / environment)
RP_ID = get_rp_id()
RP_NAME = "Freezer Inventory Tracker"

def get_expected_origin():
    """Get expected origin based on environment

    Uses the Origin header from the browser to determine if this is a dev or prod request.
    The Origin header contains the actual URL the user is accessing (e.g., https://<APP_DOMAIN>)
    """
    origin = request.headers.get('Origin', '')
    referer = request.headers.get('Referer', '')

    # Use Origin header first (sent with CORS requests), fall back to Referer
    return origin_for_request_url(origin or referer)

CHALLENGE_TTL = timedelta(minutes=5)


def _store_challenge(challenge, user_id=None, username=None):
    """Persist a challenge and return its id."""
    row = PasskeyChallenge(
        challenge=challenge.hex(),
        user_id=user_id,
        username=username,
        expires_at=datetime.now() + CHALLENGE_TTL,
    )
    db.session.add(row)
    db.session.commit()
    return row.id


def _consume_challenge(challenge_id):
    """Delete a challenge (single-use) and return it.

    Returns (challenge_row, error_response). Exactly one is not None.
    """
    row = db.session.get(PasskeyChallenge, challenge_id)
    if not row:
        return None, (jsonify({'error': 'Invalid challenge'}), 400)

    db.session.delete(row)
    db.session.commit()

    if row.expires_at < datetime.now():
        return None, (jsonify({'error': 'Challenge expired'}), 400)
    return row, None


def _credential_descriptors(user_id):
    creds = PasskeyCredential.query.filter_by(user_id=user_id).all()
    return [PublicKeyCredentialDescriptor(id=bytes.fromhex(c.credential_id)) for c in creds]

# ==================== REGISTRATION ====================

@passkey_bp.route('/register/begin', methods=['POST'])
def register_begin():
    """
    Start passkey registration
    Input: { username }
    Output: WebAuthn registration options
    """
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username required'}), 400

    # Check if user exists
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate challenge
    challenge = secrets.token_bytes(32)

    # Store challenge temporarily
    challenge_id = _store_challenge(challenge, user_id=user.id)

    # Get existing credentials to exclude
    exclude_credentials = _credential_descriptors(user.id)

    # Generate registration options
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(user.id).encode(),
        user_name=username,
        user_display_name=username,
        challenge=challenge,
        exclude_credentials=exclude_credentials if exclude_credentials else None,
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED
        )
    )

    return jsonify({
        'options': options_to_json(options),
        'challengeId': challenge_id
    })


@passkey_bp.route('/register/complete', methods=['POST'])
def register_complete():
    """
    Complete passkey registration
    Input: { credential, challengeId, name }
    """
    data = request.get_json()
    credential = data.get('credential')
    challenge_id = data.get('challengeId')
    name = data.get('name', 'Passkey')  # Default to 'Passkey' if not provided

    if not credential or not challenge_id:
        return jsonify({'error': 'Missing required fields'}), 400

    # Get and consume challenge (single-use)
    challenge_row, error = _consume_challenge(challenge_id)
    if error:
        return error
    user_id = challenge_row.user_id

    # Verify registration
    try:
        challenge = bytes.fromhex(challenge_row.challenge)
        expected_origin = get_expected_origin()

        verification = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=expected_origin,
        )

        # Store credential
        db.session.add(PasskeyCredential(
            user_id=user_id,
            credential_id=verification.credential_id.hex(),
            public_key=verification.credential_public_key.hex(),
            sign_count=verification.sign_count,
            name=name,
        ))
        db.session.commit()

        return jsonify({
            'success': True,
            'credentialId': verification.credential_id.hex()
        })

    except Exception as e:
        db.session.rollback()
        # Log the full error for debugging, but don't expose to user
        print(f'Passkey registration verification error: {str(e)}')
        return jsonify({'error': 'Passkey registration failed. Please try again.'}), 400


# ==================== AUTHENTICATION ====================

@passkey_bp.route('/login/begin', methods=['POST'])
def login_begin():
    """
    Start passkey login
    Input: { username } (optional for discoverable credentials)
    Output: WebAuthn authentication options
    """
    data = request.get_json() or {}
    username = data.get('username')

    # Generate challenge
    challenge = secrets.token_bytes(32)

    # Store challenge
    challenge_id = _store_challenge(challenge, username=username)

    # Get allowed credentials (if username provided)
    allow_credentials = None
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            allow_credentials = _credential_descriptors(user.id) or None

    # Generate authentication options
    options = generate_authentication_options(
        rp_id=RP_ID,
        challenge=challenge,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    return jsonify({
        'options': options_to_json(options),
        'challengeId': challenge_id
    })


@passkey_bp.route('/login/complete', methods=['POST'])
def login_complete():
    """
    Complete passkey login
    Input: { credential, challengeId }
    Output: { token, user }
    """
    data = request.get_json()
    credential = data.get('credential')
    challenge_id = data.get('challengeId')

    if not credential or not challenge_id:
        return jsonify({'error': 'Missing required fields'}), 400

    # Get and consume challenge (single-use)
    challenge_row, error = _consume_challenge(challenge_id)
    if error:
        return error

    # Get credential from database
    # credential['id'] is base64url-encoded from frontend
    credential_id_bytes = base64.urlsafe_b64decode(credential['id'] + '==')  # Add padding if needed
    credential_id = credential_id_bytes.hex()
    stored = PasskeyCredential.query.filter_by(credential_id=credential_id).first()

    if not stored:
        return jsonify({'error': 'Credential not found'}), 404

    # Verify authentication
    try:
        challenge = bytes.fromhex(challenge_row.challenge)
        expected_origin = get_expected_origin()

        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=expected_origin,
            credential_public_key=bytes.fromhex(stored.public_key),
            credential_current_sign_count=stored.sign_count,
        )

        # Update sign count and last_used
        stored.sign_count = verification.new_sign_count
        stored.last_used_at = datetime.now()
        db.session.commit()

        # Get user
        user = db.session.get(User, stored.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Create JWT token
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=24),
            additional_claims={'role': user.role, 'username': user.username}
        )

        return jsonify({
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        })

    except Exception as e:
        db.session.rollback()
        # Log the full error for debugging, but don't expose to user
        print(f'Passkey authentication error: {str(e)}')
        return jsonify({'error': 'Passkey authentication failed. Please try again.'}), 400


# ==================== RECOVERY CODES ====================

@passkey_bp.route('/recovery/generate', methods=['POST'])
@jwt_required()
def generate_recovery_codes():
    """Generate 8 recovery codes for the current user"""
    user_id = int(get_jwt_identity())

    # Generate 8 codes
    codes = []

    for _ in range(8):
        # Generate 20-character code
        code = secrets.token_urlsafe(15)[:20]
        codes.append(code)

        # Hash and store
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        db.session.add(RecoveryCode(user_id=user_id, code_hash=code_hash))

    db.session.commit()

    return jsonify({'codes': codes})


@passkey_bp.route('/recovery/use', methods=['POST'])
def use_recovery_code():
    """
    Use a recovery code to get temporary access
    Input: { username, code }
    Output: { temporaryToken } - allows registering new passkey
    """
    data = request.get_json()
    username = data.get('username')
    code = data.get('code')

    if not username or not code:
        return jsonify({'error': 'Username and code required'}), 400

    # Get user
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Invalid username or code'}), 401

    # Hash the provided code
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # Find matching unused code
    recovery_code = RecoveryCode.query.filter_by(
        user_id=user.id, code_hash=code_hash, used=False
    ).first()

    if not recovery_code:
        return jsonify({'error': 'Invalid username or code'}), 401

    # Mark as used
    recovery_code.used = True
    recovery_code.used_at = datetime.now()
    db.session.commit()

    # Create temporary token (short expiration - 15 minutes)
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(minutes=15)
    )

    return jsonify({'temporaryToken': access_token})


# ==================== PASSKEY MANAGEMENT ====================

@passkey_bp.route('/list', methods=['GET'])
@jwt_required()
def list_passkeys():
    """List user's registered passkeys"""
    current_user_id = int(get_jwt_identity())

    passkeys = (PasskeyCredential.query
                .filter_by(user_id=current_user_id)
                .order_by(PasskeyCredential.created_at.desc())
                .all())

    return jsonify({'passkeys': [pk.to_dict() for pk in passkeys]})


@passkey_bp.route('/delete/<int:passkey_id>', methods=['DELETE'])
@jwt_required()
def delete_passkey(passkey_id):
    """Delete a passkey"""
    current_user_id = int(get_jwt_identity())

    # Verify ownership
    passkey = db.session.get(PasskeyCredential, passkey_id)

    if not passkey or passkey.user_id != current_user_id:
        return jsonify({'error': 'Passkey not found'}), 404

    db.session.delete(passkey)
    db.session.commit()

    return jsonify({'message': 'Passkey deleted successfully'})


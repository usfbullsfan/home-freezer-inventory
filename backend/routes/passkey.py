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
    UserVerificationRequirement
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
import secrets
import hashlib
from datetime import datetime, timedelta
from models import db, User
import os

passkey_bp = Blueprint('passkey', __name__)

# Configuration
RP_ID = os.environ.get('RP_ID', 'thefreezer.xyz')
RP_NAME = "Freezer Inventory Tracker"
EXPECTED_ORIGIN_DEV = "https://dev.thefreezer.xyz"
EXPECTED_ORIGIN_PROD = "https://thefreezer.xyz"

def get_expected_origin():
    """Get expected origin based on environment"""
    hostname = request.host
    if 'dev' in hostname or 'localhost' in hostname:
        return EXPECTED_ORIGIN_DEV
    return EXPECTED_ORIGIN_PROD

def get_db_connection():
    """Get database connection"""
    import sqlite3
    return sqlite3.connect('freezer_inventory.db')

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
    conn = get_db_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(minutes=5)
    cursor.execute(
        'INSERT INTO passkey_challenges (challenge, user_id, expires_at) VALUES (?, ?, ?)',
        (challenge.hex(), user.id, expires_at.isoformat())
    )
    conn.commit()
    challenge_id = cursor.lastrowid
    conn.close()

    # Get existing credentials to exclude
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT credential_id FROM passkey_credentials WHERE user_id = ?', (user.id,))
    existing_creds = cursor.fetchall()
    conn.close()

    exclude_credentials = [
        PublicKeyCredentialDescriptor(id=bytes.fromhex(cred[0]))
        for cred in existing_creds
    ]

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
        authenticator_selection={
            'residentKey': 'preferred',
            'userVerification': 'preferred',
        }
    )

    return jsonify({
        'options': options_to_json(options),
        'challengeId': challenge_id
    })


@passkey_bp.route('/register/complete', methods=['POST'])
def register_complete():
    """
    Complete passkey registration
    Input: { credential, challengeId }
    """
    data = request.get_json()
    credential = data.get('credential')
    challenge_id = data.get('challengeId')

    if not credential or not challenge_id:
        return jsonify({'error': 'Missing required fields'}), 400

    # Get challenge
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT challenge, user_id, expires_at FROM passkey_challenges WHERE id = ?',
        (challenge_id,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'error': 'Invalid challenge'}), 400

    challenge_hex, user_id, expires_at = result

    # Check expiration
    if datetime.fromisoformat(expires_at) < datetime.now():
        cursor.execute('DELETE FROM passkey_challenges WHERE id = ?', (challenge_id,))
        conn.commit()
        conn.close()
        return jsonify({'error': 'Challenge expired'}), 400

    # Delete challenge (single-use)
    cursor.execute('DELETE FROM passkey_challenges WHERE id = ?', (challenge_id,))
    conn.commit()
    conn.close()

    # Verify registration
    try:
        challenge = bytes.fromhex(challenge_hex)
        expected_origin = get_expected_origin()

        verification = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=expected_origin,
        )

        # Store credential
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO passkey_credentials
               (user_id, credential_id, public_key, sign_count)
               VALUES (?, ?, ?, ?)''',
            (
                user_id,
                verification.credential_id.hex(),
                verification.credential_public_key.hex(),
                verification.sign_count
            )
        )
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'credentialId': verification.credential_id.hex()
        })

    except Exception as e:
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
    conn = get_db_connection()
    cursor = conn.cursor()
    expires_at = datetime.now() + timedelta(minutes=5)
    cursor.execute(
        'INSERT INTO passkey_challenges (challenge, username, expires_at) VALUES (?, ?, ?)',
        (challenge.hex(), username, expires_at.isoformat())
    )
    conn.commit()
    challenge_id = cursor.lastrowid
    conn.close()

    # Get allowed credentials (if username provided)
    allow_credentials = None
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT credential_id FROM passkey_credentials WHERE user_id = ?', (user.id,))
            creds = cursor.fetchall()
            conn.close()

            if creds:
                allow_credentials = [
                    PublicKeyCredentialDescriptor(id=bytes.fromhex(cred[0]))
                    for cred in creds
                ]

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

    # Get challenge
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT challenge, expires_at FROM passkey_challenges WHERE id = ?',
        (challenge_id,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'error': 'Invalid challenge'}), 400

    challenge_hex, expires_at = result

    # Check expiration
    if datetime.fromisoformat(expires_at) < datetime.now():
        cursor.execute('DELETE FROM passkey_challenges WHERE id = ?', (challenge_id,))
        conn.commit()
        conn.close()
        return jsonify({'error': 'Challenge expired'}), 400

    # Delete challenge (single-use)
    cursor.execute('DELETE FROM passkey_challenges WHERE id = ?', (challenge_id,))
    conn.commit()
    conn.close()

    # Get credential from database
    credential_id = bytes.fromhex(credential['id']).hex()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user_id, public_key, sign_count FROM passkey_credentials WHERE credential_id = ?',
        (credential_id,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'error': 'Credential not found'}), 404

    user_id, public_key_hex, stored_sign_count = result

    # Verify authentication
    try:
        challenge = bytes.fromhex(challenge_hex)
        expected_origin = get_expected_origin()

        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=expected_origin,
            credential_public_key=bytes.fromhex(public_key_hex),
            credential_current_sign_count=stored_sign_count,
        )

        # Update sign count and last_used
        cursor.execute(
            '''UPDATE passkey_credentials
               SET sign_count = ?, last_used_at = ?
               WHERE credential_id = ?''',
            (verification.new_sign_count, datetime.now().isoformat(), credential_id)
        )
        conn.commit()
        conn.close()

        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Create JWT token
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        })

    except Exception as e:
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
    conn = get_db_connection()
    cursor = conn.cursor()

    for _ in range(8):
        # Generate 20-character code
        code = secrets.token_urlsafe(15)[:20]
        codes.append(code)

        # Hash and store
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        cursor.execute(
            'INSERT INTO recovery_codes (user_id, code_hash) VALUES (?, ?)',
            (user_id, code_hash)
        )

    conn.commit()
    conn.close()

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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM recovery_codes WHERE user_id = ? AND code_hash = ? AND used = 0',
        (user.id, code_hash)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({'error': 'Invalid username or code'}), 401

    code_id = result[0]

    # Mark as used
    cursor.execute(
        'UPDATE recovery_codes SET used = 1, used_at = ? WHERE id = ?',
        (datetime.now().isoformat(), code_id)
    )
    conn.commit()
    conn.close()

    # Create temporary token (short expiration - 15 minutes)
    from datetime import timedelta
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(minutes=15)
    )

    return jsonify({'temporaryToken': access_token})

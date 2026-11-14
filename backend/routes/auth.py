from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from datetime import timedelta
from utils.activation_codes import (
    generate_activation_code,
    normalize_activation_code,
    has_ambiguous_chars,
    codes_match,
)

ACTIVATION_CODE_NOT_RECOGNISED = (
    "That code wasn't recognised. Check for typos, "
    "or ask your administrator for a new one."
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@jwt_required()
def register():
    """Register a new user (admin only) - generates activation code for passkey enrollment"""
    from flask_jwt_extended import get_jwt
    import secrets

    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    if not data or not data.get('username'):
        return jsonify({'error': 'Username required'}), 400

    # Normalize username to lowercase and strip whitespace
    username_lower = data['username'].strip().lower()

    if User.query.filter_by(username=username_lower).first():
        return jsonify({'error': 'Username already exists'}), 400

    # Generate activation code (8 characters, no look-alike characters)
    activation_code = generate_activation_code()

    user = User(
        username=username_lower,
        role=data.get('role', 'user'),  # Default to 'user' role
        activation_code=activation_code,
        activated=False
    )
    # Set a random password placeholder (won't be used with passkeys)
    user.set_password(secrets.token_urlsafe(32))

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User created successfully. Share the activation code with the user for passkey enrollment.',
        'user': user.to_dict(),
        'activation_code': activation_code  # Only returned once!
    }), 201


def _find_user_for_activation_code(code):
    """Find the pending user for a normalized activation code.

    Tries an exact match first. If that misses and the code contains a
    look-alike character (0/O, 1/I/L), falls back to a look-alike-tolerant
    comparison against pending codes, which covers codes issued with the old
    alphabet and users who read O as 0 (or vice versa). Ambiguous fallbacks
    (more than one candidate) are treated as no match.
    """
    user = User.query.filter_by(activation_code=code, activated=False).first()
    if user or not has_ambiguous_chars(code):
        return user

    pending = User.query.filter(
        User.activated.is_(False),
        User.activation_code.isnot(None),
    ).all()
    matches = [u for u in pending if codes_match(code, u.activation_code)]
    return matches[0] if len(matches) == 1 else None


@auth_bp.route('/activate', methods=['POST'])
def activate():
    """Activate account with one-time activation code and enroll passkey"""
    data = request.get_json()

    if not data or not data.get('activation_code'):
        return jsonify({'error': 'Activation code required'}), 400

    code = normalize_activation_code(data['activation_code'])
    if not code:
        return jsonify({'error': ACTIVATION_CODE_NOT_RECOGNISED}), 401

    user = _find_user_for_activation_code(code)

    if not user:
        # Same message whether the code never existed or was already used,
        # so the response doesn't reveal which codes are valid.
        return jsonify({'error': ACTIVATION_CODE_NOT_RECOGNISED}), 401

    # Mark as activated and clear the activation code
    user.activated = True
    user.activation_code = None  # Clear code after use
    db.session.commit()

    # Create token for passkey registration (24 hour expiration)
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=24),
        additional_claims={'role': user.role, 'username': user.username}
    )

    return jsonify({
        'token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login and receive JWT token"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    # Normalize username to lowercase and strip whitespace
    username_lower = data['username'].strip().lower()

    user = User.query.filter_by(username=username_lower).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Create access token with 24 hour expiration
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=24),
        additional_claims={'role': user.role, 'username': user.username}
    )

    return jsonify({
        'token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info from JWT token"""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route('/me', methods=['PATCH'])
@jwt_required()
def update_current_user():
    """Update current user settings"""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    # Only allow updating specific fields
    if 'pwa_install_dismissed' in data:
        user.pwa_install_dismissed = data['pwa_install_dismissed']

    db.session.commit()

    return jsonify(user.to_dict()), 200


@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)"""
    from flask_jwt_extended import get_jwt
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change current user's password"""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current password and new password required'}), 400

    # Verify current password
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401

    # Validate new password
    if len(data['new_password']) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400

    # Update password
    user.set_password(data['new_password'])
    db.session.commit()

    return jsonify({'message': 'Password changed successfully'}), 200


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user details (admin only)"""
    from flask_jwt_extended import get_jwt
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    # Update username if provided
    if 'username' in data:
        # Normalize username to lowercase and strip whitespace
        new_username_lower = data['username'].strip().lower()

        if new_username_lower != user.username:
            if User.query.filter_by(username=new_username_lower).first():
                return jsonify({'error': 'Username already exists'}), 400
            user.username = new_username_lower

    # Update role if provided
    if 'role' in data:
        if data['role'] not in ['admin', 'user']:
            return jsonify({'error': 'Invalid role. Must be "admin" or "user"'}), 400
        user.role = data['role']

    db.session.commit()

    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a user (admin only)"""
    from flask_jwt_extended import get_jwt
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    current_user_id = int(get_jwt_identity())

    # Prevent admin from deleting themselves
    if user_id == current_user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200


@auth_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password(user_id):
    """Reset a user's password (admin only)"""
    from flask_jwt_extended import get_jwt
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data or not data.get('new_password'):
        return jsonify({'error': 'New password required'}), 400

    # Validate new password
    if len(data['new_password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    user.set_password(data['new_password'])
    db.session.commit()

    return jsonify({'message': 'Password reset successfully'}), 200


@auth_bp.route('/users/<int:user_id>/regenerate-activation', methods=['POST'])
@jwt_required()
def regenerate_activation_code(user_id):
    """Regenerate activation code for a user (admin only)"""
    from flask_jwt_extended import get_jwt

    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        # Generate new activation code
        activation_code = generate_activation_code()

        # Delete any existing passkeys and recovery codes for this user (they'll
        # need to re-register). Done through db.session so it works on any
        # database and commits atomically with the new activation code. These
        # tables have no ORM models and are created by a separate migration, so
        # skip any that don't exist in this database.
        existing_tables = set(db.inspect(db.engine).get_table_names())
        for table in ('passkey_credentials', 'recovery_codes'):
            if table in existing_tables:
                db.session.execute(
                    db.text(f'DELETE FROM {table} WHERE user_id = :user_id'),
                    {'user_id': user_id},
                )

        # Set new activation code and mark as not activated
        user.activation_code = activation_code
        user.activated = False
        db.session.commit()

        return jsonify({
            'message': 'Activation code regenerated successfully',
            'activation_code': activation_code
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f'Error regenerating activation code: {str(e)}')
        return jsonify({'error': 'Failed to regenerate activation code'}), 500


@auth_bp.route('/quick-login-status', methods=['GET'])
def quick_login_status():
    """Check if no-auth mode is enabled (no JWT required)"""
    import os
    from models import Setting

    # Only available in development
    if os.environ.get('FLASK_ENV') != 'development':
        return jsonify({'enabled': False, 'reason': 'Not in development mode'}), 200

    # Check if no_auth_mode system setting is enabled
    setting = Setting.query.filter_by(
        user_id=None,
        setting_name='no_auth_mode'
    ).first()

    enabled = setting and setting.setting_value == 'true'

    return jsonify({'enabled': enabled}), 200


@auth_bp.route('/quick-login-users', methods=['GET'])
def quick_login_users():
    """Get list of users for quick login (development only, no JWT required)"""
    import os

    # Only available in development
    if os.environ.get('FLASK_ENV') != 'development':
        return jsonify({'error': 'This endpoint is only available in development'}), 403

    # Check if no_auth_mode is enabled
    from models import Setting
    setting = Setting.query.filter_by(
        user_id=None,
        setting_name='no_auth_mode'
    ).first()

    if not setting or setting.setting_value != 'true':
        return jsonify({'error': 'No-auth mode is not enabled'}), 403

    # Return all users
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


@auth_bp.route('/quick-login', methods=['POST'])
def quick_login():
    """Quick login without password (development only)"""
    import os

    # Only available in development
    if os.environ.get('FLASK_ENV') != 'development':
        return jsonify({'error': 'This endpoint is only available in development'}), 403

    # Check if no_auth_mode is enabled
    from models import Setting
    setting = Setting.query.filter_by(
        user_id=None,
        setting_name='no_auth_mode'
    ).first()

    if not setting or setting.setting_value != 'true':
        return jsonify({'error': 'No-auth mode is not enabled'}), 403

    data = request.get_json()
    if not data or not data.get('user_id'):
        return jsonify({'error': 'user_id is required'}), 400

    user = db.session.get(User, data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Create access token (same as regular login)
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=24),
        additional_claims={'role': user.role, 'username': user.username}
    )

    return jsonify({
        'token': access_token,
        'user': user.to_dict()
    }), 200


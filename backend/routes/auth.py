from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user (admin only in production, open for MVP)"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(
        username=data['username'],
        role=data.get('role', 'user')  # Default to 'user' role
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login and receive JWT token"""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Create access token with 24 hour expiration
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(hours=24),
        additional_claims={'role': user.role, 'username': user.username}
    )

    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info from JWT token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

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
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

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


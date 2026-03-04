"""Notifications blueprint – email settings and test-send endpoint.

Routes (all require JWT):
  GET  /api/notifications/email/status   – is email configured? (any role)
  GET  /api/notifications/email/settings – get SMTP settings (admin only, no secrets)
  POST /api/notifications/email/test     – send a test email (admin only)
  GET  /api/notifications/email/me       – get current user's notification email
  PUT  /api/notifications/email/me       – update current user's notification email
"""

import logging
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, User
from utils.email import is_email_configured, send_email

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/email/status', methods=['GET'])
@jwt_required()
def email_status():
    """Return whether SMTP is configured (safe for any logged-in user)."""
    return jsonify({'configured': is_email_configured()}), 200


@notifications_bp.route('/email/settings', methods=['GET'])
@jwt_required()
def get_email_settings():
    """Return non-secret SMTP settings so admins can verify configuration."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    return jsonify({
        'configured': is_email_configured(),
        'smtp_server': os.environ.get('SMTP_SERVER', ''),
        'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
        'smtp_use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true',
        'smtp_username': os.environ.get('SMTP_USERNAME', ''),
        'from_address': os.environ.get('EMAIL_FROM_ADDRESS', ''),
        'from_name': os.environ.get('EMAIL_FROM_NAME', 'Freezer Inventory'),
    }), 200


@notifications_bp.route('/email/test', methods=['POST'])
@jwt_required()
def send_test_email():
    """Send a test email to verify SMTP configuration (admin only)."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    if not is_email_configured():
        return jsonify({
            'error': 'Email is not configured. Set SMTP_SERVER, SMTP_USERNAME, '
                     'and EMAIL_FROM_ADDRESS environment variables.'
        }), 400

    data = request.get_json() or {}
    recipient = data.get('to')

    if not recipient:
        # Fall back to the requesting admin's email address
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        recipient = user.email if user else None

    if not recipient:
        return jsonify({
            'error': 'No recipient address. Provide "to" in the request body or '
                     'set your email address in your profile first.'
        }), 400

    try:
        send_email(
            to_addresses=recipient,
            subject='Freezer Inventory – Test Email',
            text_body=(
                'This is a test email from your Freezer Inventory Tracker.\n\n'
                'If you received this, SMTP is configured correctly.'
            ),
            html_body=(
                '<p>This is a test email from your <strong>Freezer Inventory Tracker</strong>.</p>'
                '<p>If you received this, SMTP is configured correctly.</p>'
            ),
        )
        return jsonify({'message': f'Test email sent to {recipient}'}), 200

    except RuntimeError as exc:
        logging.exception('Failed to send test email: %s', exc)
        return jsonify({'error': 'Failed to send test email. Check server logs for details.'}), 500


@notifications_bp.route('/email/me', methods=['GET'])
@jwt_required()
def get_my_email():
    """Return the current user's notification email address."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'email': user.email}), 200


@notifications_bp.route('/email/me', methods=['PUT'])
@jwt_required()
def update_my_email():
    """Update the current user's notification email address."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Request body required'}), 400

    email = data.get('email', '').strip()

    # Basic format check (not exhaustive – proper validation happens server-side when sending)
    if email and '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    user.email = email or None
    db.session.commit()

    return jsonify({'message': 'Email updated', 'email': user.email}), 200

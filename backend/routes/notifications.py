"""Notifications blueprint – email settings and test-send endpoint.

Routes (all require JWT):
  GET  /api/notifications/email/status            – is email configured? (any role)
  GET  /api/notifications/email/settings          – get email settings (admin only)
  POST /api/notifications/email/test              – send a test email (admin only)
  GET  /api/notifications/email/me                – get current user's notification email
  PUT  /api/notifications/email/me                – update current user's notification email
  POST /api/notifications/email/verify            – verify the 6-digit code
  POST /api/notifications/email/resend-verification – resend verification code
"""

import logging
import os
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, User
from utils.email import is_email_configured, send_email, send_verification_email

notifications_bp = Blueprint('notifications', __name__)

_CODE_TTL_MINUTES = 30


def _generate_code():
    """Return a zero-padded 6-digit verification code."""
    return f'{secrets.randbelow(1_000_000):06d}'


@notifications_bp.route('/email/status', methods=['GET'])
@jwt_required()
def email_status():
    """Return whether email is configured (safe for any logged-in user)."""
    return jsonify({'configured': is_email_configured()}), 200


@notifications_bp.route('/email/settings', methods=['GET'])
@jwt_required()
def get_email_settings():
    """Return non-secret email settings so admins can verify configuration."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    return jsonify({
        'configured': is_email_configured(),
        'from_address': os.environ.get('EMAIL_FROM_ADDRESS', ''),
        'from_name': os.environ.get('EMAIL_FROM_NAME', 'Freezer Inventory'),
    }), 200


@notifications_bp.route('/email/test', methods=['POST'])
@jwt_required()
def send_test_email():
    """Send a test email to verify email configuration (admin only)."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    if not is_email_configured():
        return jsonify({
            'error': 'Email is not configured. Set RESEND_API_KEY and '
                     'EMAIL_FROM_ADDRESS environment variables.'
        }), 400

    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if not user or not user.email:
        return jsonify({
            'error': 'No verified email address found. Add and verify your email in the Email Notifications section first.'
        }), 400

    if not user.email_verified:
        return jsonify({
            'error': 'Your email address is not verified. Please verify it in the Email Notifications section first.'
        }), 400

    recipient = user.email

    try:
        send_email(
            to_addresses=recipient,
            subject='Freezer Inventory – Test Email',
            text_body=(
                'This is a test email from your Freezer Inventory Tracker.\n\n'
                'If you received this, email is configured correctly.'
            ),
            html_body=(
                '<p>This is a test email from your <strong>Freezer Inventory Tracker</strong>.</p>'
                '<p>If you received this, email is configured correctly.</p>'
            ),
        )
        return jsonify({'message': f'Test email sent to {recipient}'}), 200

    except RuntimeError as exc:
        logging.exception('Failed to send test email: %s', exc)
        return jsonify({'error': 'Failed to send test email. Check server logs for details.'}), 500


@notifications_bp.route('/email/me', methods=['GET'])
@jwt_required()
def get_my_email():
    """Return the current user's notification email address and verification status."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'email': user.email,
        'email_verified': bool(user.email_verified),
    }), 200


@notifications_bp.route('/email/me', methods=['PUT'])
@jwt_required()
def update_my_email():
    """Update the current user's notification email address.

    If the email changes (or is not yet verified) a 6-digit verification code
    is sent to the new address.  The email is stored immediately but marked
    unverified until the code is confirmed.
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Request body required'}), 400

    email = data.get('email', '').strip()

    if email and '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    # Clearing the email is always allowed
    if not email:
        user.email = None
        user.email_verified = False
        user.email_verification_token = None
        user.email_verification_expires = None
        db.session.commit()
        return jsonify({'message': 'Email removed', 'email': None, 'email_verified': False}), 200

    # If unchanged and already verified, nothing to do
    if email == user.email and user.email_verified:
        return jsonify({
            'message': 'Email already verified',
            'email': user.email,
            'email_verified': True,
        }), 200

    # Require email service to be set up before accepting a new address
    if not is_email_configured():
        return jsonify({
            'error': 'Email notifications are not configured on this server. '
                     'Contact your administrator.'
        }), 503

    code = _generate_code()
    user.email = email
    user.email_verified = False
    user.email_verification_token = code
    user.email_verification_expires = datetime.utcnow() + timedelta(minutes=_CODE_TTL_MINUTES)
    db.session.commit()

    try:
        send_verification_email(email, code)
    except RuntimeError as exc:
        logging.exception('Failed to send verification email: %s', exc)
        return jsonify({'error': 'Email saved but verification email could not be sent. '
                                 'Try resending the code.'}), 500

    return jsonify({
        'message': f'Verification code sent to {email}',
        'email': email,
        'email_verified': False,
        'verification_required': True,
    }), 200


@notifications_bp.route('/email/verify', methods=['POST'])
@jwt_required()
def verify_email():
    """Verify the 6-digit code sent to the user's email address."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.email:
        return jsonify({'error': 'No email address set'}), 400

    if user.email_verified:
        return jsonify({'message': 'Email already verified', 'email_verified': True}), 200

    data = request.get_json()
    if not data or not data.get('code'):
        return jsonify({'error': 'Verification code required'}), 400

    submitted = str(data['code']).strip()

    if not user.email_verification_token:
        return jsonify({'error': 'No verification code found. Request a new one.'}), 400

    if datetime.utcnow() > user.email_verification_expires:
        return jsonify({'error': 'Verification code has expired. Request a new one.'}), 400

    if submitted != user.email_verification_token:
        return jsonify({'error': 'Incorrect verification code'}), 400

    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    db.session.commit()

    return jsonify({'message': 'Email verified successfully', 'email_verified': True}), 200


@notifications_bp.route('/email/resend-verification', methods=['POST'])
@jwt_required()
def resend_verification():
    """Resend the verification code to the user's current email address."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.email:
        return jsonify({'error': 'No email address set'}), 400

    if user.email_verified:
        return jsonify({'message': 'Email already verified', 'email_verified': True}), 200

    if not is_email_configured():
        return jsonify({'error': 'Email notifications are not configured on this server.'}), 503

    code = _generate_code()
    user.email_verification_token = code
    user.email_verification_expires = datetime.utcnow() + timedelta(minutes=_CODE_TTL_MINUTES)
    db.session.commit()

    try:
        send_verification_email(user.email, code)
    except RuntimeError as exc:
        logging.exception('Failed to resend verification email: %s', exc)
        return jsonify({'error': 'Failed to send verification email. Check server logs.'}), 500

    return jsonify({'message': f'Verification code resent to {user.email}'}), 200

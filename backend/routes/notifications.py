"""Notifications blueprint – email settings and test-send endpoint.

Routes (all require JWT unless noted):
  GET  /api/notifications/email/status            – is email configured? (any role)
  GET  /api/notifications/email/settings          – get email settings (admin only)
  POST /api/notifications/email/test              – send a test email to own verified address (any role)
  GET  /api/notifications/email/me                – get current user's notification email
  PUT  /api/notifications/email/me                – update current user's notification email
  POST /api/notifications/email/verify            – verify the 6-digit code
  POST /api/notifications/email/resend-verification – resend verification code

  GET    /api/notifications/low-stock             – list current user's low-stock alerts
  POST   /api/notifications/low-stock             – create a low-stock alert
  PUT    /api/notifications/low-stock/<id>        – update threshold / enabled
  DELETE /api/notifications/low-stock/<id>        – delete an alert

  GET  /api/notifications/expiration-settings     – get current user's expiration notification prefs
  PUT  /api/notifications/expiration-settings     – update current user's expiration notification prefs
  POST /api/notifications/send-expiration-digest  – cron endpoint (no JWT; optional CRON_SECRET header)
"""

import logging
import os
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from models import db, User, Item, LowStockAlert, ExpirationNotificationSettings
from utils.email import is_email_configured, send_email, send_verification_email, send_expiration_digest

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
    """Send a test email to the current user's verified address."""
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

    at_idx = email.find('@')
    if email and (
        at_idx < 1
        or at_idx != email.rfind('@')
        or at_idx == len(email) - 1
        or ' ' in email
        or '.' not in email[at_idx + 1:]
    ):
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


# ── Low-stock alerts ──────────────────────────────────────────────────────────

_LOW_STOCK_COOLDOWN_HOURS = 24


def _send_low_stock_email(to_address, item_name, current_count, threshold):
    """Send a low-stock alert email."""
    subject = f'Low stock alert – {item_name}'
    qty = f'{current_count} item{"" if current_count == 1 else "s"}'
    text = (
        f'Low stock alert for "{item_name}".\n\n'
        f'You have {qty} remaining in your freezer '
        f'(alert threshold: {threshold}).\n\n'
        'Time to restock!'
    )
    html = (
        f'<p>Low stock alert for <strong>{item_name}</strong>.</p>'
        f'<p>You have <strong>{qty}</strong> remaining in your freezer '
        f'(alert threshold: {threshold}).</p>'
        '<p>Time to restock!</p>'
    )
    send_email(to_addresses=to_address, subject=subject, text_body=text, html_body=html)


def check_and_send_low_stock_alerts(item_name):
    """Check all low-stock alerts for item_name and fire emails as needed.

    Called after an item's status changes to consumed/thrown_out.
    """
    if not is_email_configured():
        return

    current_count = Item.query.filter(
        func.lower(Item.name) == item_name.lower(),
        Item.status == 'in_freezer',
    ).count()

    alerts = LowStockAlert.query.filter(
        func.lower(LowStockAlert.item_name) == item_name.lower(),
        LowStockAlert.enabled == True,
        LowStockAlert.threshold >= current_count,
    ).all()

    for alert in alerts:
        # Respect cooldown to avoid email spam
        if alert.last_sent_at:
            hours_since = (datetime.utcnow() - alert.last_sent_at).total_seconds() / 3600
            if hours_since < _LOW_STOCK_COOLDOWN_HOURS:
                continue

        user = alert.user
        if not user or not user.email or not user.email_verified:
            continue

        try:
            _send_low_stock_email(user.email, item_name, current_count, alert.threshold)
            alert.last_sent_at = datetime.utcnow()
            db.session.commit()
        except RuntimeError:
            logging.exception('Failed to send low-stock alert for "%s" to %s', item_name, user.email)


@notifications_bp.route('/low-stock', methods=['GET'])
@jwt_required()
def list_low_stock_alerts():
    """Return all low-stock alerts for the current user."""
    current_user_id = int(get_jwt_identity())
    alerts = LowStockAlert.query.filter_by(user_id=current_user_id).order_by(LowStockAlert.item_name).all()
    return jsonify([a.to_dict() for a in alerts]), 200


@notifications_bp.route('/low-stock', methods=['POST'])
@jwt_required()
def create_low_stock_alert():
    """Create a new low-stock alert for the current user."""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    item_name = (data.get('item_name') or '').strip()
    if not item_name:
        return jsonify({'error': 'item_name is required'}), 400

    # Normalise to the canonical casing stored in the items table so that
    # alert.item_name always matches exactly what appears in the inventory.
    canonical = Item.query.filter(
        func.lower(Item.name) == item_name.lower(),
        Item.status == 'in_freezer',
    ).with_entities(Item.name).first()
    if canonical:
        item_name = canonical[0]

    threshold = data.get('threshold', 2)
    try:
        threshold = int(threshold)
        if threshold < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'threshold must be a positive integer'}), 400

    existing = LowStockAlert.query.filter(
        LowStockAlert.user_id == current_user_id,
        func.lower(LowStockAlert.item_name) == item_name.lower(),
    ).first()
    if existing:
        return jsonify({'error': f'An alert for "{item_name}" already exists'}), 409

    alert = LowStockAlert(user_id=current_user_id, item_name=item_name, threshold=threshold)
    db.session.add(alert)
    db.session.commit()
    return jsonify(alert.to_dict()), 201


@notifications_bp.route('/low-stock/<int:alert_id>', methods=['PUT'])
@jwt_required()
def update_low_stock_alert(alert_id):
    """Update threshold and/or enabled flag for an alert."""
    current_user_id = int(get_jwt_identity())
    alert = LowStockAlert.query.filter_by(id=alert_id, user_id=current_user_id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    data = request.get_json() or {}

    if 'threshold' in data:
        try:
            threshold = int(data['threshold'])
            if threshold < 1:
                raise ValueError
            alert.threshold = threshold
        except (TypeError, ValueError):
            return jsonify({'error': 'threshold must be a positive integer'}), 400

    if 'enabled' in data:
        alert.enabled = bool(data['enabled'])

    db.session.commit()
    return jsonify(alert.to_dict()), 200


@notifications_bp.route('/low-stock/<int:alert_id>', methods=['DELETE'])
@jwt_required()
def delete_low_stock_alert(alert_id):
    """Delete a low-stock alert."""
    current_user_id = int(get_jwt_identity())
    alert = LowStockAlert.query.filter_by(id=alert_id, user_id=current_user_id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    db.session.delete(alert)
    db.session.commit()
    return jsonify({'message': 'Alert deleted'}), 200


# ── Expiration notification settings ──────────────────────────────────────────

_EXP_DEFAULTS = {
    'enabled': False,
    'frequency': 'daily',
    'day_of_week': 1,
    'days_before': 7,
    'all_categories': True,
    'category_ids': [],
    'last_sent_at': None,
}


@notifications_bp.route('/expiration-settings', methods=['GET'])
@jwt_required()
def get_expiration_settings():
    """Return the current user's expiration notification preferences."""
    current_user_id = int(get_jwt_identity())
    settings = ExpirationNotificationSettings.query.filter_by(user_id=current_user_id).first()
    if not settings:
        return jsonify(_EXP_DEFAULTS), 200
    return jsonify(settings.to_dict()), 200


@notifications_bp.route('/expiration-settings', methods=['PUT'])
@jwt_required()
def update_expiration_settings():
    """Create or update the current user's expiration notification preferences."""
    import json as _json
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    settings = ExpirationNotificationSettings.query.filter_by(user_id=current_user_id).first()
    if not settings:
        settings = ExpirationNotificationSettings(user_id=current_user_id)
        db.session.add(settings)

    if 'enabled' in data:
        settings.enabled = bool(data['enabled'])

    if 'frequency' in data:
        if data['frequency'] not in ('daily', 'weekly'):
            return jsonify({'error': 'frequency must be "daily" or "weekly"'}), 400
        settings.frequency = data['frequency']

    if 'day_of_week' in data:
        try:
            dow = int(data['day_of_week'])
            if not 0 <= dow <= 6:
                raise ValueError
            settings.day_of_week = dow
        except (TypeError, ValueError):
            return jsonify({'error': 'day_of_week must be 0–6'}), 400

    if 'days_before' in data:
        try:
            days_val = int(data['days_before'])
            if days_val < 1:
                raise ValueError
            settings.days_before = days_val
        except (TypeError, ValueError):
            return jsonify({'error': 'days_before must be a positive integer'}), 400

    if 'all_categories' in data:
        settings.all_categories = bool(data['all_categories'])

    if 'category_ids' in data:
        try:
            ids = [int(i) for i in data['category_ids']]
            settings.category_ids = _json.dumps(ids)
        except (TypeError, ValueError):
            return jsonify({'error': 'category_ids must be a list of integers'}), 400

    db.session.commit()
    return jsonify(settings.to_dict()), 200


@notifications_bp.route('/send-expiration-digest', methods=['POST'])
def trigger_expiration_digest():
    """Cron endpoint – send expiration digest emails to all eligible users.

    Not JWT-protected. If CRON_SECRET env var is set the caller must supply
    the same value in the X-Cron-Secret request header.

    Intended to be called once daily (e.g. via cron, systemd timer, or a
    hosting-platform scheduler). Weekly-frequency users are skipped on days
    that don't match their chosen day_of_week.
    """
    import json as _json

    cron_secret = os.environ.get('CRON_SECRET', '')
    if cron_secret and request.headers.get('X-Cron-Secret', '') != cron_secret:
        return jsonify({'error': 'Unauthorized'}), 401

    if not is_email_configured():
        return jsonify({'error': 'Email not configured on this server'}), 503

    today = datetime.utcnow()
    results = {'sent': 0, 'skipped': 0, 'errors': 0}

    all_settings = ExpirationNotificationSettings.query.filter_by(enabled=True).all()

    for s in all_settings:
        user = s.user
        if not user or not user.email or not user.email_verified:
            results['skipped'] += 1
            continue

        # Weekly: only send on the configured day of week
        if s.frequency == 'weekly' and today.weekday() != s.day_of_week:
            results['skipped'] += 1
            continue

        threshold_dt = today + timedelta(days=s.days_before)

        query = Item.query.filter(
            Item.status == 'in_freezer',
            Item.expiration_date.isnot(None),
            Item.expiration_date <= threshold_dt,
        ).order_by(Item.expiration_date)

        if not s.all_categories:
            try:
                cat_ids = _json.loads(s.category_ids or '[]')
                if cat_ids:
                    query = query.filter(Item.category_id.in_(cat_ids))
            except (ValueError, TypeError):
                pass

        items = query.all()
        if not items:
            results['skipped'] += 1
            continue

        try:
            send_expiration_digest(user.email, [i.to_dict() for i in items], s.days_before)
            s.last_sent_at = datetime.utcnow()
            db.session.commit()
            results['sent'] += 1
        except RuntimeError:
            logging.exception('Failed to send expiration digest to %s', user.email)
            results['errors'] += 1

    return jsonify(results), 200

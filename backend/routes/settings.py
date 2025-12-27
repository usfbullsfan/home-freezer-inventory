from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Setting, Item

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/', methods=['GET'])
@jwt_required()
def get_settings():
    """Get all settings for current user"""
    current_user_id = int(get_jwt_identity())
    settings = Setting.query.filter_by(user_id=current_user_id).all()

    # Return as dictionary for easier frontend usage
    settings_dict = {s.setting_name: s.setting_value for s in settings}

    # Set defaults if not present
    if 'track_history' not in settings_dict:
        settings_dict['track_history'] = 'true'

    return jsonify(settings_dict), 200


@settings_bp.route('/', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update settings for current user"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No settings provided'}), 400

    for setting_name, setting_value in data.items():
        setting = Setting.query.filter_by(
            user_id=current_user_id,
            setting_name=setting_name
        ).first()

        if setting:
            setting.setting_value = str(setting_value)
        else:
            setting = Setting(
                user_id=current_user_id,
                setting_name=setting_name,
                setting_value=str(setting_value)
            )
            db.session.add(setting)

    db.session.commit()

    return jsonify({'message': 'Settings updated successfully'}), 200


@settings_bp.route('/purge-history', methods=['POST'])
@jwt_required()
def purge_history():
    """Purge all consumed/thrown out items (admin only)"""
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    # Delete all items not in freezer
    deleted_count = Item.query.filter(
        Item.status.in_(['consumed', 'thrown_out'])
    ).delete()

    db.session.commit()

    return jsonify({
        'message': f'Purged {deleted_count} items from history'
    }), 200

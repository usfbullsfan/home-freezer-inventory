from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Setting, Item
import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename

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


@settings_bp.route('/backup/download', methods=['GET'])
@jwt_required()
def download_backup():
    """Download database backup (admin only)"""
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    # Get the database file path
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')
    # Ensure we have an absolute path
    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        return jsonify({'error': 'Database file not found'}), 404

    # Create a timestamped backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'freezer_inventory_backup_{timestamp}.db'

    # Send the file
    return send_file(
        db_path,
        as_attachment=True,
        download_name=backup_filename,
        mimetype='application/x-sqlite3'
    )


@settings_bp.route('/backup/restore', methods=['POST'])
@jwt_required()
def restore_backup():
    """Restore database from backup file (admin only)"""
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file extension
    if not file.filename.endswith('.db'):
        return jsonify({'error': 'Invalid file type. Only .db files are allowed'}), 400

    try:
        # Get the database file path
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')

        # Create a backup of current database before restoring
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'{db_path}.backup_{timestamp}'
            shutil.copy2(db_path, backup_path)

        # Save uploaded file as new database
        file.save(db_path)

        # Test if the database is valid by trying to query it
        from models import User
        try:
            User.query.first()
        except Exception as e:
            # If database is invalid, restore from backup
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, db_path)
            return jsonify({'error': f'Invalid database file: {str(e)}'}), 400

        return jsonify({
            'message': 'Database restored successfully. Please refresh the page.'
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to restore database: {str(e)}'}), 500


@settings_bp.route('/backup/info', methods=['GET'])
@jwt_required()
def backup_info():
    """Get information about current database (admin only)"""
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    try:
        # Get the database file path
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        # Ensure we have an absolute path
        db_path = os.path.abspath(db_path)

        if not os.path.exists(db_path):
            return jsonify({'error': 'Database file not found'}), 404

        # Get file stats
        stat_info = os.stat(db_path)
        file_size = stat_info.st_size
        modified_time = datetime.fromtimestamp(stat_info.st_mtime)

        # Format file size
        if file_size < 1024:
            size_str = f'{file_size} bytes'
        elif file_size < 1024 * 1024:
            size_str = f'{file_size / 1024:.2f} KB'
        else:
            size_str = f'{file_size / (1024 * 1024):.2f} MB'

        # Get item counts
        from models import Item, Category, User
        total_items = Item.query.count()
        active_items = Item.query.filter_by(status='in_freezer').count()
        total_categories = Category.query.count()
        total_users = User.query.count()

        return jsonify({
            'file_size': size_str,
            'last_modified': modified_time.isoformat(),
            'total_items': total_items,
            'active_items': active_items,
            'total_categories': total_categories,
            'total_users': total_users
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get backup info: {str(e)}'}), 500

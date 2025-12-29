from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Item, Category, User, Setting, generate_qr_code
from datetime import datetime, timedelta
import qrcode
import io
import requests
import os

items_bp = Blueprint('items', __name__)


@items_bp.route('/', methods=['GET'])
@jwt_required()
def get_items():
    """Get all items with optional filtering"""
    current_user_id = int(get_jwt_identity())

    # Get query parameters
    status = request.args.get('status', 'in_freezer')
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    sort_by = request.args.get('sort_by', 'added_date')  # added_date, expiration_date, name
    sort_order = request.args.get('sort_order', 'desc')  # asc or desc
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Check if user wants to see history
    track_history = Setting.query.filter_by(
        user_id=current_user_id,
        setting_name='track_history'
    ).first()

    # Default to tracking history if setting doesn't exist
    track_history_enabled = True if not track_history else track_history.setting_value == 'true'

    # Build query
    query = Item.query

    # Filter by status
    if not track_history_enabled:
        # Only show items in freezer if history tracking is off
        query = query.filter_by(status='in_freezer')
    elif status != 'all':
        query = query.filter_by(status=status)

    # Search filter
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Item.name.ilike(search_pattern),
                Item.source.ilike(search_pattern),
                Item.notes.ilike(search_pattern)
            )
        )

    # Category filter
    if category_id:
        query = query.filter_by(category_id=category_id)

    # Date range filter
    if start_date:
        query = query.filter(Item.added_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Item.added_date <= datetime.fromisoformat(end_date))

    # Sorting
    if sort_by == 'added_date':
        order_col = Item.added_date
    elif sort_by == 'expiration_date':
        order_col = Item.expiration_date
    elif sort_by == 'name':
        order_col = Item.name
    else:
        order_col = Item.added_date

    if sort_order == 'asc':
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())

    items = query.all()
    return jsonify([item.to_dict() for item in items]), 200


@items_bp.route('/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    """Get a specific item by ID"""
    item = Item.query.get(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    return jsonify(item.to_dict()), 200


@items_bp.route('/qr/<qr_code>', methods=['GET'])
@jwt_required()
def get_item_by_qr(qr_code):
    """Get item by QR code"""
    item = Item.query.filter_by(qr_code=qr_code).first()

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    return jsonify(item.to_dict()), 200


@items_bp.route('/', methods=['POST'])
@jwt_required()
def create_item():
    """Create a new item"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Item name is required'}), 400

    # Validate UPC format if provided (must be 12 digits)
    if data.get('upc'):
        import re
        if not re.match(r'^\d{12}$', data['upc']):
            return jsonify({'error': 'Invalid UPC format. UPC must be exactly 12 digits.'}), 400

    # Generate or use provided QR code
    qr_code = data.get('qr_code') or generate_qr_code()

    # Check if QR code already exists
    if Item.query.filter_by(qr_code=qr_code).first():
        return jsonify({'error': 'QR code already exists'}), 400

    # Parse added_date if provided
    added_date = None
    if data.get('added_date'):
        added_date = datetime.fromisoformat(data['added_date'])

    # Calculate expiration date if not provided
    expiration_date = None
    if data.get('expiration_date'):
        expiration_date = datetime.fromisoformat(data['expiration_date'])
    elif data.get('category_id'):
        category = Category.query.get(data['category_id'])
        if category and category.default_expiration_days:
            # Use custom added_date if provided, otherwise use current time
            base_date = added_date or datetime.utcnow()
            expiration_date = base_date + timedelta(days=category.default_expiration_days)

    item = Item(
        qr_code=qr_code,
        upc=data.get('upc'),
        name=data['name'],
        source=data.get('source'),
        weight=data.get('weight'),
        weight_unit=data.get('weight_unit', 'lb'),
        category_id=data.get('category_id'),
        expiration_date=expiration_date,
        notes=data.get('notes'),
        added_by_user_id=current_user_id
    )

    # Set added_date if provided (must be set after creation to override default)
    if added_date:
        item.added_date = added_date

    db.session.add(item)
    db.session.commit()

    return jsonify(item.to_dict()), 201


@items_bp.route('/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    """Update an existing item"""
    item = Item.query.get(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    data = request.get_json()

    # Validate UPC format if provided (must be 12 digits)
    if 'upc' in data and data['upc']:
        import re
        if not re.match(r'^\d{12}$', data['upc']):
            return jsonify({'error': 'Invalid UPC format. UPC must be exactly 12 digits.'}), 400

    # Update fields if provided
    if 'name' in data:
        item.name = data['name']
    if 'upc' in data:
        item.upc = data['upc']
    if 'source' in data:
        item.source = data['source']
    if 'weight' in data:
        item.weight = data['weight']
    if 'weight_unit' in data:
        item.weight_unit = data['weight_unit']
    if 'category_id' in data:
        item.category_id = data['category_id']
    if 'added_date' in data:
        item.added_date = datetime.fromisoformat(data['added_date']) if data['added_date'] else datetime.utcnow()
    if 'expiration_date' in data:
        item.expiration_date = datetime.fromisoformat(data['expiration_date']) if data['expiration_date'] else None
    if 'notes' in data:
        item.notes = data['notes']

    db.session.commit()

    return jsonify(item.to_dict()), 200


@items_bp.route('/<int:item_id>/status', methods=['PUT'])
@jwt_required()
def update_item_status(item_id):
    """Update item status (consume, throw out, return to freezer)"""
    item = Item.query.get(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['in_freezer', 'consumed', 'thrown_out']:
        return jsonify({'error': 'Invalid status'}), 400

    item.status = new_status

    if new_status in ['consumed', 'thrown_out']:
        item.removed_date = datetime.utcnow()
    else:
        item.removed_date = None

    db.session.commit()

    return jsonify(item.to_dict()), 200


@items_bp.route('/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    """Permanently delete an item"""
    from flask_jwt_extended import get_jwt
    claims = get_jwt()

    # Only admins can permanently delete
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    item = Item.query.get(item_id)

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({'message': 'Item deleted successfully'}), 200


@items_bp.route('/qr/<qr_code>/image', methods=['GET'])
def get_qr_image(qr_code):
    """Generate and return QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Encode the QR code with the freezer item URL
    qr_data = f"freezer-item:{qr_code}"
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


@items_bp.route('/expiring-soon', methods=['GET'])
@jwt_required()
def get_expiring_soon():
    """Get items expiring within the next 30 days"""
    days = request.args.get('days', 30, type=int)
    threshold_date = datetime.utcnow() + timedelta(days=days)

    items = Item.query.filter(
        Item.status == 'in_freezer',
        Item.expiration_date.isnot(None),
        Item.expiration_date <= threshold_date
    ).order_by(Item.expiration_date.asc()).all()

    return jsonify([item.to_dict() for item in items]), 200


@items_bp.route('/oldest', methods=['GET'])
@jwt_required()
def get_oldest_items():
    """Get oldest items in freezer"""
    limit = request.args.get('limit', 10, type=int)

    items = Item.query.filter_by(status='in_freezer')\
        .order_by(Item.added_date.asc())\
        .limit(limit)\
        .all()

    return jsonify([item.to_dict() for item in items]), 200


@items_bp.route('/lookup-upc/<upc>', methods=['GET'])
@jwt_required()
def lookup_upc(upc):
    """Lookup product information by UPC code

    First checks local database, then queries upcdatabase.org API if not found locally.
    Returns product information to auto-fill the add item form.
    """
    # First check if we have this UPC in our local database
    local_item = Item.query.filter_by(upc=upc).first()

    if local_item:
        return jsonify({
            'found': True,
            'source': 'local',
            'data': {
                'name': local_item.name,
                'brand': local_item.source,
                'category': local_item.category.name if local_item.category else None,
                'category_id': local_item.category_id,
                'notes': local_item.notes,
                'upc': local_item.upc
            },
            'message': f'You already have "{local_item.name}" in your inventory!'
        }), 200

    # Not found locally, try external API
    api_key = os.environ.get('UPC_API_KEY')

    if not api_key:
        return jsonify({
            'found': False,
            'source': 'none',
            'message': 'UPC API key not configured. Please enter item details manually.',
            'data': {'upc': upc}
        }), 200

    try:
        # Call upcdatabase.org API
        response = requests.get(
            f'https://api.upcdatabase.org/product/{upc}',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=5
        )

        if response.status_code == 200:
            api_data = response.json()

            # Log the response for debugging
            import logging
            logging.info(f"UPC API Response: {api_data}")

            # Extract relevant fields from API response
            # Handle both direct fields and nested 'items' array structure
            if 'items' in api_data and len(api_data['items']) > 0:
                product_data = api_data['items'][0]
            else:
                product_data = api_data

            product_name = product_data.get('title') or product_data.get('description', '') or product_data.get('brand', '') + ' ' + product_data.get('category', '')
            brand = product_data.get('brand', '')
            category = product_data.get('category', '')

            # Build notes with additional product info
            notes_parts = []
            if brand:
                notes_parts.append(f'Brand: {brand}')
            if category:
                notes_parts.append(f'Category: {category}')

            # Add other useful info if available
            if product_data.get('size'):
                notes_parts.append(f'Size: {product_data.get("size")}')
            if product_data.get('model'):
                notes_parts.append(f'Model: {product_data.get("model")}')

            notes = ' | '.join(notes_parts) if notes_parts else ''

            return jsonify({
                'found': True,
                'source': 'api',
                'data': {
                    'name': product_name,
                    'brand': brand,
                    'category': category,
                    'notes': notes,
                    'upc': upc
                },
                'message': f'Found product: {product_name}'
            }), 200
        elif response.status_code == 404:
            return jsonify({
                'found': False,
                'source': 'api',
                'message': 'UPC not found in database. Please enter item details manually.',
                'data': {'upc': upc}
            }), 200
        else:
            return jsonify({
                'found': False,
                'source': 'api',
                'message': f'UPC lookup failed. Please enter item details manually.',
                'data': {'upc': upc}
            }), 200

    except requests.RequestException as e:
        return jsonify({
            'found': False,
            'source': 'error',
            'message': 'UPC lookup service unavailable. Please enter item details manually.',
            'data': {'upc': upc}
        }), 200

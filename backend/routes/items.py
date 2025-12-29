from flask import Blueprint, request, jsonify, send_file, render_template_string
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Item, Category, User, Setting, generate_qr_code
from datetime import datetime, timedelta
import qrcode
import io
import requests
import os
import base64
import csv
import json as json_lib

items_bp = Blueprint('items', __name__)


def get_category_stock_image(category_name):
    """Get a stock image URL for a given category.

    Args:
        category_name: Name of the category

    Returns:
        str: URL to a category-appropriate stock image, or None
    """
    if not category_name:
        return None

    # Normalize category name for matching
    category_lower = category_name.lower()

    # Hardcoded stock images for each category
    # Order matters: more specific patterns first
    stock_images = {
        # Beef varieties (most specific first)
        'beef, steak': 'https://images.pexels.com/photos/6896518/pexels-photo-6896518.jpeg',
        'beef, roast': 'https://images.pexels.com/photos/11898916/pexels-photo-11898916.jpeg',
        'beef, ground': 'https://images.pexels.com/photos/128401/pexels-photo-128401.jpeg',

        # Pork varieties
        'pork, roast': 'https://images.pexels.com/photos/18015004/pexels-photo-18015004.jpeg',
        'pork, chops': 'https://images.pexels.com/photos/2676932/pexels-photo-2676932.jpeg',
        'pork, ground': 'https://images.pexels.com/photos/7225724/pexels-photo-7225724.jpeg',

        # Poultry varieties
        'chicken, ground': 'https://media.istockphoto.com/id/498579651/photo/serving-of-ground-chicken.jpg?s=2048x2048&w=is&k=20&c=2AAP2VANjHg16UHOfhakxqkGM8X-BQk-MkexRyv0U-U=',
        'chicken': 'https://images.pexels.com/photos/616354/pexels-photo-616354.jpeg',
        'turkey': 'https://images.pexels.com/photos/5847614/pexels-photo-5847614.jpeg',

        # Other proteins
        'fish': 'https://images.pexels.com/photos/30648983/pexels-photo-30648983.jpeg',

        # Produce
        'vegetables': 'https://images.pexels.com/photos/5870328/pexels-photo-5870328.jpeg',
        'fruits': 'https://images.pexels.com/photos/14854040/pexels-photo-14854040.jpeg',

        # Prepared foods
        'ice cream': 'https://images.pexels.com/photos/749102/pexels-photo-749102.jpeg',
        'appetizers': 'https://images.pexels.com/photos/9568318/pexels-photo-9568318.jpeg',
        'entrees': 'https://images.pexels.com/photos/5419303/pexels-photo-5419303.jpeg',
        'leftovers': 'https://images.pexels.com/photos/90893/pexels-photo-90893.jpeg',
        'prepared meals': 'https://images.pexels.com/photos/90893/pexels-photo-90893.jpeg',  # Legacy support
        'staples': 'https://images.pexels.com/photos/7965898/pexels-photo-7965898.jpeg',
    }

    # Find matching pattern (most specific match wins)
    for pattern, image_url in stock_images.items():
        if pattern in category_lower:
            return image_url

    # No specific mapping found
    return None


def fetch_product_image(product_name, category_name=None):
    """Fetch product image from Pexels API.

    Args:
        product_name: Name of the product to search for
        category_name: Optional category to refine search

    Returns:
        str: Image URL if found, None otherwise
    """
    # Check if image fetching is enabled (system setting)
    enable_images = Setting.query.filter_by(
        user_id=None,
        setting_name='enable_image_fetching'
    ).first()

    if not enable_images or enable_images.setting_value != 'true':
        return None

    # Check if Pexels API key is configured
    pexels_api_key = os.environ.get('PEXELS_API_KEY')
    if not pexels_api_key:
        return None

    try:
        # Build search query - use category + food for better results
        if category_name:
            search_query = f"{category_name} food"
        else:
            search_query = f"{product_name} food"

        # Call Pexels API
        response = requests.get(
            'https://api.pexels.com/v1/search',
            headers={'Authorization': pexels_api_key},
            params={
                'query': search_query,
                'per_page': 1,
                'orientation': 'square'
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                # Return medium-sized image URL
                return data['photos'][0]['src']['medium']

        return None

    except requests.RequestException:
        return None


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
    category = None
    if data.get('expiration_date'):
        expiration_date = datetime.fromisoformat(data['expiration_date'])
    elif data.get('category_id'):
        category = Category.query.get(data['category_id'])
        if category and category.default_expiration_days:
            # Use custom added_date if provided, otherwise use current time
            base_date = added_date or datetime.utcnow()
            expiration_date = base_date + timedelta(days=category.default_expiration_days)

    # Get image URL - priority: provided URL > category stock image
    image_url = data.get('image_url')
    if not image_url and not data.get('upc'):
        # No image URL and no UPC - use category-based stock image
        if not category and data.get('category_id'):
            category = Category.query.get(data['category_id'])
        if category:
            image_url = get_category_stock_image(category.name)

    item = Item(
        qr_code=qr_code,
        upc=data.get('upc'),
        image_url=image_url,
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
    if 'image_url' in data:
        item.image_url = data['image_url']
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
                'upc': local_item.upc,
                'image_url': local_item.image_url
            },
            'message': f'You already have "{local_item.name}" in your inventory!'
        }), 200

    # Not found locally, try external APIs
    # Priority: 1. UPC Item DB (free, good images), 2. UPCDatabase.org (requires key)

    # Try UPC Item DB API first (trial endpoint, no key required)
    try:
        response = requests.get(
            f'https://api.upcitemdb.com/prod/trial/lookup',
            params={'upc': upc},
            timeout=5
        )

        if response.status_code == 200:
            api_data = response.json()

            # Log the response for debugging
            import logging
            logging.info(f"UPC Item DB Response: {api_data}")

            # Check if product was found
            if api_data.get('code') == 'OK' and api_data.get('items'):
                product_data = api_data['items'][0]

                product_name = product_data.get('title', '')
                brand = product_data.get('brand', '')
                category = product_data.get('category', '')

                # Get product image from UPC Item DB
                image_url = None
                if product_data.get('images'):
                    # Use first image from array
                    image_url = product_data['images'][0]

                # If no image from UPC Item DB, try Pexels
                if not image_url:
                    image_url = fetch_product_image(product_name, category)

                return jsonify({
                    'found': True,
                    'source': 'upcitemdb',
                    'data': {
                        'name': product_name,
                        'brand': brand,
                        'category': category,
                        'notes': '',
                        'upc': upc,
                        'image_url': image_url
                    },
                    'message': f'Found product: {product_name}'
                }), 200

    except requests.RequestException as e:
        # UPC Item DB failed, will try fallback
        import logging
        logging.warning(f"UPC Item DB lookup failed: {e}")

    # Fallback to UPCDatabase.org API
    api_key = os.environ.get('UPC_API_KEY')

    if not api_key:
        return jsonify({
            'found': False,
            'source': 'none',
            'message': 'UPC not found. Please enter item details manually.',
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
            logging.info(f"UPCDatabase.org Response: {api_data}")

            # Extract relevant fields from API response
            # Handle both direct fields and nested 'items' array structure
            if 'items' in api_data and len(api_data['items']) > 0:
                product_data = api_data['items'][0]
            else:
                product_data = api_data

            product_name = product_data.get('title') or product_data.get('description', '') or product_data.get('brand', '') + ' ' + product_data.get('category', '')
            brand = product_data.get('brand', '')
            category = product_data.get('category', '')

            # Try to get product image
            # Priority: 1. UPC API image, 2. Pexels search
            image_url = product_data.get('images', [None])[0] if product_data.get('images') else None

            # If no image from UPC API, try Pexels
            if not image_url:
                image_url = fetch_product_image(product_name, category)

            return jsonify({
                'found': True,
                'source': 'upcdatabase',
                'data': {
                    'name': product_name,
                    'brand': brand,
                    'category': category,
                    'notes': '',
                    'upc': upc,
                    'image_url': image_url
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


@items_bp.route('/search-image', methods=['POST'])
@jwt_required()
def search_image():
    """Search for product image using Pexels API.

    Accepts JSON body with 'product_name' and optional 'category_name'.
    Returns image URL if found.
    """
    data = request.get_json()

    if not data or not data.get('product_name'):
        return jsonify({'error': 'Product name is required'}), 400

    product_name = data['product_name']
    category_name = data.get('category_name')

    image_url = fetch_product_image(product_name, category_name)

    if image_url:
        return jsonify({
            'found': True,
            'image_url': image_url,
            'message': 'Image found successfully'
        }), 200
    else:
        return jsonify({
            'found': False,
            'image_url': None,
            'message': 'No image found or image fetching disabled'
        }), 200


@items_bp.route('/print-labels', methods=['POST'])
@jwt_required()
def print_labels():
    """Generate printable QR code labels for selected items.

    Accepts JSON body with:
    - item_ids: List of item IDs to print labels for
    - show_name: Boolean, include item name on label
    - show_expiration: Boolean, include expiration date on label
    - show_category: Boolean, include category on label
    - show_weight: Boolean, include weight/size on label
    """
    data = request.get_json()

    if not data or not data.get('item_ids'):
        return jsonify({'error': 'item_ids is required'}), 400

    item_ids = data['item_ids']
    show_name = data.get('show_name', False)
    show_expiration = data.get('show_expiration', False)
    show_category = data.get('show_category', False)
    show_weight = data.get('show_weight', False)

    # Fetch items
    items = Item.query.filter(Item.id.in_(item_ids)).all()

    if not items:
        return jsonify({'error': 'No items found'}), 404

    # Generate QR code images as base64
    labels_data = []
    for item in items:
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr_data = f"freezer-item:{item.qr_code}"
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode()

        # Build label data
        label_info = {
            'qr_code': item.qr_code,
            'qr_image': f"data:image/png;base64,{img_base64}",
        }

        if show_name:
            label_info['name'] = item.name
        if show_expiration and item.expiration_date:
            label_info['expiration'] = item.expiration_date.strftime('%m/%d/%Y')
        if show_category and item.category:
            label_info['category'] = item.category.name
        if show_weight and item.weight:
            label_info['weight'] = f"{item.weight} {item.weight_unit}"

        labels_data.append(label_info)

    # Generate HTML template for printing
    html_template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Freezer Inventory Labels</title>
    <style>
        @page {
            size: letter;
            margin: 0.5in;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }

        .label-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.25in;
            padding: 0;
        }

        .label {
            width: 1.5in;
            height: 1.5in;
            border: 1px solid #000;
            padding: 0.1in;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            page-break-inside: avoid;
            background: white;
        }

        .label img {
            width: 0.9in;
            height: 0.9in;
            margin-bottom: 0.05in;
        }

        .label .qr-code-text {
            font-size: 11pt;
            font-weight: bold;
            margin-bottom: 0.03in;
            font-family: 'Courier New', monospace;
        }

        .label .info {
            font-size: 7pt;
            line-height: 1.1;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .label .info-line {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 1.3in;
        }

        @media print {
            .no-print {
                display: none !important;
            }

            body {
                margin: 0;
                padding: 0;
            }
        }

        .print-button {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .print-button:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <button class="print-button no-print" onclick="window.print()">🖨️ Print Labels</button>

    <div class="label-container">
        {% for label in labels %}
        <div class="label">
            <img src="{{ label.qr_image }}" alt="QR Code">
            <div class="qr-code-text">{{ label.qr_code }}</div>
            {% if label.name or label.expiration or label.category or label.weight %}
            <div class="info">
                {% if label.name %}
                <div class="info-line"><strong>{{ label.name }}</strong></div>
                {% endif %}
                {% if label.category %}
                <div class="info-line">{{ label.category }}</div>
                {% endif %}
                {% if label.weight %}
                <div class="info-line">{{ label.weight }}</div>
                {% endif %}
                {% if label.expiration %}
                <div class="info-line">Exp: {{ label.expiration }}</div>
                {% endif %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
    '''

    html = render_template_string(html_template, labels=labels_data)
    return html, 200, {'Content-Type': 'text/html'}


@items_bp.route('/export/csv', methods=['GET'])
@jwt_required()
def export_csv():
    """Export all items to CSV format.

    Query parameters:
    - status: Filter by status (in_freezer, consumed, thrown_out, all)
    """
    current_user_id = int(get_jwt_identity())
    status = request.args.get('status', 'in_freezer')

    # Build query
    query = Item.query

    if status != 'all':
        query = query.filter_by(status=status)

    items = query.all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'QR Code', 'UPC', 'Name', 'Category', 'Source', 'Weight',
        'Weight Unit', 'Added Date', 'Expiration Date', 'Status',
        'Removed Date', 'Notes'
    ])

    # Write data
    for item in items:
        writer.writerow([
            item.qr_code,
            item.upc or '',
            item.name,
            item.category.name if item.category else '',
            item.source or '',
            item.weight or '',
            item.weight_unit or '',
            item.added_date.isoformat() if item.added_date else '',
            item.expiration_date.isoformat() if item.expiration_date else '',
            item.status,
            item.removed_date.isoformat() if item.removed_date else '',
            item.notes or ''
        ])

    # Prepare response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'freezer_inventory_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@items_bp.route('/export/json', methods=['GET'])
@jwt_required()
def export_json():
    """Export all items to JSON format.

    Query parameters:
    - status: Filter by status (in_freezer, consumed, thrown_out, all)
    """
    current_user_id = int(get_jwt_identity())
    status = request.args.get('status', 'in_freezer')

    # Build query
    query = Item.query

    if status != 'all':
        query = query.filter_by(status=status)

    items = query.all()

    # Convert to JSON-serializable format
    items_data = []
    for item in items:
        item_dict = {
            'qr_code': item.qr_code,
            'upc': item.upc,
            'image_url': item.image_url,
            'name': item.name,
            'category': item.category.name if item.category else None,
            'source': item.source,
            'weight': item.weight,
            'weight_unit': item.weight_unit,
            'added_date': item.added_date.isoformat() if item.added_date else None,
            'expiration_date': item.expiration_date.isoformat() if item.expiration_date else None,
            'status': item.status,
            'removed_date': item.removed_date.isoformat() if item.removed_date else None,
            'notes': item.notes
        }
        items_data.append(item_dict)

    # Create JSON response
    json_data = json_lib.dumps({
        'exported_at': datetime.utcnow().isoformat(),
        'total_items': len(items_data),
        'items': items_data
    }, indent=2)

    return send_file(
        io.BytesIO(json_data.encode('utf-8')),
        mimetype='application/json',
        as_attachment=True,
        download_name=f'freezer_inventory_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
    )


@items_bp.route('/import/csv', methods=['POST'])
@jwt_required()
def import_csv():
    """Import items from CSV file.

    Expects a CSV file with columns:
    QR Code, UPC, Name, Category, Source, Weight, Weight Unit,
    Added Date, Expiration Date, Status, Removed Date, Notes

    Returns summary of imported items.
    """
    current_user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        csv_reader = csv.DictReader(stream)

        imported = 0
        skipped = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Get or create category
                category = None
                if row.get('Category'):
                    category = Category.query.filter_by(name=row['Category']).first()
                    if not category:
                        # Create category if it doesn't exist
                        category = Category(
                            name=row['Category'],
                            default_expiration_days=180,
                            created_by_user_id=current_user_id
                        )
                        db.session.add(category)
                        db.session.flush()  # Get the ID

                # Generate or use provided QR code
                qr_code = row.get('QR Code') or generate_qr_code()

                # Check if item already exists
                if Item.query.filter_by(qr_code=qr_code).first():
                    skipped += 1
                    errors.append(f"Row {row_num}: QR code '{qr_code}' already exists")
                    continue

                # Parse dates
                added_date = None
                if row.get('Added Date'):
                    try:
                        added_date = datetime.fromisoformat(row['Added Date'].replace('Z', '+00:00'))
                    except ValueError:
                        pass

                expiration_date = None
                if row.get('Expiration Date'):
                    try:
                        expiration_date = datetime.fromisoformat(row['Expiration Date'].replace('Z', '+00:00'))
                    except ValueError:
                        pass

                removed_date = None
                if row.get('Removed Date'):
                    try:
                        removed_date = datetime.fromisoformat(row['Removed Date'].replace('Z', '+00:00'))
                    except ValueError:
                        pass

                # Create item
                item = Item(
                    qr_code=qr_code,
                    upc=row.get('UPC') or None,
                    name=row.get('Name') or 'Unnamed Item',
                    source=row.get('Source') or None,
                    weight=float(row['Weight']) if row.get('Weight') else None,
                    weight_unit=row.get('Weight Unit') or 'lb',
                    category_id=category.id if category else None,
                    added_date=added_date,
                    expiration_date=expiration_date,
                    status=row.get('Status') or 'in_freezer',
                    removed_date=removed_date,
                    notes=row.get('Notes') or None,
                    added_by_user_id=current_user_id
                )

                db.session.add(item)
                imported += 1

            except Exception as e:
                skipped += 1
                errors.append(f"Row {row_num}: {str(e)}")

        db.session.commit()

        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors[:10]  # Limit to first 10 errors
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to import CSV: {str(e)}'}), 500


@items_bp.route('/import/json', methods=['POST'])
@jwt_required()
def import_json():
    """Import items from JSON file.

    Expects a JSON file with structure:
    {
      "items": [
        {
          "qr_code": "ABC123",
          "name": "Item name",
          "category": "Category name",
          ...
        }
      ]
    }

    Returns summary of imported items.
    """
    current_user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.json'):
        return jsonify({'error': 'File must be a JSON'}), 400

    try:
        # Read JSON file
        data = json_lib.load(file.stream)

        if 'items' not in data or not isinstance(data['items'], list):
            return jsonify({'error': 'Invalid JSON format. Expected {"items": [...]}'}), 400

        imported = 0
        skipped = 0
        errors = []

        for idx, item_data in enumerate(data['items'], start=1):
            try:
                # Get or create category
                category = None
                if item_data.get('category'):
                    category = Category.query.filter_by(name=item_data['category']).first()
                    if not category:
                        # Create category if it doesn't exist
                        category = Category(
                            name=item_data['category'],
                            default_expiration_days=180,
                            created_by_user_id=current_user_id
                        )
                        db.session.add(category)
                        db.session.flush()

                # Generate or use provided QR code
                qr_code = item_data.get('qr_code') or generate_qr_code()

                # Check if item already exists
                if Item.query.filter_by(qr_code=qr_code).first():
                    skipped += 1
                    errors.append(f"Item {idx}: QR code '{qr_code}' already exists")
                    continue

                # Parse dates
                added_date = None
                if item_data.get('added_date'):
                    try:
                        added_date = datetime.fromisoformat(item_data['added_date'].replace('Z', '+00:00'))
                    except ValueError:
                        pass

                expiration_date = None
                if item_data.get('expiration_date'):
                    try:
                        expiration_date = datetime.fromisoformat(item_data['expiration_date'].replace('Z', '+00:00'))
                    except ValueError:
                        pass

                removed_date = None
                if item_data.get('removed_date'):
                    try:
                        removed_date = datetime.fromisoformat(item_data['removed_date'].replace('Z', '+00:00'))
                    except ValueError:
                        pass

                # Create item
                item = Item(
                    qr_code=qr_code,
                    upc=item_data.get('upc'),
                    image_url=item_data.get('image_url'),
                    name=item_data.get('name') or 'Unnamed Item',
                    source=item_data.get('source'),
                    weight=item_data.get('weight'),
                    weight_unit=item_data.get('weight_unit') or 'lb',
                    category_id=category.id if category else None,
                    added_date=added_date,
                    expiration_date=expiration_date,
                    status=item_data.get('status') or 'in_freezer',
                    removed_date=removed_date,
                    notes=item_data.get('notes'),
                    added_by_user_id=current_user_id
                )

                db.session.add(item)
                imported += 1

            except Exception as e:
                skipped += 1
                errors.append(f"Item {idx}: {str(e)}")

        db.session.commit()

        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors[:10]  # Limit to first 10 errors
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to import JSON: {str(e)}'}), 500

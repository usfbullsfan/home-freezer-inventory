from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Category
from routes.items import get_category_stock_image

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all categories"""
    categories = Category.query.order_by(Category.name).all()
    return jsonify([category.to_dict() for category in categories]), 200


@categories_bp.route('/<int:category_id>', methods=['GET'])
@jwt_required()
def get_category(category_id):
    """Get a specific category"""
    category = db.session.get(Category, category_id)

    if not category:
        return jsonify({'error': 'Category not found'}), 404

    return jsonify(category.to_dict()), 200


@categories_bp.route('/', methods=['POST'])
@jwt_required()
def create_category():
    """Create a new category"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Category name is required'}), 400

    # Check if category already exists
    if Category.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Category already exists'}), 400

    category = Category(
        name=data['name'],
        default_expiration_days=data.get('default_expiration_days', 180),
        image_url=data.get('image_url'),
        created_by_user_id=current_user_id
    )

    db.session.add(category)
    db.session.commit()

    return jsonify(category.to_dict()), 201


@categories_bp.route('/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    """Update an existing category"""
    category = db.session.get(Category, category_id)

    if not category:
        return jsonify({'error': 'Category not found'}), 404

    if category.is_system:
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Cannot modify system category'}), 403

    data = request.get_json()

    if 'name' in data:
        # Check if new name already exists
        existing = Category.query.filter(
            Category.name == data['name'],
            Category.id != category_id
        ).first()
        if existing:
            return jsonify({'error': 'Category name already exists'}), 400
        category.name = data['name']

    if 'default_expiration_days' in data:
        category.default_expiration_days = data['default_expiration_days']

    if 'image_url' in data:
        category.image_url = data['image_url']

    db.session.commit()

    return jsonify(category.to_dict()), 200


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    """Delete a category (admin only)"""
    # Check if user is admin
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    category = db.session.get(Category, category_id)

    if not category:
        return jsonify({'error': 'Category not found'}), 404

    if category.is_system:
        return jsonify({'error': 'Cannot delete system category'}), 403

    # Check if category has items
    if category.items:
        return jsonify({'error': 'Cannot delete category with existing items'}), 400

    db.session.delete(category)
    db.session.commit()

    return jsonify({'message': 'Category deleted successfully'}), 200


@categories_bp.route('/<int:category_id>/stock-image', methods=['GET'])
@jwt_required()
def get_category_stock_image_url(category_id):
    """Get the stock image URL for a category"""
    category = db.session.get(Category, category_id)

    if not category:
        return jsonify({'error': 'Category not found'}), 404

    # Prioritize custom category image, then fall back to hardcoded stock image
    image_url = category.image_url if category.image_url else get_category_stock_image(category.name)

    return jsonify({
        'category_id': category_id,
        'category_name': category.name,
        'stock_image_url': image_url
    }), 200

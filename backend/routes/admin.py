from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func
from models import db, Item, LowStockAlert

admin_bp = Blueprint('admin', __name__)


def _require_admin():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None


# ── Item name cleanup ─────────────────────────────────────────────────────────

@admin_bp.route('/cleanup/names', methods=['GET'])
@jwt_required()
def list_names():
    """List all distinct item names with active and total item counts."""
    err = _require_admin()
    if err:
        return err

    rows = (
        db.session.query(Item.name, func.count(Item.id).label('total_count'))
        .group_by(Item.name)
        .order_by(Item.name)
        .all()
    )

    active_counts = dict(
        db.session.query(Item.name, func.count(Item.id))
        .filter(Item.status == 'in_freezer')
        .group_by(Item.name)
        .all()
    )

    return jsonify([
        {
            'name': row.name,
            'total_count': row.total_count,
            'active_count': active_counts.get(row.name, 0),
        }
        for row in rows
    ]), 200


@admin_bp.route('/cleanup/names', methods=['PATCH'])
@jwt_required()
def rename_name():
    """Rename all items from old_name to new_name (all statuses)."""
    err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}
    old_name = (data.get('old_name') or '').strip()
    new_name = (data.get('new_name') or '').strip()

    if not old_name or not new_name:
        return jsonify({'error': 'old_name and new_name are required'}), 400
    if old_name == new_name:
        return jsonify({'error': 'New name is the same as the old name'}), 400

    updated = Item.query.filter_by(name=old_name).update({'name': new_name})

    # Also update any low-stock alerts referencing the old name
    LowStockAlert.query.filter(
        func.lower(LowStockAlert.item_name) == old_name.lower()
    ).update({'item_name': new_name}, synchronize_session=False)

    db.session.commit()
    return jsonify({'updated_count': updated}), 200


@admin_bp.route('/cleanup/names', methods=['DELETE'])
@jwt_required()
def delete_name():
    """Permanently delete all item records with this name.

    Blocked if any items with this name are currently in the freezer.
    Also removes associated low-stock alerts.
    """
    err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400

    active_count = Item.query.filter_by(name=name, status='in_freezer').count()
    if active_count > 0:
        return jsonify({
            'error': f'Cannot delete: {active_count} item(s) with this name are currently in the freezer'
        }), 409

    deleted = Item.query.filter_by(name=name).delete()

    # Clean up low-stock alerts for this name
    LowStockAlert.query.filter(
        func.lower(LowStockAlert.item_name) == name.lower()
    ).delete(synchronize_session=False)

    db.session.commit()
    return jsonify({'deleted_count': deleted}), 200


# ── Source (store) cleanup ────────────────────────────────────────────────────

@admin_bp.route('/cleanup/sources', methods=['GET'])
@jwt_required()
def list_sources():
    """List all distinct source values with active and total item counts."""
    err = _require_admin()
    if err:
        return err

    rows = (
        db.session.query(Item.source, func.count(Item.id).label('total_count'))
        .filter(Item.source.isnot(None), Item.source != '')
        .group_by(Item.source)
        .order_by(Item.source)
        .all()
    )

    active_counts = dict(
        db.session.query(Item.source, func.count(Item.id))
        .filter(Item.status == 'in_freezer', Item.source.isnot(None), Item.source != '')
        .group_by(Item.source)
        .all()
    )

    return jsonify([
        {
            'source': row.source,
            'total_count': row.total_count,
            'active_count': active_counts.get(row.source, 0),
        }
        for row in rows
    ]), 200


@admin_bp.route('/cleanup/sources', methods=['PATCH'])
@jwt_required()
def rename_source():
    """Rename all items from old_source to new_source (all statuses)."""
    err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}
    old_source = (data.get('old_source') or '').strip()
    new_source = (data.get('new_source') or '').strip()

    if not old_source or not new_source:
        return jsonify({'error': 'old_source and new_source are required'}), 400
    if old_source == new_source:
        return jsonify({'error': 'New source is the same as the old source'}), 400

    updated = Item.query.filter_by(source=old_source).update({'source': new_source})
    db.session.commit()
    return jsonify({'updated_count': updated}), 200


@admin_bp.route('/cleanup/sources', methods=['DELETE'])
@jwt_required()
def delete_source():
    """Clear the source field from all items with this source value.

    Blocked if any items with this source are currently in the freezer.
    """
    err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}
    source = (data.get('source') or '').strip()
    if not source:
        return jsonify({'error': 'source is required'}), 400

    active_count = Item.query.filter_by(source=source, status='in_freezer').count()
    if active_count > 0:
        return jsonify({
            'error': f'Cannot delete: {active_count} item(s) with this store are currently in the freezer'
        }), 409

    updated = Item.query.filter_by(source=source).update({'source': None})
    db.session.commit()
    return jsonify({'updated_count': updated}), 200

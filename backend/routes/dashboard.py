from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import db, Item, Category
from datetime import datetime, timedelta
from sqlalchemy import func, extract

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Return aggregated inventory statistics for the dashboard."""
    now = datetime.utcnow()

    # --- Summary counts ---
    total_in_freezer = Item.query.filter_by(status='in_freezer').count()
    total_consumed = Item.query.filter_by(status='consumed').count()
    total_thrown_out = Item.query.filter_by(status='thrown_out').count()

    expiring_soon = Item.query.filter(
        Item.status == 'in_freezer',
        Item.expiration_date != None,
        Item.expiration_date <= now + timedelta(days=30)
    ).count()

    expired = Item.query.filter(
        Item.status == 'in_freezer',
        Item.expiration_date != None,
        Item.expiration_date < now
    ).count()

    # --- Items by category (current freezer contents) ---
    category_rows = (
        db.session.query(Category.name, func.count(Item.id).label('count'))
        .join(Item, Item.category_id == Category.id)
        .filter(Item.status == 'in_freezer')
        .group_by(Category.id, Category.name)
        .order_by(func.count(Item.id).desc())
        .all()
    )
    items_by_category = [{'category': row.name, 'count': row.count} for row in category_rows]

    # Items with no category
    no_category_count = Item.query.filter(
        Item.status == 'in_freezer',
        Item.category_id == None
    ).count()
    if no_category_count:
        items_by_category.append({'category': 'Uncategorized', 'count': no_category_count})

    # --- Oldest items in freezer (top 10) ---
    oldest_items_rows = (
        Item.query
        .filter_by(status='in_freezer')
        .order_by(Item.added_date.asc())
        .limit(10)
        .all()
    )
    oldest_items = []
    for item in oldest_items_rows:
        days_in_freezer = (now - item.added_date).days
        oldest_items.append({
            'id': item.id,
            'name': item.name,
            'category': item.category.name if item.category else 'Uncategorized',
            'added_date': item.added_date.isoformat(),
            'days_in_freezer': days_in_freezer,
        })

    # --- Expiration timeline: items expiring per month over next 12 months ---
    expiration_timeline = []
    for i in range(12):
        month_start = (now.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        if i < 11:
            month_end = (month_start + timedelta(days=32)).replace(day=1)
        else:
            month_end = (month_start + timedelta(days=32)).replace(day=1)

        count = Item.query.filter(
            Item.status == 'in_freezer',
            Item.expiration_date != None,
            Item.expiration_date >= month_start,
            Item.expiration_date < month_end
        ).count()

        expiration_timeline.append({
            'month': month_start.strftime('%b %Y'),
            'count': count,
        })

    # --- Consumption patterns: items removed per month over past 12 months ---
    consumption_patterns = []
    for i in range(11, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=32 * i)).replace(day=1)
        if i > 0:
            month_end = (now.replace(day=1) - timedelta(days=32 * (i - 1))).replace(day=1)
        else:
            # Current month: end is today
            month_end = now

        consumed_count = Item.query.filter(
            Item.status == 'consumed',
            Item.removed_date != None,
            Item.removed_date >= month_start,
            Item.removed_date < month_end
        ).count()

        thrown_count = Item.query.filter(
            Item.status == 'thrown_out',
            Item.removed_date != None,
            Item.removed_date >= month_start,
            Item.removed_date < month_end
        ).count()

        consumption_patterns.append({
            'month': month_start.strftime('%b %Y'),
            'consumed': consumed_count,
            'thrown_out': thrown_count,
        })

    # --- Items added per month over past 12 months ---
    added_per_month = []
    for i in range(11, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=32 * i)).replace(day=1)
        if i > 0:
            month_end = (now.replace(day=1) - timedelta(days=32 * (i - 1))).replace(day=1)
        else:
            month_end = now

        count = Item.query.filter(
            Item.added_date >= month_start,
            Item.added_date < month_end
        ).count()

        added_per_month.append({
            'month': month_start.strftime('%b %Y'),
            'count': count,
        })

    return jsonify({
        'summary': {
            'total_in_freezer': total_in_freezer,
            'total_consumed': total_consumed,
            'total_thrown_out': total_thrown_out,
            'expiring_soon': expiring_soon,
            'expired': expired,
        },
        'items_by_category': items_by_category,
        'oldest_items': oldest_items,
        'expiration_timeline': expiration_timeline,
        'consumption_patterns': consumption_patterns,
        'added_per_month': added_per_month,
    })

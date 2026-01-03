#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

This script migrates data from a SQLite database to PostgreSQL.
It preserves all data including users, categories, items, and settings.

Usage:
    python migrate_sqlite_to_postgres.py

Environment Variables Required:
    DATABASE_URL - PostgreSQL connection string
                   Format: postgresql://user:password@host:port/database

Optional Environment Variables:
    SQLITE_DB_PATH - Path to SQLite database
                     Default: instance/freezer_inventory.db
"""

import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, inspect
from models import db, User, Category, Item, Setting
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_sqlite_app():
    """Create Flask app connected to SQLite database"""
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_filename = os.environ.get('SQLITE_DB_PATH', 'instance/freezer_inventory.db')
    db_path = os.path.join(basedir, db_filename)

    if not os.path.exists(db_path):
        print(f"ERROR: SQLite database not found at: {db_path}")
        print("Please set SQLITE_DB_PATH environment variable or ensure database exists.")
        sys.exit(1)

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    print(f"✓ Connected to SQLite database: {db_path}")
    return app


def create_postgres_app():
    """Create Flask app connected to PostgreSQL database"""
    app = Flask(__name__)
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Format: postgresql://user:password@host:port/database")
        sys.exit(1)

    # Handle postgres:// vs postgresql:// prefix (some services use postgres://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Test connection
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            print(f"✓ Connected to PostgreSQL database")
    except Exception as e:
        print(f"ERROR: Could not connect to PostgreSQL: {e}")
        sys.exit(1)

    return app


def check_postgres_empty(app):
    """Check if PostgreSQL database is empty"""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if tables:
            print(f"\nWARNING: PostgreSQL database is not empty. Found tables: {tables}")
            response = input("Do you want to continue? This will DROP all tables and recreate them. (yes/no): ")
            if response.lower() != 'yes':
                print("Migration cancelled.")
                sys.exit(0)
            return False
        return True


def migrate_data():
    """Main migration function"""
    print("\n" + "="*60)
    print("SQLite to PostgreSQL Migration")
    print("="*60 + "\n")

    # Create connections
    print("Step 1: Connecting to databases...")
    sqlite_app = create_sqlite_app()
    postgres_app = create_postgres_app()

    # Check if PostgreSQL is empty
    print("\nStep 2: Checking PostgreSQL database...")
    is_empty = check_postgres_empty(postgres_app)

    # Create PostgreSQL schema
    print("\nStep 3: Creating PostgreSQL schema...")
    with postgres_app.app_context():
        db.drop_all()  # Drop existing tables if any
        db.create_all()
        print("✓ PostgreSQL tables created")

    # Migrate data
    print("\nStep 4: Migrating data...")

    stats = {
        'users': 0,
        'categories': 0,
        'items': 0,
        'settings': 0
    }

    # Read from SQLite
    with sqlite_app.app_context():
        users_data = User.query.all()
        categories_data = Category.query.all()
        items_data = Item.query.all()
        settings_data = Setting.query.all()

        print(f"  Found {len(users_data)} users")
        print(f"  Found {len(categories_data)} categories")
        print(f"  Found {len(items_data)} items")
        print(f"  Found {len(settings_data)} settings")

    # Write to PostgreSQL
    with postgres_app.app_context():
        try:
            # Migrate users
            for user in users_data:
                new_user = User(
                    id=user.id,
                    username=user.username,
                    password_hash=user.password_hash,
                    role=user.role,
                    created_at=user.created_at
                )
                db.session.add(new_user)
                stats['users'] += 1

            db.session.commit()
            print(f"  ✓ Migrated {stats['users']} users")

            # Migrate categories
            for category in categories_data:
                new_category = Category(
                    id=category.id,
                    name=category.name,
                    default_expiration_days=category.default_expiration_days,
                    image_url=category.image_url,
                    created_by_user_id=category.created_by_user_id,
                    created_at=category.created_at,
                    is_system=category.is_system
                )
                db.session.add(new_category)
                stats['categories'] += 1

            db.session.commit()
            print(f"  ✓ Migrated {stats['categories']} categories")

            # Migrate items
            for item in items_data:
                new_item = Item(
                    id=item.id,
                    qr_code=item.qr_code,
                    upc=item.upc,
                    image_url=item.image_url,
                    name=item.name,
                    source=item.source,
                    weight=item.weight,
                    weight_unit=item.weight_unit,
                    category_id=item.category_id,
                    added_date=item.added_date,
                    expiration_date=item.expiration_date,
                    status=item.status,
                    removed_date=item.removed_date,
                    notes=item.notes,
                    added_by_user_id=item.added_by_user_id,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                )
                db.session.add(new_item)
                stats['items'] += 1

            db.session.commit()
            print(f"  ✓ Migrated {stats['items']} items")

            # Migrate settings
            for setting in settings_data:
                new_setting = Setting(
                    id=setting.id,
                    user_id=setting.user_id,
                    setting_name=setting.setting_name,
                    setting_value=setting.setting_value
                )
                db.session.add(new_setting)
                stats['settings'] += 1

            db.session.commit()
            print(f"  ✓ Migrated {stats['settings']} settings")

            # Update sequences for PostgreSQL
            # PostgreSQL uses sequences for auto-increment, need to update them
            if stats['users'] > 0:
                max_user_id = db.session.query(db.func.max(User.id)).scalar()
                db.session.execute(db.text(f"SELECT setval('users_id_seq', {max_user_id})"))

            if stats['categories'] > 0:
                max_category_id = db.session.query(db.func.max(Category.id)).scalar()
                db.session.execute(db.text(f"SELECT setval('categories_id_seq', {max_category_id})"))

            if stats['items'] > 0:
                max_item_id = db.session.query(db.func.max(Item.id)).scalar()
                db.session.execute(db.text(f"SELECT setval('items_id_seq', {max_item_id})"))

            if stats['settings'] > 0:
                max_setting_id = db.session.query(db.func.max(Setting.id)).scalar()
                db.session.execute(db.text(f"SELECT setval('settings_id_seq', {max_setting_id})"))

            db.session.commit()
            print(f"  ✓ Updated PostgreSQL sequences")

        except Exception as e:
            db.session.rollback()
            print(f"\nERROR during migration: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    # Summary
    print("\n" + "="*60)
    print("Migration completed successfully!")
    print("="*60)
    print(f"\nMigrated:")
    print(f"  • {stats['users']} users")
    print(f"  • {stats['categories']} categories")
    print(f"  • {stats['items']} items")
    print(f"  • {stats['settings']} settings")
    print(f"\nYour application is now ready to use PostgreSQL.")
    print(f"Make sure to set DATABASE_URL in your .env file or environment.")
    print("\n")


if __name__ == '__main__':
    migrate_data()

#!/usr/bin/env python3
"""
Migration script to add image_url column to categories table.
Run this once to update your database schema.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db

def migrate():
    """Add image_url column to categories table"""
    app = create_app()

    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(db.text("PRAGMA table_info(categories)"))
            columns = [row[1] for row in result]

            if 'image_url' in columns:
                print("✓ Migration already applied - image_url column exists")
                return

            print("Adding image_url column to categories table...")

            # Add the new column
            db.session.execute(db.text(
                "ALTER TABLE categories ADD COLUMN image_url VARCHAR(500)"
            ))
            db.session.commit()

            print("✓ Successfully added image_url column to categories table")

        except Exception as e:
            print(f"✗ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()

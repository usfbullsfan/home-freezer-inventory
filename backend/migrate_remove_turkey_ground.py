#!/usr/bin/env python3
"""
Migration Script: Remove Turkey, Ground Category

This script removes the "Turkey, Ground" category and reassigns any items
using it to the "Turkey" category.

Usage:
    python migrate_remove_turkey_ground.py

The script is idempotent and can be run multiple times safely.
"""

import sqlite3
import os
import sys
from datetime import datetime


def migrate_database():
    """Remove Turkey, Ground category and reassign items."""

    # Get database path from environment or check common locations
    db_path = os.environ.get('DATABASE_PATH')

    if not db_path:
        # Check common locations
        possible_paths = [
            'freezer_inventory.db',  # Current directory
            '../freezer_inventory.db',  # Parent directory
            'backend/freezer_inventory.db',  # If run from root
            os.path.expanduser('~/freezer_inventory.db'),  # Home directory
        ]

        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break

        if not db_path:
            print("❌ Database not found in common locations:")
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                print(f"   - {abs_path}")
            print()
            print("   Please set DATABASE_PATH environment variable:")
            print("   export DATABASE_PATH=/path/to/freezer_inventory.db")
            sys.exit(1)

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        sys.exit(1)

    abs_path = os.path.abspath(db_path)
    print(f"🔧 Migrating database: {abs_path}")
    print()

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Show ALL categories to help debug
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        all_categories = cursor.fetchall()

        print("📋 All categories in database:")
        for cat_id, cat_name in all_categories:
            print(f"   - ID {cat_id}: '{cat_name}'")
        print()

        # First, let's see all turkey-related categories
        cursor.execute("SELECT id, name FROM categories WHERE name LIKE '%urkey%'")
        turkey_categories = cursor.fetchall()

        if turkey_categories:
            print("📋 Found turkey-related categories:")
            for cat_id, cat_name in turkey_categories:
                print(f"   - ID {cat_id}: '{cat_name}'")
            print()

        # Find Turkey, Ground category (try different variations)
        cursor.execute(
            "SELECT id FROM categories WHERE name IN (?, ?, ?, ?)",
            ('Turkey, Ground', 'Turkey Ground', 'turkey, ground', 'Turkey,Ground')
        )
        turkey_ground = cursor.fetchone()

        if not turkey_ground:
            print("✅ Turkey, Ground category not found - already removed or never existed")
            print("   (Checked variations: 'Turkey, Ground', 'Turkey Ground', etc.)")
            return

        turkey_ground_id = turkey_ground[0]

        # Get the actual name
        cursor.execute("SELECT name FROM categories WHERE id = ?", (turkey_ground_id,))
        actual_name = cursor.fetchone()[0]
        print(f"📋 Found '{actual_name}' category (ID: {turkey_ground_id})")

        # Find Turkey category (to reassign items)
        cursor.execute("SELECT id FROM categories WHERE name = ?", ('Turkey',))
        turkey = cursor.fetchone()

        if not turkey:
            print("⚠️  Turkey category not found - creating it first")
            cursor.execute(
                "INSERT INTO categories (name, default_expiration_days, is_system) VALUES (?, ?, ?)",
                ('Turkey', 270, True)
            )
            cursor.execute("SELECT id FROM categories WHERE name = ?", ('Turkey',))
            turkey = cursor.fetchone()

        turkey_id = turkey[0]

        # Check for items using Turkey, Ground
        cursor.execute("SELECT COUNT(*) FROM items WHERE category_id = ?", (turkey_ground_id,))
        item_count = cursor.fetchone()[0]

        if item_count > 0:
            print(f"📦 Found {item_count} item(s) using 'Turkey, Ground' category")
            print(f"   → Reassigning to 'Turkey' category (ID: {turkey_id})")

            # Reassign items from Turkey, Ground to Turkey
            cursor.execute(
                "UPDATE items SET category_id = ? WHERE category_id = ?",
                (turkey_id, turkey_ground_id)
            )
            print(f"   ✅ Reassigned {item_count} item(s)")
        else:
            print("   No items using this category")

        # Delete Turkey, Ground category
        cursor.execute("DELETE FROM categories WHERE id = ?", (turkey_ground_id,))
        print(f"🗑️  Removed 'Turkey, Ground' category")

        # Commit changes
        conn.commit()
        print()
        print("✅ Migration completed successfully!")
        print()

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == '__main__':
    print()
    print("=" * 60)
    print("Remove Turkey, Ground Category Migration")
    print("=" * 60)
    print()

    migrate_database()

    print("=" * 60)
    print()

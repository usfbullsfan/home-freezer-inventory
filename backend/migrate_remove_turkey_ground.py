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

    # Get database path from environment or use default
    db_path = os.environ.get('DATABASE_PATH', 'freezer_inventory.db')

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("   Please ensure you're running this from the backend directory")
        print("   or set DATABASE_PATH environment variable")
        sys.exit(1)

    print(f"🔧 Migrating database: {db_path}")
    print()

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Find Turkey, Ground category
        cursor.execute("SELECT id FROM categories WHERE name = ?", ('Turkey, Ground',))
        turkey_ground = cursor.fetchone()

        if not turkey_ground:
            print("✅ Turkey, Ground category not found - already removed or never existed")
            return

        turkey_ground_id = turkey_ground[0]
        print(f"📋 Found 'Turkey, Ground' category (ID: {turkey_ground_id})")

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

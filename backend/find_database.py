#!/usr/bin/env python3
"""
Find Database Helper Script

Searches for freezer_inventory.db files and shows their contents.
"""

import os
import sqlite3
from pathlib import Path


def find_databases():
    """Find all freezer_inventory.db files."""

    print("🔍 Searching for freezer_inventory.db files...")
    print()

    # Start from parent directory and search
    start_dir = Path(__file__).parent.parent
    db_files = list(start_dir.rglob('freezer_inventory.db'))

    if not db_files:
        print("❌ No freezer_inventory.db files found")
        return

    print(f"✅ Found {len(db_files)} database file(s):")
    print()

    for db_path in db_files:
        abs_path = db_path.absolute()
        print(f"📁 {abs_path}")
        print(f"   Size: {os.path.getsize(abs_path):,} bytes")
        print(f"   Modified: {os.path.getmtime(abs_path)}")

        try:
            conn = sqlite3.connect(abs_path)
            cursor = conn.cursor()

            # Count categories
            cursor.execute("SELECT COUNT(*) FROM categories")
            cat_count = cursor.fetchone()[0]

            # Check for Turkey, Ground
            cursor.execute("SELECT COUNT(*) FROM categories WHERE name = 'Turkey, Ground'")
            has_turkey_ground = cursor.fetchone()[0] > 0

            # Check for USDA categories (Beef, Steak)
            cursor.execute("SELECT COUNT(*) FROM categories WHERE name = 'Beef, Steak'")
            has_usda = cursor.fetchone()[0] > 0

            print(f"   Categories: {cat_count}")
            print(f"   Has USDA categories: {'✅ Yes' if has_usda else '❌ No'}")
            print(f"   Has Turkey, Ground: {'✅ Yes' if has_turkey_ground else '❌ No'}")

            conn.close()

        except Exception as e:
            print(f"   ⚠️  Error reading database: {e}")

        print()


if __name__ == '__main__':
    print()
    print("=" * 70)
    print("Find Freezer Inventory Database Files")
    print("=" * 70)
    print()

    find_databases()

    print("=" * 70)
    print()
    print("💡 To use a specific database with the migration script:")
    print("   export DATABASE_PATH=/path/to/freezer_inventory.db")
    print("   python migrate_remove_turkey_ground.py")
    print()

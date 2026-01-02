#!/usr/bin/env python3
"""
Migration script to add Pet category to existing databases.
Run this on both dev and production databases after deploying v1.1.0
"""

import sqlite3
import sys
from pathlib import Path

def add_pet_category(db_path):
    """Add Pet category if it doesn't already exist."""
    print(f"Checking database: {db_path}")

    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if Pet category already exists
        cursor.execute("SELECT id FROM categories WHERE name = 'Pet'")
        existing = cursor.fetchone()

        if existing:
            print(f"✓ Pet category already exists (ID: {existing[0]})")
            conn.close()
            return True

        # Add Pet category
        cursor.execute("""
            INSERT INTO categories (name, default_expiration_days, is_system)
            VALUES ('Pet', 180, 1)
        """)
        conn.commit()

        # Get the new category ID
        cursor.execute("SELECT id FROM categories WHERE name = 'Pet'")
        new_id = cursor.fetchone()[0]

        print(f"✅ Added Pet category (ID: {new_id}, 180 days default expiration)")
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 50)
    print("Pet Category Migration Script")
    print("=" * 50)
    print()

    # Determine which databases to update based on arguments
    if len(sys.argv) > 1:
        db_paths = sys.argv[1:]
    else:
        # Default: update both dev and prod
        base_dir = Path(__file__).parent
        db_paths = [
            base_dir / "instance" / "freezer_inventory.db",  # Production
            base_dir / "instance" / "freezer_inventory_dev.db"  # Dev (if in same dir)
        ]

        # Also check common dev location
        dev_path = Path("/home/michaelt452/freezer-inventory-dev/backend/instance/freezer_inventory_dev.db")
        if dev_path.exists() and dev_path not in db_paths:
            db_paths.append(dev_path)

    success = True
    for db_path in db_paths:
        db_path = Path(db_path)
        if db_path.exists():
            if not add_pet_category(str(db_path)):
                success = False
            print()

    if success:
        print("=" * 50)
        print("✅ Migration complete!")
        print("=" * 50)
        return 0
    else:
        print("=" * 50)
        print("⚠️  Migration completed with errors")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())

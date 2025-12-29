#!/usr/bin/env python3
"""Migration script to:
1. Add image_url column to items table
2. Update category names and expiration days to match USDA/FDA guidelines
3. Add new categories based on USDA recommendations
"""

import sqlite3
import os
import sys

def migrate_database():
    """Run all migrations."""

    # Try both possible database locations
    db_paths = [
        'instance/freezer_inventory.db',
        'freezer_inventory.db'
    ]

    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print(f"❌ Database not found at any of these locations:")
        for path in db_paths:
            print(f"   - {path}")
        return False

    print(f"📁 Using database: {db_path}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Migration 1: Add image_url column to items table
        print("🔧 Migration 1: Adding 'image_url' column to items table...")
        cursor.execute("PRAGMA table_info(items)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'image_url' in columns:
            print("   ✅ image_url column already exists")
        else:
            cursor.execute("ALTER TABLE items ADD COLUMN image_url VARCHAR(500)")
            conn.commit()
            print("   ✅ Added image_url column")

        # Migration 2: Update existing categories with USDA values
        print("\n🔧 Migration 2: Updating category names and expiration days...")

        # Category mappings: old_name -> (new_name, new_days)
        category_updates = {
            'Beef': ('Beef, Steak', 365),  # Beef steaks: 12 months
            'Pork': ('Pork, Roast', 180),  # Pork roasts: 4-6 months (using 6)
            'Ice Cream': ('Ice Cream', 60),  # Ice cream: 1-2 months
            'Appetizers': ('Appetizers', 90),  # Frozen dinners: 3-4 months
            'Entrees': ('Entrees', 90),  # Frozen dinners: 3-4 months
            'Prepared Meals': ('Leftovers', 90),  # Rename to Leftovers
            'Staples': ('Staples', 90),  # Frozen dinners: 3-4 months
            # Chicken stays at 270, Fish stays at 180
        }

        for old_name, (new_name, new_days) in category_updates.items():
            cursor.execute("SELECT id, name, default_expiration_days FROM categories WHERE name = ?", (old_name,))
            category = cursor.fetchone()

            if category:
                cat_id, current_name, current_days = category
                cursor.execute(
                    "UPDATE categories SET name = ?, default_expiration_days = ? WHERE id = ?",
                    (new_name, new_days, cat_id)
                )
                print(f"   ✅ Updated '{old_name}' -> '{new_name}' ({current_days} -> {new_days} days)")

        # Migration 3: Add new categories
        print("\n🔧 Migration 3: Adding new USDA-based categories...")

        new_categories = [
            ('Beef, Roast', 365, True),  # Beef roasts: 12 months
            ('Beef, Ground', 120, True),  # Ground beef: 3-4 months
            ('Pork, Chops', 180, True),  # Pork chops: 4-6 months
            ('Pork, Ground', 120, True),  # Ground pork: 3-4 months
            ('Turkey', 270, True),  # Turkey parts: 9 months
            ('Chicken, Ground', 120, True),  # Ground chicken: 3-4 months
            ('Turkey, Ground', 120, True),  # Ground turkey: 3-4 months
            ('Vegetables', 300, True),  # Blanched vegetables: 8-12 months
            ('Fruits', 300, True),  # Frozen fruits: 8-12 months
        ]

        for name, days, is_system in new_categories:
            cursor.execute("SELECT id FROM categories WHERE name = ?", (name,))
            if cursor.fetchone():
                print(f"   ⏭️  Category '{name}' already exists")
            else:
                cursor.execute(
                    "INSERT INTO categories (name, default_expiration_days, is_system) VALUES (?, ?, ?)",
                    (name, days, is_system)
                )
                print(f"   ✅ Added category '{name}' ({days} days)")

        conn.commit()
        print("\n" + "="*60)
        print("✅ All migrations completed successfully!")
        print("="*60)
        print("\n📋 USDA/FDA Guidelines Applied:")
        print("   - Beef (steaks/roasts): 12 months")
        print("   - Ground beef/pork: 3-4 months")
        print("   - Pork (roasts/chops): 4-6 months")
        print("   - Chicken/Turkey parts: 9 months")
        print("   - Ground chicken/turkey: 3-4 months")
        print("   - Vegetables: 8-12 months")
        print("   - Fruits: 8-12 months")
        print("   - Ice cream: 1-2 months")
        print("   - Frozen dinners/entrees: 3-4 months")
        print("\n⚠️  IMPORTANT: These dates are for QUALITY, not safety.")
        print("   Food stored at 0°F is safe indefinitely per USDA guidelines.\n")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == '__main__':
    print("="*60)
    print("USDA Guidelines & Image Support Migration")
    print("="*60)
    print()

    success = migrate_database()
    sys.exit(0 if success else 1)

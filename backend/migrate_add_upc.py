#!/usr/bin/env python3
"""
Migration script to add UPC column to items table.

This script safely adds the 'upc' column to the existing database
without losing any data.

Usage:
    python migrate_add_upc.py
"""

import sqlite3
import os
import sys

def add_upc_column():
    """Add UPC column to items table if it doesn't exist."""

    # Get database path
    db_path = 'freezer_inventory.db'

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("The database will be created automatically when you start the app.")
        return True

    print(f"📁 Found database at: {db_path}")

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(items)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'upc' in columns:
            print("✅ UPC column already exists. No migration needed.")
            conn.close()
            return True

        # Add the column
        print("🔧 Adding 'upc' column to items table...")
        cursor.execute("ALTER TABLE items ADD COLUMN upc VARCHAR(50)")
        conn.commit()

        print("✅ Migration completed successfully!")
        print("   - UPC column added to items table")

        # Verify the column was added
        cursor.execute("PRAGMA table_info(items)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'upc' in columns:
            print("✅ Verification passed: UPC column exists")
        else:
            print("⚠️  Warning: Could not verify column was added")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add UPC Column")
    print("=" * 60)
    print()

    success = add_upc_column()

    print()
    if success:
        print("Migration completed. You can now restart the application.")
        sys.exit(0)
    else:
        print("Migration failed. Please check the errors above.")
        sys.exit(1)

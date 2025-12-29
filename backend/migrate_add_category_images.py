#!/usr/bin/env python3
"""
Migration script to add image_url column to categories table.
Run this once to update your database schema.
"""

import sys
import os
import sqlite3

def migrate():
    """Add image_url column to categories table"""
    # Determine database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'freezer_inventory.db')

    # Also check instance directory
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'freezer_inventory.db')

    if os.path.exists(instance_path):
        db_path = instance_path
        print(f"Using database at: {instance_path}")
    elif os.path.exists(db_path):
        print(f"Using database at: {db_path}")
    else:
        print("✗ Database not found. Please run the app first to create the database.")
        print(f"  Looked in: {db_path}")
        print(f"  Looked in: {instance_path}")
        return

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(categories)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'image_url' in columns:
            print("✓ Migration already applied - image_url column exists")
            conn.close()
            return

        print("Adding image_url column to categories table...")

        # Add the new column
        cursor.execute("ALTER TABLE categories ADD COLUMN image_url VARCHAR(500)")
        conn.commit()

        print("✓ Successfully added image_url column to categories table")
        conn.close()

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise

if __name__ == '__main__':
    migrate()

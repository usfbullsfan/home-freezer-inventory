#!/usr/bin/env python3
"""
Migration: Add pwa_install_dismissed column to users table
Run from backend directory: python3 migrations/run_pwa_migration.py
"""
import sqlite3
import os

# Database path - adjust if needed
db_path = 'instance/freezer_inventory.db'

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    print("Please run this script from the backend directory")
    exit(1)

print(f"Running migration on: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'pwa_install_dismissed' in columns:
        print("✓ Column 'pwa_install_dismissed' already exists")
    else:
        # Add the column
        cursor.execute('ALTER TABLE users ADD COLUMN pwa_install_dismissed BOOLEAN DEFAULT 0')
        conn.commit()
        print("✓ Added column 'pwa_install_dismissed'")

    # Verify
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"✓ Migration complete - {user_count} users in database")

except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

print("\n✅ Migration successful!")

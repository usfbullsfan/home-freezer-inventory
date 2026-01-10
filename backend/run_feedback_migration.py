#!/usr/bin/env python3
"""
Migration script to add feedback_submissions table
Run this on both dev and prod databases
"""
import sqlite3
import os

def run_migration(db_path):
    """Run the feedback migration on the specified database"""
    print(f"Running migration on: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Read and execute migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), 'migrations', 'add_feedback_table.sql')
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        cursor.executescript(migration_sql)
        conn.commit()

        # Verify table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_submissions'")
        if cursor.fetchone():
            print("✅ feedback_submissions table created successfully")
        else:
            print("❌ Table creation failed")
            return False

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    # Run on both dev and prod databases
    base_dir = os.path.dirname(__file__)

    databases = [
        os.path.join(base_dir, 'instance', 'freezer_inventory.db'),  # Prod
        os.path.join(base_dir, 'instance', 'freezer_inventory_dev.db')  # Dev
    ]

    success_count = 0
    for db_path in databases:
        if os.path.exists(db_path):
            if run_migration(db_path):
                success_count += 1
            print()

    print(f"Migration complete: {success_count}/{len([d for d in databases if os.path.exists(d)])} databases updated")

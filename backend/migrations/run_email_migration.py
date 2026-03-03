#!/usr/bin/env python3
"""Migration: add nullable email column to users table.

Safe to run multiple times – skips if the column already exists.
Run on each environment (dev / prod) after deployment.
"""
import os
import sqlite3


def run_migration(db_path):
    """Add email column to users table in the given SQLite database."""
    print(f'Running email migration on: {db_path}')

    if not os.path.exists(db_path):
        print(f'  Skipped – database not found: {db_path}')
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check whether the column already exists
        cursor.execute('PRAGMA table_info(users)')
        columns = [row[1] for row in cursor.fetchall()]

        if 'email' in columns:
            print('  email column already exists – skipping')
            conn.close()
            return True

        cursor.execute('ALTER TABLE users ADD COLUMN email VARCHAR(255)')
        conn.commit()
        conn.close()
        print('  email column added successfully')
        return True

    except Exception as exc:
        print(f'  Migration failed: {exc}')
        return False


if __name__ == '__main__':
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'instance')
    databases = [
        os.path.join(base_dir, 'freezer_inventory.db'),
        os.path.join(base_dir, 'freezer_inventory_dev.db'),
    ]

    results = []
    for db_path in databases:
        if os.path.exists(db_path):
            results.append(run_migration(db_path))

    success = sum(1 for r in results if r)
    total = len(results)
    print(f'\nMigration complete: {success}/{total} databases updated')

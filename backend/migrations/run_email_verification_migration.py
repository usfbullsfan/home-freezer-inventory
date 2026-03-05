#!/usr/bin/env python3
"""Migration: add email verification columns to users table.

Safe to run multiple times – skips columns that already exist.
Run on each environment (dev / prod) after deployment.
"""
import os
import sqlite3

COLUMNS = [
    ('email_verified',            'BOOLEAN DEFAULT 0'),
    ('email_verification_token',  'VARCHAR(6)'),
    ('email_verification_expires','DATETIME'),
]


def run_migration(db_path):
    """Add email-verification columns to users table in the given SQLite database."""
    print(f'Running email-verification migration on: {db_path}')

    if not os.path.exists(db_path):
        print(f'  Skipped – database not found: {db_path}')
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('PRAGMA table_info(users)')
        existing = {row[1] for row in cursor.fetchall()}

        added = []
        for col_name, col_def in COLUMNS:
            if col_name in existing:
                print(f'  {col_name} already exists – skipping')
            else:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {col_name} {col_def}')
                added.append(col_name)
                print(f'  Added column: {col_name}')

        conn.commit()
        conn.close()
        if added:
            print(f'  Done – added: {", ".join(added)}')
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

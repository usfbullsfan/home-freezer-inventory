#!/usr/bin/env python3
"""Migration: create expiration_notification_settings table.

Safe to run multiple times – skips if the table already exists.
Supports both SQLite and PostgreSQL (via DATABASE_URL env var).

Run from the backend directory:
  python3 migrations/run_expiration_notifications_migration.py
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    pass

# ── Detect database type ───────────────────────────────────────────────────────

database_url = os.environ.get('DATABASE_URL', '')

if database_url:
    try:
        import psycopg2
    except ImportError:
        print('psycopg2 not installed; falling back to SQLAlchemy approach')
        psycopg2 = None

    if psycopg2:
        print('Running expiration_notification_settings migration on PostgreSQL...')
        try:
            conn = psycopg2.connect(database_url)
            conn.autocommit = True
            cur = conn.cursor()

            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'expiration_notification_settings'
                )
            """)
            exists = cur.fetchone()[0]

            if exists:
                print('  expiration_notification_settings table already exists – skipping')
            else:
                cur.execute("""
                    CREATE TABLE expiration_notification_settings (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
                        enabled BOOLEAN DEFAULT FALSE,
                        frequency VARCHAR(10) DEFAULT 'daily',
                        day_of_week INTEGER DEFAULT 1,
                        days_before INTEGER DEFAULT 7,
                        all_categories BOOLEAN DEFAULT TRUE,
                        category_ids TEXT DEFAULT '[]',
                        last_sent_at TIMESTAMP
                    )
                """)
                print('  expiration_notification_settings table created')

            cur.close()
            conn.close()
            print('\n✅ Migration successful!')
        except Exception as exc:
            print(f'❌ Migration failed: {exc}')
            sys.exit(1)
        sys.exit(0)

# ── SQLite fallback ────────────────────────────────────────────────────────────

import sqlite3

_basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_db_filename = os.environ.get('DATABASE_PATH', 'freezer_inventory.db')
db_path = os.path.join(_basedir, 'instance', _db_filename)

if not os.path.exists(db_path):
    print(f'❌ Database not found at: {db_path}')
    print('Run this script from the backend directory, or set DATABASE_PATH in .env.')
    sys.exit(1)

print(f'Running expiration_notification_settings migration on SQLite: {db_path}\n')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='expiration_notification_settings'"
    )
    exists = cursor.fetchone()

    if exists:
        print('✓ expiration_notification_settings table already exists – skipping')
    else:
        cursor.execute("""
            CREATE TABLE expiration_notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
                enabled BOOLEAN DEFAULT 0,
                frequency VARCHAR(10) DEFAULT 'daily',
                day_of_week INTEGER DEFAULT 1,
                days_before INTEGER DEFAULT 7,
                all_categories BOOLEAN DEFAULT 1,
                category_ids TEXT DEFAULT '[]',
                last_sent_at DATETIME
            )
        """)
        conn.commit()
        print('✓ expiration_notification_settings table created')

except Exception as exc:
    print(f'❌ Migration failed: {exc}')
    conn.rollback()
    conn.close()
    sys.exit(1)

conn.close()
print('\n✅ Migration successful!')

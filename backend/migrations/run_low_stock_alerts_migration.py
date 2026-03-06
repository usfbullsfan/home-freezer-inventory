#!/usr/bin/env python3
"""Migration: create low_stock_alerts table.

Safe to run multiple times – skips if the table already exists.
Supports both SQLite and PostgreSQL (via DATABASE_URL env var).

Run from the backend directory:
  python3 migrations/run_low_stock_alerts_migration.py
"""
import os
import sys

# ── Detect database type ───────────────────────────────────────────────────────

database_url = os.environ.get('DATABASE_URL', '')

if database_url:
    # PostgreSQL
    try:
        import psycopg2
    except ImportError:
        print('psycopg2 not installed; falling back to SQLAlchemy approach')
        psycopg2 = None

    if psycopg2:
        print(f'Running low_stock_alerts migration on PostgreSQL...')
        try:
            conn = psycopg2.connect(database_url)
            conn.autocommit = True
            cur = conn.cursor()

            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'low_stock_alerts'
                )
            """)
            exists = cur.fetchone()[0]

            if exists:
                print('  low_stock_alerts table already exists – skipping')
            else:
                cur.execute("""
                    CREATE TABLE low_stock_alerts (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        item_name VARCHAR(200) NOT NULL,
                        threshold INTEGER NOT NULL DEFAULT 2,
                        enabled BOOLEAN DEFAULT TRUE,
                        last_sent_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT NOW(),
                        CONSTRAINT _user_item_alert_uc UNIQUE (user_id, item_name)
                    )
                """)
                print('  low_stock_alerts table created')

            cur.close()
            conn.close()
            print('\n✅ Migration successful!')
        except Exception as exc:
            print(f'❌ Migration failed: {exc}')
            sys.exit(1)
        sys.exit(0)

# ── SQLite fallback ────────────────────────────────────────────────────────────

import sqlite3

db_path = os.environ.get('DATABASE_PATH', 'instance/freezer_inventory.db')

if not os.path.exists(db_path):
    print(f'❌ Database not found at: {db_path}')
    print('Run this script from the backend directory, or set DATABASE_PATH.')
    sys.exit(1)

print(f'Running low_stock_alerts migration on SQLite: {db_path}\n')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='low_stock_alerts'")
    exists = cursor.fetchone()

    if exists:
        print('✓ low_stock_alerts table already exists – skipping')
    else:
        cursor.execute("""
            CREATE TABLE low_stock_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                item_name VARCHAR(200) NOT NULL,
                threshold INTEGER NOT NULL DEFAULT 2,
                enabled BOOLEAN DEFAULT 1,
                last_sent_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, item_name)
            )
        """)
        conn.commit()
        print('✓ low_stock_alerts table created')

except Exception as exc:
    print(f'❌ Migration failed: {exc}')
    conn.rollback()
    conn.close()
    sys.exit(1)

conn.close()
print('\n✅ Migration successful!')

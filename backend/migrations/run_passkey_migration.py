#!/usr/bin/env python3
"""Migration: create passkey authentication tables.

Safe to run multiple times – skips tables that already exist.
Creates: passkey_challenges, passkey_credentials, recovery_codes

Run from the backend directory:
  python3 migrations/run_passkey_migration.py
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    pass

import sqlite3

_basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_db_filename = os.environ.get('DATABASE_PATH', 'freezer_inventory.db')
db_path = os.path.join(_basedir, 'instance', _db_filename)

if not os.path.exists(db_path):
    print(f'❌ Database not found at: {db_path}')
    print('Run this script from the backend directory, or set DATABASE_PATH in .env.')
    sys.exit(1)

print(f'Running passkey migration on SQLite: {db_path}\n')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # passkey_challenges – stores temporary WebAuthn challenge nonces
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='passkey_challenges'")
    if cursor.fetchone():
        print('✓ passkey_challenges already exists – skipping')
    else:
        cursor.execute("""
            CREATE TABLE passkey_challenges (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge TEXT NOT NULL,
                user_id  INTEGER,
                username TEXT,
                expires_at TEXT NOT NULL
            )
        """)
        print('✓ passkey_challenges created')

    # passkey_credentials – stores registered WebAuthn credentials per user
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='passkey_credentials'")
    if cursor.fetchone():
        print('✓ passkey_credentials already exists – skipping')
    else:
        cursor.execute("""
            CREATE TABLE passkey_credentials (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                credential_id TEXT NOT NULL UNIQUE,
                public_key    TEXT NOT NULL,
                sign_count    INTEGER NOT NULL DEFAULT 0,
                name          TEXT,
                created_at    TEXT DEFAULT (datetime('now')),
                last_used_at  TEXT
            )
        """)
        print('✓ passkey_credentials created')

    # recovery_codes – one-time codes used to regain access if passkey is lost
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recovery_codes'")
    if cursor.fetchone():
        print('✓ recovery_codes already exists – skipping')
    else:
        cursor.execute("""
            CREATE TABLE recovery_codes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                code_hash TEXT NOT NULL,
                used      INTEGER NOT NULL DEFAULT 0,
                used_at   TEXT
            )
        """)
        print('✓ recovery_codes created')

    conn.commit()

except Exception as exc:
    print(f'❌ Migration failed: {exc}')
    conn.rollback()
    conn.close()
    sys.exit(1)

conn.close()
print('\n✅ Passkey migration successful!')

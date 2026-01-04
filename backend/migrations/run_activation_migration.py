#!/usr/bin/env python3
"""
Migration: Add activation_code and activated columns to users table
Run this from the backend directory: python migrations/run_activation_migration.py
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
import sqlite3

def run_migration():
    """Run the activation code migration"""
    app = create_app()

    with app.app_context():
        # Get database URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']

        if db_uri.startswith('sqlite:///'):
            # SQLite database
            db_path = db_uri.replace('sqlite:///', '')
            print(f"Running migration on SQLite database: {db_path}")

            # Ensure directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                print(f"Created directory: {db_dir}")

            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                # Check if users table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if not cursor.fetchone():
                    print("⚠️  Users table doesn't exist yet. Run the app first to create tables.")
                    conn.close()
                    return

                # Check if columns already exist
                cursor.execute("PRAGMA table_info(users)")
                columns = [col[1] for col in cursor.fetchall()]

                needs_activation_code = 'activation_code' not in columns
                needs_activated = 'activated' not in columns

                if not needs_activation_code and not needs_activated:
                    print("✓ Migration already applied - columns exist")
                    conn.close()
                    return

                # Add activation_code column
                if needs_activation_code:
                    cursor.execute('ALTER TABLE users ADD COLUMN activation_code TEXT')
                    print("✓ Added activation_code column")

                # Add activated column
                if needs_activated:
                    cursor.execute('ALTER TABLE users ADD COLUMN activated BOOLEAN DEFAULT 0')
                    print("✓ Added activated column")

                # Create index
                try:
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_activation_code ON users(activation_code)')
                    print("✓ Created activation_code index")
                except Exception as e:
                    print(f"  Index creation: {e}")

                # Mark existing users as activated (they have passwords)
                cursor.execute('UPDATE users SET activated = 1 WHERE activated IS NULL OR activated = 0')
                affected = cursor.rowcount
                if affected > 0:
                    print(f"✓ Marked {affected} existing user(s) as activated")

                conn.commit()
                print("\n✅ Migration completed successfully!")

            except Exception as e:
                print(f"\n❌ Migration failed: {e}")
                conn.rollback()
                raise
            finally:
                conn.close()

        else:
            # PostgreSQL or other database - use SQLAlchemy
            print(f"Running migration on database: {db_uri.split('@')[0]}@***")

            # For PostgreSQL, we'd use ALTER TABLE commands through SQLAlchemy
            # This is a simple approach - production would use Alembic
            try:
                with db.engine.connect() as conn:
                    # Check if columns exist
                    result = conn.execute(db.text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name='users'
                    """))
                    columns = [row[0] for row in result]

                    needs_activation_code = 'activation_code' not in columns
                    needs_activated = 'activated' not in columns

                    if not needs_activation_code and not needs_activated:
                        print("✓ Migration already applied - columns exist")
                        return

                    # Add columns
                    if needs_activation_code:
                        conn.execute(db.text('ALTER TABLE users ADD COLUMN activation_code VARCHAR(20)'))
                        conn.commit()
                        print("✓ Added activation_code column")

                    if needs_activated:
                        conn.execute(db.text('ALTER TABLE users ADD COLUMN activated BOOLEAN DEFAULT FALSE'))
                        conn.commit()
                        print("✓ Added activated column")

                    # Create index
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_users_activation_code ON users(activation_code)'))
                    conn.commit()
                    print("✓ Created activation_code index")

                    # Mark existing users as activated
                    result = conn.execute(db.text("UPDATE users SET activated = TRUE WHERE activated IS NULL OR activated = FALSE"))
                    conn.commit()
                    affected = result.rowcount
                    if affected > 0:
                        print(f"✓ Marked {affected} existing user(s) as activated")

                    print("\n✅ Migration completed successfully!")

            except Exception as e:
                print(f"\n❌ Migration failed: {e}")
                raise

if __name__ == '__main__':
    run_migration()

#!/usr/bin/env python3
"""Run activation code migration"""
import sqlite3

conn = sqlite3.connect('/home/user/home-freezer-inventory/backend/freezer_inventory.db')
cursor = conn.cursor()

try:
    # Add activation_code column
    cursor.execute('ALTER TABLE users ADD COLUMN activation_code TEXT')
    print("✓ Added activation_code column")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print("✓ activation_code column already exists")
    else:
        raise

try:
    # Add activated column
    cursor.execute('ALTER TABLE users ADD COLUMN activated BOOLEAN DEFAULT 0')
    print("✓ Added activated column")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print("✓ activated column already exists")
    else:
        raise

try:
    # Add index for activation codes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_activation_code ON users(activation_code)')
    print("✓ Created activation_code index")
except Exception as e:
    print(f"Index creation: {e}")

# Mark existing users as activated (they have passwords)
cursor.execute('UPDATE users SET activated = 1 WHERE activated IS NULL OR activated = 0')
affected = cursor.rowcount
print(f"✓ Marked {affected} existing users as activated")

conn.commit()
conn.close()

print("\n✅ Migration completed successfully!")

# Passkey Deployment Guide

## Prerequisites
The passkey code is already deployed to dev, but needs dependencies and database migration.

## Step 1: Install Dependencies

```bash
cd /home/michaelt452/freezer-inventory-dev/backend
source venv/bin/activate
pip3 install webauthn>=2.2.0
```

## Step 2: Run Database Migration

```bash
cd /home/michaelt452/freezer-inventory-dev/backend
python3 << 'EOF'
import sqlite3
import os

db_path = 'instance/freezer_inventory_dev.db'

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    needs_activation_code = 'activation_code' not in columns
    needs_activated = 'activated' not in columns

    if not needs_activation_code and not needs_activated:
        print("✓ Columns already exist - migration complete")
        exit(0)

    if needs_activation_code:
        cursor.execute('ALTER TABLE users ADD COLUMN activation_code TEXT')
        print("✓ Added activation_code column")

    if needs_activated:
        cursor.execute('ALTER TABLE users ADD COLUMN activated BOOLEAN DEFAULT 0')
        print("✓ Added activated column")

    cursor.execute('UPDATE users SET activated = 1 WHERE activated IS NULL OR activated = 0')
    affected = cursor.rowcount
    print(f"✓ Marked {affected} existing user(s) as activated")

    conn.commit()
    print("\n✅ Migration completed successfully!")

except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()
EOF
```

## Step 3: Restart Backend

```bash
sudo systemctl restart freezer-backend-dev
sudo systemctl status freezer-backend-dev
```

## Step 4: Verify

```bash
# Check health
curl https://dev.thefreezer.xyz/api/health

# Try logging in
# Should work now!
```

## What This Fixes

- **500 errors on login**: Backend was crashing due to missing database columns
- **Worker boot failures**: `webauthn` package was not installed
- **Settings page errors**: All API calls were failing due to backend crash loop

## After Deployment

You'll be able to:
1. Log in with your password
2. Go to Settings > Passkey Authentication
3. Click "Add Passkey" to register Face ID/Touch ID/Windows Hello
4. Save the recovery codes
5. Log in with passkey from the login page

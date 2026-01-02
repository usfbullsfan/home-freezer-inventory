#!/bin/bash
# Sync production database to dev database
# This creates a fresh copy of production data for safe testing in dev
# Preserves dev admin user(s) to maintain separate dev credentials

set -e  # Exit on error

# Production and dev are in separate directories
PROD_DIR="/home/michaelt452/freezer-inventory/backend/instance"
DEV_DIR="/home/michaelt452/freezer-inventory-dev/backend/instance"

PROD_DB="$PROD_DIR/freezer_inventory.db"
DEV_DB="$DEV_DIR/freezer_inventory_dev.db"
BACKUP_DIR="$DEV_DIR/backups"
ADMIN_BACKUP="/tmp/dev_admins_backup.sql"

echo "=========================================="
echo "Database Sync: Production → Dev"
echo "=========================================="
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if production database exists
if [ ! -f "$PROD_DB" ]; then
    echo "❌ Error: Production database not found at: $PROD_DB"
    exit 1
fi

echo "Production DB: $PROD_DB"
echo "Dev DB:        $DEV_DB"
echo ""

# Save dev admin users before copying
if [ -f "$DEV_DB" ]; then
    echo "💾 Saving dev admin user(s)..."
    sqlite3 "$DEV_DB" "SELECT * FROM users WHERE role='admin';" > /dev/null 2>&1 && \
    sqlite3 "$DEV_DB" <<EOF > "$ADMIN_BACKUP"
.mode insert users
SELECT * FROM users WHERE role='admin';
EOF

    ADMIN_COUNT=$(sqlite3 "$DEV_DB" "SELECT COUNT(*) FROM users WHERE role='admin';" 2>/dev/null || echo "0")
    if [ "$ADMIN_COUNT" -gt 0 ]; then
        echo "   Saved $ADMIN_COUNT dev admin user(s)"
    else
        echo "   No admin users found in dev database"
        rm -f "$ADMIN_BACKUP"
    fi
    echo ""
fi

# Backup existing dev database if it exists
if [ -f "$DEV_DB" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/freezer_inventory_dev_backup_$TIMESTAMP.db"
    echo "📦 Backing up existing dev database..."
    cp "$DEV_DB" "$BACKUP_FILE"
    echo "   Backup saved to: $BACKUP_FILE"
    echo ""
fi

# Copy production database to dev
echo "🔄 Copying production database to dev..."
cp "$PROD_DB" "$DEV_DB"

# Restore dev admin users if they were saved
if [ -f "$ADMIN_BACKUP" ] && [ -s "$ADMIN_BACKUP" ]; then
    echo "🔑 Restoring dev admin user(s)..."

    # For each admin in the backup, update or insert them
    sqlite3 "$DEV_DB" <<EOF
-- Create a temporary table to hold backup admin data
CREATE TEMP TABLE temp_admins AS SELECT * FROM users WHERE 0;

-- Load the backup admin data
$(cat "$ADMIN_BACKUP")

-- Update existing users or insert new ones
-- First, update any users that exist in both databases
UPDATE users
SET password_hash = (SELECT password_hash FROM temp_admins WHERE temp_admins.username = users.username),
    role = 'admin'
WHERE username IN (SELECT username FROM temp_admins);

-- Then insert any that don't exist
INSERT OR IGNORE INTO users (id, username, password_hash, role, created_at)
SELECT id, username, password_hash, role, created_at FROM temp_admins
WHERE username NOT IN (SELECT username FROM users);

-- Clean up
DROP TABLE temp_admins;
EOF

    RESTORED_COUNT=$(sqlite3 "$DEV_DB" "SELECT COUNT(*) FROM users WHERE role='admin';" 2>/dev/null || echo "0")
    echo "   Restored $RESTORED_COUNT admin user(s)"

    # Clean up backup file
    rm -f "$ADMIN_BACKUP"
    echo ""
fi

# Get database stats
PROD_SIZE=$(du -h "$PROD_DB" | cut -f1)
DEV_SIZE=$(du -h "$DEV_DB" | cut -f1)
ITEM_COUNT=$(sqlite3 "$DEV_DB" "SELECT COUNT(*) FROM items;" 2>/dev/null || echo "?")
USER_COUNT=$(sqlite3 "$DEV_DB" "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "?")

echo "✅ Sync complete!"
echo ""
echo "Database sizes:"
echo "  Production: $PROD_SIZE"
echo "  Dev:        $DEV_SIZE"
echo ""
echo "Database contents:"
echo "  Items:      $ITEM_COUNT"
echo "  Users:      $USER_COUNT"
echo ""
echo "=========================================="
echo "✅ Dev database is now a copy of production"
echo "   (with dev admin credentials preserved)"
echo "   Restart dev backend: sudo systemctl restart freezer-backend-dev"
echo "=========================================="

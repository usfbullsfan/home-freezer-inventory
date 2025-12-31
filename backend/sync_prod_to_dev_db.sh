#!/bin/bash
# Sync production database to dev database
# This creates a fresh copy of production data for safe testing in dev

set -e  # Exit on error

# Production and dev are in separate directories
PROD_DIR="/home/michaelt452/freezer-inventory/backend/instance"
DEV_DIR="/home/michaelt452/freezer-inventory-dev/backend/instance"

PROD_DB="$PROD_DIR/freezer_inventory.db"
DEV_DB="$DEV_DIR/freezer_inventory_dev.db"
BACKUP_DIR="$DEV_DIR/backups"

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

# Get database stats
PROD_SIZE=$(du -h "$PROD_DB" | cut -f1)
DEV_SIZE=$(du -h "$DEV_DB" | cut -f1)

echo "✅ Sync complete!"
echo ""
echo "Database sizes:"
echo "  Production: $PROD_SIZE"
echo "  Dev:        $DEV_SIZE"
echo ""
echo "=========================================="
echo "✅ Dev database is now a copy of production"
echo "   Restart dev backend: sudo systemctl restart freezer-backend-dev"
echo "=========================================="

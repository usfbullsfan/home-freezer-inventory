# Database Separation Guide (Issue #55)

## Problem
Dev and production backends are currently sharing the same database file, which means:
- Changes in dev affect production data ❌
- Can't safely test destructive operations ❌
- No isolation between environments ❌

## Solution
Separate databases using environment variables:
- **Production**: `instance/freezer_inventory.db`
- **Dev**: `instance/freezer_inventory_dev.db`

## Implementation Steps

### Step 1: Update Systemd Services

#### Production Backend Service
```bash
sudo nano /etc/systemd/system/freezer-backend.service
```

Add this line in the `[Service]` section:
```ini
Environment="DATABASE_PATH=freezer_inventory.db"
```

#### Dev Backend Service
```bash
sudo nano /etc/systemd/system/freezer-backend-dev.service
```

Add this line in the `[Service]` section:
```ini
Environment="DATABASE_PATH=freezer_inventory_dev.db"
```

### Step 2: Reload Systemd and Restart Services
```bash
sudo systemctl daemon-reload
sudo systemctl restart freezer-backend
sudo systemctl restart freezer-backend-dev
```

### Step 3: Verify Separation
Check that each service is using the correct database:

```bash
# Check production backend logs
sudo journalctl -u freezer-backend --since "1 minute ago" | grep "Database will be created at"

# Check dev backend logs
sudo journalctl -u freezer-backend-dev --since "1 minute ago" | grep "Database will be created at"
```

You should see:
- **Production**: `/home/michaelt452/freezer-inventory/backend/instance/freezer_inventory.db`
- **Dev**: `/home/michaelt452/freezer-inventory/backend/instance/freezer_inventory_dev.db`

### Step 4: Sync Production Data to Dev

After separation, the dev database will be empty. Sync production data to dev:

```bash
cd /home/michaelt452/freezer-inventory/backend
./sync_prod_to_dev_db.sh
```

This will:
- ✅ Backup existing dev database (if any)
- ✅ Copy production database to dev
- ✅ Show database statistics
- ✅ Preserve production database (read-only copy)

### Step 5: Test Separation

Test that changes in dev don't affect production:

```bash
# Add a test item in dev (port 5002)
curl -X POST http://localhost:5002/api/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <dev_token>" \
  -d '{
    "name": "TEST ITEM - DEV ONLY",
    "category_id": 1,
    "quantity": 999,
    "location": "DEV TEST"
  }'

# Check production (port 5001) - should NOT have this item
curl http://localhost:5001/api/items \
  -H "Authorization: Bearer <prod_token>"
```

If the test item only appears in dev, databases are properly separated! ✅

## Ongoing Maintenance

### Regular Sync from Prod to Dev
Run this whenever you want fresh production data in dev:

```bash
cd /home/michaelt452/freezer-inventory/backend
./sync_prod_to_dev_db.sh
sudo systemctl restart freezer-backend-dev
```

**Note**: This overwrites dev database, so any dev-only test data will be lost.

### Backup Strategy
- Dev database backups are automatically created before each sync
- Backups are stored in: `backend/instance/backups/`
- Consider setting up automated daily backups of production DB

## Environment Variables Summary

| Variable | Production | Dev |
|----------|-----------|-----|
| `DATABASE_PATH` | `freezer_inventory.db` | `freezer_inventory_dev.db` |
| Port | 5001 | 5002 |
| Service | `freezer-backend` | `freezer-backend-dev` |

## Rollback Plan

If something goes wrong, you can revert by:

1. Remove the `Environment=` lines from systemd services
2. Reload and restart: `sudo systemctl daemon-reload && sudo systemctl restart freezer-backend freezer-backend-dev`
3. Both will use the default `freezer_inventory.db` (pre-separation behavior)

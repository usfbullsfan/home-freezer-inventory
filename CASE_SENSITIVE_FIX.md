# Case-Insensitive Username Fix - Deployment Guide

## Problem
The case-insensitive username code is deployed, but existing usernames in the database may still have mixed case (e.g., "Admin"). When you login with "Admin", the code converts it to "admin" for lookup, but if "Admin" is stored in the database, it won't find it.

## Solution Steps

### Step 1: Verify Latest Code is Deployed
```bash
cd /home/michaelt452/freezer-inventory-dev
git status
git log --oneline -3
```

**Expected output:**
- Should be on `dev` branch
- Latest commit should be: "Merge pull request #96 from usfbullsfan/claude/fix-case-insensitive-usernames-PAOgF"

If not on latest dev:
```bash
git checkout dev
git pull origin dev
sudo systemctl restart freezer-backend-dev
```

### Step 2: Check Current Usernames in Database
```bash
cd /home/michaelt452/freezer-inventory-dev/backend
source venv/bin/activate
python3 -c "
from app import create_app
from models import User, db

app = create_app()
with app.app_context():
    users = User.query.all()
    print('Current usernames:')
    for u in users:
        print(f'  ID {u.id}: \"{u.username}\" (role: {u.role})')
"
```

**Check:** Are any usernames NOT all lowercase? If yes, proceed to Step 3.

### Step 3: Pull Latest Code (Includes Migration Script)
```bash
cd /home/michaelt452/freezer-inventory-dev
git pull origin dev
```

### Step 4: Run Migration Script
```bash
cd /home/michaelt452/freezer-inventory-dev/backend
source venv/bin/activate
python3 migrate_usernames_lowercase.py
```

This will:
- Show all current usernames
- Check for conflicts
- Migrate usernames to lowercase
- Verify the migration

### Step 5: Restart Backend Service
```bash
sudo systemctl restart freezer-backend-dev
sudo systemctl status freezer-backend-dev
```

### Step 6: Test Case-Insensitive Login
Try logging in with different variations:
- "admin" (lowercase)
- "Admin" (capitalized)
- "ADMIN" (uppercase)

All should work now!

## Troubleshooting

### If migration shows conflicts:
This means you have users like both "Admin" and "admin" in the database. You'll need to manually resolve:
```bash
# Login to SQLite database
sqlite3 /home/michaelt452/freezer-inventory-dev/backend/instance/freezer_inventory.db

# Check users
SELECT id, username, role FROM users;

# Delete duplicate (choose carefully!)
DELETE FROM users WHERE id = <duplicate_id>;

# Exit
.quit
```

Then re-run the migration script.

### If login still doesn't work:
1. Check gunicorn logs for errors:
```bash
sudo journalctl -u freezer-backend-dev --since "5 minutes ago" | grep -i "error\|login"
```

2. Verify the code has the fix:
```bash
grep -A 3 "username_lower = data\['username'\].lower()" /home/michaelt452/freezer-inventory-dev/backend/routes/auth.py
```

Should show the normalization code in the login function.

3. Check if Python bytecode cache needs clearing:
```bash
cd /home/michaelt452/freezer-inventory-dev/backend
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
sudo systemctl restart freezer-backend-dev
```

-- Debug script to check passkey_credentials schema and data
-- Run with: sqlite3 ~/freezer-inventory-dev/instance/freezer_inventory_dev.db < debug_passkey_name.sql

.mode column
.headers on

-- Check table schema
SELECT '=== TABLE SCHEMA ===' as Info;
PRAGMA table_info(passkey_credentials);

-- Check existing passkey data
SELECT '=== EXISTING PASSKEYS ===' as Info;
SELECT id, user_id, name, created_at FROM passkey_credentials ORDER BY created_at DESC LIMIT 10;

-- Check if name column exists and has data
SELECT '=== NAME COLUMN CHECK ===' as Info;
SELECT
    CASE
        WHEN COUNT(*) > 0 THEN 'Name column EXISTS'
        ELSE 'Name column MISSING'
    END as Status
FROM pragma_table_info('passkey_credentials')
WHERE name = 'name';

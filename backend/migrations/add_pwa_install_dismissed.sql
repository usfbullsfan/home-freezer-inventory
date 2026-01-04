-- Add PWA install prompt tracking to users table
-- Run after deployment with: python3 migrations/run_pwa_migration.py

ALTER TABLE users ADD COLUMN pwa_install_dismissed BOOLEAN DEFAULT 0;

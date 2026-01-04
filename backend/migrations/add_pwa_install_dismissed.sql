-- Add PWA install prompt tracking to users table
-- Allows admins to reset all users: UPDATE users SET pwa_install_dismissed = 0;

ALTER TABLE users ADD COLUMN pwa_install_dismissed BOOLEAN DEFAULT 0;

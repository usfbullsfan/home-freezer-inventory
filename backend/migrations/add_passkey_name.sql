-- Add name column to passkey_credentials table
-- This allows users to give friendly names to their passkeys

ALTER TABLE passkey_credentials ADD COLUMN name TEXT DEFAULT NULL;

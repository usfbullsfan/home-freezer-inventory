-- Add activation code support for user enrollment
-- Users must be created by admin with activation code, then activate using passkey

ALTER TABLE users ADD COLUMN activation_code TEXT;
ALTER TABLE users ADD COLUMN activated BOOLEAN DEFAULT 0;

-- Add index for faster activation code lookups
CREATE INDEX IF NOT EXISTS idx_users_activation_code ON users(activation_code);

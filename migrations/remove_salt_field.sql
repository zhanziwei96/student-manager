-- Migration: Remove deprecated salt field from users and students tables
-- Date: 2026-03-26
-- Reason: SEC-003 - bcrypt already includes salt internally, this field is no longer needed

-- Remove salt column from users table
ALTER TABLE users DROP COLUMN salt;

-- Remove salt column from students table
ALTER TABLE students DROP COLUMN salt;

-- Note: This migration is irreversible. Make sure to backup data before running.
-- The salt field was deprecated and no longer used since SEC-003 implementation.

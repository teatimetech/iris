-- Migration 012: Add Unique Constraint to Email
-- Ensures users cannot register with duplicate email addresses

-- Add unique constraint to profiles.email
ALTER TABLE profiles ADD CONSTRAINT unique_email UNIQUE (email);

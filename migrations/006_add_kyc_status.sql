-- Add kyc_status column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS kyc_status VARCHAR(50) DEFAULT 'PENDING';

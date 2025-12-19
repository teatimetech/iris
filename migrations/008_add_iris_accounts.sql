-- 1. Create Sequence for IRIS Account Number
CREATE SEQUENCE IF NOT EXISTS iris_acct_seq START 1;

-- 2. Add New Columns
ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS iris_account_id VARCHAR(64);
ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS iris_account_number VARCHAR(11);
ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS alpaca_account_id VARCHAR(64);

-- 3. Migrate Existing Data
-- Move existing Account Number (Alpaca ID) to alpaca_account_id
UPDATE portfolios SET alpaca_account_id = account_number WHERE alpaca_account_id IS NULL;

-- 4. Generate Data for Existing Accounts (if missing)
UPDATE portfolios 
SET iris_account_id = gen_random_uuid()::text 
WHERE iris_account_id IS NULL;

UPDATE portfolios 
SET iris_account_number = LPAD(nextval('iris_acct_seq')::text, 11, '0') 
WHERE iris_account_number IS NULL;

-- 5. Add Constraints (Optional but good)
-- ALTER TABLE portfolios ADD CONSTRAINT unique_iris_acct_num UNIQUE (iris_account_number);

-- check outcome
SELECT id, user_id, iris_account_number, iris_account_id, alpaca_account_id FROM portfolios;

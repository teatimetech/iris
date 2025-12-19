-- Add cash_balance to portfolios table
ALTER TABLE portfolios 
ADD COLUMN cash_balance DECIMAL(15, 2) DEFAULT 0.00;

-- Comment on column
COMMENT ON COLUMN portfolios.cash_balance IS 'Available cash balance in the account';

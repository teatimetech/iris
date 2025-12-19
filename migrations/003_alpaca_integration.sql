-- Migration: Alpaca Integration and External Accounts
-- Splits the concept of "Core" (Managed by IRIS/Alpaca) and "External" (Read-only)

-- 1. Add Alpaca to brokers
INSERT INTO brokers (name, display_name, description) VALUES
('alpaca', 'Alpaca Markets', 'Core IRIS Brokerage & Clearing')
ON CONFLICT (name) DO NOTHING;

-- 2. Add 'is_core' flag to portfolios to identify the Alpaca managed account
ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS is_core BOOLEAN DEFAULT FALSE;
ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP WITH TIME ZONE;

-- 3. Create table for External Accounts (Read-only aggregation)
-- This replaces the need to store external holdings in the main 'holdings' table if we want a clean separation.
-- However, for simplicity in queries, if they share the same structure, 'holdings' table could be used.
-- But user requested "another table for external accounts".
CREATE TABLE IF NOT EXISTS external_accounts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL, -- No foreign key enforcement on users table if users are in a different service/auth, but here they are local.
    institution_name VARCHAR(100) NOT NULL,
    account_name VARCHAR(100),
    symbol VARCHAR(20) NOT NULL,
    shares DECIMAL(18, 5) NOT NULL,
    avg_price DECIMAL(18, 2), -- Cost basis per share
    current_price DECIMAL(18, 2), -- Snapshot price for Net Worth calc
    currency VARCHAR(10) DEFAULT 'USD',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Set up an existing portfolio as Core for test-user (or create one)
DO $$
DECLARE
    alpaca_id INTEGER;
BEGIN
    SELECT id INTO alpaca_id FROM brokers WHERE name = 'alpaca';
    
    -- Insert core portfolio if not exists
    INSERT INTO portfolios (user_id, name, broker_id, is_core)
    VALUES ('test-user', 'IRIS Core Portfolio', alpaca_id, TRUE)
    ON CONFLICT (user_id, name) DO UPDATE SET is_core = TRUE, broker_id = alpaca_id;
END $$;

-- 5. Migrate some existing "fake" external data to external_accounts
-- Move Alice's Fidelity Retirement to External Accounts
INSERT INTO external_accounts (user_id, institution_name, account_name, symbol, shares, avg_price)
SELECT p.user_id, b.display_name, p.name, h.symbol, h.shares, h.avg_price
FROM portfolios p
JOIN brokers b ON p.broker_id = b.id
JOIN holdings h ON p.id = h.portfolio_id
WHERE p.user_id = 'user-001' AND b.name = 'fidelity';

-- (Optional) Clean up the migrated data from portfolios/holdings if strict separation is desired.
-- For now, we leave them or let application logic handle "Core" vs "External" visibility.

-- Migration 010: Schema Refactoring
-- Implements proper entity relationships: User -> Account -> Portfolio -> Holdings
-- Separates authentication (Profile) and KYC from user data

-- ============================================================================
-- STEP 1: Create new tables
-- ============================================================================

-- New users table (simplified, only identity info)
CREATE TABLE IF NOT EXISTS users_new (
    id VARCHAR(50) PRIMARY KEY,  -- UUID hex string
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Account sequence for 12-digit account numbers
CREATE SEQUENCE IF NOT EXISTS account_number_seq START 1;

-- Accounts table (1:1 with users)
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(50) PRIMARY KEY,  -- UUID hex
    user_id VARCHAR(50) UNIQUE NOT NULL REFERENCES users_new(id) ON DELETE CASCADE,
    account_number VARCHAR(12) UNIQUE NOT NULL DEFAULT LPAD(nextval('account_number_seq')::text, 12, '0'),
    alpaca_account_number VARCHAR(50),
    alpaca_account_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLOSED', 'SUSPENDED')),
    kyc_status VARCHAR(20) DEFAULT 'NOT_STARTED' CHECK (kyc_status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Profiles table (1:1 with users, contains auth info)
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL REFERENCES users_new(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone VARCHAR(20),
    address_line1 TEXT,
    address_line2 TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- KYC table (1:1 with accounts)
CREATE TABLE IF NOT EXISTS kyc (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(50) UNIQUE NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    tax_id VARCHAR(20),
    tax_id_type VARCHAR(20),
    date_of_birth DATE,
    citizenship VARCHAR(50),
    employment_status VARCHAR(50),
    annual_income DECIMAL(15,2),
    net_worth DECIMAL(15,2),
    documents JSONB DEFAULT '{}',
    kyc_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios table (many:1 with accounts)
CREATE TABLE IF NOT EXISTS portfolios_new (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('IRIS Core', 'IRIS Crypto')),
    is_default BOOLEAN DEFAULT FALSE,
    broker_id INTEGER REFERENCES brokers(id),
    iris_account_number VARCHAR(50),
    iris_account_id VARCHAR(50),
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, name)
);

-- Holdings table (many:1 with portfolios)
CREATE TABLE IF NOT EXISTS holdings_new (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios_new(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    shares DECIMAL(18,8) NOT NULL,
    avg_price DECIMAL(18,4) NOT NULL,
    purchase_date DATE,
    ytd_start_value DECIMAL(18,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, symbol)
);

-- ============================================================================
-- STEP 2: Migrate existing data
-- ============================================================================

-- Migrate users (split into users_new and profiles)
INSERT INTO users_new (id, first_name, middle_name, last_name, created_at)
SELECT 
    id,
    COALESCE(first_name, SPLIT_PART(full_name, ' ', 1)),
    NULL,
    COALESCE(last_name, CASE 
        WHEN full_name IS NOT NULL AND POSITION(' ' IN full_name) > 0 
        THEN SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1)
        ELSE NULL 
    END),
    COALESCE(created_at, CURRENT_TIMESTAMP)
FROM users
ON CONFLICT (id) DO NOTHING;

-- Create accounts for each user
INSERT INTO accounts (id, user_id, alpaca_account_number, alpaca_account_id, kyc_status, created_at)
SELECT 
    gen_random_uuid()::text,
    u.id,
    NULL,  -- Will be updated from portfolios
    NULL,
    CASE 
        WHEN u.kyc_status = 'VERIFIED' THEN 'COMPLETED'
        WHEN u.kyc_status IS NOT NULL THEN 'IN_PROGRESS'
        ELSE 'NOT_STARTED'
    END,
    COALESCE(u.created_at, CURRENT_TIMESTAMP)
FROM users u
ON CONFLICT DO NOTHING;

-- Create profiles for each user
INSERT INTO profiles (user_id, email, password_hash, created_at)
SELECT 
    id,
    email,
    COALESCE(password_hash, '$2a$10$DummyHashNeedsReset'),
    COALESCE(created_at, CURRENT_TIMESTAMP)
FROM users
WHERE email IS NOT NULL
ON CONFLICT (user_id) DO NOTHING;

-- Migrate portfolios
INSERT INTO portfolios_new (
    account_id, name, type, is_default, broker_id,
    iris_account_number, iris_account_id, last_synced_at, created_at
)
SELECT 
    a.id,
    COALESCE(p.name, 'Core Portfolio'),
    CASE 
        WHEN p.name ILIKE '%crypto%' THEN 'IRIS Crypto'
        ELSE 'IRIS Core'
    END,
    COALESCE(p.is_core, TRUE),
    p.broker_id,
    p.iris_account_number,
    p.iris_account_id,
    p.last_synced_at,
    COALESCE(p.created_at, CURRENT_TIMESTAMP)
FROM portfolios p
JOIN accounts a ON a.user_id = p.user_id
ON CONFLICT DO NOTHING;

-- Update accounts with Alpaca IDs from portfolios
UPDATE accounts a
SET 
    alpaca_account_number = p.account_number,
    alpaca_account_id = p.alpaca_account_id
FROM portfolios p
JOIN accounts acc ON acc.user_id = p.user_id
WHERE a.id = acc.id
AND p.alpaca_account_id IS NOT NULL
AND a.alpaca_account_id IS NULL;

-- Migrate holdings
INSERT INTO holdings_new (portfolio_id, symbol, shares, avg_price, purchase_date, ytd_start_value, created_at)
SELECT 
    pn.id,
    h.symbol,
    h.shares,
    h.avg_price,
    h.original_purchase_date,
    h.ytd_start_value,
    COALESCE(h.created_at, CURRENT_TIMESTAMP)
FROM holdings h
JOIN portfolios p ON h.portfolio_id = p.id
JOIN accounts a ON a.user_id = p.user_id
JOIN portfolios_new pn ON pn.account_id = a.id AND pn.name = p.name
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- (Skipping migration of legacy KYC data as column u.kyc_data does not exist in base schema)

-- ============================================================================
-- STEP 3: Create indexes for  performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_accounts_alpaca_account_id ON accounts(alpaca_account_id);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_portfolios_account_id ON portfolios_new(account_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_type ON portfolios_new(type);
CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_id ON holdings_new(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON holdings_new(symbol);
CREATE INDEX IF NOT EXISTS idx_kyc_account_id ON kyc(account_id);

-- ============================================================================
-- STEP 4: Create triggers for updated_at timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for all tables with updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users_new;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users_new
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_accounts_updated_at ON accounts;
CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_portfolios_updated_at ON portfolios_new;
CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios_new
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_holdings_updated_at ON holdings_new;
CREATE TRIGGER update_holdings_updated_at BEFORE UPDATE ON holdings_new
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_kyc_updated_at ON kyc;
CREATE TRIGGER update_kyc_updated_at BEFORE UPDATE ON kyc
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STEP 5: Swap tables (drop old, rename new)
-- ============================================================================

-- Drop old tables (be careful!)
DROP TABLE IF EXISTS holdings CASCADE;
DROP TABLE IF EXISTS portfolios CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Rename new tables to final names
ALTER TABLE users_new RENAME TO users;
ALTER TABLE portfolios_new RENAME TO portfolios;
ALTER TABLE holdings_new RENAME TO holdings;

-- ============================================================================
-- STEP 6: Grant permissions
-- ============================================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iris_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iris_user;

-- ============================================================================
-- Verification queries
-- ============================================================================

-- Verify migration
-- SELECT COUNT(*) as user_count FROM users;
-- SELECT COUNT(*) as account_count FROM accounts;
-- SELECT COUNT(*) as profile_count FROM profiles;
-- SELECT COUNT(*) as portfolio_count FROM portfolios;
-- SELECT COUNT(*) as holding_count FROM holdings;

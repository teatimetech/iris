-- Migration: Enhanced Portfolio Features
-- Adds broker/institution support, YTD tracking, and comprehensive test data

-- 1. Create brokers table
CREATE TABLE IF NOT EXISTS brokers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Add broker_id to portfolios (can be NULL for existing data)
ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS broker_id INTEGER REFERENCES brokers(id);
ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS account_number VARCHAR(50);

-- 3. Add YTD tracking fields to holdings
ALTER TABLE holdings ADD COLUMN IF NOT EXISTS original_purchase_date DATE;
ALTER TABLE holdings ADD COLUMN IF NOT EXISTS ytd_start_value DECIMAL(18, 2);

-- 4. Insert broker/institution data
INSERT INTO brokers (name, display_name, description) VALUES
('fidelity', 'Fidelity Investments', 'Brokerage and retirement accounts'),
('schwab', 'Charles Schwab', 'Investment and trading accounts'),
('vanguard', 'Vanguard', 'Index funds and retirement accounts'),
('etrade', 'E*TRADE', 'Online brokerage')
ON CONFLICT (name) DO NOTHING;

-- 5. Create additional test users
INSERT INTO users (id, username, email, full_name) VALUES
('user-001', 'alice_investor', 'alice@example.com', 'Alice Johnson'),
('user-002', 'bob_trader', 'bob@example.com', 'Bob Smith'),
('user-003', 'carol_saver', 'carol@example.com', 'Carol Davis')
ON CONFLICT (id) DO NOTHING;

-- 6. Create sub-portfolios for test-user with different brokers
WITH fidelity_broker AS (SELECT id FROM brokers WHERE name = 'fidelity'),
     schwab_broker AS (SELECT id FROM brokers WHERE name = 'schwab')
INSERT INTO portfolios (user_id, name, broker_id, account_number) VALUES
-- Reassign existing portfolio to Fidelity
('test-user', 'Fidelity - Tech Growth', (SELECT id FROM fidelity_broker), 'FID-987654'),
('test-user', 'Charles Schwab - Diversified', (SELECT id FROM schwab_broker), 'SCH-123456')
ON CONFLICT (user_id, name) DO UPDATE 
SET broker_id = EXCLUDED.broker_id, account_number = EXCLUDED.account_number;

-- 7. Create portfolios for other test users
WITH fidelity_broker AS (SELECT id FROM brokers WHERE name = 'fidelity'),
     schwab_broker AS (SELECT id FROM brokers WHERE name = 'schwab'),
     vanguard_broker AS (SELECT id FROM brokers WHERE name = 'vanguard')
INSERT INTO portfolios (user_id, name, broker_id, account_number) VALUES
-- Alice's portfolios
('user-001', 'Fidelity Retirement', (SELECT id FROM fidelity_broker), 'FID-111111'),
('user-001', 'Schwab Trading', (SELECT id FROM schwab_broker), 'SCH-222222'),
-- Bob's portfolios
('user-002', 'Vanguard Index Funds', (SELECT id FROM vanguard_broker), 'VAN-333333'),
('user-002', 'Fidelity Growth', (SELECT id FROM fidelity_broker), 'FID-444444'),
-- Carol's portfolio
('user-003', 'Schwab Balanced', (SELECT id FROM schwab_broker), 'SCH-555555')
ON CONFLICT (user_id, name) DO NOTHING;

-- 8. Add holdings to test-user's Fidelity portfolio (Tech stocks + ETFs)
-- Cost basis ~20% lower than current prices
WITH p AS (SELECT id FROM portfolios WHERE user_id = 'test-user' AND name = 'Fidelity - Tech Growth')
INSERT INTO holdings (portfolio_id, symbol, shares, avg_price, original_purchase_date, ytd_start_value) 
SELECT p.id, 'NVDA', 50, 140.00, '2023-06-15'::DATE, 7500.00 FROM p  -- Current ~$175, Cost $140
UNION ALL
SELECT p.id, 'AAPL', 100, 222.00, '2023-03-20'::DATE, 23000.00 FROM p  -- Current ~$278, Cost $222
UNION ALL
SELECT p.id, 'MSFT', 75, 382.00, '2023-01-10'::DATE, 29500.00 FROM p   -- Current ~$478, Cost $382
UNION ALL
SELECT p.id, 'GOOGL', 120, 247.00, '2023-05-05'::DATE, 30200.00 FROM p  -- Current ~$309, Cost $247
UNION ALL
SELECT p.id, 'QQQ', 200, 320.00, '2023-02-15'::DATE, 65000.00 FROM p    -- Tech ETF
UNION ALL
SELECT p.id, 'VOO', 150, 380.00, '2023-01-05'::DATE, 58000.00 FROM p    -- S&P500 ETF
UNION ALL
SELECT p.id, 'VGT', 100, 405.00, '2023-04-10'::DATE, 41500.00 FROM p    -- Tech sector ETF
UNION ALL
SELECT p.id, 'ARKK', 300, 48.00, '2023-07-20'::DATE, 15000.00 FROM p    -- Innovation ETF
ON CONFLICT (portfolio_id, symbol) DO UPDATE
SET avg_price = EXCLUDED.avg_price, 
    original_purchase_date = EXCLUDED.original_purchase_date,
    ytd_start_value = EXCLUDED.ytd_start_value;

-- 9. Add holdings to test-user's Schwab portfolio (Stocks)
WITH p AS (SELECT id FROM portfolios WHERE user_id = 'test-user' AND name = 'Charles Schwab - Diversified')
INSERT INTO holdings (portfolio_id, symbol, shares, avg_price, original_purchase_date, ytd_start_value)
SELECT p.id, 'TSLA', 80, 200.00, '2023-08-01'::DATE, 17000.00 FROM p   -- Current varies, Cost $200
UNION ALL
SELECT p.id, 'AMD', 200, 110.00, '2023-02-28'::DATE, 23000.00 FROM p   -- Cost $110
UNION ALL
SELECT p.id, 'META', 60, 320.00, '2023-05-15'::DATE, 20500.00 FROM p   -- Cost $320
UNION ALL
SELECT p.id, 'NFLX', 40, 425.00, '2023-03-10'::DATE, 18500.00 FROM p   -- Cost $425
UNION ALL
SELECT p.id, 'AMZN', 100, 145.00, '2023-01-20'::DATE, 15200.00 FROM p  -- Cost $145
UNION ALL
SELECT p.id, 'DIS', 150, 88.00, '2023-06-05'::DATE, 13500.00 FROM p    -- Cost $88
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- 10. Add holdings for Alice (Fidelity portfolio)
WITH p AS (SELECT id FROM portfolios WHERE user_id = 'user-001' AND name = 'Fidelity Retirement')
INSERT INTO holdings (portfolio_id, symbol, shares, avg_price, original_purchase_date, ytd_start_value)
SELECT p.id, 'VTI', 500, 200.00, '2022-01-15'::DATE, 105000.00 FROM p
UNION ALL
SELECT p.id, 'BND', 400, 72.00, '2022-01-15'::DATE, 29500.00 FROM p
UNION ALL
SELECT p.id, 'VNQ', 200, 80.00, '2022-06-10'::DATE, 17000.00 FROM p
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- 11. Add holdings for Alice (Schwab portfolio - trading)
WITH p AS (SELECT id FROM portfolios WHERE user_id = 'user-001' AND name = 'Schwab Trading')
INSERT INTO holdings (portfolio_id, symbol, shares, avg_price, original_purchase_date, ytd_start_value)
SELECT p.id, 'SPY', 100, 410.00, '2023-09-01'::DATE, 42000.00 FROM p
UNION ALL
SELECT p.id, 'NVDA', 30, 150.00, '2023-10-15'::DATE, 4800.00 FROM p
UNION ALL
SELECT p.id, 'COIN', 150, 95.00, '2023-11-01'::DATE, 15000.00 FROM p
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- 12. Add holdings for Bob (Vanguard)
WITH p AS (SELECT id FROM portfolios WHERE user_id = 'user-002' AND name = 'Vanguard Index Funds')
INSERT INTO holdings (portfolio_id, symbol, shares, avg_price, original_purchase_date, ytd_start_value)
SELECT p.id, 'VTSAX', 1000, 95.00, '2021-01-10'::DATE, 98000.00 FROM p
UNION ALL
SELECT p.id, 'VFIAX', 500, 350.00, '2021-01-10'::DATE, 180000.00 FROM p
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- 13. Add holdings for Bob (Fidelity)
WITH p AS (SELECT id FROM portfolios WHERE user_id = 'user-002' AND name = 'Fidelity Growth')
INSERT INTO holdings (portfolio_id, symbol, shares, avg_price, original_purchase_date, ytd_start_value)
SELECT p.id, 'AAPL', 150, 180.00, '2023-01-05'::DATE, 28000.00 FROM p
UNION ALL
SELECT p.id, 'MSFT', 100, 320.00, '2023-01-05'::DATE, 33000.00 FROM p
UNION ALL
SELECT p.id, 'GOOGL', 80, 110.00, '2023-02-10'::DATE, 9200.00 FROM p
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- 14. Add holdings for Carol (Schwab)
WITH p AS (SELECT id FROM portfolios WHERE user_id = 'user-003' AND name = 'Schwab Balanced')
INSERT INTO holdings (portfolio_id, symbol, shares, avg_price, original_purchase_date, ytd_start_value)
SELECT p.id, 'VOO', 200, 360.00, '2022-12-15'::DATE, 74000.00 FROM p
UNION ALL
SELECT p.id, 'BND', 300, 75.00, '2022-12-15'::DATE, 23000.00 FROM p
UNION ALL
SELECT p.id, 'VWO', 250, 42.00, '2023-03-20'::DATE, 10800.00 FROM p
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

-- 15. Clean up old portfolio entry if it exists
DELETE FROM portfolios WHERE user_id = 'test-user' AND name = 'My Tech Portfolio';

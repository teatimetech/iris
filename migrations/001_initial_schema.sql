-- Initial Schema for IRIS

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY, -- e.g., 'test_user_id', or generated UUID
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL REFERENCES users(id),
    name VARCHAR(100) DEFAULT 'Main Portfolio',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_portfolio_name UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS holdings (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    shares DECIMAL(18, 6) NOT NULL,
    avg_price DECIMAL(18, 2) NOT NULL, -- Average cost basis
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_portfolio_symbol UNIQUE (portfolio_id, symbol)
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id),
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('BUY', 'SELL', 'DEPOSIT', 'WITHDRAWAL')),
    shares DECIMAL(18, 6),
    price DECIMAL(18, 2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed Data for Demo
INSERT INTO users (id, username, email, full_name) 
VALUES ('test-user', 'demo', 'demo@iris.ai', 'Iris Demo User')
ON CONFLICT (id) DO NOTHING;

INSERT INTO portfolios (user_id, name) 
VALUES ('test-user', 'My Tech Portfolio')
ON CONFLICT (user_id, name) DO NOTHING;

-- Holdings for 'My Tech Portfolio' (assuming ID 1 if fresh, but we can sub-select)
WITH p AS (SELECT id FROM portfolios WHERE user_id = 'test-user' LIMIT 1)
INSERT INTO holdings (portfolio_id, symbol, shares, avg_price)
SELECT p.id, 'NVDA', 50, 420.00 FROM p
UNION ALL
SELECT p.id, 'AAPL', 100, 175.50 FROM p
UNION ALL
SELECT p.id, 'MSFT', 75, 350.00 FROM p
UNION ALL
SELECT p.id, 'GOOGL', 120, 135.00 FROM p
ON CONFLICT (portfolio_id, symbol) DO NOTHING;

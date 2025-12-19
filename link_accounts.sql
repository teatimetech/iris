-- Reset Passwords to 'password123'
UPDATE users SET password_hash = '$2b$12$qOWSSEZp005pP6awBN09M.C7NI3ocLjlmHZlPGiS5PV6WXqezoori' 
WHERE id IN ('alice-id', 'bob-id', 'charlie-id');

-- Link Alice (Update existing)
UPDATE portfolios 
SET iris_account_id = '74c7957b-e06c-4b3b-ace1-ec5d1ebe5433', 
    iris_account_number = '124999528',
    account_number = '124999528' -- Also update generic number field
WHERE user_id = 'alice-id' AND name = 'Alice Tech Portfolio';

-- Link Bob (Insert new or update)
INSERT INTO portfolios (user_id, name, iris_account_id, iris_account_number, account_number, description)
VALUES ('bob-id', 'Bob Growth Portfolio', '9e8f5ff1-086d-4b26-b63d-cf1faeda86d6', '124719886', '124719886', 'Aggressive Growth')
ON CONFLICT (user_id, name) DO UPDATE 
SET iris_account_id = EXCLUDED.iris_account_id,
    iris_account_number = EXCLUDED.iris_account_number,
    account_number = EXCLUDED.account_number;

-- Link Charlie (Insert new or update)
INSERT INTO portfolios (user_id, name, iris_account_id, iris_account_number, account_number, description)
VALUES ('charlie-id', 'Charlie Balanced Portfolio', '3d028c50-c1e3-439c-b189-55f22c91b379', '123591151', '123591151', 'Balanced Wealth')
ON CONFLICT (user_id, name) DO UPDATE 
SET iris_account_id = EXCLUDED.iris_account_id,
    iris_account_number = EXCLUDED.iris_account_number,
    account_number = EXCLUDED.account_number;

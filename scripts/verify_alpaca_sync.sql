-- Verification Query: Check all synced Alpaca accounts in IRIS database

SELECT 
    u.id AS iris_user_id,
    u.username,
    u.email AS login,
    u.first_name,
    u.last_name,
    p.iris_account_number,
    p.iris_account_id,
    p.alpaca_account_id,
    p.account_number AS alpaca_account_number,
    p.name AS portfolio_name,
    p.last_synced_at
FROM users u
LEFT JOIN portfolios p ON u.id = p.user_id
WHERE p.alpaca_account_id IS NOT NULL
ORDER BY p.iris_account_number;

SELECT 1
FROM accounts
WHERE username = %s OR email = %s
LIMIT 1;
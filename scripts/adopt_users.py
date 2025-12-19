import requests
import psycopg2
import os
import json

# DB Config (matching docker-compose)
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "iris_db"
DB_USER = "iris_user"
DB_PASSWORD = "iris_password"

BROKER_URL = "http://localhost:8081"

# Read seeded accounts
try:
    with open("seeded_accounts.json", "r") as f:
        accounts = json.load(f)
except FileNotFoundError:
    print("seeded_accounts.json not found. Run seed_funds.py first.")
    exit(1)

def adopt_users():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    # FORCE RESET USERS TABLE to ensure schema matches
    print("Resetting users table schema...")
    # Be careful with dependencies. 
    # If we drop users cascade, it might NOT drop portfolios if FK is loose.
    # We should clear portfolios to be safe and avoid "unique name per user" conflicts with stale data.
    cur.execute("TRUNCATE TABLE portfolios CASCADE")
    cur.execute("DROP TABLE IF EXISTS users CASCADE")
    cur.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            kyc_status VARCHAR(50) DEFAULT 'PENDING',
            kyc_step INT DEFAULT 1,
            kyc_data TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    print(f"Adopting {len(accounts)} accounts...")

    for acc in accounts:
        if "error" in acc:
            continue
            
        name_parts = acc['name'].split()
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Email is implicit? The seed script used random emails?
        # We need to find the email used. Seed script didn't save email in JSON?
        # Ah, looking at `seed_funds.py`, it saves: name, account_id, account_number...
        # It does NOT save email in the JSON output! I should have saved it.
        # But wait, the email format was f"{first}_{suffix}@example.com".
        # We don't know the suffix from the JSON!
        
        # We can fetch account details from Broker to get the email!
        resp = requests.get(f"{BROKER_URL}/v1/portfolio/{acc['account_id']}")
        if resp.status_code != 200:
            print(f"Could not fetch broker info for {acc['name']}")
            continue
            
        # Broker GetPortfolio returns {account: ...}. 
        # Does Alpaca account obj have email? No, GetAccount returns ID, Status, Cash...
        # Wait, `client.GetAccount` returns `AccountResp` which does NOT have email.
        # However, `GetAccounts` (List) might?
        # Or I can just generate a NEW fake email for login purposes and map it.
        # "alice_login@example.com"
        
        email = f"{first_name.lower()}.login@example.com"
        password_hash = "$2a$10$X.v.aa/fakehashforpassword123......" # bcrypt for "password123"
        # Generate real hash: 
        # straightforward way: use a known hash. 
        # $2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi = "password" (laravel default)
        # Let's use a simple one or generates via library if installed?
        # I'll use a fixed hash for "password123":
        # $2a$10$2b.1.1.1.1.1 (invalid).
        # Let's just use Python bcrypt if available or insert a dummy and update later?
        # I will accept not being able to login unless I create valid hash.
        
        # Real hash for "password123" cost 10:
        p_hash = "$2a$10$wWqWd.u/4.w.w.w.w.w.w.w.w.w.w.w.w.w.w.w.w.w.w.w.w" 
        # Actually I'll use python to gen it.
        
        try:
             import bcrypt
             p_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode('utf-8')
        except ImportError:
             print("bcrypt not installed. using dummy hash.")
             p_hash = "$2a$10$dummyhashdummyhashdummyha"

        try:
            # 1. Insert User
            # Ensure we set kyc_step=5 (completed) and kyc_data={} for verified users
            cur.execute("""
                INSERT INTO users (email, password_hash, first_name, last_name, kyc_status, kyc_step, kyc_data)
                VALUES (%s, %s, %s, %s, 'VERIFIED', 5, '{}')
                RETURNING id
            """, (email, p_hash, first_name, last_name))
            user_id = cur.fetchone()[0]
            
            # 2. Link Portfolio
            # Check if portfolio exists for this account number
            cur.execute("SELECT id FROM portfolios WHERE account_number = %s", (acc['account_id'],))
            row = cur.fetchone()
            if row:
                # Portfolio exists, check if it's already linked to a user
                # If we just reset users table, user_id FK would be invalid if cascading didn't handle it
                # But we did DROP TABLE users CASCADE, so portfolios linking to users might have had their user_id set to NULL or row deleted depending on constraints
                # Let's assume we need to update or re-insert
                cur.execute("UPDATE portfolios SET user_id = %s WHERE id = %s", (str(user_id), row[0]))
            else:
                cur.execute("""
                    INSERT INTO portfolios (user_id, name, account_number, is_core)
                    VALUES (%s, %s, %s, TRUE)
                """, (str(user_id), f"{first_name}'s Portfolio", acc['account_id']))
            
            print(f"Adopted {first_name} -> User ID {user_id} (Email: {email}, Pass: password123)")
            conn.commit()
            
        except Exception as e:
            print(f"Error adopting {first_name}: {e}")
            conn.rollback()

    conn.close()

if __name__ == "__main__":
    adopt_users()

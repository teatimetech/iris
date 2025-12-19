#!/usr/bin/env python3
"""
DB Seeding Script for Alpaca Accounts
Seeds IRIS database with 22 Alpaca accounts after make clean-all
Queries Alpaca API for live cash balances and creates user/portfolio mappings
"""

import requests
import psycopg2
import json
import sys
from typing import Dict, List, Optional

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "iris_db",
    "user": "iris_user",
    "password": "iris_password"
}

BROKER_SERVICE_URL = "http://localhost:8081"

# 22 Alpaca accounts to seed (from user's table)
ALPACA_ACCOUNTS = [
    {"account_number": "124515122", "account_id": "7e47986e-f83e-4c47-8244-6793ae0d3d90", "name": "Charlie Yield", "email": "charlie.login@example.com"},
    {"account_number": "124999528", "account_id": "74c7957b-e06c-4b3b-ace1-ec5d1ebe5433", "name": "Investor Final User", "email": "investor_final@example.com"},
    {"account_number": "124719886", "account_id": "9e8f5ff1-086d-4b26-b63d-cf1faeda86d6", "name": "API Test", "email": "api_test_user_4@example.com"},
    {"account_number": "123591151", "account_id": "3d028c50-c1e3-439c-b189-55f22c91b379", "name": "API Test", "email": "api_test_user_3@example.com"},
    {"account_number": "123409926", "account_id": "ba911c85-41ca-45c9-b00e-c52f6b9610d4", "name": "API Test", "email": "api_test_user_2@example.com"},
    {"account_number": "123373602", "account_id": "bd1cfdb2-c884-4b22-b506-5c305da6c726", "name": "Browser Test User", "email": "fix_test@example.com"},
    {"account_number": "123627500", "account_id": "04892f7d-5bee-40c6-92bb-b4b554b534bc", "name": "Charlie Yield", "email": "charlie_8638@example.com"},
    {"account_number": "123488287", "account_id": "d9795f06-bd7d-4a24-af1e-f32a375ea65f", "name": "Bob Investor", "email": "bob_8638@example.com"},
    {"account_number": "123322347", "account_id": "1a3a5474-83ee-4132-8092-bfad2e758c28", "name": "Alice Trader", "email": "alice_8638@example.com"},
    {"account_number": "123330643", "account_id": "278bed09-af83-4156-b041-3bcc73a0f1e7", "name": "Charlie Yield", "email": "charlie_6712@example.com"},
    {"account_number": "123445664", "account_id": "a9c997ca-a81c-4390-8548-09d45b51f507", "name": "Bob Investor", "email": "bob_6712@example.com"},
    {"account_number": "123103312", "account_id": "b751b9a7-bcb0-4993-9696-8833fff8f363", "name": "Alice Trader", "email": "alice_6712@example.com"},
    {"account_number": "123901040", "account_id": "2ce1cf8f-b691-4cf8-93da-f86d0ac880a1", "name": "Charlie Yield", "email": "charlie_2525@example.com"},
    {"account_number": "123713870", "account_id": "6926c224-5a2d-4d37-a985-2bdc71d15df1", "name": "Bob Investor", "email": "bob_2525@example.com"},
    {"account_number": "123304342", "account_id": "b999ee6c-2c67-4bbf-9e0c-370cd8ca2b95", "name": "Alice Trader", "email": "alice_2525@example.com"},
    {"account_number": "123756037", "account_id": "dcb7f45c-c3eb-4cdb-80a5-240b0733aa6d", "name": "Charlie Yield", "email": "charlie_8991@example.com"},
    {"account_number": "123294086", "account_id": "016f8c03-4b01-41fd-b482-ff73abbb5b4b", "name": "Bob Investor", "email": "bob_8991@example.com"},
    {"account_number": "123359115", "account_id": "1d93ecfa-e37f-44aa-a5c7-880e7805a4f1", "name": "Alice Trader", "email": "alice_8991@example.com"},
    {"account_number": "123256007", "account_id": "e2eb37ff-199f-47ce-a9c6-6aadeb902ab8", "name": "Charlie Yield", "email": "charlie@example.com"},
    {"account_number": "123601773", "account_id": "d6efc63f-15ae-429f-bcc0-97eea1417deb", "name": "Bob Investor", "email": "bob@example.com"},
    {"account_number": "123579853", "account_id": "e4b13393-b63c-4dc3-bcf8-4aa2f4377f8b", "name": "Alice Trader", "email": "alice@example.com"},
    {"account_number": "122766601", "account_id": "b0238cb6-de24-43f9-9c57-d80ae3b6641a", "name": "Iris Test", "email": "iris_test_105@example.com"},
]


def generate_password_hash(password: str = "password123") -> str:
    """Generate bcrypt hash for the given password"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        print("[WARN] bcrypt not installed. Install with: pip install bcrypt")
        print("[WARN] Using dummy hash - accounts won't be loginable!")
        return "$2a$10$DummyHashForTestingPurposesOnly.NotSecure"


def query_alpaca_balance(account_id: str) -> Optional[Dict]:
    """Query Alpaca broker service for account balance"""
    try:
        url = f"{BROKER_SERVICE_URL}/v1/portfolio/{account_id}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            account = data.get('account', {})
            return {
                'cash': float(account.get('cash', 0)),
                'equity': float(account.get('equity', 0)),
                'buying_power': float(account.get('buying_power', 0))
            }
    except Exception as e:
        print(f"[WARN] Failed to query Alpaca for {account_id[:8]}...: {e}")
    return None


def seed_database():
    """Main seeding function"""
    print("=" * 80)
    print("IRIS Database Seeding - Alpaca Accounts")
    print("=" * 80)
    print(f"\nSeeding {len(ALPACA_ACCOUNTS)} accounts...")
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("[OK] Connected to database")
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        print("Make sure PostgreSQL is running: docker ps | grep postgres")
        sys.exit(1)
    
    # Ensure iris_acct_seq exists
    try:
        cur.execute("CREATE SEQUENCE IF NOT EXISTS iris_acct_seq START 1;")
        conn.commit()
    except Exception as e:
        print(f"[WARN] Could not create sequence: {e}")
    
    # Get Alpaca broker ID
    cur.execute("SELECT id FROM brokers WHERE name = 'alpaca'")
    broker_row = cur.fetchone()
    if not broker_row:
        print("[INFO] Alpaca broker not found, creating...")
        cur.execute("""
            INSERT INTO brokers (name, display_name, description)
            VALUES ('alpaca', 'Alpaca Markets', 'Core IRIS Brokerage')
            RETURNING id
        """)
        broker_id = cur.fetchone()[0]
        conn.commit()
    else:
        broker_id = broker_row[0]
    print(f"[OK] Alpaca broker ID: {broker_id}")
    
    # Generate password hash once
    password_hash = generate_password_hash("password123")
    
    success_count = 0
    results = []
    
    print("\nProcessing accounts...")
    print("-" * 80)
    
    for idx, acc in enumerate(ALPACA_ACCOUNTS, 1):
        account_id = acc['account_id']
        account_number = acc['account_number']
        name = acc['name']
        email = acc['email']
        
        print(f"\n[{idx}/{len(ALPACA_ACCOUNTS)}] {name} ({email})")
        print(f"  Alpaca: {account_number} / {account_id[:8]}...")
        
        # Query Alpaca for balances
        alpaca_data = query_alpaca_balance(account_id)
        if alpaca_data:
            print(f"  Balance: ${alpaca_data['cash']:,.2f} cash, ${alpaca_data['equity']:,.2f} equity")
        
        # Parse name
        name_parts = name.split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ""
        username = f"{first_name.lower()}_{account_number[-4:]}"
        
        try:
            # Check if user exists (checking profiles table for email)
            # Schema: users(id) <- accounts(user_id) <- profiles(user_id)
            
            # Need to verify if the email exists in profiles
            cur.execute("SELECT user_id FROM profiles WHERE email = %s", (email,))
            profile_row = cur.fetchone()
            
            user_id = None
            if profile_row:
                user_id = profile_row[0]
                print(f"  [OK] User/Profile exists (ID: {user_id[:8]}...)")
            else:
                # 1. Create User
                cur.execute("""
                    INSERT INTO users (id, first_name, last_name)
                    VALUES (gen_random_uuid()::text, %s, %s)
                    RETURNING id
                """, (first_name, last_name))
                user_id = cur.fetchone()[0]
                
                # 2. Create Profile
                cur.execute("""
                    INSERT INTO profiles (user_id, email, password_hash)
                    VALUES (%s, %s, %s)
                """, (user_id, email, password_hash))
                
                print(f"  [OK] Created user & profile (ID: {user_id[:8]}...)")

            # 3. Check/Create Account
            cur.execute("SELECT id FROM accounts WHERE user_id = %s", (user_id,))
            account_row = cur.fetchone()
            account_id = None
            
            if account_row:
                account_id = account_row[0]
                # Update Alpaca info on existing account
                cur.execute("""
                    UPDATE accounts 
                    SET alpaca_account_id = %s, alpaca_account_number = %s, kyc_status = 'COMPLETED'
                    WHERE id = %s
                """, (account_id, account_number, account_id))
            else:
                cur.execute("""
                    INSERT INTO accounts (id, user_id, alpaca_account_number, alpaca_account_id, kyc_status, status)
                    VALUES (gen_random_uuid()::text, %s, %s, %s, 'COMPLETED', 'ACTIVE')
                    RETURNING id
                """, (user_id, account_number, account_id))
                account_id = cur.fetchone()[0]
                print(f"  [OK] Created/Updated Account (ID: {account_id[:8]}...)")
                
            # 4. Create/Update Portfolio
            # New schema: portfolios linked to accounts
            cur.execute("""
                SELECT id, iris_account_number
                FROM portfolios
                WHERE account_id = %s AND name = %s
            """, (account_id, f"{first_name}'s Portfolio"))
            
            portfolio_row = cur.fetchone()
            
            iris_acct_num = "N/A"
            if portfolio_row:
                print(f"  [OK] Portfolio exists")
                iris_acct_num = portfolio_row[1]
                # Update broker if needed
                cur.execute("UPDATE portfolios SET broker_id = %s WHERE id = %s", (broker_id, portfolio_row[0]))
            else:
                # Create portfolio
                # Generate iris_account_number manually or let DB default if logic exists? 
                # Migration 010 didn't set default for iris_account_number, but previous schema used LPAD sequence.
                # Let's use the sequence logic here.
                cur.execute("""
                    INSERT INTO portfolios (
                        account_id, name, type, is_default, broker_id,
                        iris_account_number, iris_account_id, last_synced_at
                    )
                    VALUES (
                        %s, %s, 'IRIS Core', TRUE, %s,
                        LPAD(nextval('iris_acct_seq')::text, 11, '0'),
                        gen_random_uuid()::text,
                        CURRENT_TIMESTAMP
                    )
                    RETURNING id, iris_account_number
                """, (account_id, f"{first_name}'s Portfolio", broker_id))
                pid, iris_acct_num = cur.fetchone()
                print(f"  [OK] Created portfolio (IRIS: {iris_acct_num})")
            
            # 5. Create KYC entry if missing
            cur.execute("""
                INSERT INTO kyc (account_id, citizenship, kyc_data)
                VALUES (%s, 'USA', '{}')
                ON CONFLICT (account_id) DO NOTHING
            """, (account_id,))
            
            conn.commit()
            success_count += 1
            
            results.append({
                'email': email,
                'iris_account_number': iris_acct_num,
                'alpaca_account_number': account_number,
                'status': 'success'
            })
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            conn.rollback()
            results.append({'email': email, 'error': str(e)})
    
    cur.close()
    conn.close()
    
    # Summary
    print("\n" + "=" * 80)
    print("SEEDING COMPLETE")
    print("=" * 80)
    print(f"\nSuccessfully seeded: {success_count}/{len(ALPACA_ACCOUNTS)} accounts")
    
    if success_count < len(ALPACA_ACCOUNTS):
        print("\n[WARN] Some accounts failed. Check errors above.")
        sys.exit(1)
    else:
        print("\n[OK] All accounts seeded successfully!")
        print("\nDefault password for all accounts: password123")
        print("\nExample logins:")
        for acc in ALPACA_ACCOUNTS[:3]:
            print(f"  - {acc['email']} / password123")


if __name__ == "__main__":
    seed_database()

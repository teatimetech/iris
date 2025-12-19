#!/usr/bin/env python3
"""
Sync all Alpaca accounts to IRIS database
- Queries Alpaca API for each account's cash balance and equity
- Creates/updates users and portfolios in IRIS database
- Maps Alpaca account_number and account_id to IRIS accounts
- Generates login credentials table
"""

import requests
import psycopg2
import json
import sys
from typing import Dict, List, Optional
from datetime import datetime

# Configuration
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "iris_db"
DB_USER = "iris_user"
DB_PASSWORD = "iris_password"

BROKER_SERVICE_URL = "http://localhost:8081"

# Alpaca accounts data
ALPACA_ACCOUNTS = [
    {"account_number": "124515122", "account_id": "7e47986e-f83e-4c47-8244-6793ae0d3d90", "name": "Charlie Yield", "email": "charlie.login@example.com", "equity": 0},
    {"account_number": "124999528", "account_id": "74c7957b-e06c-4b3b-ace1-ec5d1ebe5433", "name": "Investor Final User", "email": "investor_final@example.com", "equity": 44917.61},
    {"account_number": "124719886", "account_id": "9e8f5ff1-086d-4b26-b63d-cf1faeda86d6", "name": "API Test", "email": "api_test_user_4@example.com", "equity": 45000},
    {"account_number": "123591151", "account_id": "3d028c50-c1e3-439c-b189-55f22c91b379", "name": "API Test", "email": "api_test_user_3@example.com", "equity": 45000},
    {"account_number": "123409926", "account_id": "ba911c85-41ca-45c9-b00e-c52f6b9610d4", "name": "API Test", "email": "api_test_user_2@example.com", "equity": 45000},
    {"account_number": "123373602", "account_id": "bd1cfdb2-c884-4b22-b506-5c305da6c726", "name": "Browser Test User", "email": "fix_test@example.com", "equity": 0},
    {"account_number": "123627500", "account_id": "04892f7d-5bee-40c6-92bb-b4b554b534bc", "name": "Charlie Yield", "email": "charlie_8638@example.com", "equity": 20000},
    {"account_number": "123488287", "account_id": "d9795f06-bd7d-4a24-af1e-f32a375ea65f", "name": "Bob Investor", "email": "bob_8638@example.com", "equity": 10000},
    {"account_number": "123322347", "account_id": "1a3a5474-83ee-4132-8092-bfad2e758c28", "name": "Alice Trader", "email": "alice_8638@example.com", "equity": 14934.06},
    {"account_number": "123330643", "account_id": "278bed09-af83-4156-b041-3bcc73a0f1e7", "name": "Charlie Yield", "email": "charlie_6712@example.com", "equity": 20000},
    {"account_number": "123445664", "account_id": "a9c997ca-a81c-4390-8548-09d45b51f507", "name": "Bob Investor", "email": "bob_6712@example.com", "equity": 10000},
    {"account_number": "123103312", "account_id": "b751b9a7-bcb0-4993-9696-8833fff8f363", "name": "Alice Trader", "email": "alice_6712@example.com", "equity": 15000},
    {"account_number": "123901040", "account_id": "2ce1cf8f-b691-4cf8-93da-f86d0ac880a1", "name": "Charlie Yield", "email": "charlie_2525@example.com", "equity": 0},
    {"account_number": "123713870", "account_id": "6926c224-5a2d-4d37-a985-2bdc71d15df1", "name": "Bob Investor", "email": "bob_2525@example.com", "equity": 50000},
    {"account_number": "123304342", "account_id": "b999ee6c-2c67-4bbf-9e0c-370cd8ca2b95", "name": "Alice Trader", "email": "alice_2525@example.com", "equity": 0},
    {"account_number": "123756037", "account_id": "dcb7f45c-c3eb-4cdb-80a5-240b0733aa6d", "name": "Charlie Yield", "email": "charlie_8991@example.com", "equity": 0},
    {"account_number": "123294086", "account_id": "016f8c03-4b01-41fd-b482-ff73abbb5b4b", "name": "Bob Investor", "email": "bob_8991@example.com", "equity": 0},
    {"account_number": "123359115", "account_id": "1d93ecfa-e37f-44aa-a5c7-880e7805a4f1", "name": "Alice Trader", "email": "alice_8991@example.com", "equity": 0},
    {"account_number": "123256007", "account_id": "e2eb37ff-199f-47ce-a9c6-6aadeb902ab8", "name": "Charlie Yield", "email": "charlie@example.com", "equity": 0},
    {"account_number": "123601773", "account_id": "d6efc63f-15ae-429f-bcc0-97eea1417deb", "name": "Bob Investor", "email": "bob@example.com", "equity": 0},
    {"account_number": "123579853", "account_id": "e4b13393-b63c-4dc3-bcf8-4aa2f4377f8b", "name": "Alice Trader", "email": "alice@example.com", "equity": 0},
    {"account_number": "122766601", "account_id": "b0238cb6-de24-43f9-9c57-d80ae3b6641a", "name": "Iris Test", "email": "iris_test_105@example.com", "equity": 0},
]


def query_alpaca_account(account_id: str) -> Optional[Dict]:
    """Query Alpaca API for account details including cash balance and equity"""
    try:
        resp = requests.get(f"{BROKER_SERVICE_URL}/v1/portfolio/{account_id}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            account_info = data.get('account', {})
            return {
                'cash': float(account_info.get('cash', 0)),
                'equity': float(account_info.get('equity', 0)),
                'buying_power': float(account_info.get('buying_power', 0)),
                'portfolio_value': float(account_info.get('portfolio_value', 0)),
                'status': account_info.get('status', 'UNKNOWN')
            }
        else:
            print(f"  [WARN] Failed to query Alpaca for {account_id}: {resp.status_code}")
            return None
    except Exception as e:
        print(f"  [ERROR] Error querying Alpaca for {account_id}: {e}")
        return None


def generate_password_hash(password: str = "password123") -> str:
    """Generate bcrypt hash for password"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        print("  [WARN] bcrypt not installed, using dummy hash")
        return "$2a$10$DummyHashDummyHashDummyHashDummyHashDummyHashDummy"


def sync_accounts():
    """Main sync function"""
    print("=" * 80)
    print("IRIS Alpaca Account Synchronization Tool")
    print("=" * 80)
    print(f"\nSyncing {len(ALPACA_ACCOUNTS)} Alpaca accounts to IRIS database...")
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        print("[OK] Connected to IRIS database")
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        sys.exit(1)
    
    # Get broker ID for Alpaca
    cur.execute("SELECT id FROM brokers WHERE name = 'alpaca'")
    broker_row = cur.fetchone()
    if not broker_row:
        print("[ERROR] Alpaca broker not found in database. Run migrations first.")
        conn.close()
        sys.exit(1)
    broker_id = broker_row[0]
    print(f"[OK] Found Alpaca broker (ID: {broker_id})")
    
    results = []
    password = "password123"
    password_hash = generate_password_hash(password)
    
    print(f"\n{'':60}")
    print("Processing accounts...")
    print("-" * 80)
    
    for idx, acc in enumerate(ALPACA_ACCOUNTS, 1):
        account_id = acc['account_id']
        account_number = acc['account_number']
        name = acc['name']
        email = acc['email']
        
        print(f"\n[{idx}/{len(ALPACA_ACCOUNTS)}] {name} ({email})")
        print(f"  Alpaca Account: {account_number} / {account_id}")
        
        # Query Alpaca for latest balance
        alpaca_data = query_alpaca_account(account_id)
        if alpaca_data:
            cash = alpaca_data['cash']
            equity = alpaca_data['equity']
            print(f"  Alpaca Balance: Cash=${cash:,.2f}, Equity=${equity:,.2f}")
        else:
            # Use provided equity value if query failed
            cash = 0
            equity = acc['equity']
            print(f"  Using provided equity: ${equity:,.2f}")
        
        # Parse name
        name_parts = name.split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        try:
            # Check if user exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_row = cur.fetchone()
            
            if user_row:
                user_id = user_row[0]
                print(f"  [OK] User exists (IRIS ID: {user_id})")
            else:
                # Create user with username
                username = f"{first_name.lower()}_{account_number[-4:]}"  # e.g., "charlie_5122"
                cur.execute("""
                    INSERT INTO users (id, username, email, password_hash, first_name, last_name, kyc_status, kyc_step, kyc_data)
                    VALUES (gen_random_uuid()::text, %s, %s, %s, %s, %s, 'VERIFIED', 5, '{}')
                    RETURNING id
                """, (username, email, password_hash, first_name, last_name))
                user_id = cur.fetchone()[0]
                print(f"  [OK] Created user (IRIS ID: {user_id})")
            
            # Check if portfolio exists
            cur.execute("""
                SELECT id, iris_account_number, iris_account_id
                FROM portfolios
                WHERE alpaca_account_id = %s
            """, (account_id,))
            portfolio_row = cur.fetchone()
            
            if portfolio_row:
                portfolio_id, iris_acct_num, iris_acct_id = portfolio_row
                print(f"  [OK] Portfolio exists (ID: {portfolio_id})")
                print(f"    IRIS Account: {iris_acct_num} / {iris_acct_id}")
                
                # Update portfolio user_id if needed
                cur.execute("""
                    UPDATE portfolios
                    SET user_id = %s, last_synced_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (str(user_id), portfolio_id))
                
            else:
                # Create portfolio with IRIS account numbers
                cur.execute("""
                    INSERT INTO portfolios (
                        user_id, name, broker_id, is_core,
                        alpaca_account_id, account_number,
                        iris_account_id, iris_account_number,
                        last_synced_at
                    )
                    VALUES (
                        %s, %s, %s, TRUE,
                        %s, %s,
                        gen_random_uuid()::text,
                        LPAD(nextval('iris_acct_seq')::text, 11, '0'),
                        CURRENT_TIMESTAMP
                    )
                    RETURNING id, iris_account_number, iris_account_id
                """, (str(user_id), f"{first_name}'s Alpaca Portfolio", broker_id, account_id, account_number))
                portfolio_id, iris_acct_num, iris_acct_id = cur.fetchone()
                print(f"  [OK] Created portfolio (ID: {portfolio_id})")
                print(f"    IRIS Account: {iris_acct_num} / {iris_acct_id}")
            
            # Store result
            results.append({
                'iris_user_id': user_id,
                'iris_account_number': iris_acct_num,
                'iris_account_id': iris_acct_id,
                'alpaca_account_number': account_number,
                'alpaca_account_id': account_id,
                'name': name,
                'email': email,
                'login': email,
                'password': password,
                'cash_balance': cash,
                'equity': equity,
                'status': alpaca_data['status'] if alpaca_data else 'UNKNOWN'
            })
            
            conn.commit()
            print(f"  [OK] Synced successfully")
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            conn.rollback()
            results.append({
                'name': name,
                'email': email,
                'error': str(e)
            })
    
    conn.close()
    
    # Print summary table
    print("\n" + "=" * 80)
    print("SYNC COMPLETE - ACCOUNT SUMMARY")
    print("=" * 80)
    
    print("\n{:<25} {:<15} {:<12} {:<12} {:<12}".format(
        "Name", "IRIS ID", "IRIS Acct#", "Cash", "Equity"))
    print("-" * 80)
    
    for r in results:
        if 'error' not in r:
            print("{:<25} {:<15} {:<12} ${:<11,.2f} ${:<11,.2f}".format(
                r['name'][:24],
                str(r['iris_user_id']),
                r['iris_account_number'],
                r['cash_balance'],
                r['equity']
            ))
    
    # Save detailed results
    output_file = "alpaca_sync_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[OK] Detailed results saved to: {output_file}")
    
    # Print credentials table
    print("\n" + "=" * 80)
    print("LOGIN CREDENTIALS")
    print("=" * 80)
    print("\n{:<40} {:<40} {:<15}".format("Email/Login", "Password", "Status"))
    print("-" * 95)
    
    for r in results:
        if 'error' not in r:
            print("{:<40} {:<40} {:<15}".format(
                r['email'],
                r['password'],
                r['status']
            ))
    
    print("\n" + "=" * 80)
    print(f"Total synced: {len([r for r in results if 'error' not in r])}/{len(ALPACA_ACCOUNTS)}")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    sync_accounts()

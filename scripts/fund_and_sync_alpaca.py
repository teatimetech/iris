import os
import time
import psycopg2
import requests
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../.env")

# Broker Service Config
BROKER_SERVICE_URL = os.getenv("BROKER_SERVICE_URL", "http://iris-broker-service:8081")

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "iris_user"),
        password=os.getenv("DB_PASSWORD", "iris_password"),
        dbname=os.getenv("DB_NAME", "iris_db")
    )

def get_alpaca_balance(account_id):
    """Query IRIS Broker Service for balance"""
    try:
        url = f"{BROKER_SERVICE_URL}/v1/portfolio/{account_id}"
        # print(f"Querying {url}...")
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Response format expected from broker service:
            # { "account": { "cash": "...", "equity": "...", ... } }
            account = data.get('account', {})
            return float(account.get('cash', 0.0))
        else:
            print(f"Broker Service Error ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    return None

def sync_accounts():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. Fetch all portfolios joined with accounts
        print("Fetching portfolios...")
        # We need the Alpaca ACCOUNT ID (UUID), not the account number, for the Broker Service usually?
        # seed_script used account_id.
        cur.execute("""
            SELECT p.id as portfolio_id, p.name, a.alpaca_account_id, a.id as local_account_id
            FROM portfolios p
            JOIN accounts a ON p.account_id = a.id
            WHERE a.alpaca_account_id IS NOT NULL
        """)
        portfolios = cur.fetchall()

        print(f"Found {len(portfolios)} portfolios linked to Alpaca.")

        for p in portfolios:
            pf_id = p['portfolio_id']
            alpaca_id = p['alpaca_account_id']
            
            cash = get_alpaca_balance(alpaca_id)
            
            if cash is None:
                print(f"  [WARN] API failed for {alpaca_id}. Fallback to mock funding ($100k).")
                cash = 100000.0
            
            if cash is not None:
                print(f"Portfolio {pf_id} (Alpaca {alpaca_id[:8]}): Cash=${cash:,.2f}")
                
                # Update DB
                cur.execute("""
                    UPDATE portfolios 
                    SET cash_balance = %s, updated_at = NOW()
                    WHERE id = %s
                """, (cash, pf_id))
                conn.commit()

    except Exception as e:
        print(f"Sync failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    sync_accounts()

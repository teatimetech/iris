#!/usr/bin/env python3
"""
Alpaca Account Synchronization Script for IRIS

Synchronizes Alpaca broker accounts from CSV to IRIS database.
- Deletes all existing users, accounts, profiles, portfolios, and holdings
- Creates users from CSV data with password 'password123'
- Queries Alpaca API for account balances and positions
- Funds zero-balance accounts with $100,000
- Populates IRIS database with complete account data

Usage:
    python sync_alpaca_accounts_v2.py <csv_file> [--dry-run]

Environment Variables:
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    ALPACA_API_KEY, ALPACA_API_SECRET
"""

import csv
import sys
import os
import logging
import uuid
import re
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import bcrypt
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Install with: pip install psycopg2-binary bcrypt requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_alpaca_accounts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AlpacaClient:
    """Client for Alpaca Broker API"""
    
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://broker-api.sandbox.alpaca.markets/v1" if sandbox else "https://broker-api.alpaca.markets/v1"
        self.auth = HTTPBasicAuth(api_key, api_secret)
        self.session = requests.Session()
        self.session.auth = self.auth
        
    def get_account(self, account_id: str) -> Optional[Dict]:
        """Get account details including cash, equity, buying power"""
        try:
            url = f"{self.base_url}/trading/accounts/{account_id}/account"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get account {account_id}: {e}")
            return None
    
    def get_positions(self, account_id: str) -> List[Dict]:
        """Get all positions for an account"""
        try:
            url = f"{self.base_url}/trading/accounts/{account_id}/positions"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get positions for {account_id}: {e}")
            return []
    
    def create_ach_relationship(self, account_id: str) -> Optional[str]:
        """Create ACH relationship for funding"""
        try:
            url = f"{self.base_url}/accounts/{account_id}/ach_relationships"
            payload = {
                "account_owner_name": "Test User",
                "bank_account_type": "CHECKING",
                "bank_account_number": "123456789012",
                "bank_routing_number": "111000025",
                "nickname": "Sandbox Bank"
            }
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json().get('id')
        except Exception as e:
            logger.error(f"Failed to create ACH relationship for {account_id}: {e}")
            return None
    
    def fund_account(self, account_id: str, amount: Decimal) -> bool:
        """Fund an account via transfer"""
        try:
            # First create ACH relationship
            relationship_id = self.create_ach_relationship(account_id)
            if not relationship_id:
                logger.error(f"Cannot fund account {account_id}: ACH relationship creation failed")
                return False
            
            # Create transfer
            url = f"{self.base_url}/accounts/{account_id}/transfers"
            payload = {
                "transfer_type": "ach",
                "relationship_id": relationship_id,
                "direction": "INCOMING",
                "timing": "immediate",
                "amount": str(amount)
            }
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully funded account {account_id} with ${amount}")
            return True
        except Exception as e:
            logger.error(f"Failed to fund account {account_id}: {e}")
            return False


class IRISDBSync:
    """IRIS Database Synchronization Handler"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Connected to IRIS database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def clear_all_data(self):
        """Delete all existing data from tables"""
        logger.warning("Clearing all data from database...")
        try:
            # Delete in correct order due to foreign key constraints
            tables = ['holdings', 'portfolios', 'kyc', 'profiles', 'accounts', 'users']
            for table in tables:
                self.cursor.execute(f"DELETE FROM {table};")
                logger.info(f"Cleared table: {table}")
            
            # Reset sequences
            self.cursor.execute("ALTER SEQUENCE IF EXISTS account_number_seq RESTART WITH 1;")
            self.cursor.execute("ALTER SEQUENCE IF EXISTS iris_acct_seq RESTART WITH 1;")
            
            self.conn.commit()
            logger.info("All data cleared successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to clear data: {e}")
            raise
    
    def get_alpaca_broker_id(self) -> Optional[int]:
        """Get the broker ID for Alpaca"""
        try:
            self.cursor.execute("SELECT id FROM brokers WHERE name = 'alpaca';")
            result = self.cursor.fetchone()
            if result:
                return result['id']
            logger.warning("Alpaca broker not found in database")
            return None
        except Exception as e:
            logger.error(f"Failed to get Alpaca broker ID: {e}")
            return None
    
    def create_user(self, user_id: str, first_name: str, last_name: str) -> bool:
        """Create user record"""
        try:
            self.cursor.execute("""
                INSERT INTO users (id, first_name, last_name, created_at, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """, (user_id, first_name, last_name))
            return True
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            return False
    
    def create_account(self, account_id: str, user_id: str, alpaca_account_number: str,
                       alpaca_account_id: str, status: str) -> bool:
        """Create account record"""
        try:
            self.cursor.execute("""
                INSERT INTO accounts (
                    id, user_id, alpaca_account_number, alpaca_account_id,
                    status, kyc_status, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """, (account_id, user_id, alpaca_account_number, alpaca_account_id, status))
            return True
        except Exception as e:
            logger.error(f"Failed to create account {account_id}: {e}")
            return False
    
    def create_profile(self, user_id: str, email: str, password: str, address_data: Dict) -> bool:
        """Create profile record with hashed password"""
        try:
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            self.cursor.execute("""
                INSERT INTO profiles (
                    user_id, email, password_hash, address_line1,
                    city, state, postal_code, country, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """, (
                user_id, email, password_hash, address_data.get('line1'),
                address_data.get('city'), address_data.get('state'),
                address_data.get('postal_code'), address_data.get('country', 'USA')
            ))
            return True
        except Exception as e:
            logger.error(f"Failed to create profile for {user_id}: {e}")
            return False
    
    def create_portfolio(self, account_id: str, name: str, broker_id: int) -> Optional[int]:
        """Create portfolio record and return its ID"""
        try:
            self.cursor.execute("""
                INSERT INTO portfolios (
                    account_id, name, type, is_default, broker_id,
                    created_at, updated_at
                )
                VALUES (%s, %s, 'IRIS Core', TRUE, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id;
            """, (account_id, name, broker_id))
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except Exception as e:
            logger.error(f"Failed to create portfolio for account {account_id}: {e}")
            return None
    
    def create_holding(self, portfolio_id: int, symbol: str, shares: Decimal, avg_price: Decimal) -> bool:
        """Create holding record"""
        try:
            self.cursor.execute("""
                INSERT INTO holdings (
                    portfolio_id, symbol, shares, avg_price,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """, (portfolio_id, symbol, shares, avg_price))
            return True
        except Exception as e:
            logger.error(f"Failed to create holding {symbol} for portfolio {portfolio_id}: {e}")
            return False
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.conn.rollback()


def parse_name(full_name: str) -> Tuple[str, str]:
    """Parse full name into first and last name"""
    parts = full_name.strip().split(maxsplit=1)
    first_name = parts[0] if len(parts) > 0 else "User"
    last_name = parts[1] if len(parts) > 1 else "Unknown"
    return first_name, last_name


def parse_address(address_str: str) -> Dict[str, str]:
    """Parse address string into structured components"""
    # Example: "123 Tech Blvd, San Francisco, CA, 94107, USA"
    parts = [p.strip() for p in address_str.split(',')]
    
    result = {
        'line1': parts[0] if len(parts) > 0 else '',
        'city': parts[1] if len(parts) > 1 else '',
        'state': parts[2] if len(parts) > 2 else '',
        'postal_code': parts[3] if len(parts) > 3 else '',
        'country': parts[4] if len(parts) > 4 else 'USA'
    }
    return result


def sync_accounts(csv_file: str, dry_run: bool = False):
    """Main synchronization function"""
    logger.info(f"Starting Alpaca account synchronization from {csv_file}")
    logger.info(f"Dry run mode: {dry_run}")
    
    # Load environment variables
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'iris_db'),
        'user': os.getenv('POSTGRES_USER', 'iris_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'iris_password')
    }
    
    alpaca_api_key = os.getenv('ALPACA_API_KEY')
    alpaca_api_secret = os.getenv('ALPACA_API_SECRET')
    
    if not alpaca_api_key or not alpaca_api_secret:
        logger.error("ALPACA_API_KEY and ALPACA_API_SECRET environment variables required")
        return False
    
    # Initialize clients
    alpaca = AlpacaClient(alpaca_api_key, alpaca_api_secret, sandbox=True)
    db = IRISDBSync(db_config)
    
    try:
        # Connect to database
        db.connect()
        
        # Clear existing data
        if not dry_run:
            db.clear_all_data()
        else:
            logger.info("DRY RUN: Would clear all existing data")
        
        # Get Alpaca broker ID
        broker_id = db.get_alpaca_broker_id()
        if not broker_id:
            logger.error("Alpaca broker not found in database. Please run migrations.")
            return False
        
        # Read CSV file
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            accounts = list(reader)
        
        logger.info(f"Found {len(accounts)} accounts in CSV")
        
        # Process each account
        success_count = 0
        funded_count = 0
        
        for idx, row in enumerate(accounts, 1):
            account_number = row['account_number']
            alpaca_account_id = row['account_id']
            name = row['name']
            email = row['email']
            address = row['address']
            status = row['status']
            
            logger.info(f"\n[{idx}/{len(accounts)}] Processing: {name} ({email})")
            
            # Generate UUIDs
            user_id = str(uuid.uuid4()).replace('-', '')
            account_id = str(uuid.uuid4()).replace('-', '')
            
            # Parse name and address
            first_name, last_name = parse_name(name)
            address_data = parse_address(address)
            
            # Query Alpaca for account details
            alpaca_account = alpaca.get_account(alpaca_account_id)
            if not alpaca_account:
                logger.warning(f"Could not fetch Alpaca account data for {alpaca_account_id}, using CSV data")
                cash_balance = Decimal(0)
            else:
                cash_balance = Decimal(alpaca_account.get('cash', '0'))
                logger.info(f"  Cash balance: ${cash_balance}")
            
            # Check if funding needed
            needs_funding = cash_balance == 0
            if needs_funding:
                logger.info(f"  Account has zero balance, funding with $100,000")
                if not dry_run:
                    if alpaca.fund_account(alpaca_account_id, Decimal('100000')):
                        funded_count += 1
                        cash_balance = Decimal('100000')
                else:
                    logger.info("  DRY RUN: Would fund account")
            
            # Get positions
            positions = alpaca.get_positions(alpaca_account_id)
            logger.info(f"  Found {len(positions)} positions")
            
            if dry_run:
                logger.info(f"  DRY RUN: Would create user, account, profile, portfolio, and {len(positions)} holdings")
                success_count += 1
                continue
            
            # Create database records
            try:
                # Create user
                if not db.create_user(user_id, first_name, last_name):
                    raise Exception("Failed to create user")
                
                # Create account
                if not db.create_account(account_id, user_id, account_number, alpaca_account_id, status):
                    raise Exception("Failed to create account")
                
                # Create profile
                if not db.create_profile(user_id, email, 'password123', address_data):
                    raise Exception("Failed to create profile")
                
                # Create portfolio
                portfolio_id = db.create_portfolio(account_id, 'Core Portfolio', broker_id)
                if not portfolio_id:
                    raise Exception("Failed to create portfolio")
                
                # Create holdings
                for position in positions:
                    symbol = position.get('symbol')
                    qty = Decimal(position.get('qty', '0'))
                    cost_basis = Decimal(position.get('cost_basis', '0'))
                    
                    if qty > 0:
                        avg_price = cost_basis / qty if qty > 0 else Decimal(0)
                        db.create_holding(portfolio_id, symbol, qty, avg_price)
                
                # Commit transaction for this account
                db.commit()
                success_count += 1
                logger.info(f"  ✓ Successfully synced account")
                
            except Exception as e:
                db.rollback()
                logger.error(f"  ✗ Failed to sync account: {e}")
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Synchronization {'DRY RUN ' if dry_run else ''}complete!")
        logger.info(f"Total accounts processed: {len(accounts)}")
        logger.info(f"Successfully synced: {success_count}")
        logger.info(f"Accounts funded: {funded_count}")
        logger.info(f"{'='*60}")
        
        return True
        
    except Exception as e:
        logger.error(f"Synchronization failed: {e}", exc_info=True)
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Sync Alpaca accounts to IRIS database')
    parser.add_argument('csv_file', help='Path to CSV file with account data')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying database')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        logger.error(f"CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    success = sync_accounts(args.csv_file, args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

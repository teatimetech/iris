# Alpaca Account Synchronization Scripts

This directory contains scripts to synchronize Alpaca broker accounts to the IRIS database.

## Files

- **sync_alpaca_accounts_v2.py** - Complete synchronization script (recommended)
- **sync_alpaca_accounts.py** - Legacy script (deprecated)
- **accounts.csv** - CSV file with Alpaca account data
- **requirements.txt** - Python dependencies

## Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Database configuration
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=iris_db
export POSTGRES_USER=iris_user
export POSTGRES_PASSWORD=iris_password

# Alpaca API credentials
export ALPACA_API_KEY=your_api_key
export ALPACA_API_SECRET=your_api_secret
```

### 3. Run Synchronization

**Dry run (preview changes)**:
```bash
python sync_alpaca_accounts_v2.py accounts.csv --dry-run
```

**Full synchronization**:
```bash
python sync_alpaca_accounts_v2.py accounts.csv
```

## Features

- **Data Cleanup**: Deletes all existing users, accounts, profiles, portfolios, and holdings
- **CSV Parsing**: Reads account data from CSV file
- **Address Parsing**: Parses address strings into structured fields
- **Alpaca API Integration**: Queries balances and positions for each account
- **Auto-Funding**: Funds zero-balance accounts with $100,000
- **Complete Schema**: Creates records in users, accounts, profiles, portfolios, and holdings tables
- **Error Handling**: Comprehensive logging and transaction rollback on failure
- **Dry Run Mode**: Preview changes without database modifications

## What the Script Does

1. **Clears Database**: Deletes all existing data from IRIS tables
2. **For Each CSV Account**:
   - Parses name and address
   - Queries Alpaca API for cash balance and equity
   - Checks if funding needed (balance = $0)
   - Funds account via Alpaca Transfer API if needed
   - Queries positions from Alpaca
   - Creates user record with UUID
   - Creates account record linking to Alpaca
   - Creates profile with hashed password ('password123')
   - Creates portfolio record
   - Creates holdings for each position
3. **Logs Results**: Outputs sync status and saves detailed log

## Output

- **Console**: Real-time progress for each account
- **sync_alpaca_accounts.log**: Detailed log file
- **Database**: Populated IRIS tables

## Troubleshooting

- **Missing dependencies**: Run `pip install -r requirements.txt`
- **Database connection fails**: Check POSTGRES_* environment variables
- **Alpaca API errors**: Verify ALPACA_API_KEY and ALPACA_API_SECRET
- **Permission denied**: Ensure database user has INSERT/DELETE permissions

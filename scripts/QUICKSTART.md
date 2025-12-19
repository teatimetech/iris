# Quick Start Guide: Alpaca Account Sync

## Prerequisites
- Docker services running (`make up`)
- Python 3.11+ installed
- Alpaca API credentials

## Step-by-Step

### 1. Install Dependencies
```powershell
cd c:\ai_IRIS\IRIS\scripts
pip install -r requirements.txt
```

### 2. Set Environment Variables

**Option A: Edit and source PowerShell script**
```powershell
# Edit set_env.ps1 and add your Alpaca credentials
notepad set_env.ps1

# Source the script
. .\set_env.ps1
```

**Option B: Set manually**
```powershell
$env:ALPACA_API_KEY = "your_key_here"
$env:ALPACA_API_SECRET = "your_secret_here"
```

### 3. Test with Dry Run
```powershell
python sync_alpaca_accounts_v2.py accounts.csv --dry-run
```

Expected output:
- "DRY RUN: Would clear all existing data"
- "Found 22 accounts in CSV"
- Processing status for each account
- "Synchronization DRY RUN complete!"

### 4. Run Full synchronization
```powershell
python sync_alpaca_accounts_v2.py accounts.csv
```

Expected output:
- "Clearing all data from database..."
- Processing each of 22 accounts
- "Successfully synced: 22"
- "Accounts funded: X" (where X = number of zero-balance accounts)

### 5. Verify Results

**Check database counts:**
```powershell
docker exec iris-postgres-1 psql -U iris_user -d iris_db -c "SELECT COUNT(*) FROM users;"
docker exec iris-postgres-1 psql -U iris_user -d iris_db -c "SELECT COUNT(*) FROM profiles;"
```

**Check sample data:**
```powershell
docker exec iris-postgres-1 psql -U iris_user -d iris_db -c "SELECT u.first_name, u.last_name, p.email FROM users u JOIN profiles p ON u.id = p.user_id LIMIT 5;"
```

### 6. Test Login

Open browser to http://localhost:3000/auth/login

Try logging in with:
- Email: `alice_8638@example.com`
- Password: `password123`

## Troubleshooting

### "ALPACA_API_KEY environment variable required"
- Make sure you sourced `set_env.ps1` or set the variables manually
- Check: `echo $env:ALPACA_API_KEY`

### "Database connection failed"
- Ensure Docker services are running: `make up`
- Check database is healthy: `docker ps`
- Verify environment variables are correct

### "Alpaca broker not found"
- Run database migrations: `make migrate` or check that Alpaca broker exists in `brokers` table

### Script creates users but no holdings
- Check Alpaca API response - account may have no positions
- Verify account_id is correct in CSV
- Check logs for Alpaca API errors

## Files Created
- `scripts/sync_alpaca_accounts_v2.py` - Main sync script
- `scripts/accounts.csv` - Account data (22 accounts)
- `scripts/requirements.txt` - Python dependencies
- `scripts/set_env.ps1` - Environment variable helper (Windows)
- `scripts/set_env.sh` - Environment variable helper (Linux/Mac)
- `scripts/README.md` - Detailed documentation
- `scripts/QUICKSTART.md` - This file

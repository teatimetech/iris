import requests
import json
import sys

BASE_URL = "http://localhost:8080"
USER_ID = "test-user"

def check_portfolio():
    print(f"Fetching portfolio for {USER_ID}...")
    try:
        resp = requests.get(f"{BASE_URL}/v1/portfolio/{USER_ID}")
        if resp.status_code != 200:
            print(f"FAILED: Status {resp.status_code}")
            print(resp.text)
            return False
            
        data = resp.json()
        print("Response received.")
        
        # Check Structure
        if "brokerGroups" not in data:
            print("FAILED: 'brokerGroups' missing")
            return False
            
        groups = data["brokerGroups"]
        print(f"Found {len(groups)} broker groups.")
        
        has_alpaca = False
        has_external = False
        
        for g in groups:
            print(f" - {g.get('displayName')} (${g.get('totalValue')})")
            if "Alpaca" in g.get('displayName', '') or g.get('brokerName') == 'alpaca':
                has_alpaca = True
            else:
                has_external = True
                
        if not has_alpaca:
            print("WARNING: No Core Alpaca portfolio found (might need mock data if broker service is empty)")
        if not has_external:
            print("WARNING: No External accounts found (migration might have failed?)")
            
        print(f"Total Value: ${data.get('totalValue')}")
        print(f"Overall P/L: {data.get('overallPL')}")
        
        return True
    
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = check_portfolio()
    sys.exit(0 if success else 1)

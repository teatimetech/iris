import requests
import json
import time

BROKER_SERVICE_URL = "http://localhost:8081"

def create_account(name, email):
    print(f"Creating account for {name} ({email})...")
    payload = {
        "contact": {
            "email_address": email,
            "phone_number": "555-555-0100",
            "street_address": ["123 Tech Blvd"],
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94107",
            "country": "USA"
        },
        "identity": {
            "given_name": name.split()[0],
            "family_name": name.split()[1],
            "date_of_birth": "1990-01-01",
            "tax_id": "555-55-4321",
            "tax_id_type": "USA_SSN",
            "country_of_tax_residence": "USA",
            "funding_source": ["employment_income"]
        },
        "disclosures": {
            "is_control_person": False,
            "is_affiliated_exchange_or_finra": False,
            "is_politically_exposed": False,
            "immediate_family_exposed": False
        },
        "agreements": [
            {
                "agreement": "margin_agreement",
                "signed_at": "2023-01-01T00:00:00Z",
                "ip_address": "127.0.0.1"
            },
            {
                "agreement": "account_agreement",
                "signed_at": "2023-01-01T00:00:00Z",
                "ip_address": "127.0.0.1"
            },
            {
                "agreement": "customer_agreement",
                "signed_at": "2023-01-01T00:00:00Z",
                "ip_address": "127.0.0.1"
            }
        ]
    }
    
    try:
        resp = requests.post(f"{BROKER_SERVICE_URL}/v1/accounts", json=payload)
        resp.raise_for_status()
        acct = resp.json()
        print(f"SUCCESS: Created Account ID: {acct['id']} | Account #: {acct['account_number']}")
        return acct
    except Exception as e:
        print(f"FAILED: {e}")
        if 'resp' in locals():
            print(resp.text)
        return None

def fund_account(account_id, amount):
    print(f"Funding account {account_id} with ${amount}...")
    payload = {
        "account_id": account_id,
        "amount": str(amount)
    }
    try:
        resp = requests.post(f"{BROKER_SERVICE_URL}/v1/funds", json=payload)
        resp.raise_for_status()
        print(f"SUCCESS: Funded {account_id}")
    except Exception as e:
        print(f"FAILED to fund: {e}")
        if 'resp' in locals():
            print(resp.text)

import random

def main():
    print("--- IRIS Broker Seeding Tool ---")
    
    suffix = random.randint(1000, 9999)
    # Create 3 Test Accounts (Reduced amounts to meet Sandbox limits of ~50k/day)
    users = [
        ("Alice Trader", f"alice_{suffix}@example.com", 15000),
        ("Bob Investor", f"bob_{suffix}@example.com", 10000),
        ("Charlie Yield", f"charlie_{suffix}@example.com", 20000)
    ]
    
    results = []
    
    for name, email, funds in users:
        acct = create_account(name, email)
        if acct:
            # Wait a bit for propagation if needed (Mock sync)
            time.sleep(1) 
            fund_account(acct['id'], funds)
            
            # Verify Balance
            try:
                verify_resp = requests.get(f"{BROKER_SERVICE_URL}/v1/portfolio/{acct['id']}")
                verify_data = verify_resp.json()
                # Alpaca sandbox transfers update cash instantly usually
                cash = verify_data.get('account', {}).get('cash')
                results.append({
                    "name": name,
                    "account_id": acct['id'],
                    "account_number": acct['account_number'],
                    "funds_requested": funds,
                    "current_cash": cash
                })
            except:
                results.append({"name": name, "error": "Verification Failed"})
        else:
            results.append({"name": name, "error": "Creation Failed"})
            
    print("\n--- Summary of Created Accounts ---")
    print(json.dumps(results, indent=2))
    
    # Save to file for user reference
    with open("seeded_accounts.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved details to seeded_accounts.json")

if __name__ == "__main__":
    main()

import requests
import json
import sys

BASE_URL = "http://localhost:8080"
EMAIL = "api_test_user_4@example.com"
PASSWORD = "password123"

def run():
    # 1. Signup
    print("1. Signing up...")
    signup_payload = {
        "email": EMAIL,
        "password": PASSWORD,
        "first_name": "API",
        "last_name": "Test"
    }
    try:
        res = requests.post(f"{BASE_URL}/v1/auth/signup", json=signup_payload)
        if res.status_code != 200:
            # If user exists, try login
            print(f"   Signup Status: {res.status_code}. Trying login...")
            res = requests.post(f"{BASE_URL}/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
            
        res.raise_for_status()
        data = res.json()
        token = data.get("token")
        user_id = data.get("user").get("id")
        print(f"   Success. User ID: {user_id}")
    except Exception as e:
        print(f"   Signup/Login failed: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Onboarding Step 1 (Save KYC Data)
    print("2. Saving KYC Data (Step 1)...")
    step1_payload = {
        "step": 2,
        "data": json.dumps({
            "dob": "1990-01-01",
            "tax_id": "210-50-6782" # Valid format
        })
    }
    requests.post(f"{BASE_URL}/v1/auth/onboarding/step", json=step1_payload, headers=headers)

    # 3. Final Onboarding (Create Account)
    print("3. Finalizing Onboarding (Create Account)...")
    final_payload = {
        "user_id": user_id,
        "phone": "555-000-0000",
        "street_address": ["123 Test St"],
        "city": "Test City",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA",
        "date_of_birth": "1990-01-01",
        "tax_id": "210-50-6782",
        "funding_source": ["employment_income"]
    }
    
    res = requests.post(f"{BASE_URL}/v1/auth/onboarding", json=final_payload, headers=headers)
    if res.status_code != 200:
        print(f"   Onboarding Failed: {res.status_code} {res.text}")
        return
    else:
        print(f"   Onboarding Success: {res.text}")

    import time
    print("4. Checking Portfolio for Cash (Waiting 5s)...")
    time.sleep(5)
    
    res = requests.get(f"{BASE_URL}/v1/portfolio/{user_id}", headers=headers)
    if res.status_code != 200:
        print(f"   Get Portfolio Failed: {res.status_code} {res.text}")
        return
    
    port_data = res.json()
    # Remove heavy data for printing
    if 'performance' in port_data: del port_data['performance']
    if 'allocation' in port_data: del port_data['allocation']
    print(f"   DEBUG RAW: {json.dumps(port_data, indent=2)}")
    # Check broker groups
    groups = port_data.get("brokerGroups", [])
    if not groups:
        print("   No broker groups found!")
        return
    
    core = groups[0]
    print(f"   Core Portfolio: Value=${core.get('totalValue')}, Cash=${core.get('cash')}, BP=${core.get('buyingPower')}")
    
    if core.get('cash') == 45000:
        print("   SUCCESS! Cash is 45,000.")
    else:
        print(f"   FAILURE! Cash is {core.get('cash')}")

if __name__ == "__main__":
    run()

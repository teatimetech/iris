import requests
import json

accounts = [
    "74c7957b-e06c-4b3b-ace1-ec5d1ebe5433",
    "9e8f5ff1-086d-4b26-b63d-cf1faeda86d6",
    "3d028c50-c1e3-439c-b189-55f22c91b379"
]

for acct_id in accounts:
    try:
        data = {"account_id": acct_id, "amount": "100000"}
        print(f"Funding {acct_id}...")
        resp = requests.post('http://localhost:8081/v1/funds', json=data)
        if resp.status_code == 200:
            print(f"Success: {resp.json()}")
        else:
            print(f"Failed: {resp.text}")
    except Exception as e:
        print(f"Error funding {acct_id}: {e}")

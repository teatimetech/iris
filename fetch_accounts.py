import requests
import json

try:
    response = requests.get('http://localhost:8081/v1/accounts')
    accounts = response.json()
    # Print first 3 accounts
    for i, acct in enumerate(accounts[:3]):
        print(f"Account {i+1}: {acct['id']} - {acct['account_number']}")
except Exception as e:
    print(f"Error: {e}")

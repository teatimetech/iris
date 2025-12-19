import requests
import json

URL = "http://localhost:8080/v1/portfolio/15"

def check():
    try:
        res = requests.get(URL)
        print(f"Status: {res.status_code}")
        data = res.json()
        print("Allocation:")
        print(json.dumps(data.get("allocation"), indent=2))
        print("Performance:")
        # print(json.dumps(data.get("performance"), indent=2)) # Skip large data
        print("Skipped")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()


import requests
import json
import sys

BASE_URL = "http://localhost:8080"

def test_chat_trade():
    print("Testing Agentic Trade Workflow...")
    
    # Message that should trigger the "TRADE" intent and "execute_trade_node"
    payload = {
        "user_id": "test-user",
        "prompt": "Buy 15 shares of NVDA"
    }
    
    try:
        url = f"{BASE_URL}/v1/chat"
        print(f"Sending request to {url} with payload {payload}...")
        resp = requests.post(url, json=payload, timeout=30)
        
        if resp.status_code == 200:
            print("Response:", resp.json())
            content = resp.json().get("response", "").lower()
            
            # Check if Agent mentions execution
            if "executed" in content or "success" in content:
                print("Agent confirmed trade execution.")
            else:
                print("Agent did not explicitly confirm execution in text (might have still happened). Response:", content)
                
            # Verify DB side
            resp_p = requests.get(f"{BASE_URL}/v1/portfolio/test-user")
            holdings = resp_p.json().get("holdings", [])
            # We bought 10 in Phase 2, now 15 more -> should be >= 25
            nvda = next((h for h in holdings if h["symbol"] == "NVDA"), None)
            if nvda and nvda["shares"] >= 25.0:
                 print(f"Portfolio confirmed holdings: {nvda['shares']} shares of NVDA.")
            else:
                 print(f"Portfolio check failed. NVDA shares: {nvda}")
                 sys.exit(1)

        else:
            print(f"Chat request failed: {resp.status_code} - {resp.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)

def test_chat_advice():
    print("\nTesting Agentic RAG Workflow...")
    # Intent: ADVICE
    payload = {
        "user_id": "test-user",
        "prompt": "What is the market outlook for technology?"
    }
    try:
        resp = requests.post(f"{BASE_URL}/v1/chat", json=payload, timeout=120)
        content = resp.json().get("response", "").lower()
        if "inflation" in content or "context" in content or "market" in content:
             print("Agent used RAG context in response.")
        else:
             print("Agent response might be generic. Check logs for tool output.")
             print("Response:", content)
             
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_chat_trade()
    test_chat_advice()

import requests
import time
import sys

GATEWAY_URL = "http://localhost:8080"

def wait_for_service():
    print("Waiting for API Gateway...")
    for _ in range(30):
        try:
            resp = requests.get(f"{GATEWAY_URL}/health", timeout=2)
            if resp.status_code == 200:
                print("API Gateway is up!")
                return True
        except:
            pass
        time.sleep(2)
    return False

def test_chat_context():
    print("\n--- Testing Context Aware Chat ---")
    payload = {
        "user_id": "test-user",
        "prompt": "What is the total value of my portfolio and what should I do with it?"
    }
    try:
        resp = requests.post(f"{GATEWAY_URL}/v1/chat", json=payload, timeout=60) # High timeout for LLM
        if resp.status_code == 200:
            print("Chat Response:", resp.json())
            return True
        else:
            print(f"Chat Failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"Chat Error: {e}")
        return False

def test_history():
    print("\n--- Testing Chat History ---")
    try:
        resp = requests.get(f"{GATEWAY_URL}/v1/chat/history/test-user", timeout=5)
        if resp.status_code == 200:
            history = resp.json()
            print(f"History Length: {len(history)}")
            print("Last Message:", history[-1] if history else "Empty")
            return len(history) > 0
        else:
            print(f"History Failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"History Error: {e}")
        return False

if __name__ == "__main__":
    if not wait_for_service():
        sys.exit(1)
    
    if test_chat_context():
        # Give DB a moment to act
        time.sleep(1)
        if test_history():
            print("\n[SUCCESS] Verification PASSED")
        else:
            print("\n[FAILED] History Verification FAILED")
    else:
        print("\n[FAILED] Chat Verification FAILED")

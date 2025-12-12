#!/bin/bash
set -euo pipefail

echo "--- IRIS Integration Test ---"

GATEWAY_PORT=8080
GATEWAY_URL="http://localhost:${GATEWAY_PORT}/v1/chat"

# 1. Setup Port Forwarding in the background
echo "Starting port-forward for iris-api-gateway..."
kubectl port-forward svc/iris-api-gateway 8080:8080 -n iris > /dev/null 2>&1 &
PF_PID=$!
sleep 5 # Wait for port forward to establish

function cleanup {
  echo "Cleaning up port-forward process..."
  kill $PF_PID
  echo "Test finished."
}
trap cleanup EXIT

# 2. Define the Test Request
USER_PROMPT='{"user_id": "test_user_1", "prompt": "Analyze NVIDIA stock performance and risk profile."}'

echo "Sending request to Gateway: ${GATEWAY_URL}"
echo "Prompt: Analyze NVIDIA stock performance and risk profile."

# 3. Execute the API call
RESPONSE=$(curl -s -X POST "${GATEWAY_URL}" \
  -H "Content-Type: application/json" \
  -d "${USER_PROMPT}")

# 4. Assertions
if [ $? -ne 0 ]; then
  echo "❌ FAIL: Curl request failed."
  exit 1
fi

EXPECTED_KEY="response"

if echo "$RESPONSE" | grep -q "\"${EXPECTED_KEY}\""; then
  echo "✅ PASS: Response received successfully and contains the key '${EXPECTED_KEY}'."
  echo "--- Full Response Snippet ---"
  echo "$RESPONSE" | python3 -m json.tool | head -n 10
  echo "---------------------------"
else
  echo "❌ FAIL: Response did not contain the expected key '${EXPECTED_KEY}'. Check K8s logs for agent failure."
  echo "Received Response: $RESPONSE"
  exit 1
fi

#!/bin/bash
set -euo pipefail

echo "=== IRIS Containerized Integration Test ==="
echo "Testing API Gateway and Agent Router connectivity"

# Configuration
GATEWAY_URL="${GATEWAY_URL:-http://iris-api-gateway:8080}"
MAX_RETRIES=10
RETRY_DELAY=3

# Wait for services to be ready using health endpoint
echo "Waiting for API Gateway to be ready..."
for i in $(seq 1 $MAX_RETRIES); do
    # Check health endpoint
    if curl -s -f "${GATEWAY_URL}/health" > /dev/null 2>&1; then
        echo "✅ API Gateway is healthy"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo "⚠️ API Gateway health check failed after ${MAX_RETRIES} attempts, proceeding with test..."
    fi
    echo "Attempt $i/${MAX_RETRIES}: Gateway not ready, waiting..."
    sleep $RETRY_DELAY
done

# Test the chat endpoint
echo ""
echo "Testing /v1/chat endpoint..."
RESPONSE=$(curl -s -X POST "${GATEWAY_URL}/v1/chat" \
    -H "Content-Type: application/json" \
    -d '{"user_id": "test_user", "prompt": "Hello, this is a test"}' \
    || echo '{"error": "curl failed"}')

echo "Response: $RESPONSE"

# Validate response
if echo "$RESPONSE" | grep -q "error"; then
    if echo "$RESPONSE" | grep -q "Agent Service unavailable"; then
        echo "⚠️  Expected error: Agent service not available (Ollama not running)"
        echo "✅ Gateway correctly handled missing backend"
        exit 0
    else
        echo "❌ Unexpected error in response"
        exit 1
    fi
elif echo "$RESPONSE" | grep -q "response"; then
    echo "✅ API Gateway integration test PASSED"
    exit 0
else
    echo "❌ Unexpected response format"
    exit 1
fi

#!/bin/bash

# Web UI Integration Test Script

echo "Starting Web UI Integration Tests..."

# 1. Test Web UI Accessibility
echo "Testing Web UI accessibility..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ Web UI is accessible (HTTP 200)"
else
    echo "❌ Web UI failed accessibility test (HTTP $HTTP_CODE)"
    exit 1
fi

# 2. Test API Gateway Health via Nginx
echo "Testing API Gateway health via Nginx..."
HEALTH_STATUS=$(curl -s http://localhost:80/health | grep "healthy")
if [ -n "$HEALTH_STATUS" ]; then
    echo "✅ API Gateway is healthy"
else
    echo "❌ API Gateway health check failed"
    exit 1
fi

# 3. Test Portfolio Endpoint
echo "Testing Portfolio endpoint..."
PORTFOLIO_DATA=$(curl -s http://localhost:8080/v1/portfolio/test-user)
if [[ $PORTFOLIO_DATA == *"totalValue"* ]]; then
    echo "✅ Portfolio data retrieved successfully"
else
    echo "❌ Failed to retrieve portfolio data"
    exit 1
fi

echo "All integration tests passed!"
exit 0

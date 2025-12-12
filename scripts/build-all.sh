#!/bin/bash
# Build script that runs in Docker container
set -euo pipefail

echo "=== Building IRIS Services ==="

# Build Go Gateway
echo "Building Go API Gateway..."
cd /workspace/microservices/iris-api-gateway
go mod download
go build -o iris-gateway main.go
echo "✅ Go Gateway built successfully"

# The Python service is built via Dockerfile, no need for script build
echo "✅ Build complete"

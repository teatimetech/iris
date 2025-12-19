#!/bin/bash
# Helper script to set environment variables for sync script
# Source this file before running sync: source set_env.sh

# Database configuration (adjust if different)
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=iris_db
export POSTGRES_USER=iris_user
export POSTGRES_PASSWORD=iris_password

# Alpaca API credentials (REQUIRED - replace with your actual credentials)
export ALPACA_API_KEY=${ALPACA_API_KEY:-"YOUR_ALPACA_API_KEY_HERE"}
export ALPACA_API_SECRET=${ALPACA_API_SECRET:-"YOUR_ALPACA_API_SECRET_HERE"}

echo "Environment variables set for Alpaca synchronization"
echo "POSTGRES_HOST=$POSTGRES_HOST"
echo "POSTGRES_DB=$POSTGRES_DB"
echo "ALPACA_API_KEY=${ALPACA_API_KEY:0:10}..."

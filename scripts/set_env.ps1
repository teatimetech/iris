# PowerShell script to set environment variables for sync script
# Run this before executing the sync script: . .\set_env.ps1

# Database configuration (adjust if different)
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "iris_db"
$env:POSTGRES_USER = "iris_user"
$env:POSTGRES_PASSWORD = "iris_password"

# Alpaca API credentials (REQUIRED - replace with your actual credentials)
if (-not $env:ALPACA_API_KEY) {
    $env:ALPACA_API_KEY = "YOUR_ALPACA_API_KEY_HERE"
}
if (-not $env:ALPACA_API_SECRET) {
    $env:ALPACA_API_SECRET = "YOUR_ALPACA_API_SECRET_HERE"
}

Write-Host "Environment variables set for Alpaca synchronization" -ForegroundColor Green
Write-Host "POSTGRES_HOST=$env:POSTGRES_HOST"
Write-Host "POSTGRES_DB=$env:POSTGRES_DB"
Write-Host "ALPACA_API_KEY=$($env:ALPACA_API_KEY.Substring(0, [Math]::Min(10, $env:ALPACA_API_KEY.Length)))..."

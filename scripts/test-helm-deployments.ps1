# Test Helm Chart Deployments (PowerShell)
# This script validates all Helm charts and their environment-specific values

$ErrorActionPreference = "Continue"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  IRIS Helm Chart Validation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
if (!(Get-Command helm -ErrorAction SilentlyContinue)) {
    Write-Host "Error: helm not found. Please install Helm 3.x first." -ForegroundColor Red
    exit 1
}

$helmVersion = (helm version --short)
Write-Host "✓ Helm found: $helmVersion" -ForegroundColor Green
Write-Host ""

# Services to test
$services = @("iris-api-gateway", "iris-agent-router", "iris-web-ui", "postgresql", "ollama")
$environments = @("dev", "qa", "stage", "prod")

$totalTests = 0
$passedTests = 0
$failedTests = 0

# Function to lint chart
function Test-HelmChart {
    param(
        [string]$Service,
        [string]$ValuesFile,
        [string]$Environment
    )
    
    $script:totalTests++
    Write-Host -NoNewline "Linting $Service ($Environment)... "
    
    try {
        if ($ValuesFile -and (Test-Path "helm\$Service\$ValuesFile")) {
            $output = helm lint "helm\$Service" -f "helm\$Service\$ValuesFile" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ PASSED" -ForegroundColor Green
                $script:passedTests++
                return $true
            }
            else {
                Write-Host "✗ FAILED" -ForegroundColor Red
                Write-Host $output -ForegroundColor Yellow
                $script:failedTests++
                return $false
            }
        }
        else {
            $output = helm lint "helm\$Service" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ PASSED" -ForegroundColor Green
                $script:passedTests++
                return $true
            }
            else {
                Write-Host "✗ FAILED" -ForegroundColor Red
                Write-Host $output -ForegroundColor Yellow
                $script:failedTests++
                return $false
            }
        }
    }
    catch {
        Write-Host "✗ FAILED" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Yellow
        $script:failedTests++
        return $false
    }
}

# Test base charts
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Phase 1: Linting Base Charts" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($service in $services) {
    Test-HelmChart -Service $service -Environment "base"
}

Write-Host ""

# Test environment-specific values
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Phase 2: Linting with Environment Values" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($service in $services) {
    foreach ($env in $environments) {
        $valuesFile = "values-$env.yaml"
        if (Test-Path "helm\$service\$valuesFile") {
            Test-HelmChart -Service $service -ValuesFile $valuesFile -Environment $env
        } else {
            Write-Host "⊘ Skipping $service ($env) - values file not found" -ForegroundColor DarkYellow
        }
    }
}

Write-Host ""

# Summary
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests"
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor Red
Write-Host "=========================================" -ForegroundColor Cyan

if ($failedTests -eq 0) {
    Write-Host "All tests passed! ✓" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed. Please review the errors above." -ForegroundColor Red
    exit 1
}

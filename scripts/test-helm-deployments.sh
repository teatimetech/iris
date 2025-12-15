#!/bin/bash

# Test Helm Chart Deployments
# This script validates all Helm charts and their environment-specific values

set -e

echo "========================================="
echo "  IRIS Helm Chart Validation"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm not found. Please install Helm 3.x first.${NC}"
    exit 1
fi

HELM_VERSION=$(helm version --short | cut -d: -f2 | cut -d. -f1 | tr -d 'v ')
if [ "$HELM_VERSION" -lt 3 ]; then
    echo -e "${RED}Error: Helm 3.x or higher is required.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Helm $(helm version --short) found${NC}"
echo ""

# Services to test
SERVICES=("iris-api-gateway" "iris-agent-router" "iris-web-ui" "postgresql" "ollama")
ENVIRONMENTS=("dev" "qa" "stage" "prod")

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run helm lint
lint_chart() {
    local service=$1
    local values_file=$2
    local env=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Linting $service ($env)... "
    
    if [ -n "$values_file" ] && [ -f "helm/$service/$values_file" ]; then
        if helm lint "helm/$service" -f "helm/$service/$values_file" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PASSED${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            helm lint "helm/$service" -f "helm/$service/$values_file"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    else
        if helm lint "helm/$service" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PASSED${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            helm lint "helm/$service"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    fi
}

# Function to test template rendering
test_template() {
    local service=$1
    local values_file=$2
    local env=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Template rendering $service ($env)... "
    
    if [ -n "$values_file" ] && [ -f "helm/$service/$values_file" ]; then
        if helm template "test-$service" "helm/$service" -f "helm/$service/$values_file" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PASSED${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            helm template "test-$service" "helm/$service" -f "helm/$service/$values_file"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    else
        if helm template "test-$service" "helm/$service" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PASSED${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            helm template "test-$service" "helm/$service"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    fi
}

# Test base charts
echo "========================================="
echo "Phase 1: Linting Base Charts"
echo "========================================="
echo ""

for service in "${SERVICES[@]}"; do
    lint_chart "$service" "" "base"
done

echo ""

# Test environment-specific values
echo "========================================="
echo "Phase 2: Linting with Environment Values"
echo "========================================="
echo ""

for service in "${SERVICES[@]}"; do
    for env in "${ENVIRONMENTS[@]}"; do
        values_file="values-$env.yaml"
        if [ -f "helm/$service/$values_file" ]; then
            lint_chart "$service" "$values_file" "$env"
        else
            echo -e "${YELLOW}⊘ Skipping $service ($env) - values file not found${NC}"
        fi
    done
done

echo ""

# Test template rendering
echo "========================================="
echo "Phase 3: Template Rendering Tests"
echo "========================================="
echo ""

for service in "${SERVICES[@]}"; do
    test_template "$service" "" "base"
    
    for env in "${ENVIRONMENTS[@]}"; do
        values_file="values-$env.yaml"
        if [ -f "helm/$service/$values_file" ]; then
            test_template "$service" "$values_file" "$env"
        fi
    done
done

echo ""

# Validate Argo CD applications
echo "========================================="
echo "Phase 4: Argo CD Application Validation"
echo "========================================="
echo ""

if command -v kubectl &> /dev/null; then
    echo "Validating Argo CD application manifests..."
    
    for app_file in gitops/applications/*.yaml; do
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        app_name=$(basename "$app_file")
        echo -n "Validating $app_name... "
        
        if kubectl apply --dry-run=client -f "$app_file" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PASSED${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗ FAILED${NC}"
            kubectl apply --dry-run=client -f "$app_file"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    done
else
    echo -e "${YELLOW}⊘ kubectl not found, skipping Argo CD validation${NC}"
fi

echo ""

# Summary
echo "========================================="
echo "  Test Summary"
echo "========================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo "========================================="

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the errors above.${NC}"
    exit 1
fi

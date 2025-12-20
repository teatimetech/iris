#!/usr/bin/env bash
set -e

echo "======================================"
echo "IRIS CI/CD Validation Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
ERRORS=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((SUCCESS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((ERRORS++))
    fi
}

echo "Checking prerequisites..."
echo ""

# Check Docker
docker --version > /dev/null 2>&1
check "Docker installed"

# Check kubectl
kubectl version --client > /dev/null 2>&1
check "kubectl installed"

# Check Helm
helm version > /dev/null 2>&1
check "Helm installed"

echo ""
echo "Validating Helm charts..."
echo ""

# Lint all Helm charts
for chart in helm/*; do
    if [ -d "$chart" ] && [ -f "$chart/Chart.yaml" ]; then
        chart_name=$(basename "$chart")
        helm lint "$chart" > /dev/null 2>&1
        check "Helm chart: $chart_name"
    fi
done

echo ""
echo "Validating GitHub Actions workflows..."
echo ""

# Check workflow files exist
for workflow in .github/workflows/*.yml; do
    if [ -f "$workflow" ]; then
        workflow_name=$(basename "$workflow")
        # Basic YAML syntax check
        python -c "import yaml; yaml.safe_load(open('$workflow'))" > /dev/null 2>&1
        check "Workflow: $workflow_name"
    fi
done

echo ""
echo "Validating GitOps structure..."
echo ""

# Check GitOps directories
[ -d "gitops-example/applications" ]
check "GitOps applications directory"

[ -d "gitops-example/environments/dev" ]
check "GitOps dev environment"

[ -d "gitops-example/environments/prod" ]
check "GitOps prod environment"

echo ""
echo "Testing Helm template rendering..."
echo ""

# Test rendering each chart
helm template iris-api-gateway ./helm/iris-api-gateway \
    -f ./helm/iris-api-gateway/values-dev.yaml > /dev/null 2>&1
check "iris-api-gateway dev template"

helm template iris-agent-router ./helm/iris-agent-router > /dev/null 2>&1
check "iris-agent-router template"

helm template iris-web-ui ./helm/iris-web-ui > /dev/null 2>&1
check "iris-web-ui template"

echo ""
echo "======================================"
echo "Validation Summary"
echo "======================================"
echo -e "${GREEN}Passed:${NC} $SUCCESS"
echo -e "${RED}Failed:${NC} $ERRORS"

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All validations passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Some validations failed. Please fix the issues above.${NC}"
    exit 1
fi

#!/bin/bash

# Deploy Argo CD and IRIS Applications
# This script installs Argo CD on a Kubernetes cluster and deploys all IRIS applications

set -e

echo "========================================="
echo "  Argo CD Deployment for IRIS"
echo "========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl first."
    exit 1
fi

if !kubectl cluster-info &> /dev/null; then
    echo "Error: No Kubernetes cluster found. Please configure kubectl first."
    exit 1
fi

echo "✓ kubectl configured and cluster accessible"
echo ""

# Install Argo CD
echo "Installing Argo CD..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "Waiting for Argo CD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
kubectl wait --for=condition=available --timeout=300s deployment/argocd-repo-server -n argocd
kubectl wait --for=condition=available --timeout=300s deployment/argocd-application-controller -n argocd

echo "✓ Argo CD installed successfully"
echo ""

# Install Argo CD CLI (optional)
echo "Checking for Argo CD CLI..."
if ! command -v argocd &> /dev/null; then
    echo "Argo CD CLI not found. You can install it later for easier management."
    echo "See: https://argo-cd.readthedocs.io/en/stable/cli_installation/"
else
    echo "✓ Argo CD CLI found"
fi
echo ""

# Get Argo CD admin password
echo "Retrieving Argo CD admin credentials..."
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo ""
echo "========================================="
echo "  Argo CD Access Information"
echo "========================================="
echo "URL: https://localhost:8080"
echo "Username: admin"
echo "Password: $ARGOCD_PASSWORD"
echo ""
echo "To access Argo CD UI, run:"
echo "  kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "========================================="
echo ""

# Create IRIS project
echo "Creating IRIS Argo CD project..."
kubectl apply -f gitops/argocd/project.yaml
echo "✓ IRIS project created"
echo ""

# Deploy applications by environment
echo "Deploying IRIS applications..."
echo ""

# Function to deploy applications for an environment
deploy_environment() {
    local env=$1
    echo "Deploying $env environment applications..."
    
    kubectl apply -f gitops/applications/iris-api-gateway-$env.yaml
    kubectl apply -f gitops/applications/iris-agent-router-$env.yaml
    kubectl apply -f gitops/applications/iris-web-ui-$env.yaml
    kubectl apply -f gitops/applications/postgresql-$env.yaml
    kubectl apply -f gitops/applications/ollama-$env.yaml
    
    echo "✓ $env environment applications deployed"
}

# Prompt user for which environments to deploy
echo "Which environments would you like to deploy?"
echo "1) Dev only"
echo "2) Dev + QA"
echo "3) All environments (dev, qa, stage, prod)"
echo "4) Custom selection"
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        deploy_environment "dev"
        ;;
    2)
        deploy_environment "dev"
        deploy_environment "qa"
        ;;
    3)
        deploy_environment "dev"
        deploy_environment "qa"
        deploy_environment "stage"
        deploy_environment "prod"
        ;;
    4)
        for env in dev qa stage prod; do
            read -p "Deploy $env? (y/n): " answer
            if [ "$answer" = "y" ]; then
                deploy_environment "$env"
            fi
        done
        ;;
    *)
        echo "Invalid choice. Deploying dev environment only."
        deploy_environment "dev"
        ;;
esac

echo ""
echo "========================================="
echo "  Deployment Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Access Argo CD UI:"
echo "   kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "   Open https://localhost:8080"
echo ""
echo "2. Check application status:"
echo "   kubectl get applications -n argocd"
echo ""
echo "3. Sync an application (if not auto-synced):"
echo "   kubectl patch application iris-api-gateway-dev -n argocd --type merge -p '{\"spec\":{\"syncPolicy\":{\"automated\":{\"prune\":true,\"selfHeal\":true}}}}'"
echo "   Or use Argo CD UI/CLI"
echo ""
echo "4. Access IRIS services (after sync completes):"
echo "   kubectl get pods -n iris-dev"
echo "   kubectl port-forward -n iris-dev svc/iris-api-gateway 8080:8080"
echo "   kubectl port-forward -n iris-dev svc/iris-web-ui 3000:3000"
echo ""
echo "For more information, see gitops/README.md"
echo "========================================="

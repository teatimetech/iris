# IRIS CI/CD Prerequisites & Installation Guide

## Prerequisites

### Required Software

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| **Docker Desktop** | Latest | Container runtime & local K8s | [Download](https://www.docker.com/products/docker-desktop) |
| **kubectl** | 1.28+ | Kubernetes CLI | Included with Docker Desktop |
| **Helm** | 3.0+ or 4.0+ | Package manager for K8s | `winget install Helm.Helm` |
| **Git** | Latest | Version control | [Download](https://git-scm.com/) |
| **Argo CD CLI** (optional) | Latest | Argo CD management | [Install Guide](https://argo-cd.readthedocs.io/en/stable/cli_installation/) |

### Cluster Requirements

- **Kubernetes cluster** running (Docker Desktop, minikube, kubeadm, or cloud provider)
- **Minimum resources**: 4 CPU cores, 8GB RAM
- **Storage class** configured for persistent volumes
- **Ingress controller** (optional for production)

###  Network Requirements

- Internet access for pulling container images
- Access to GitHub Container Registry (ghcr.io)
- Access to Docker Hub (for base images)

## Installation Steps

### 1. Install Prerequisites

#### Windows (PowerShell)

```powershell
# Install Helm
winget install Helm.Helm

# Restart PowerShell to update PATH

# Verify installations
docker version
kubectl version --client
helm version
git --version
```

#### macOS

```bash
# Install Helm
brew install helm

# Verify installations
docker version
kubectl version --client
helm version
git --version
```

#### Linux

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installations
docker version
kubectl version --client
helm version
git --version
```

### 2. Enable Kubernetes in Docker Desktop

1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Check "Enable Kubernetes"
4. Click "Apply & Restart"
5. Wait for Kubernetes to start

**Verify:**
```bash
kubectl cluster-info
kubectl get nodes
```

Expected output:
```
NAME             STATUS   ROLES           AGE     VERSION
docker-desktop   Ready    control-plane   X days  v1.34.1
```

### 3. Install Argo CD

```bash
# Create Argo CD namespace
kubectl create namespace argocd

# Install Argo CD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for Argo CD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Verify installation
kubectl get pods -n argocd
```

All pods should be in `Running` status.

### 4. Access Argo CD UI

#### Get Admin Password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**Windows PowerShell:**
```powershell
$password = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($password))
```

#### Port Forward to Argo CD

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

#### Access UI

1. Open browser to: `https://localhost:8080`
2. Accept security warning (self-signed cert)
3. Login with:
   - Username: `admin`
   - Password: (from above command)

### 5. Install Argo CD CLI (Optional)

#### Windows

```powershell
# Download latest release
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-cd/releases/latest).tag_name
$url = "https://github.com/argoproj/argo-cd/releases/download/$version/argocd-windows-amd64.exe"
Invoke-WebRequest -Uri $url -OutFile "$env:USERPROFILE\bin\argocd.exe"

# Add to PATH or move to existing PATH location
```

#### macOS

```bash
brew install argocd
```

#### Linux

```bash
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd
```

#### Login via CLI

```bash
# Port forward must be running
argocd login localhost:8080 --insecure --username admin --password <password-from-above>
```

## Deploy IRIS to Kubernetes

### Option 1: GitOps with Argo CD (Recommended)

1. **Create IRIS project:**
   ```bash
   kubectl apply -f gitops-example/argocd/project.yaml
   ```

2. **Deploy services to dev environment:**
   ```bash
   kubectl create namespace iris-dev
   kubectl apply -f gitops-example/applications/postgresql-dev.yaml
   kubectl apply -f gitops-example/applications/iris-agent-router-dev.yaml
   kubectl apply -f gitops-example/applications/iris-api-gateway-dev.yaml
   kubectl apply -f gitops-example/applications/iris-web-ui-dev.yaml
   ```

3. **Monitor deployment in Argo CD UI:**
   - Applications will auto-sync and deploy
   - View sync status, health, and logs

4. **Verify deployments:**
   ```bash
   kubectl get pods -n iris-dev
   kubectl get all -n iris-dev
   ```

### Option 2: Direct Helm Install

```bash
# Create namespace
kubectl create namespace iris-dev

# Install PostgreSQL first (dependency)
helm install postgresql ./helm/postgresql \
  -f ./helm/postgresql/values-dev.yaml \
  -n iris-dev

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n iris-dev --timeout=180s

# Install Agent Router
helm install iris-agent-router ./helm/iris-agent-router \
  -f ./helm/iris-agent-router/values-dev.yaml \
  -n iris-dev

# Install API Gateway
helm install iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-dev.yaml \
  -n iris-dev

# Install Web UI
helm install iris-web-ui ./helm/iris-web-ui \
  -f ./helm/iris-web-ui/values-dev.yaml \
  -n iris-dev

# Verify
helm list -n iris-dev
kubectl get pods -n iris-dev
```

## Accessing IRIS Services

### Port Forward to Services

```bash
# API Gateway
kubectl port-forward svc/iris-api-gateway -n iris-dev 8080:8080

# Web UI (if not using Ingress)
kubectl port-forward svc/iris-web-ui -n iris-dev 3000:3000

# PostgreSQL (for debugging)
kubectl port-forward svc/postgresql -n iris-dev 5432:5432
```

### Using Ingress (Production)

Ensure you have an Ingress controller installed:

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.0/deploy/static/provider/cloud/deploy.yaml
```

Then access via configured domain (from values-*.yaml).

## Common Operations

### Update Application

#### Via Argo CD
```bash
# Trigger sync
kubectl -n argocd patch app iris-api-gateway-dev -p '{"operation":{"sync":{}}}' --type merge

# Or via CLI
argocd app sync iris-api-gateway-dev
```

#### Via Helm
```bash
helm upgrade iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-dev.yaml \
  --set image.tag=v1.2.3 \
  -n iris-dev
```

### View Logs

```bash
# All pods in namespace
kubectl logs -n iris-dev -l app=iris-api-gateway --tail=100 -f

# Specific pod
kubectl logs -n iris-dev <pod-name> -f

# Via Argo CD
argocd app logs iris-api-gateway-dev
```

### Rollback

```bash
# Via Helm
helm rollback iris-api-gateway -n iris-dev

# Via Argo CD (use UI or CLI to select previous revision)
argocd app rollback iris-api-gateway-dev <revision-number>
```

### Scale Service

```bash
# Manual scaling
kubectl scale deployment iris-api-gateway --replicas=5 -n iris-dev

# HPA will auto-scale if enabled in values
kubectl get hpa -n iris-dev
```

## Troubleshooting

### Helm Not Found After Installation

**Issue:** `helm: command not found` or similar

**Solution:** Restart your terminal/PowerShell to reload PATH

```powershell
# Or use full path temporarily (Windows)
& "C:\Program Files\Helm\helm.exe" version

# macOS/Linux
export PATH=$PATH:/usr/local/bin
```

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n iris-dev

# View pod events
kubectl describe pod <pod-name> -n iris-dev

# View logs
kubectl logs <pod-name> -n iris-dev
```

### Argo CD Application Not Syncing

```bash
# Check application status
kubectl describe application iris-api-gateway-dev -n argocd

# View sync status
argocd app get iris-api-gateway-dev

# Force sync
argocd app sync iris-api-gateway-dev --force
```

### Image Pull Errors

**Issue:** `ImagePullBackOff` or `ErrImagePull`

**Solution:**
1. Verify image repository in values files
2. Ensure container registry authentication is configured
3. Check image exists:
   ```bash
   docker pull ghcr.io/your-org/iris-api-gateway:latest
   ```

### Storage Issues

**Issue:** PVC pending or pod can't mount volume

**Solution:**
```bash
# Check PVCs
kubectl get pvc -n iris-dev

# Check storage class
kubectl get storageclass

# Docker Desktop uses 'hostpath' by default
# Ensure it's available
```

### Network Issues

**Issue:** Services can't communicate

**Solution:**
1. Check NetworkPolicy (disable in dev if needed)
2. Verify service names and ports
3. Test connectivity:
   ```bash
   kubectl run test --rm -it --image=busybox -n iris-dev -- sh
   wget -O- http://iris-api-gateway:8080/health
   ```

## Next Steps

1. ✅ Install prerequisites
2. ✅ Deploy Argo CD
3. ✅ Create IRIS project
4. ✅ Deploy to dev environment
5. 🔜 Configure domain names for production
6. 🔜 Set up TLS certificates (cert-manager)
7. 🔜 Configure Vault for secrets management
8. 🔜 Set up monitoring (Prometheus/Grafana)
9. 🔜 Configure CI/CD pipeline (GitHub Actions)

## References

- [Docker Desktop Documentation](https://docs.docker.com/desktop/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Argo CD Documentation](https://argo-cd.readthedocs.io/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

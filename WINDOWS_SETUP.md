# Quick Start Guide for Windows Users

## Prerequisites Check
✅ Docker Desktop is running  
✅ Kubernetes is **enabled** in Docker Desktop (Settings > Kubernetes > Enable Kubernetes)

## Verify Kubernetes Connection
```powershell
kubectl cluster-info
```
Should show: `Kubernetes control plane is running at https://kubernetes.docker.internal:6443`

## Build Only (Recommended for Windows)
Since full K8s orchestration requires additional setup on Windows, start with just building the Docker images:

```powershell
# Clean previous builds
make clean-all

# Build both services
make build
```

This will create:
- `127.0.0.1:5000/iris-api-gateway:latest`
- `127.0.0.1:5000/iris-agent-router:latest`

## Deploy to Docker Desktop Kubernetes

If you want to deploy to Kubernetes:

```powershell
# Run full deployment (will skip k3d, use Docker Desktop K8s)
make all
```

**Note:** On Windows this will:
- ✅ Build Docker images
- ✅ Create Kubernetes namespace and resources
- ⚠️ Skip k3d cluster creation (uses Docker Desktop K8s instead)
- ⚠️ Skip Ollama deployment (too resource-intensive, can deploy manually)

## Manual Steps for Windows

### 1. Enable Kubernetes in Docker Desktop
- Open Docker Desktop
- Go to Settings (gear icon)
- Click "Kubernetes" tab
- Check "Enable Kubernetes"
- Click "Apply & Restart"
- Wait for Kubernetes to start (green indicator)

### 2. Verify Setup
```powershell
kubectl get nodes
# Should show docker-desktop node as Ready
```

### 3. Deploy Services
```powershell
# Deploy IRIS services
kubectl apply -f infra/k8s/01-namespace.yaml
kubectl apply -f infra/k8s/05-iris-deployments.yaml

# Check deployment status
kubectl get pods -n iris
```

### 4. Access the API
```powershell
# Port forward the gateway
kubectl port-forward svc/iris-api-gateway 8080:8080 -n iris

# Test in another terminal
curl -X POST http://localhost:8080/v1/chat -H "Content-Type: application/json" -d "{\"user_id\": \"test\", \"prompt\": \"Hello\"}"
```

## Troubleshooting Windows Issues

### "kubectl not configured"
**Fix:** Enable Kubernetes in Docker Desktop settings

### "No connection could be made"  
**Fix:** Ensure Docker Desktop is running and Kubernetes is started (green status)

### "context deadline exceeded"
**Fix:** Kubernetes might still be starting. Wait 1-2 minutes and try again

### Registry Issues
If the local registry fails to start on port 5000:
```powershell
# Check if port is in use
netstat -ano | findstr :5000

# Remove existing registry
docker rm -f iris-local-registry

# Restart
make docker-registry-run
```

## Quick Test (No Kubernetes)

To test the services without Kubernetes:

```powershell
# Run Go Gateway
docker run -d -p 8080:8080 --name test-gateway `
  -e AGENT_SERVICE_URL=http://host.docker.internal:8000 `
  iris-api-gateway:test

# Run Python Agent (will fail without Ollama, but container starts)
docker run -d -p 8000:8000 --name test-agent `
  -e OLLAMA_BASE_URL=http://localhost:11434 `
  iris-agent-router:test

# Check logs
docker logs test-gateway
docker logs test-agent

# Cleanup
docker rm -f test-gateway test-agent
```

# DevOps & CI/CD Guide - IRIS Project

## Overview

IRIS uses an enterprise-grade GitOps-based CI/CD pipeline with:
- **GitHub Actions** for Continuous Integration
- **Argo CD** for Continuous Delivery (GitOps)
- **Helm** for declarative Kubernetes deployments
- **HashiCorp Vault** for secrets management
- **Multi-environment** K8s clusters (Ephemeral → Dev → QA → Stage → Prod)

## Architecture

```
Developer → GitHub → CI (Actions) → GHCR → GitOps Repo → Argo CD →  K8s Clusters
                                                              ├─ Ephemeral (PR)
                                                              ├─ Dev (auto)
                                                              ├─ QA (auto)
                                                              ├─ Stage (manual)
                                                              └─ Prod (approval)
```

## Prerequisites

> [!IMPORTANT]
> For detailed installation instructions, see [INSTALLATION_GUIDE.md](file:///C:/ai_IRIS/IRIS/INSTALLATION_GUIDE.md)

**Required:** Docker Desktop, kubectl, Helm 3+, Git  
**Optional:** Argo CD CLI

**Quick Install (Windows):**
```powershell
winget install Helm.Helm
# Restart PowerShell
```

**Quick Install (macOS):**
```bash
brew install helm
```

## Quick Start

### 1. Local Development

```bash
# Use DevContainer (recommended)
code .
# VS Code will prompt to reopen in container

# Or use Docker Compose
docker-compose up -d
```

### 2. CI/CD Pipeline

#### Push Code → PR
```bash
git checkout -b feature/my-feature
git add .
git commit -m "Add feature"
git push origin feature/my-feature
# Create PR on GitHub
```

**What Happens:**
1. `.github/workflows/pr-checks.yml` runs:
   - Lint & format checks
   - Unit tests
   - SAST (CodeQL)
   - Container builds
   - Security scans (Trivy)
   - SBOM generation
   - Integration tests

#### Merge to Main
```bash
# After PR approval and merge
```

**What Happens:**
1. `.github/workflows/build-main.yml` runs:
   - Builds containers
   - Pushes to GHCR with tags: `gitsha`, `latest`
   - Signs images (Cosign)
   - Generates SBOM
   - Updates GitOps repo (dev environment)

2. Argo CD detects GitOps change:
   - Auto-syncs to **dev** environment
   - Creates PR for **staging** promotion

#### Release
```bash
git tag v1.2.3
git push origin v1.2.3
```

**What Happens:**
- Creates GitHub release
- Tags images with semver

## GitHub Actions Workflows

### PR Validation (`.github/workflows/pr-checks.yml`)
**Triggers:** PR opened, updated
**Jobs:**
- `lint`: Go, Python, TypeScript
- `test`: Unit tests with coverage
- `sast`: CodeQL analysis
- `dependency-scan`: Snyk
- `build`: Container builds (3 services)
- `container-scan`: Trivy + SBOM
- `integration-test`: Docker Compose tests

### Main Branch Build (`.github/workflows/build-main.yml`)
**Triggers:** Push to main
**Jobs:**
- `build-and-push`: Build, scan, sign, push to GHCR
- `update-gitops`: Update dev environment, create staging PR

### Release (`.github/workflows/release.yml`)
**Triggers:** Version tags (`v*.*.*`)
**Jobs:**
- Create GitHub release
- Tag images with semver

## Helm Charts

IRIS includes production-ready Helm charts for all microservices:

### Available Charts

| Chart | Description | Templates |
|-------|-------------|----------|
| **iris-api-gateway** | Go-based API gateway | Deployment, Service, HPA, NetworkPolicy, ExternalSecret, ServiceMonitor |
| **iris-agent-router** | Python AI agent orchestrator | Deployment, Service, HPA, NetworkPolicy, PVC, ServiceAccount |
| **iris-web-ui** | Next.js frontend | Deployment, Service, HPA, Ingress, ConfigMap, ServiceAccount |
| **postgresql** | PostgreSQL database | StatefulSet, Service (Headless + Standard), PVC, Secret/ExternalSecret |
| **ollama** | LLM inference engine | Deployment, Service, PVC |
| **redis** | Cache & session store | (Use Bitnami Helm chart) |
| **minio** | Object storage | (Use MinIO Helm chart) |

### Chart Structure

```
helm/iris-api-gateway/
├── Chart.yaml               # Chart metadata
├── values.yaml              # Base values
├── values-dev.yaml          # Development overrides
├── values-qa.yaml           # QA overrides
├── values-stage.yaml        # Staging overrides
├── values-prod.yaml         # Production overrides
└── templates/
    ├── deployment.yaml      # Deployment spec
    ├── service.yaml         # Service definition
    ├── serviceaccount.yaml  # Service account
    ├── externalsecret.yaml  # Vault secret integration
    ├── hpa.yaml             # Auto-scaling policy
    ├── networkpolicy.yaml   # Network security
    ├── servicemonitor.yaml  # Prometheus metrics
    └── _helpers.tpl         # Template helpers
```

### Deploy with Helm

#### Development Environment
```bash
# Create namespace
kubectl create namespace iris-dev

# Install all services
helm install postgresql ./helm/postgresql -f ./helm/postgresql/values-dev.yaml -n iris-dev
helm install iris-agent-router ./helm/iris-agent-router -f ./helm/iris-agent-router/values-dev.yaml -n iris-dev
helm install iris-api-gateway ./helm/iris-api-gateway -f ./helm/iris-api-gateway/values-dev.yaml -n iris-dev
helm install iris-web-ui ./helm/iris-web-ui -f ./helm/iris-web-ui/values-dev.yaml -n iris-dev
```

#### Production (GitOps Preferred)
```bash
# Direct Helm install (not recommended for prod)
helm upgrade --install iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-prod.yaml \
  --set image.tag=v1.2.3 \
  -n iris-prod

# Better: Use Argo CD (see GitOps section below)
```

### Testing Charts Locally

```bash
# Lint chart
helm lint helm/iris-api-gateway

# Dry-run install
helm install iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-dev.yaml \
  --dry-run --debug

# Template rendering (view generated YAML)
helm template iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-dev.yaml > output.yaml
```

## Multi-Environment Strategy

| Environment | Purpose | Deploy | Lifespan |
|-------------|---------|--------|----------|
| Ephemeral | PR testing | Auto | PR lifecycle |
| Dev | Integration | Auto | Permanent |
| QA | QA validation | Auto | Permanent |
| Stage | Pre-prod | Manual | Permanent |
| Prod | Production | Approval | Permanent |

## Secrets Management

### With Vault + External Secrets Operator

1. **Store secret in Vault:**
```bash
vault kv put iris/dev/DB_CONFIG \
  host=postgres.iris-dev.svc.cluster.local \
  port=5432 \
  user=iris_user \
  password=secure_password \
  dbname=iris_db
```

2. **ExternalSecret syncs to K8s:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: iris-api-gateway-db-secret
spec:
  secretStoreRef:
    name: vault-backend
  data:
  - secretKey: DB_PASSWORD
    remoteRef:
      key: iris/dev/DB_CONFIG
      property: password
```

3. **Pod uses secret:**
```yaml
envFrom:
- secretRef:
    name: iris-api-gateway-db-secret
```

## Security Features

### CI Pipeline
- ✅ SAST (CodeQL)
- ✅ Dependency scanning (Snyk)
- ✅ Container scanning (Trivy)
- ✅ SBOM generation
- ✅ Image signing (Cosign)

### Kubernetes
- ✅ Pod Security Standards (restricted)
- ✅ Network Policies (zero-trust)
- ✅ RBAC (least privilege)
- ✅ Non-root containers
- ✅ Read-only root filesystem
- ✅ Dropped capabilities

## Observability

### Metrics (Prometheus)
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open http://localhost:9090
```

### Dashboards (Grafana)
```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
# Open http://localhost:3000
```

### Logs (Loki)
```bash
kubectl logs -n iris-dev deployment/iris-api-gateway -f
```

## Troubleshooting

### CI Pipeline Fails
1. Check GitHub Actions tab
2. Review failed job logs
3. Fix issues locally
4. Push changes

### Deployment Fails
1. Check Argo CD UI
2. View sync status and events
3. Check pod logs:
```bash
kubectl logs -n iris-dev deployment/iris-api-gateway
```

### Secrets Not Loading
1. Verify Vault path
2. Check ExternalSecret status:
```bash
kubectl get externalsecret -n iris-dev
kubectl describe externalsecret iris-api-gateway-db-secret -n iris-dev
```

## Common Operations

### Rollback
```bash
# Via Helm
helm rollback iris-api-gateway -n iris-dev

# Via Argo CD
argocd app rollback iris-api-gateway-dev
```

### Scale Service
```bash
kubectl scale deployment iris-api-gateway --replicas=5 -n iris-dev
```

### View Logs
```bash
kubectl logs -n iris-dev -l app=iris-api-gateway --tail=100 -f
```

## Argo CD GitOps Deployment

### GitOps Repository Structure

IRIS now has a production-ready GitOps structure in `gitops/`:

```
gitops/
├── README.md                          # GitOps usage guide
├── argocd/
│   └── project.yaml                   # Argo CD project with RBAC
├── applications/                      # 20 Application manifests
│   ├── iris-api-gateway-{env}.yaml    # 4 environments each
│   ├── iris-agent-router-{env}.yaml
│   ├── iris-web-ui-{env}.yaml
│   ├── postgresql-{env}.yaml
│   └── ollama-{env}.yaml
└── environments/                      # Environment-specific values
    ├── dev/
    ├── qa/
    ├── stage/
    └── prod/
```

### Quick Deployment

**Using Makefile (Recommended)**:

```bash
# Deploy Argo CD and all IRIS applications
make deploy-argocd

# Or validate Helm charts first
make helm-test
make deploy-argocd
```

**Direct Python Script**:

The deployment uses a cross-platform Python script that works on **Windows**, **macOS**, and **Linux**:

```bash
# Run directly
python scripts/deploy-argocd.py

# Follow the interactive prompts to select environments
```

**Prerequisites**:
- Python 3.6+ (comes with macOS/Linux, install on Windows)
- kubectl configured to access your cluster
- Helm 3.x (optional, for validation)

### Manual Deployment

```bash
# Install Argo CD (if not already installed)
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Create IRIS project
kubectl apply -f gitops/argocd/project.yaml

# Deploy all dev applications
kubectl apply -f gitops/applications/iris-api-gateway-dev.yaml
kubectl apply -f gitops/applications/iris-agent-router-dev.yaml
kubectl apply -f gitops/applications/iris-web-ui-dev.yaml
kubectl apply -f gitops/applications/postgresql-dev.yaml
kubectl apply -f gitops/applications/ollama-dev.yaml

# Access Argo CD UI
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080 (username: admin)
```

### Environment Promotion

- **Dev & QA**: Auto-sync enabled (changes deploy automatically)
- **Stage & Prod**: Manual sync required (approval workflow)

See [gitops/README.md](file:///c:/ai_IRIS/IRIS/gitops/README.md) for complete GitOps documentation.

## Next Steps

1. ✅ GitHub Actions workflows created
2. ✅ Helm charts complete (iris-api-gateway, iris-agent-router, iris-web-ui, postgresql)
3. ✅ Environment-specific values (dev, qa, stage, prod)
4. ✅ Argo CD project and applications configured
5. ⏭️  Install Argo CD on your cluster
6. ⏭️  Deploy applications via Argo CD
7. ⏭️  Configure Vault + External Secrets (optional)
8. ⏭️  Deploy observability stack (Prometheus/Grafana)

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Argo CD Documentation](https://argo-cd.readthedocs.io/)
- [Helm Documentation](https://helm.sh/docs/)
- [External Secrets Operator](https://external-secrets.io/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

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

### Local Development
- Docker Desktop
- kubectl
- Helm 3
- Git

### Cloud/GitHub Setup
- GitHub repository
- GitHub Container Registry (GHCR) access
- Kubernetes clusters (dev, qa, stage, prod)
- Vault instance (or cloud-managed secrets)

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

Each microservice has a comprehensive Helm chart:

```
helm/iris-api-gateway/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-qa.yaml
├── values-stage.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── serviceaccount.yaml
    ├── externalsecret.yaml
    ├── hpa.yaml
    ├── networkpolicy.yaml
    ├── servicemonitor.yaml
    └── _helpers.tpl
```

### Deploy with Helm

```bash
# Dev environment
helm upgrade --install iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-dev.yaml \
  -n iris-dev

# Production (via GitOps preferred)
helm upgrade --install iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-prod.yaml \
  -n iris-prod
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

## Next Steps

1. ✅ GitHub Actions workflows created
2. ✅ Helm chart for iris-api-gateway complete
3. 🚧 Create remaining Helm charts (agent-router, web-ui)
4. 🚧 Set up GitOps repository
5. 🚧 Install Argo CD
6. 🚧 Configure Vault + External Secrets
7. 🚧 Deploy observability stack

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Argo CD Documentation](https://argo-cd.readthedocs.io/)
- [Helm Documentation](https://helm.sh/docs/)
- [External Secrets Operator](https://external-secrets.io/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

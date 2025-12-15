# IRIS CI/CD Configuration Guide

## Table of Contents
1. [GitHub Secrets Configuration](#github-secrets)
2. [Helm Values Customization](#helm-values)
3. [Argo CD Setup](#argocd-setup)
4. [Vault Configuration](#vault-configuration)
5. [Environment Variables](#environment-variables)

## GitHub Secrets Configuration

### Required Secrets

Configure these in GitHub repository settings (`Settings` → `Secrets and variables` → `Actions`):

```bash
# Container Registry
GITHUB_TOKEN  # Automatically provided by GitHub

# GitOps Repository Access
GITOPS_PAT    # Personal Access Token with repo write permissions

# Snyk Security Scanning (optional)
SNYK_TOKEN    # From snyk.io account

# Additional secrets per environment
```

### Creating GITOPS_PAT

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full control)
4. Copy token and add to repository secrets as `GITOPS_PAT`

## Helm Values Customization

### Quick Start

Each service has environment-specific values files:

```bash
helm/iris-api-gateway/
├── values.yaml           # Base/default values
├── values-dev.yaml       # Dev overrides
├── values-qa.yaml        # QA overrides
├── values-stage.yaml     # Staging overrides
└── values-prod.yaml      # Production overrides
```

### Service-Specific Customization

#### iris-api-gateway

**Key Configuration Options:**

```yaml
image:
  repository: ghcr.io/your-org/iris-api-gateway
  tag: "v1.2.3"

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

env:
  - name: AGENT_SERVICE_URL
    value: "http://iris-agent-router:8000"
  - name: ALLOW_ORIGIN
    value: "https://iris.your-domain.com"

externalSecrets:
  enabled: true  # Use Vault for DB credentials
  secretStore: vault-backend
```

#### iris-agent-router

**Key Configuration Options:**

```yaml
resources:
  limits:
    cpu: 1000m
    memory: 2Gi

persistence:
  enabled: true
  storageClass: "fast-ssd"
  size: 10Gi
  mountPath: /data/db

env:
  - name: OLLAMA_BASE_URL
    value: "http://ollama:11434"
  - name: OLLAMA_MODEL
    value: "qwen2.5:7b"
  - name: LANCE_DB_PATH
    value: "/data/db/lancedb"
```

#### iris-web-ui

**Key Configuration Options:**

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: iris.your-domain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: iris-web-ui-tls
      hosts:
        - iris.your-domain.com

env:
  - name: NEXT_PUBLIC_API_URL
    value: "http://iris-api-gateway:8080"
  - name: NODE_ENV
    value: "production"
```

#### PostgreSQL

**Key Configuration Options:**

```yaml
auth:
  username: iris_user
  password: "CHANGEME"  # Or use externalSecrets
  database: iris_db

persistence:
  enabled: true
  storageClass: "fast-ssd"
  size: 100Gi  # Adjust based on data volume

resources:
  limits:
    cpu: 2000m
    memory: 4Gi

externalSecrets:
  enabled: true  # Recommended for production
  secretStore: vault-backend
  remoteRefKey: iris/prod/DB_CONFIG
```

### Environment Comparison

| Setting | Dev | QA | Stage | Prod |
|---------|-----|----|----|------|
| Replicas | 1 | 2 | 2-3 | 3-5 |
| Auto-scaling | Disabled | Enabled | Enabled | Enabled |
| Resource limits | Low | Medium | High | High |
| Ingress/TLS | Disabled | Enabled | Enabled (staging cert) | Enabled (prod cert) |
| External Secrets | Disabled | Optional | Enabled | Enabled |
| NetworkPolicy | Disabled | Enabled | Enabled | Enabled |

## Argo CD Setup

### Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### Access Argo CD UI

```bash
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Port forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Access: https://localhost:8080
# Username: admin
# Password: (from command above)
```

### Create Project

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: iris
  namespace: argocd
spec:
  description: IRIS Financial Advisor Platform
  sourceRepos:
    - 'https://github.com/your-org/IRIS-gitops'
  destinations:
    - namespace: 'iris-*'
      server: https://kubernetes.default.svc
  clusterResourceWhitelist:
    - group: ''
      kind: Namespace
  namespaceResourceWhitelist:
    - group: '*'
      kind: '*'
```

Apply:
```bash
kubectl apply -f gitops-example/argocd/project.yaml
```

### Deploy Applications

```bash
# Deploy all dev environment applications
kubectl apply -f gitops-example/applications/
```

## Vault Configuration

### 1. Install Vault (Development Mode)

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --namespace vault --create-namespace
```

> **⚠️ Production**: Use proper Vault deployment with HA, encryption, and unsealing

### 2. Configure K8s Auth

```bash
# Port forward to Vault
kubectl port-forward -n vault svc/vault 8200:8200

# Set Vault address
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'  # Dev mode token

# Enable K8s auth
vault auth enable kubernetes

# Configure K8s auth
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc"

# Create policy
vault policy write iris-policy - <<EOF
path "iris/*" {
  capabilities = ["read", "list"]
}
EOF

# Create role
vault write auth/kubernetes/role/iris \
  bound_service_account_names=iris-api-gateway \
  bound_service_account_namespaces=iris-dev,iris-qa,iris-stage,iris-prod \
  policies=iris-policy \
  ttl=24h
```

### 3. Store Secrets

```bash
# Database credentials
vault kv put iris/dev/DB_CONFIG \
  host=postgres.iris-dev.svc.cluster.local \
  port=5432 \
  user=iris_user \
  password=CHANGE_ME_DEV \
  dbname=iris_db

# Production (use strong passwords!)
vault kv put iris/prod/DB_CONFIG \
  host=postgres.iris-prod.svc.cluster.local \
  port=5432 \
  user=iris_user \
  password=STRONG_PASSWORD_HERE \
  dbname=iris_db
```

### 4. Install External Secrets Operator

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace
```

### 5. Create SecretStore

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: iris-dev
spec:
  provider:
    vault:
      server: "http://vault.vault:8200"
      path: "iris"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "iris"
          serviceAccountRef:
            name: "iris-api-gateway"
```

## Environment Variables

### API Gateway

| Variable | Description | Example |
|----------|-------------|---------|
| `PORT` | API server port | `8080` |
| `AGENT_SERVICE_URL` | Agent router URL | `http://iris-agent-router:8000` |
| `DB_HOST` | PostgreSQL host | From Vault |
| `DB_PORT` | PostgreSQL port | From Vault |
| `DB_USER` | Database user | From Vault |
| `DB_PASSWORD` | Database password | From Vault |
| `DB_NAME` | Database name | From Vault |

### Agent Router

| Variable | Description | Example |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama API URL | `http://ollama:11434` |
| `OLLAMA_MODEL` | LLM model name | `qwen2.5:7b` |
| `LANCE_DB_PATH` | LanceDB storage  path | `/data/db/lancedb` |

### Web UI

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | API gateway URL | `http://iris-api-gateway:8080` |
| `NODE_ENV` | Node environment | `production` |

## Testing Configuration

### Test Helm Charts

```bash
# Lint chart
helm lint helm/iris-api-gateway

# Dry-run install
helm install iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-dev.yaml \
  --dry-run --debug

# Template rendering
helm template iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-dev.yaml
```

### Test GitOps Workflow

1. Make change in app repo
2. Push to branch, create PR
3. CI runs validation
4. Merge PR
5. CI builds and pushes image
6. CI updates GitOps repo (`environments/dev/`)
7. Argo CD auto-syncs to cluster
8. Verify deployment

### Test Secrets

```bash
# Create test ExternalSecret
kubectl create -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: test-secret
  namespace: iris-dev
spec:
  refreshInterval: 15s
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: test-secret
  data:
  - secretKey: password
    remoteRef:
      key: iris/dev/DB_CONFIG
      property: password
EOF

# Check secret was created
kubectl get secret test-secret -n iris-dev -o yaml

# Verify value
kubectl get secret test-secret -n iris-dev \
  -o jsonpath='{.data.password}' | base64 -d
```

## Troubleshooting

### CI Pipeline Issues

**Problem**: GitHub Actions failing  
**Solution**: Check workflow logs, verify secrets, ensure GHCR push permissions

**Problem**: Image scan fails  
**Solution**: Fix vulnerabilities or add exceptions in Trivy config

### Deployment Issues

**Problem**: Argo CD not syncing  
**Solution**: Check application status, verify GitOps repo access

**Problem**: Pods crash looping  
**Solution**: 
```bash
kubectl logs -n iris-dev deployment/iris-api-gateway
kubectl describe pod -n iris-dev <pod-name>
```

### Secrets Issues

**Problem**: ExternalSecret not syncing  
**Solution**:
```bash
kubectl describe externalsecret -n iris-dev <name>
kubectl logs -n external-secrets-system deployment/external-secrets
```

**Problem**: Vault authentication failing  
**Solution**: Verify ServiceAccount, role binding, Vault policy

## Next Steps

1. ✅ Configure GitHub secrets
2. ✅ Customize Helm values files for all services
3. ✅ Install Argo CD
4. ✅ Create IRIS project in Argo CD
5. ✅ Deploy to dev environment
6. ⏭️ Set up Vault (optional for enhanced security)
7. ⏭️ Test end-to-end workflow
8. ⏭️ Promote to QA/Stage/Prod

## Quick Reference Commands

### Helm

```bash
# List installed releases
helm list -n iris-dev

# Get values
helm get values iris-api-gateway -n iris-dev

# Upgrade release
helm upgrade iris-api-gateway ./helm/iris-api-gateway \
  -f ./helm/iris-api-gateway/values-dev.yaml \
  --set image.tag=v1.2.4 \
  -n iris-dev

# Rollback
helm rollback iris-api-gateway -n iris-dev

# Uninstall
helm uninstall iris-api-gateway -n iris-dev
```

### Argo CD

```bash
# Sync application
kubectl -n argocd patch app iris-api-gateway-dev -p '{"operation":{"sync":{}}}' --type merge

# Or use Argo CD CLI
argocd app sync iris-api-gateway-dev

# Get app status
argocd app get iris-api-gateway-dev

# View application logs
argocd app logs iris-api-gateway-dev
```

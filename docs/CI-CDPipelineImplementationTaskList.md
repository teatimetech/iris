# CI/CD Pipeline Implementation Task List

## Phase 1: Requirements & Planning
- [ ] Review DevOps best practices document (waiting for readable format)
- [/] Analyze current IRIS project structure
- [ ] Design CI/CD architecture
- [ ] Create implementation plan document

## Phase 2: GitHub Actions CI Pipeline
- [ ] Create directory structure for workflows (`.github/workflows/`)
- [ ] Implement PR validation workflow (lint, test, security scan)
- [ ] Implement build workflow for containers
- [ ] Set up container registry authentication
- [ ] Configure automated testing pipeline
- [ ] Add quality gates (code coverage, security scans)

## Phase 3: Helm Charts & Kustomize
- [x] Create Helm charts for each microservice
  - [x] iris-api-gateway (comprehensive with all templates)
  - [x] iris-agent-router (deployment, service, HPA, NetworkPolicy, PVC)
  - [x] iris-web-ui (complete with Ingress and ConfigMap)
  - [x] PostgreSQL (StatefulSet with ExternalSecrets support)
- [x] Define environment-specific values (dev/staging/prod)
- [x] Add ConfigMaps and Secrets templates
- [ ] Create Kustomize overlays as alternative (optional - Helm is primary)

## Phase 4: Argo CD Setup
- [x] Create Argo CD application manifests
  - [x] iris-api-gateway (all 4 environments: dev, qa, stage, prod)
  - [x] iris-agent-router (all 4 environments)
  - [x] iris-web-ui (all 4 environments)
  - [x] postgresql (all 4 environments with prune protection)
  - [x] ollama (all 4 environments)
- [x] Create Argo CD project definition with RBAC
- [x] Configure GitOps repository structure (gitops/ directory)
- [x] Set up auto-sync for dev and qa environments
- [x] Configure manual approval for stage and prod
- [x] Add health checks and sync policies

## Phase 5: Secrets Management (Vault)
- [ ] Design secrets hierarchy
- [ ] Create Vault integration for K8s
- [ ] Migrate hardcoded secrets to Vault
- [ ] Configure external-secrets operator or CSI driver
- [ ] Document secret access patterns

## Phase 6: Artifact Registry
- [ ] Set up container registry (GitHub CR or alternative)
- [ ] Configure LLM model artifact storage
- [ ] Set up dependency caching strategy
- [ ] Implement image signing and scanning

## Phase 7: Multi-Environment K8s Setup
- [ ] Document cluster provisioning (dev/staging/prod)
- [ ] Create namespace isolation strategy
- [ ] Configure RBAC for each environment
- [ ] Set up network policies
- [ ] Configure resource quotas

## Phase 8: Testing & Validation
- [ ] Test CI pipeline with sample PR
- [ ] Validate Argo CD deployments
- [ ] Test secret rotation from Vault
- [ ] Verify multi-environment promotion flow
- [ ] Load test deployed services

## Phase 9: Documentation
- [ ] Create comprehensive DevOps README
- [ ] Document CI/CD pipeline flow
- [ ] Create runbooks for common operations
- [ ] Add architecture diagrams
- [ ] Document disaster recovery procedures

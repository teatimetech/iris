# IRIS GitOps Repository Structure

This directory demonstrates the GitOps repository structure for IRIS. In production, this would be a separate Git repository (IRIS-gitops).

## Structure

```
gitops-example/
├── applications/          # Argo CD Application definitions
├── environments/          # Environment-specific configs
│   ├── dev/
│   ├── qa/
│   ├── stage/
│   └── prod/
└── argocd/               # Argo CD configuration
```

## Creating the GitOps Repository

1. **Create a new repository** (e.g., `IRIS-gitops`)

2. **Copy this structure** to the new repo

3. **Update CI/CD workflows** to point to the new repo

4. **Configure Argo CD** to watch the GitOps repo

## Environment Promotion Flow

```
Dev (auto-sync) → QA (auto-sync) → Stage (manual) → Prod (approval)
```

- **Dev**: Automatically deployed on merge to main
- **QA**: Automatically synced after validation
- **Stage**: Manual kubectl/argocd command required
- **Prod**: Requires approval + manual promotion

## GitOps Best Practices

1. **Never commit to prod directly** - always promote through environments
2. **Use Git commits** as audit trail
3. **Rollback = Git revert**
4. **Separate app code from config** - this repo contains only K8s manifests
5. **Use sealed-secrets** or External Secrets for sensitive data

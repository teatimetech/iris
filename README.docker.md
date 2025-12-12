# IRIS - Containerized Development Guide

## Prerequisites

**Only Docker is required** - works on Windows, macOS, and Linux.

- [Docker Desktop](https://www.docker.com/products/docker-desktop) (Windows/Mac)
- Docker Engine (Linux)

Verify Docker is running:
```bash
docker --version
docker-compose --version
```

## Quick Start (works on all operating systems)

```bash
# Clone the repository
git clone <repo-url>
cd IRIS

# Option 1: Using new containerized Makefile
cp Makefile.docker Makefile
make all

# Option 2: Using Docker Compose directly
docker-compose up -d
```

That's it! No Go, Python, kubectl, or other tools needed locally.

## Development Workflow

### Build Services
```bash
make build           # Build both services
make build-go        # Build Go gateway only
make build-python    # Build Python agent only
```

### Run Tests
```bash
make test            # Run all tests
make test-unit       # Unit tests only
make test-integration # Integration tests only
```

### Start Services Locally
```bash
make up              # Start gateway + agent
make up-all          # Start all services including Ollama
make logs            # View logs
make down            # Stop services
```

### Access Services
- **API Gateway**: http://localhost:8080
- **Agent Router**: http://localhost:8000
- **Ollama** (if started): http://localhost:11434

### Test the API
```bash
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "prompt": "Should I invest in NVIDIA?"}'
```

## CI/CD Pipeline

The GitHub Actions workflow automatically:
1. ✅ Builds Docker images
2. ✅ Runs unit tests in containers
3. ✅ Runs integration tests
4. ✅ Scans for security vulnerabilities
5. ✅ Pushes images to GitHub Container Registry

**No OS-specific configuration needed** - all CI runs in Docker.

## Troubleshooting

###error: Cannot connect to Docker daemon"
**Fix**: Ensure Docker Desktop is running

### "Port already in use"
**Fix**: Stop conflicting services or change ports in `docker-compose.yml`

### "Container exits immediately"
**Fix**: Check logs with `make logs` or `docker-compose logs <service>`

## Advanced Usage

### Run individual containers
```bash
# Python unit tests
docker-compose run --rm python-tester

# Integration tests
docker-compose run --rm integration-tester

# Get shell in test runner
make shell-test-runner
```

### Custom Docker registry
```bash
# Edit docker-compose.yml to change image names
# Then push to your registry
make push
```

### Debug mode
```bash
# Start services with logs attached
docker-compose up
```

## Differences from Original Makefile

| Operation | Old (OS-specific) | New (Containerized) |
|-----------|-------------------|---------------------|
| **Build** | `go build` locally | `docker-compose build` |
| **Test** | Local Python/Go | All in containers |
| **K8s** | k3d (Mac) / Docker Desktop (Windows) | Docker Compose |
| **CI/CD** | OS-dependent scripts | GitHub Actions with Docker |

## File Structure

```
/IRIS
├── docker-compose.yml          # Service orchestration
├── Makefile.docker             # OS-agnostic commands
├── docker/                     # Build containers
│   ├── go-builder.Dockerfile
│   ├── python-tester.Dockerfile
│   └── test-runner.Dockerfile
├── scripts/                    # Containerized scripts
│   ├── build-all.sh
│   └── integration-test-docker.sh
└── .github/workflows/          # CI/CD pipelines
    └── ci.yml
```

## Migration from Old Makefile

If you were using the old OS-specific Makefile:

```bash
# Backup old Makefile
mv Makefile Makefile.old

# Use new containerized version
cp Makefile.docker Makefile

# Everything now works the same on all OSes
make clean-all
make all
```

No more OS detection, no more PowerShell vs bash issues!

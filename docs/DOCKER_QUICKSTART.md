# IRIS Containerized CI/CD - Quick Reference

## One-Line Setup
```bash
cp Makefile.docker Makefile && make all
```

## Common Commands

### Development
- `make build` - Build all images
- `make test` - Run all tests
- `make up` - Start services
- `make down` - Stop services
- `make logs` - View logs

### Testing
- `make test-unit` - Python tests
- `make test-integration` - API tests
- `make ci` - Full CI pipeline

### Cleanup
- `make clean` - Remove containers/images
- `make clean-all` - Complete cleanup

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                      │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────┐             │
│  │ Go Builder   │  │ Python Tester   │             │
│  │ (Alpine)     │  │ (Debian-slim)   │             │
│  └──────────────┘  └─────────────────┘             │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │        Integration Test Runner                │  │
│  │  (Alpine + kubectl + curl + bash)             │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────┐  ┌─────────────────┐             │
│  │ API Gateway  │  │ Agent Router    │             │
│  │ (Go/Gin)     │  │ (Python/FastAPI)│             │
│  │ Port: 8080   │  │ Port: 8000      │             │
│  └──────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────┘
```

## File Mapping
- `Makefile.docker` → `Makefile` (copy to use)
- `README.docker.md` → Primary docs
- Old `Makefile` → `Makefile.old` (backup)

## Benefits
✅ No Python/Go/kubectl needed locally  
✅ Works on Windows/Mac/Linux identically  
✅ Same containers in CI and dev  
✅ Reproducible builds

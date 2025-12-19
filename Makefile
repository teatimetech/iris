# Makefile for IRIS Project (Containerized CI/CD)
# All operations run in Docker containers for OS independence

# OS Detection and GPU Configuration
# OS Detection and GPU Configuration
ifeq ($(OS),Windows_NT)
    OS_NAME := Windows
else
    OS_NAME := $(shell uname -s)
endif

DOCKER_COMPOSE_FLAGS := -f docker-compose.yml

# Check configuration based on OS
ifeq ($(OS_NAME),Linux)
    SLEEP_CMD := sleep
    ifneq ($(shell which nvidia-smi 2>/dev/null),)
        DOCKER_COMPOSE_FLAGS += -f docker-compose.nvidia.yml
        export PYTORCH_INDEX := https://download.pytorch.org/whl/cu124
        @echo "Detected Linux with NVIDIA GPU - enabling GPU support (CUDA 12.4)"
    endif
else ifeq ($(OS_NAME),Darwin)
    # MacOS
    SLEEP_CMD := sleep
    # macOS leverages Metal (M1/M2/M3) automatically with Ollama
    export PYTORCH_INDEX := https://download.pytorch.org/whl/cpu
    $(info Detected MacOS (Darwin) - GPU support enabled via Metal)
else
    # Windows / MinGW
    # Use Python for sleep to ensuring cross-platform compatibility
    SLEEP_CMD := python -c "import time, sys; time.sleep(float(sys.argv[1]))"
    
    # Robust GPU detection using Python (Cross-platform & checks standard paths)
    NVIDIA_SMI := $(shell python -c "import shutil, os; path = shutil.which('nvidia-smi'); print(path or (r'C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe' if os.path.exists(r'C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe') else ''))")
    
    ifneq ($(NVIDIA_SMI),)
        DOCKER_COMPOSE_FLAGS += -f docker-compose.nvidia.yml
        export PYTORCH_INDEX := https://download.pytorch.org/whl/cu124
        $(info Windows detected with NVIDIA GPU - enabling GPU support (CUDA 12.4))
    else
        $(info Windows detected - NO GPU FOUND or nvidia-smi missing (skipping GPU config))
        export PYTORCH_INDEX := https://download.pytorch.org/whl/cpu
    endif
endif

.PHONY: all build test clean help up down logs infra deploy-argocd helm-test helm-lint

# --- HELP ---
help:
	@echo "IRIS Containerized Build System"
	@echo "================================"
	@echo ""
	@echo "All commands run in Docker containers - works on Windows/Mac/Linux"
	@echo ""
	@echo "Development Commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make test           - Run all tests in containers"
	@echo "  make test-unit      - Run Python unit tests"
	@echo "  make test-integration - Run API integration tests"
	@echo "  make up             - Start all services locally"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View service logs"
	@echo ""
	@echo "CI/CD Commands:"
	@echo "  make ci             - Run full CI pipeline (build + test)"
	@echo "  make push           - Push images to registry"
	@echo ""
	@echo "GitOps/Kubernetes Commands:"
	@echo "  make deploy-argocd  - Deploy Argo CD and IRIS applications to K8s"
	@echo "  make helm-test      - Validate all Helm charts"
	@echo "  make seed-db        - Seed database with 22 Alpaca test accounts"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  make clean-app      - Remove app containers and built images (keeps infra)"
	@echo "  make clean-all      - Complete cleanup (everything including Ollama)"

# --- FULL CI PIPELINE ---
ci: build test
	@echo "✅ CI Pipeline Complete"

all: build test up
	@echo ""
	@echo "========================================================================="
	@echo "✅ IRIS Services Running"
	@echo "API Gateway: http://localhost:8080"
	@echo "Agent Router: http://localhost:8000"
	@echo "Web UI: http://localhost:3000"
	@echo ""
	@echo "Test the API:"
	@echo '  curl -X POST http://localhost:8080/v1/chat \'
	@echo '    -H "Content-Type: application/json" \'
	@echo '    -d '"'"'{"user_id": "test", "prompt": "Hello"}'"'"
	@echo ""
	@echo "View logs: make logs"
	@echo "Stop services: make down"
	@echo "========================================================================="

# --- BUILD COMMANDS ---
build:
	@echo "Building all IRIS services..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) build iris-api-gateway iris-agent-router iris-web-ui iris-broker-service
	@echo "✅ Build complete"

build-go:
	@echo "Building Go API Gateway..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) build iris-api-gateway
	@echo "✅ Go service built"

build-python:
	@echo "Building Python Agent Router..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) build iris-agent-router
	@echo "✅ Python service built"

build-web:
	@echo "Building Web UI..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) build iris-web-ui
	@echo "✅ Web UI built"

# --- TEST COMMANDS ---
test: test-unit test-integration
	@echo "✅ All tests passed"

test-unit:
	@echo "Running Python unit tests in container..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) run --rm python-tester
	@echo "✅ Unit tests passed"

test-integration:
	@echo "Starting services for integration testing..."
	$(MAKE) infra
	docker-compose $(DOCKER_COMPOSE_FLAGS) up -d iris-api-gateway iris-agent-router
	@echo "Waiting for services to be ready..."
	$(SLEEP_CMD) 10
	@echo "Running integration tests..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) run --rm integration-tester
	@echo "Stopping test services..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) down
	@echo "✅ Integration tests passed"


# --- INFRASTRUCTURE ---
infra:
	@echo "Starting infrastructure services..."
	docker volume create lancedb-data || true
	docker-compose $(DOCKER_COMPOSE_FLAGS) up -d ollama postgres redis
	@echo "waiting for ollama to be healthy..."
	$(SLEEP_CMD) 5
	@echo "Pulling LLM models (this may take a while)..."
	@echo "Primary: FinGPT-MT-Llama-3-8B..."
	-docker-compose $(DOCKER_COMPOSE_FLAGS) exec ollama ollama pull fingpt-mt-llama3:latest || echo "FinGPT not available, will use fallback"
	@echo "Fallback: qwen2.5:14b..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) exec ollama ollama pull qwen2.5:14b
	@echo "✅ Infrastructure up"

# --- LOCAL DEVELOPMENT ---
up: infra
	@echo "Starting IRIS services..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) up -d iris-api-gateway iris-agent-router iris-web-ui iris-broker-service
	@echo "✅ Services started"
	@echo "API Gateway: http://localhost:8080"
	@echo "Agent Router: http://localhost:8000"
	@echo "Web UI: http://localhost:3000"

up-all:
	@echo "Starting all services including Ollama..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) up -d
	@echo "⚠️  Ollama will start and potentially download the configured model (check docker-compose $(DOCKER_COMPOSE_FLAGS).yml)"

web:
	@echo "Opening web UI..."
	@start http://localhost:3000

down:
	@echo "Stopping all services..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) down
	@echo "✅ Services stopped"

logs:
	docker-compose $(DOCKER_COMPOSE_FLAGS) logs -f

restart:
	@$(MAKE) down
	@$(MAKE) up

# --- DATABASE SEEDING ---
seed-db:
	@echo "Seeding database with Alpaca accounts..."
	@echo "Waiting for PostgreSQL..."
	$(SLEEP_CMD) 3
	@echo "Running seed script..."
	python scripts/seed_alpaca_accounts.py
	@echo "✅ Database seeded with 22 Alpaca accounts"
	@echo "Login with any account using password: password123"


# --- REGISTRY COMMANDS ---
push:
	@echo "Pushing images to registry..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) push iris-api-gateway iris-agent-router
	@echo "✅ Images pushed"

# --- GITOPS / KUBERNETES DEPLOYMENT ---
deploy-argocd:
	@echo "Deploying Argo CD and IRIS applications..."
	@echo "This will install Argo CD on your Kubernetes cluster and deploy IRIS apps."
	@echo ""
	python scripts/deploy-argocd.py

helm-test:
	@echo "Validating Helm charts..."
ifeq ($(OS_NAME),Windows)
	@echo "Running PowerShell test script..."
	powershell -ExecutionPolicy Bypass -File scripts/test-helm-deployments.ps1
else
	@echo "Running bash test script..."
	bash scripts/test-helm-deployments.sh
endif

helm-lint:
	@echo "Linting all Helm charts..."
	@helm lint helm/iris-api-gateway
	@helm lint helm/iris-agent-router
	@helm lint helm/iris-web-ui
	@helm lint helm/postgresql
	@helm lint helm/ollama
	@echo "✅ All charts passed linting"

# --- CLEANUP COMMANDS ---
# --- CLEANUP COMMANDS ---
clean-app:
	@echo "Removing application containers and built images (keeping infra)..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) down --rmi local
	@echo "✅ App cleanup complete"

clean: clean-app

clean-infra:
	@echo "Removing infrastructure containers and volumes..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) rm -s -v -f ollama
	docker volume rm lancedb-data || echo "Volume lancedb-data not found or already removed"
	@echo "✅ Infra cleanup complete"

clean-all:
	@echo "Cleaning containers and volumes (preserving LLM models and images)..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) down --volumes --remove-orphans
	@echo "Note: LLM models in ./data/ollama are preserved for faster rebuilds"
	@echo "✅ Cleanup complete (Images and LLMs preserved)"

nuke-all:
	@echo "Full nuclear clean (removing ALL images, volumes, and build cache)..."
	docker-compose $(DOCKER_COMPOSE_FLAGS) down --rmi all --volumes
	docker system prune -f
	@echo "✅ Full system wipe complete"

# --- UTILITY COMMANDS ---
shell-go:
	docker-compose run --rm go-builder sh

shell-python:
	docker-compose run --rm python-tester bash

shell-test-runner:
	docker-compose run --rm integration-tester /bin/bash

status:
	@echo "IRIS Services Status:"
	@docker-compose ps

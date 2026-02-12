# PresenceOS - Makefile
# Usage: make <target>

.DEFAULT_GOAL := help
COMPOSE := docker compose

# ── Lifecycle ─────────────────────────────────────────

.PHONY: up
up: ## Start all services (detached)
	$(COMPOSE) up -d

.PHONY: up-build
up-build: ## Build images and start all services
	$(COMPOSE) up -d --build

.PHONY: down
down: ## Stop all services
	$(COMPOSE) down

.PHONY: restart
restart: ## Restart all services
	$(COMPOSE) restart

.PHONY: build
build: ## Build all Docker images
	$(COMPOSE) build

.PHONY: pull
pull: ## Pull latest base images
	$(COMPOSE) pull

# ── Logs ──────────────────────────────────────────────

.PHONY: logs
logs: ## Tail logs for all services
	$(COMPOSE) logs -f

.PHONY: logs-backend
logs-backend: ## Tail backend logs
	$(COMPOSE) logs -f backend

.PHONY: logs-frontend
logs-frontend: ## Tail frontend logs
	$(COMPOSE) logs -f frontend

.PHONY: logs-worker
logs-worker: ## Tail celery worker logs
	$(COMPOSE) logs -f celery-worker

# ── Database ──────────────────────────────────────────

.PHONY: db-migrate
db-migrate: ## Run Alembic migrations
	$(COMPOSE) exec backend alembic upgrade head

.PHONY: db-seed
db-seed: ## Seed the database
	$(COMPOSE) exec backend python -m scripts.seed

.PHONY: db-reset
db-reset: ## Reset database (drop + recreate + migrate + seed)
	$(COMPOSE) exec postgres psql -U presenceos -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(COMPOSE) exec backend alembic upgrade head
	$(COMPOSE) exec backend python -m scripts.seed

.PHONY: db-shell
db-shell: ## Open psql shell
	$(COMPOSE) exec postgres psql -U presenceos

# ── Testing ───────────────────────────────────────────

.PHONY: test
test: ## Run backend tests
	$(COMPOSE) exec backend pytest -x -q

.PHONY: test-cov
test-cov: ## Run tests with coverage
	$(COMPOSE) exec backend pytest --cov=app --cov-report=term-missing

.PHONY: lint
lint: ## Run linters (ruff + black check)
	$(COMPOSE) exec backend ruff check .
	$(COMPOSE) exec backend black --check .

# ── Status ────────────────────────────────────────────

.PHONY: ps
ps: ## Show running services
	$(COMPOSE) ps

.PHONY: health
health: ## Check health of all services
	@echo "=== Service Health ==="
	@$(COMPOSE) ps --format "table {{.Name}}\t{{.Status}}"
	@echo ""
	@echo "=== Backend Health ==="
	@curl -sf http://localhost:$${BACKEND_PORT:-8000}/health | python3 -m json.tool 2>/dev/null || echo "Backend unreachable"

# ── Cleanup ───────────────────────────────────────────

.PHONY: clean
clean: ## Stop services and remove volumes
	$(COMPOSE) down -v --remove-orphans

.PHONY: clean-images
clean-images: ## Remove all project images
	$(COMPOSE) down --rmi all -v --remove-orphans

# ── Shortcuts ─────────────────────────────────────────

.PHONY: shell-backend
shell-backend: ## Open a bash shell in backend container
	$(COMPOSE) exec backend bash

.PHONY: shell-frontend
shell-frontend: ## Open a shell in frontend container
	$(COMPOSE) exec frontend sh

.PHONY: setup
setup: ## First-time setup: copy env, build, start, migrate, seed
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d --build
	@echo "Waiting for services to be healthy..."
	@sleep 15
	$(COMPOSE) exec backend alembic upgrade head || true
	$(COMPOSE) exec backend python -m scripts.seed || true
	@echo ""
	@echo "PresenceOS is running!"
	@echo "  Backend:  http://localhost:$${BACKEND_PORT:-8000}/api/v1/docs"
	@echo "  Frontend: http://localhost:$${FRONTEND_PORT:-3001}"
	@echo "  MinIO:    http://localhost:$${MINIO_CONSOLE_PORT:-9001}"

# ── Help ──────────────────────────────────────────────

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: help dev up down restart logs clean rebuild db-shell backend-shell migrate-create migrate-upgrade migrate-downgrade test-user test test-models test-unit test-coverage lint

help:
	@echo "NewsWatcher - Available Commands"
	@echo "================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start development environment"
	@echo "  make up               - Start all services (alias for dev)"
	@echo "  make down             - Stop all services"
	@echo "  make restart          - Restart all services"
	@echo "  make logs             - View logs from all services"
	@echo "  make logs-backend     - View backend logs"
	@echo "  make logs-frontend    - View frontend logs"
	@echo "  make clean            - Stop and remove all containers and volumes"
	@echo "  make rebuild          - Clean and rebuild everything"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-models      - Run model tests only"
	@echo "  make test-unit        - Run a specific test file (FILE=path/to/test.py)"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             - Run ruff linter with autofix"
	@echo ""
	@echo "Database Migrations:"
	@echo "  make migrate-create   - Create new migration (MSG='description')"
	@echo "  make migrate-upgrade  - Apply pending migrations"
	@echo "  make migrate-downgrade- Rollback last migration"
	@echo "  make migrate-history  - Show migration history"
	@echo "  make migrate-current  - Show current revision"
	@echo ""
	@echo "Database Access:"
	@echo "  make db-shell         - Access PostgreSQL shell"
	@echo "  make backend-shell    - Access backend container shell"
	@echo ""
	@echo "Utilities:"
	@echo "  make test-user        - Create test user (test@example.com / password123)"
	@echo "  make status           - Show service status"
	@echo "  make ps               - Show running containers (alias for status)"
	@echo ""

# Development commands
dev:
	docker-compose -f docker-compose.dev.yml up --build

up: dev

down:
	docker-compose -f docker-compose.dev.yml down

restart:
	docker-compose -f docker-compose.dev.yml restart

logs:
	docker-compose -f docker-compose.dev.yml logs -f

logs-backend:
	docker-compose -f docker-compose.dev.yml logs -f backend

logs-frontend:
	docker-compose -f docker-compose.dev.yml logs -f frontend

clean:
	docker-compose -f docker-compose.dev.yml down -v

rebuild: clean dev

status:
	docker-compose -f docker-compose.dev.yml ps

ps: status

# Database migrations
migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a message. Usage: make migrate-create MSG='description'"; \
		exit 1; \
	fi
	@echo "Creating migration: $(MSG)"
	docker-compose -f docker-compose.dev.yml exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-upgrade:
	@echo "Applying pending migrations..."
	docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

migrate-downgrade:
	@echo "Rolling back last migration..."
	docker-compose -f docker-compose.dev.yml exec backend alembic downgrade -1

migrate-history:
	@echo "Migration history:"
	docker-compose -f docker-compose.dev.yml exec backend alembic history

migrate-current:
	@echo "Current revision:"
	docker-compose -f docker-compose.dev.yml exec backend alembic current

# Database access
db-shell:
	docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d newswatcher

backend-shell:
	docker-compose -f docker-compose.dev.yml exec backend sh

# Utilities
test-user:
	@echo "Creating test user..."
	docker-compose -f docker-compose.dev.yml exec backend python create_test_user.py

# Testing commands
test:
	@echo "Running all tests..."
	docker-compose -f docker-compose.dev.yml exec backend pytest tests/ -v

test-models:
	@echo "Running model tests..."
	docker-compose -f docker-compose.dev.yml exec backend pytest tests/test_models.py -v

test-unit:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please provide a test file. Usage: make test-unit FILE=tests/test_models.py"; \
		exit 1; \
	fi
	@echo "Running tests from $(FILE)..."
	docker-compose -f docker-compose.dev.yml exec backend pytest $(FILE) -v

test-coverage:
	@echo "Running tests with coverage..."
	docker-compose -f docker-compose.dev.yml exec backend pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in backend/htmlcov/index.html"

# Code quality
lint:
	@echo "Running ruff linter..."
	docker-compose -f docker-compose.dev.yml exec backend ruff check . --fix
	@echo "Linting complete!"

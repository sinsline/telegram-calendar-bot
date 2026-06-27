# Makefile for Telegram Calendar Bot
# Provides convenient commands for development and deployment

.PHONY: help install test build deploy clean dev prod backup restore logs status health

# Default target
.DEFAULT_GOAL := help

# Configuration
PROJECT_NAME = telegram-calendar-bot
IMAGE_NAME = telegram-calendar-bot
PYTHON = python3
PIP = pip3

# Colors for output
COLOR_RESET = \033[0m
COLOR_GREEN = \033[32m
COLOR_YELLOW = \033[33m
COLOR_RED = \033[31m
COLOR_BLUE = \033[34m

define log
	@echo "$(COLOR_GREEN)[$(shell date +'%H:%M:%S')] $(1)$(COLOR_RESET)"
endef

define warn
	@echo "$(COLOR_YELLOW)[$(shell date +'%H:%M:%S')] Warning: $(1)$(COLOR_RESET)"
endef

define error
	@echo "$(COLOR_RED)[$(shell date +'%H:%M:%S')] Error: $(1)$(COLOR_RESET)"
endef

help: ## Show this help message
	@echo "$(COLOR_BLUE)Telegram Calendar Bot - Available Commands$(COLOR_RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_GREEN)%-15s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(COLOR_BLUE)Examples:$(COLOR_RESET)"
	@echo "  make install     # Install dependencies"
	@echo "  make test        # Run all tests"
	@echo "  make dev         # Start development environment"
	@echo "  make prod        # Deploy to production"
	@echo "  make backup      # Create backup"
	@echo "  make logs        # Show logs"

# Development Setup
install: ## Install Python dependencies
	$(call log,Installing dependencies...)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(call log,Dependencies installed successfully)

install-dev: ## Install development dependencies
	$(call log,Installing development dependencies...)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-cov black flake8 mypy
	$(call log,Development dependencies installed)

setup: ## Run initial setup wizard
	$(call log,Running setup wizard...)
	$(PYTHON) -m src.cli setup

# Code Quality
format: ## Format code with black
	$(call log,Formatting code...)
	black src/ tests/
	$(call log,Code formatting complete)

lint: ## Run linting with flake8
	$(call log,Running linter...)
	flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503
	$(call log,Linting complete)

typecheck: ## Run type checking with mypy
	$(call log,Running type checker...)
	mypy src/ --ignore-missing-imports
	$(call log,Type checking complete)

check: lint typecheck ## Run all code quality checks
	$(call log,All code quality checks passed)

# Testing
test: ## Run all tests
	$(call log,Running tests...)
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	$(call log,All tests completed)

test-unit: ## Run unit tests only
	$(call log,Running unit tests...)
	pytest tests/services/ tests/test_telegram_bot.py -v
	$(call log,Unit tests completed)

test-integration: ## Run integration tests only
	$(call log,Running integration tests...)
	pytest tests/integration/ -v
	$(call log,Integration tests completed)

test-watch: ## Run tests in watch mode
	$(call log,Starting test watcher...)
	pytest-watch tests/ -- -v

coverage: ## Generate test coverage report
	$(call log,Generating coverage report...)
	pytest tests/ --cov=src --cov-report=html
	$(call log,Coverage report generated in htmlcov/)

# Docker Operations
build: ## Build Docker image
	$(call log,Building Docker image...)
	docker build -t $(IMAGE_NAME):latest .
	$(call log,Docker image built successfully)

build-no-cache: ## Build Docker image without cache
	$(call log,Building Docker image without cache...)
	docker build --no-cache -t $(IMAGE_NAME):latest .
	$(call log,Docker image built successfully)

# Deployment
dev: ## Start development environment
	$(call log,Starting development environment...)
	./scripts/deploy.sh dev

prod: ## Deploy to production
	$(call log,Deploying to production...)
	./scripts/deploy.sh prod

update: ## Update existing deployment
	$(call log,Updating deployment...)
	./scripts/deploy.sh update

rollback: ## Rollback to previous version
	$(call warn,Rolling back to previous version...)
	./scripts/deploy.sh rollback

# Runtime Management
start: ## Start the bot (local)
	$(call log,Starting bot locally...)
	$(PYTHON) -m src.cli start

start-daemon: ## Start the bot as daemon (local)
	$(call log,Starting bot as daemon...)
	$(PYTHON) -m src.cli start --daemon

stop: ## Stop the bot
	$(call log,Stopping bot...)
	if [ -f "bot.pid" ]; then \
		$(PYTHON) -m src.cli stop; \
	else \
		./scripts/deploy.sh stop; \
	fi

restart: ## Restart the bot
	$(call log,Restarting bot...)
	$(MAKE) stop
	sleep 2
	$(MAKE) start

# Monitoring
status: ## Show bot status
	$(call log,Checking bot status...)
	./scripts/deploy.sh status

health: ## Run health check
	$(call log,Running health check...)
	./scripts/healthcheck.sh

logs: ## Show bot logs
	$(call log,Showing recent logs...)
	./scripts/deploy.sh logs

logs-follow: ## Follow bot logs in real-time
	$(call log,Following logs...)
	docker-compose logs -f $(PROJECT_NAME)

# Backup & Restore
backup: ## Create backup
	$(call log,Creating backup...)
	./scripts/backup.sh create

backup-list: ## List available backups
	$(call log,Listing backups...)
	./scripts/backup.sh list

restore: ## Restore from backup (use: make restore BACKUP=filename)
	$(call warn,Restoring from backup...)
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(COLOR_RED)Error: Please specify BACKUP=filename$(COLOR_RESET)"; \
		echo "Available backups:"; \
		./scripts/backup.sh list; \
		exit 1; \
	fi
	./scripts/backup.sh restore $(BACKUP)

# Maintenance
clean: ## Clean up containers and images
	$(call warn,Cleaning up Docker resources...)
	./scripts/deploy.sh clean

clean-all: clean ## Clean everything (containers, images, data)
	$(call warn,Cleaning all data...)
	rm -rf data/ logs/ backups/ htmlcov/ .pytest_cache/ .mypy_cache/
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete

reset: ## Reset to clean state (dangerous!)
	$(call warn,Resetting to clean state...)
	@echo "$(COLOR_RED)This will delete all data, logs, and backups!$(COLOR_RESET)"
	@read -p "Are you sure? (type 'yes' to confirm): " confirm && [ "$$confirm" = "yes" ]
	$(MAKE) clean-all

# Configuration
config: ## Show current configuration
	$(call log,Current configuration...)
	$(PYTHON) -m src.cli config

config-set: ## Set configuration (use: make config-set KEY=value VALUE=newvalue)
	$(call log,Setting configuration...)
	@if [ -z "$(KEY)" ] || [ -z "$(VALUE)" ]; then \
		echo "$(COLOR_RED)Error: Please specify KEY and VALUE$(COLOR_RESET)"; \
		echo "Example: make config-set KEY=LOG_LEVEL VALUE=DEBUG"; \
		exit 1; \
	fi
	$(PYTHON) -m src.cli config $(KEY) "$(VALUE)"

# Development Utilities
shell: ## Open Python shell with bot context
	$(call log,Opening Python shell...)
	PYTHONPATH=. $(PYTHON) -c "from src.telegram_bot import *; print('Bot modules loaded. Happy debugging!')"

ipython: ## Open IPython shell with bot context
	$(call log,Opening IPython shell...)
	PYTHONPATH=. ipython -c "from src.telegram_bot import *; print('Bot modules loaded in IPython!')"

debug: ## Start bot in debug mode with extra logging
	$(call log,Starting bot in debug mode...)
	LOG_LEVEL=DEBUG $(PYTHON) -m src.cli start

# Statistics
stats: ## Show project statistics
	$(call log,Project statistics...)
	@echo "$(COLOR_BLUE)Lines of Code:$(COLOR_RESET)"
	@find src/ -name "*.py" -exec wc -l {} + | tail -1
	@echo ""
	@echo "$(COLOR_BLUE)Test Coverage:$(COLOR_RESET)"
	@find tests/ -name "*.py" -exec wc -l {} + | tail -1
	@echo ""
	@echo "$(COLOR_BLUE)Docker Image Size:$(COLOR_RESET)"
	@docker images $(IMAGE_NAME):latest --format "{{.Size}}" 2>/dev/null || echo "Not built"
	@echo ""
	@echo "$(COLOR_BLUE)Dependencies:$(COLOR_RESET)"
	@grep -c "^[^#]" requirements.txt 2>/dev/null || echo "0"

# CI/CD Helpers
ci-test: install-dev lint typecheck test ## Run full CI test suite

pre-commit: format lint typecheck test ## Run pre-commit checks
	$(call log,Pre-commit checks completed successfully)

# Quick shortcuts
up: dev ## Alias for 'make dev'
down: stop ## Alias for 'make stop'
test-fast: test-unit ## Alias for 'make test-unit'
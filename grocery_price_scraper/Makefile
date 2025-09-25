# Makefile for Grocery Price Scraper

# Variables
PYTHON = python3
VENV = venv
VENV_BIN = $(VENV)/bin
PIP = $(VENV_BIN)/pip
PYTHON_VENV = $(VENV_BIN)/python
PYTEST = $(VENV_BIN)/pytest

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help setup install test clean run lint format check-deps

# Default target
help: ## Show this help message
	@echo "$(BLUE)Grocery Price Scraper - Available Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Quick start:$(NC)"
	@echo "  make setup    # Initial setup"
	@echo "  make run      # Run price comparison"
	@echo "  make test     # Run tests"

setup: ## Complete initial setup (venv, dependencies, browsers)
	@echo "$(BLUE)Setting up Grocery Price Scraper...$(NC)"
	@bash tooling/local_setup.sh
	@echo "$(GREEN)Setup completed! Run 'make run' to start.$(NC)"

install: $(VENV)/bin/activate ## Install dependencies only
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@$(VENV_BIN)/playwright install chromium
	@echo "$(GREEN)Dependencies installed successfully$(NC)"

$(VENV)/bin/activate: requirements.txt ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	@$(PYTHON) -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@touch $(VENV)/bin/activate

run: $(VENV)/bin/activate ## Run the price comparison pipeline
	@echo "$(BLUE)Running price comparison...$(NC)"
	@$(PYTHON_VENV) runner.py

run-categories: $(VENV)/bin/activate ## Run with specific categories (usage: make run-categories CATS="vegetables fruits")
	@echo "$(BLUE)Running price comparison for categories: $(CATS)$(NC)"
	@$(PYTHON_VENV) runner.py --categories $(CATS)

run-sites: $(VENV)/bin/activate ## Run with specific sites (usage: make run-sites SITES="bigbasket jiomart")
	@echo "$(BLUE)Running price comparison for sites: $(SITES)$(NC)"
	@$(PYTHON_VENV) runner.py --sites $(SITES)

stats: $(VENV)/bin/activate ## Show database statistics
	@echo "$(BLUE)Database Statistics:$(NC)"
	@$(PYTHON_VENV) runner.py --stats

cleanup: $(VENV)/bin/activate ## Clean old data (usage: make cleanup DAYS=30)
	@echo "$(BLUE)Cleaning up data older than $(or $(DAYS),90) days...$(NC)"
	@$(PYTHON_VENV) runner.py --cleanup $(or $(DAYS),90)

test: $(VENV)/bin/activate ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(PYTEST) tests/ -v

test-unit: $(VENV)/bin/activate ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(PYTEST) tests/unit/ -v

test-integration: $(VENV)/bin/activate ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(PYTEST) tests/integration/ -v

test-coverage: $(VENV)/bin/activate ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(PIP) install coverage
	@$(VENV_BIN)/coverage run -m pytest tests/
	@$(VENV_BIN)/coverage report
	@$(VENV_BIN)/coverage html

lint: $(VENV)/bin/activate ## Check code style and quality
	@echo "$(BLUE)Checking code style...$(NC)"
	@$(PIP) install flake8 black isort
	@$(VENV_BIN)/flake8 --max-line-length=100 --ignore=E203,W503 .
	@$(VENV_BIN)/black --check --diff .
	@$(VENV_BIN)/isort --check-only --diff .

format: $(VENV)/bin/activate ## Format code automatically
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(PIP) install black isort
	@$(VENV_BIN)/black .
	@$(VENV_BIN)/isort .
	@echo "$(GREEN)Code formatted successfully$(NC)"

check-deps: $(VENV)/bin/activate ## Check for outdated dependencies
	@echo "$(BLUE)Checking for outdated dependencies...$(NC)"
	@$(PIP) list --outdated

update-deps: $(VENV)/bin/activate ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@$(PIP) install --upgrade -r requirements.txt

clean: ## Clean up generated files and cache
	@echo "$(BLUE)Cleaning up...$(NC)"
	@rm -rf $(VENV)
	@rm -rf .pytest_cache
	@rm -rf __pycache__
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@rm -rf htmlcov
	@rm -f .coverage
	@echo "$(GREEN)Cleanup completed$(NC)"

clean-data: ## Clean up data files (CAUTION: This will delete all scraped data!)
	@echo "$(RED)WARNING: This will delete all scraped data and reports!$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -rf data/; \
		mkdir -p data/reports; \
		echo "$(GREEN)Data cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Operation cancelled$(NC)"; \
	fi

install-dev: $(VENV)/bin/activate ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@$(PIP) install flake8 black isort coverage pytest-cov

docs: $(VENV)/bin/activate ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@$(PIP) install sphinx
	@mkdir -p docs
	@echo "Documentation generation not implemented yet"

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t grocery-price-scraper .

docker-run: ## Run in Docker container
	@echo "$(BLUE)Running in Docker container...$(NC)"
	@docker run --rm -v $(PWD)/data:/app/data grocery-price-scraper

# Development shortcuts
dev-run: ## Quick development run with basic categories
	@echo "$(BLUE)Development run (vegetables, fruits)...$(NC)"
	@$(PYTHON_VENV) runner.py --categories vegetables fruits --sites bigbasket

dev-test: ## Quick development test
	@echo "$(BLUE)Running quick development tests...$(NC)"
	@$(PYTEST) tests/unit/test_normalizer.py -v

# Utility targets
check-python: ## Check Python version
	@echo "$(BLUE)Checking Python version...$(NC)"
	@$(PYTHON) --version
	@$(PYTHON) -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

check-setup: $(VENV)/bin/activate ## Verify setup is working
	@echo "$(BLUE)Verifying setup...$(NC)"
	@$(PYTHON_VENV) -c "from scrapers import Farm2bagScraper; from normalizer import ProductNormalizer; from comparator import PriceComparator; from reporter import ExcelReporter; from db import Database; print('✅ All imports successful')"
	@echo "$(GREEN)Setup verification passed$(NC)"

show-config: ## Show current configuration
	@echo "$(BLUE)Current Configuration:$(NC)"
	@echo "Config files:"
	@ls -la config/
	@echo "\nData directory:"
	@ls -la data/ 2>/dev/null || echo "No data directory yet"

# Quick aliases
r: run ## Alias for run
t: test ## Alias for test
s: stats ## Alias for stats
c: clean ## Alias for clean
f: format ## Alias for format
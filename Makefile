.PHONY: help probe run run-debug report all clean setup lint test ruff bandit check infra-plan infra-apply infra-destroy web

CFG?=configs/exa_vs_ch_1g.yaml
PORT?=8000

# Default target
help: ## Show this help message
	@echo "Database Benchmark Framework - Available Commands:"
	@echo
	@echo "Main workflow:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(probe|run|report|all|web):' | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
	@echo
	@echo "Development:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(setup|lint|ruff|bandit|check|test|clean):' | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
	@echo
	@echo "Infrastructure:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '^(infra-|check-aws)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
	@echo
	@echo "Usage:"
	@echo "  make all CFG=configs/your-config.yaml"
	@echo "  make web PORT=8000  # Start web server"
	@echo "  make check  # Run all quality checks"
	@echo

# Main workflow commands
probe: ## Gather system information for benchmark
	python -m benchkit probe --config $(CFG)

probe-debug: ## Gather system information for benchmark in debug mode
	python -m benchkit probe --config $(CFG) --debug

run: ## Execute benchmark with specified configuration
	python -m benchkit run --config $(CFG)

run-debug: ## Execute benchmark with specified configuration and debug flag
	python -m benchkit run --config $(CFG) --debug

report: ## Generate reports from benchmark results
	python -m benchkit report --config $(CFG)

status: ## Show status of the projects
	python -m benchkit status

web: ## Start web server to view generated reports (default port 8000)
	@echo "Starting web server on http://localhost:$(PORT)"
	@echo "Blog posts available at: http://localhost:$(PORT)/"
	@echo "Press Ctrl+C to stop the server"
	@cd results && python -m http.server $(PORT)

all: infra-check probe run report ## Run complete benchmark workflow (infra-check + probe + run + report)
all-debug: infra-check probe-debug run-debug report ## Run complete benchmark workflow in debug mode (infra-check + probe + run + report)

# Development commands
setup: ## Install package and development dependencies
	python -m pip install -e .
	python -m pip install -e ".[dev]"
	python -m pip install ruff bandit

lint: ## Format code with black and isort, check types with mypy
	black benchkit/ tests/
	isort benchkit/ tests/
	mypy benchkit/

ruff: ## Run ruff linter
	ruff check benchkit/ tests/

bandit: ## Run bandit security checks
	bandit -r benchkit/ -f json -o bandit-report.json || true
	bandit -r benchkit/ --severity-level high || true

check: lint ruff bandit ## Run all code quality and security checks

test: ## Run pytest test suite
	pytest tests/ -v

clean: ## Clean up generated files and cache
	rm -rf results/*/
	rm -rf posts/*/
	rm -f bandit-report.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Infrastructure commands
infra-check: ## Check and deploy infrastructure if using cloud mode
	@echo "Checking if cloud infrastructure deployment is needed..."
	@if grep -q 'mode: *"aws"' $(CFG) || grep -q 'mode: *"gcp"' $(CFG) || grep -q 'mode: *"azure"' $(CFG); then \
		echo "Cloud mode detected, checking terraform installation..."; \
		if ! command -v terraform >/dev/null 2>&1; then \
			echo "Error: Terraform not found. Please install Terraform first:"; \
			echo "  https://developer.hashicorp.com/terraform/install"; \
			exit 1; \
		fi; \
		echo "Deploying cloud infrastructure..."; \
		python -m benchkit infra apply --config $(CFG); \
	else \
		echo "Local mode detected, skipping infrastructure deployment"; \
	fi

infra-plan: ## Plan cloud infrastructure changes
	python -m benchkit infra plan --config $(CFG)

infra-apply: ## Deploy cloud infrastructure
	python -m benchkit infra apply --config $(CFG)

infra-destroy: ## Destroy cloud infrastructure
	python -m benchkit infra destroy --config $(CFG)

check-aws: ## Check AWS credentials and permissions
	python scripts/check_aws_credentials.py


# Code Quality & Unused Code Detection
analyze-unused: ## Run custom AST-based unused code analyzer
	python3 scripts/find_unused_code.py

lint-unused: ## Find unused imports and variables with ruff
	ruff check --select F401,F841 benchkit/

fix-imports: ## Automatically remove unused imports
	ruff check --select F401 --fix benchkit/

check-dead-code: ## Run vulture for dead code detection
	@command -v vulture >/dev/null 2>&1 || { echo "Installing vulture..."; pip install vulture; }
	vulture benchkit/ --min-confidence 70 --sort-by-size || true

coverage: ## Run tests with coverage report
	pytest --cov=benchkit --cov-report=html --cov-report=term-missing

quality-full: analyze-unused lint-unused check-dead-code ## Run comprehensive code quality analysis
	@echo ""
	@echo "✅ Quality analysis complete!"
	@echo "📄 See UNUSED_CODE_ANALYSIS.md for detailed report"


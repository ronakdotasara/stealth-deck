# Stealth Deck - Raspberry Pi Makefile
# Build automation and common tasks

.PHONY: help install test lint format clean run setup dev-install

# Default target
help:
	@echo "Stealth Deck - Raspberry Pi Build System"
	@echo "=========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev-install  - Install development dependencies"
	@echo "  make setup        - Initial setup (creates directories)"
	@echo "  make run          - Run the application"
	@echo "  make test         - Run tests"
	@echo "  make coverage     - Run tests with coverage"
	@echo "  make lint         - Run code linters"
	@echo "  make format       - Format code"
	@echo "  make type-check   - Run type checker"
	@echo "  make clean        - Clean temporary files"
	@echo "  make docs         - Build documentation"
	@echo "  make package      - Create distribution package"
	@echo ""

# Installation
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

dev-install: install
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	pre-commit install

setup:
	@echo "Creating directories..."
	mkdir -p data/cache
	mkdir -p data/notes
	mkdir -p data/logs
	mkdir -p logs
	@echo "Setup complete!"

# Running
run:
	@echo "Starting Stealth Deck..."
	python -m src.main

run-debug:
	@echo "Starting Stealth Deck (debug mode)..."
	LOGLEVEL=DEBUG python -m src.main

# Testing
test:
	@echo "Running tests..."
	pytest tests/ -v

test-fast:
	@echo "Running tests (fast, no integration)..."
	pytest tests/ -v -m "not integration"

coverage:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v -m integration

# Code Quality
lint:
	@echo "Running linters..."
	@echo "==> flake8"
	flake8 src/ tests/
	@echo "==> pylint"
	pylint src/
	@echo "Linting complete!"

format:
	@echo "Formatting code..."
	black src/ tests/
	isort src/ tests/
	@echo "Formatting complete!"

format-check:
	@echo "Checking code format..."
	black --check src/ tests/
	isort --check-only src/ tests/

type-check:
	@echo "Running type checker..."
	mypy src/ --ignore-missing-imports

# Security
security-check:
	@echo "Running security scan..."
	bandit -r src/ -f json -o security-report.json
	bandit -r src/ -f screen

# Cleaning
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf build dist *.egg-info
	@echo "Clean complete!"

clean-data:
	@echo "Warning: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/cache/*; \
		rm -rf data/notes/*; \
		rm -rf logs/*; \
		echo "Data cleaned!"; \
	fi

# Documentation
docs:
	@echo "Building documentation..."
	cd ../docs && make html
	@echo "Documentation built in docs/_build/html/"

docs-serve:
	@echo "Serving documentation..."
	cd ../docs/_build/html && python -m http.server 8000

# Packaging
package:
	@echo "Creating package..."
	python setup.py sdist bdist_wheel
	@echo "Package created in dist/"

# Utilities
config-validate:
	@echo "Validating configuration..."
	python ../tools/config_validator.py config.json

benchmark:
	@echo "Running benchmarks..."
	python ../tools/benchmark.py

diagnostics:
	@echo "Running diagnostics..."
	sudo python ../tools/diagnostic_mode/diagnostics.py

# Development helpers
dev-setup: dev-install setup
	@echo "Development environment ready!"

check: lint type-check test
	@echo "All checks passed!"

all: clean install test lint
	@echo "Build complete!"

# Service management (requires sudo)
install-service:
	@echo "Installing systemd service..."
	sudo cp ../deployment/systemd/stealth-deck.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable stealth-deck.service
	@echo "Service installed. Start with: sudo systemctl start stealth-deck"

start-service:
	@echo "Starting service..."
	sudo systemctl start stealth-deck.service

stop-service:
	@echo "Stopping service..."
	sudo systemctl stop stealth-deck.service

restart-service:
	@echo "Restarting service..."
	sudo systemctl restart stealth-deck.service

status-service:
	@echo "Service status:"
	sudo systemctl status stealth-deck.service

logs-service:
	@echo "Service logs:"
	sudo journalctl -u stealth-deck.service -f

# Quick commands
qa: format lint type-check test
	@echo "Quality assurance complete!"

ci: format-check lint type-check test
	@echo "CI checks complete!"

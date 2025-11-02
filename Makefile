
.PHONY: install-dev lint format test test-services test-one

PYTEST=poetry run pytest

install-dev:
	poetry install --with dev,tests --no-root

# Apply all possible automatic fixes using the configured linters/formatters
format:
	poetry run black .
	poetry run ruff check --fix --unsafe-fixes .

# Run all code checks and report issues without modifying files
lint:
	poetry run black --check .
	poetry run ruff check .
	poetry run mypy .
	poetry run bandit -r . -c pyproject.toml

# Tests
test:
	$(PYTEST) -q

test-services:
	$(PYTEST) -q tests/services

# Run a specific test file or node id: make test-one p=tests/services/test_delivery_service.py::test_case
# Shows usage when p is not provided
# Note: pass additional pytest args via A, e.g., make test-one p=tests A="-k smoke -vv"
# (advanced usage intentionally lightweight; main path is p=...)
test-one:
	@if [ -z "$(p)" ]; then \
		echo "Usage: make test-one p=PATH_OR_NODEID [A='additional pytest args']"; \
		exit 1; \
	fi
	$(PYTEST) -q $(p) $(A)

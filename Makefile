# Local equivalents of .github/workflows/ci.yml, docs.yml, and release verify.
# Usage: make ci   (or: make help)

PYTHON ?= python3
PIP := $(PYTHON) -m pip
export PYTHONPATH := src

.PHONY: help ci install test stores compat lint format format-check ty docs docs-linkcheck \
	build examples release-check clean

help:
	@echo "TripleModel — local CI targets"
	@echo ""
	@echo "  make ci              Run all PR CI checks (test, stores, lint, docs)"
	@echo "  make install         Editable install with dev+shacl+sqlalchemy+docs extras"
	@echo "  make test            pytest (100% coverage)"
	@echo "  make stores          Store-focused pytest subset (--no-cov, like CI)"
	@echo "  make compat          pytest with min pydantic/rdflib pins (like CI compat job)"
	@echo "  make lint            ruff check + ty"
	@echo "  make format          ruff format (fix)"
	@echo "  make format-check    ruff format --check (CI)"
	@echo "  make docs            sphinx-build html -W"
	@echo "  make docs-linkcheck  sphinx linkcheck -W (slow; weekly on GitHub)"
	@echo "  make build           python -m build"
	@echo "  make examples        exit_criteria + readme_examples"
	@echo "  make release-check   ci + examples + twine check dist/*"
	@echo "  make clean           remove build artifacts"

install:
	$(PIP) install -e ".[dev,shacl,sqlalchemy,docs]" build twine

test:
	$(PYTHON) -m pytest

stores:
	$(PYTHON) -m pytest tests/test_stores.py tests/test_streaming.py tests/test_stores_extra.py -q --no-cov

compat:
	$(PIP) install "pydantic==2.5.0" "rdflib==7.0.0" -e ".[dev,shacl,sqlalchemy]"
	$(PYTHON) -m pytest

format:
	$(PYTHON) -m ruff format src tests

format-check:
	$(PYTHON) -m ruff format --check src tests

ruff:
	$(PYTHON) -m ruff check src tests

ty:
	$(PYTHON) -m ty check src tests

lint: format-check ruff ty

docs:
	sphinx-build -b html docs docs/_build/html -W

docs-linkcheck:
	sphinx-build -b linkcheck docs docs/_build/linkcheck -W

build:
	rm -rf dist
	$(PYTHON) -m build

examples:
	TRIPLEMODEL_BENCH_COUNT=1000 $(PYTHON) examples/exit_criteria_05.py
	TRIPLEMODEL_BENCH_COUNT=1000 $(PYTHON) examples/exit_criteria_06.py
	TRIPLEMODEL_BENCH_COUNT=1000 $(PYTHON) examples/exit_criteria_07.py
	TRIPLEMODEL_BENCH_COUNT=1000 $(PYTHON) examples/exit_criteria_08.py
	$(PYTHON) examples/exit_criteria_09.py
	$(PYTHON) examples/readme_examples.py

release-check: ci examples build
	$(PYTHON) -m twine check dist/*

# Matches GitHub Actions CI workflow (ci.yml + docs.yml html job).
ci: install
	$(PYTHON) -m build
	$(PYTHON) -m pytest
	$(PYTHON) -m pytest tests/test_stores.py tests/test_streaming.py tests/test_stores_extra.py -q --no-cov
	$(PIP) install "pydantic==2.5.0" "rdflib==7.0.0"
	$(PYTHON) -m pytest
	$(PIP) install --upgrade "pydantic>=2.5,<3" "rdflib>=7.0,<8" -e ".[dev,shacl,sqlalchemy,docs]"
	$(PYTHON) -m ruff format --check src tests
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ty check src tests
	rm -rf docs/_build/html
	sphinx-build -b html docs docs/_build/html -W

clean:
	rm -rf dist build docs/_build .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

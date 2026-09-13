PYTHON ?= python3

.PHONY: help install test lint docs check

help:
	@echo "make install  Install runtime and development dependencies"
	@echo "make test     Run the test suite"
	@echo "make lint     Run import/syntax lint checks"
	@echo "make docs     Build the Sphinx documentation"
	@echo "make check    Run lint checks and tests"

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests example --select E4,E7,E9,F

docs:
	$(MAKE) -C docs html

check: lint test

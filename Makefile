PYTHON := .venv/bin/python
PIP := .venv/bin/python -m pip
NPM := npm --prefix apps/web

.PHONY: setup test web-build check api web dev clean-runtime

setup:
	python3 -m venv .venv
	$(PIP) install -e '.[dev]'
	$(NPM) ci

test:
	$(PYTHON) -m pytest -q

web-build:
	$(NPM) run build

check: test web-build

api:
	$(PYTHON) -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000

web:
	$(NPM) run dev

dev:
	./scripts/dev.sh

clean-runtime:
	@echo "Refusing to delete .threecraft-data automatically. Remove it explicitly if you no longer need local artifacts."

.PHONY: up down install test lint build audit backend-test frontend-test

up:
	docker compose up --build

down:
	docker compose down

install:
	python3 -m venv backend/.venv
	backend/.venv/bin/python -m pip install --upgrade pip
	backend/.venv/bin/python -m pip install -r backend/requirements.txt
	cd frontend && npm ci

test: backend-test frontend-test

backend-test:
	cd backend && .venv/bin/python -m pytest -q

frontend-test:
	cd frontend && npm test

lint:
	cd backend && .venv/bin/ruff check app tests

build:
	cd frontend && npm run build
	docker compose config

audit:
	cd backend && .venv/bin/pip-audit -r requirements-prod.txt
	cd frontend && npm audit --audit-level=moderate

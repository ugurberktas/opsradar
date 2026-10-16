.PHONY: up down test backend-test frontend-test

up:
	docker compose up --build

down:
	docker compose down

backend-test:
	cd backend && python3 -m pytest tests/ -v

frontend-test:
	cd frontend && npm ci && npm run test

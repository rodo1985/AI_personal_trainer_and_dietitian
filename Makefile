.DEFAULT_GOAL := help

BACKEND_ENTRYPOINT := backend/app/main.py
FRONTEND_DIR := frontend

.PHONY: help setup backend-dev frontend-install frontend-dev test test-backend test-frontend lint build

help: ## Show available local development commands.
	@printf "Repository shortcuts\n\n"
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Create Python venv and install backend dependencies via uv.
	uv venv
	uv sync --group dev

backend-dev: ## Run FastAPI development server.
	uv run fastapi dev $(BACKEND_ENTRYPOINT)

frontend-install: ## Install frontend dependencies.
	npm --prefix $(FRONTEND_DIR) install

frontend-dev: ## Run React development server.
	npm --prefix $(FRONTEND_DIR) run dev

test: test-backend test-frontend ## Run backend and frontend test suites.

test-backend: ## Run backend API tests.
	uv run pytest

test-frontend: ## Run frontend tests.
	npm --prefix $(FRONTEND_DIR) test

lint: ## Run Python lint checks.
	uv run ruff check .

build: ## Build the React production bundle.
	npm --prefix $(FRONTEND_DIR) run build

.DEFAULT_GOAL := help

PYTHON_ENTRYPOINT := backend/app/main.py
FRONTEND_DIR := frontend

.PHONY: help setup backend-dev frontend-install frontend-dev test backend-test frontend-test lint build

help: ## Show common local development commands.
	@printf "Personal Endurance Trainer Log - developer shortcuts\n\n"
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Create the uv environment and sync Python dependencies.
	uv venv
	uv sync

backend-dev: ## Start the FastAPI development server.
	uv run fastapi dev $(PYTHON_ENTRYPOINT)

frontend-install: ## Install frontend dependencies.
	npm --prefix $(FRONTEND_DIR) install

frontend-dev: ## Start the Vite development server.
	npm --prefix $(FRONTEND_DIR) run dev

backend-test: ## Run backend tests.
	uv run pytest

frontend-test: ## Run frontend tests.
	npm --prefix $(FRONTEND_DIR) run test

test: backend-test frontend-test ## Run both backend and frontend tests.

lint: ## Run backend linting and frontend type checks.
	uv run ruff check .
	npm --prefix $(FRONTEND_DIR) run lint

build: ## Build the frontend production bundle.
	npm --prefix $(FRONTEND_DIR) run build

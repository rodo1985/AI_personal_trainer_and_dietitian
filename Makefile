.DEFAULT_GOAL := help

PYTHON_ENTRYPOINT := backend/app/main.py
FRONTEND_DIR := frontend
FRONTEND_PACKAGE := $(FRONTEND_DIR)/package.json

.PHONY: help setup backend-dev frontend-install frontend-dev test lint build

help: ## Show repository shortcuts and current branch notes.
	@printf "Repository shortcuts\n\n"
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf "\n"
	@printf "Tip: GNU Make also supports the built-in flag \`make --help\` for CLI usage details.\n"
	@printf "This branch is documentation-only today, so some targets print guidance until the scaffold exists.\n"

setup: ## Create or sync the Python environment with uv when pyproject.toml exists.
	@if [ -f pyproject.toml ]; then \
		uv venv; \
		uv sync; \
	else \
		printf "%s\n" "No pyproject.toml yet. The foundation scaffold has not been added on this branch."; \
	fi

backend-dev: ## Start the FastAPI development server when the backend scaffold exists.
	@if [ -f $(PYTHON_ENTRYPOINT) ]; then \
		uv run fastapi dev $(PYTHON_ENTRYPOINT); \
	else \
		printf "%s\n" "Missing $(PYTHON_ENTRYPOINT). Add the backend scaffold before starting the API."; \
	fi

frontend-install: ## Install frontend dependencies when the React app exists.
	@if [ -f $(FRONTEND_PACKAGE) ]; then \
		npm --prefix $(FRONTEND_DIR) install; \
	else \
		printf "%s\n" "Missing $(FRONTEND_PACKAGE). Add the React scaffold before installing frontend dependencies."; \
	fi

frontend-dev: ## Start the frontend development server when the React app exists.
	@if [ -f $(FRONTEND_PACKAGE) ]; then \
		npm --prefix $(FRONTEND_DIR) run dev; \
	else \
		printf "%s\n" "Missing $(FRONTEND_PACKAGE). Add the React scaffold before starting the frontend."; \
	fi

test: ## Run backend and frontend tests when the corresponding scaffolds exist.
	@if [ -f pyproject.toml ]; then \
		uv run pytest; \
	else \
		printf "%s\n" "Skipping Python tests because pyproject.toml is not present yet."; \
	fi
	@if [ -f $(FRONTEND_PACKAGE) ]; then \
		npm --prefix $(FRONTEND_DIR) test; \
	else \
		printf "%s\n" "Skipping frontend tests because $(FRONTEND_PACKAGE) is not present yet."; \
	fi

lint: ## Run Python lint checks when the backend scaffold exists.
	@if [ -f pyproject.toml ]; then \
		uv run ruff check .; \
	else \
		printf "%s\n" "Skipping lint because pyproject.toml is not present yet."; \
	fi

build: ## Build the frontend when the React app exists.
	@if [ -f $(FRONTEND_PACKAGE) ]; then \
		npm --prefix $(FRONTEND_DIR) run build; \
	else \
		printf "%s\n" "Skipping frontend build because $(FRONTEND_PACKAGE) is not present yet."; \
	fi

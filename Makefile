SHELL := /bin/bash

BACKEND_DIR := backend
FRONTEND_DIR := frontend

.DEFAULT_GOAL := help
.PHONY: help install install-backend install-frontend install-e2e \
	dev backend frontend test test-backend e2e typecheck build

help: ## Show available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install backend and frontend dependencies

install-backend: ## uv sync the backend
	cd $(BACKEND_DIR) && uv sync

install-frontend: ## npm install the frontend
	cd $(FRONTEND_DIR) && npm install

install-e2e: ## Install the Playwright Chromium browser (first time only)
	cd $(FRONTEND_DIR) && npx playwright install chromium

# Runs both servers in one terminal; Ctrl-C stops both.
dev: ## Run backend (:8000) and frontend (:5173) together
	@trap 'kill 0' INT TERM EXIT; \
	(cd $(BACKEND_DIR) && uv run python -m spend_assistant) & \
	(cd $(FRONTEND_DIR) && npm run dev) & \
	wait

backend: ## Run only the backend (http://localhost:8000)
	cd $(BACKEND_DIR) && uv run python -m spend_assistant

frontend: ## Run only the frontend (http://localhost:5173)
	cd $(FRONTEND_DIR) && npm run dev

test: test-backend ## Run backend unit tests

test-backend: ## Run backend pytest suite
	cd $(BACKEND_DIR) && uv run pytest

e2e: ## Run Playwright end-to-end tests (needs data pack + AWS credentials)
	cd $(FRONTEND_DIR) && npm run e2e

typecheck: ## Typecheck backend (pyright) and frontend (tsc)
	cd $(BACKEND_DIR) && uv run pyright spend_assistant tests
	cd $(FRONTEND_DIR) && npm run typecheck

build: ## Build the frontend for production
	cd $(FRONTEND_DIR) && npm run build

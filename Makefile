.PHONY: help setup dev test lint clean build deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Setup development environment
	@echo "Setting up development environment..."
	poetry install --with dev
	@echo "Setup complete! Copy env.example to .env and add your OpenAI API key"

dev: ## Start development server
	@echo "Starting development server..."
	docker-compose down --remove-orphans
	docker-compose up --build

start: ## Start the application (without rebuild)
	@echo "Starting application..."
	docker-compose up

stop: ## Stop the application
	@echo "Stopping application..."
	docker-compose down

restart: ## Restart the application
	@echo "Restarting application..."
	docker-compose restart

logs: ## Show application logs
	@echo "Showing logs..."
	docker-compose logs -f api

test: ## Run tests
	@echo "Running tests..."
	poetry run pytest tests/ -v

lint: ## Run linting and formatting
	@echo "Running linting and formatting..."
	poetry run black app/ tests/
	poetry run ruff check app/ tests/ --fix
	poetry run mypy app/

clean: ## Clean up containers and volumes
	@echo "Cleaning up..."
	docker-compose down -v
	docker system prune -f

build: ## Build production Docker image
	@echo "Building production image..."
	docker build -t ai-invoice-agent:latest .

deploy: ## Deploy to Google Cloud Run
	@echo "Deploying to Google Cloud Run..."
	gcloud run deploy ai-invoice-agent \
		--source . \
		--platform managed \
		--region us-central1 \
		--allow-unauthenticated \
		--set-env-vars ENVIRONMENT=production,AI_PROVIDER=openai 
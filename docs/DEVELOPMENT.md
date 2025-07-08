# Development Guide

## Prerequisites

- **Python 3.11+**
- **Poetry** (dependency management)
- **Docker** (for containerized development)
- **OpenAI API Key**

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd ai-invoice-agent

# Setup development environment
make setup
```

### 2. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your OpenAI API key
nano .env
```

### 3. Start Development Server

```bash
# Using Docker (recommended)
make dev

# Or using Poetry directly
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/v1/

# Process invoice (replace with your PDF)
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@examples/sample-invoice.pdf"
```

## Project Structure

```
ai-invoice-agent/
├── app/                    # Application code
│   ├── api/               # FastAPI routes
│   │   ├── health.py      # Health check endpoints
│   │   └── invoice.py     # Invoice processing endpoints
│   ├── core/              # Core business logic
│   │   ├── config.py      # Configuration management
│   │   └── pdf_processor.py # PDF text extraction
│   ├── models/            # Pydantic data models
│   │   └── invoice.py     # Request/response models
│   ├── providers/         # AI providers
│   │   ├── base.py        # Abstract base class
│   │   └── openai_provider.py # OpenAI implementation
│   └── main.py            # FastAPI application
├── docs/                  # Documentation
├── examples/              # Example files
├── tests/                 # Test suite
├── Dockerfile             # Container definition
├── docker-compose.yml     # Development environment
├── pyproject.toml         # Poetry configuration
├── Makefile               # Development commands
└── .pre-commit-config.yaml # Code quality hooks
```

## Development Commands

### Using Makefile

```bash
# Show all available commands
make help

# Setup development environment
make setup

# Start development server
make dev

# Run tests
make test

# Run linting and formatting
make lint

# Clean up containers
make clean

# Build production image
make build

# Deploy to Google Cloud Run
make deploy
```

### Using Poetry Directly

```bash
# Install dependencies
poetry install

# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Run application
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest

# Run linting
poetry run black app/ tests/
poetry run ruff check app/ tests/ --fix
poetry run mypy app/
```

## Code Quality

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Linting and Formatting

- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Type checking

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_models.py

# Run with verbose output
poetry run pytest -v
```

## Adding New Features

### 1. New AI Provider

Create a new provider in `app/providers/`:

```python
# app/providers/claude_provider.py
from app.providers.base import AIProvider

class ClaudeProvider(AIProvider):
    async def extract_transactions(self, text: str) -> List[Transaction]:
        # Implementation here
        pass

    @property
    def provider_name(self) -> str:
        return "claude"
```

### 2. New Endpoint

Add new routes in `app/api/`:

```python
# app/api/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/v1", tags=["new-feature"])

@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "New feature"}
```

Register in `app/api/__init__.py`:

```python
from .new_feature import router as new_feature_router

__all__ = ["health_router", "invoice_router", "new_feature_router"]
```

### 3. New Data Model

Add models in `app/models/`:

```python
# app/models/new_model.py
from pydantic import BaseModel

class NewModel(BaseModel):
    field: str
```

## Debugging

### Local Development

```bash
# Enable debug mode
export DEBUG=true

# Run with debug logging
poetry run uvicorn app.main:app --reload --log-level debug
```

### Docker Development

```bash
# View logs
docker-compose logs -f

# Execute commands in container
docker-compose exec ai-invoice-agent bash

# Rebuild container
docker-compose build --no-cache
```

### Testing with Sample Data

```bash
# Create test PDF
# Add sample invoice PDF to examples/

# Test processing
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@examples/sample-invoice.pdf" \
  -H "Content-Type: multipart/form-data"
```

## Environment Variables

### Development (.env)

```env
# Environment
ENVIRONMENT=development
DEBUG=true

# AI Provider
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key

# File processing limits
MAX_FILE_SIZE=10485760
TIMEOUT_SECONDS=60
```

### Production

Set via Google Cloud Run:

```bash
gcloud run services update ai-invoice-agent \
  --set-env-vars ENVIRONMENT=production,DEBUG=false
```

## Performance Optimization

### Local Testing

```bash
# Test with larger files
# Monitor memory usage
docker stats

# Test concurrent requests
ab -n 100 -c 10 -p test.pdf -T multipart/form-data \
  http://localhost:8000/v1/process-invoice
```

### Profiling

```bash
# Install profiling tools
poetry add --group dev py-spy

# Profile application
py-spy record --format speedscope --output profile.speedscope \
  -- uvicorn app.main:app
```

## Troubleshooting

### Common Issues

1. **Poetry Installation**

   ```bash
   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Docker Issues**

   ```bash
   # Clean Docker
   docker system prune -a
   docker volume prune
   ```

3. **OpenAI API Issues**

   ```bash
   # Test API key
   curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.openai.com/v1/models
   ```

4. **PDF Processing Issues**

   ```bash
   # Check Tesseract installation
   tesseract --version

   # Test OCR
   tesseract test.png stdout -l por+eng
   ```

### Getting Help

1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `echo $OPENAI_API_KEY`
3. Test individual components
4. Check API documentation at `http://localhost:8000/docs`

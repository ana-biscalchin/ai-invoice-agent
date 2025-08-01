# Development Guide - AI Invoice Agent

> **Setup e workflow de desenvolvimento**

## Quick Setup

### Prerequisites

```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get install -y tesseract-ocr tesseract-ocr-por poppler-utils

# Python 3.11+
# Poetry or pip
```

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/ai-invoice-agent.git
cd ai-invoice-agent

# Install dependencies
poetry install
poetry shell

# Configure
cp env.example .env
# Add API keys to .env
```

### Configuration

```env
# Required (at least one)
OPENAI_API_KEY=sk-your-openai-key
DEEPSEEK_API_KEY=your-deepseek-key
GEMINI_API_KEY=your-gemini-key

# Optional
DEFAULT_AI_PROVIDER=openai
DEBUG=true
```

### Run

```bash
# Development
make dev

# Or directly
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker
docker-compose up -d
```

## Testing

```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=app --cov-report=html

# Specific test
poetry run pytest tests/test_models.py -v
```

## Development Workflow

### Code Quality

```bash
# Formatting
black app/ tests/

# Linting
ruff check app/ tests/

# Type checking
mypy app/
```

### Feature Development

```bash
# Create feature branch
git checkout -b feature/new-provider

# Development
# - Implement functionality
# - Write tests
# - Run tests locally
# - Code quality checks

# Commit
git add .
git commit -m "feat: add new provider support"
git push origin feature/new-provider
```

## Coding Standards

### Python Style

```python
# Follow PEP 8 + Black formatting
# Type hints required
from typing import List, Optional, Tuple

async def extract_transactions(
    self,
    text: str,
    institution: str
) -> Tuple[List[Transaction], float, str]:
    """Extract transactions from text."""
    pass
```

### Error Handling

```python
# Use specific exceptions
class InvalidPDFError(ValueError):
    """Raised when PDF cannot be processed."""
    pass

# Structured logging
logger.error(
    "Failed to extract transactions",
    extra={"provider": provider_name, "error": str(e)}
)

# HTTP exceptions
raise HTTPException(
    status_code=400,
    detail="Only PDF files are supported"
)
```

## Extensibility

### Adding New AI Provider

#### 1. Implement Interface

```python
# app/providers/claude.py
from app.providers.base import AIProvider

class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")

    @property
    def name(self) -> str:
        return "claude"

    async def extract_transactions(
        self,
        text: str,
        institution: str
    ) -> Tuple[List[Transaction], float, str]:
        # Implementation logic
        pass
```

#### 2. Register Provider

```python
# app/providers/__init__.py
from .claude import ClaudeProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "claude": ClaudeProvider,  # New
}
```

#### 3. Add Tests

```python
# tests/test_providers.py
def test_claude_provider_creation():
    provider = create_provider("claude", api_key="test")
    assert provider.name == "claude"
```

### Adding New Institution

#### 1. Detection Logic

```python
# app/utils.py
def _detect_institution(self, text: str) -> str:
    text_upper = text.upper()

    if any(pattern in text_upper for pattern in ["SANTANDER"]):
        return "SANTANDER"

    return "GENERIC"
```

#### 2. Processing Config

```python
# app/utils.py
def _get_institution_config(self, institution: str) -> dict:
    configs = {
        "SANTANDER": {
            "preserve_sections": ["RESUMO", "LANÇAMENTOS"],
            "remove_patterns": [r"^SAC SANTANDER.*"],
        }
    }
    return configs.get(institution, configs["GENERIC"])
```

## Debugging

### Local Debugging

```python
# Add detailed logs
import logging
logging.basicConfig(level=logging.DEBUG)

# Add breakpoints
import pdb; pdb.set_trace()
```

### API Debugging

```bash
# Verbose curl
curl -v -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@test.pdf" \
  -F "provider=openai"

# Health check
curl http://localhost:8000/health
```

## Project Structure

```
app/
├── main.py              # FastAPI app + routes
├── extractor.py         # Core extraction logic
├── models.py           # Pydantic models
├── utils.py            # PDF processing & validation
└── providers/          # AI agents
    ├── __init__.py     # Factory pattern
    ├── base.py         # Abstract interface
    ├── openai.py       # OpenAI agent
    ├── deepseek.py     # DeepSeek agent
    └── gemini.py       # Gemini agent
```

## Key Classes

```python
# Core processing pipeline
class TransactionExtractor:
    """Orchestrates the complete extraction process"""
    async def process_invoice(self, pdf_bytes, filename) -> InvoiceResponse

# PDF processing utilities
class PDFProcessor:
    """Handles PDF text extraction and institution detection"""
    def extract_text(self, pdf_bytes, filename) -> Tuple[str, str]

# AI provider interface
class AIProvider(ABC):
    """Abstract base for all AI providers"""
    async def extract_transactions(self, text, institution) -> Tuple[...]
```

## Resources

### Dependencies

- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **PyMuPDF**: PDF processing
- **Tesseract**: OCR
- **HTTPX**: Async HTTP client
- **Pytest**: Testing framework

### Tools

```bash
# Code quality
poetry add --group dev black ruff mypy

# Testing
poetry add --group dev pytest pytest-cov pytest-asyncio

# Debugging
poetry add --group dev ipdb
```

## Next Steps

### Learning Objectives

1. **Implement integration tests** end-to-end
2. **Add observability** (structured logging, metrics)
3. **Implement authentication** (API keys)
4. **Optimize performance** (caching, connection pooling)
5. **Add new providers** (Claude)
6. **Integration** with main finance system

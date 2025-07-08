# 🛠️ Development Guide - AI Invoice Agent

> **Setup e workflow de desenvolvimento para agentes de IA**

## 📖 Contexto de Desenvolvimento

Este projeto faz parte de um **estudo sobre agentes de IA** para construção de uma aplicação de gestão de finanças pessoais. O foco está em criar um microserviço especializado que demonstra implementação de agentes de IA com boas práticas de desenvolvimento.

## ⚡ Quick Setup

### **Pré-requisitos**

```bash
# Sistema
Python 3.11+
Docker (opcional)
Poetry ou pip

# Dependências do sistema (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    poppler-utils
```

### **Instalação**

```bash
# Clone do repositório
git clone https://github.com/your-org/ai-invoice-agent.git
cd ai-invoice-agent

# Opção 1: Poetry (recomendado)
poetry install
poetry shell

# Opção 2: pip + venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### **Configuração**

```bash
# Copiar template
cp env.example .env

# Configurar API keys (obrigatório)
nano .env
```

**Variáveis essenciais**:

```env
# API Keys (pelo menos uma)
OPENAI_API_KEY=sk-your-openai-key
DEEPSEEK_API_KEY=your-deepseek-key

# Configuração
DEFAULT_AI_PROVIDER=openai
ENVIRONMENT=development
DEBUG=true
```

### **Executar**

```bash
# Opção 1: Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Opção 2: Python direto
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Opção 3: Docker
docker-compose up -d

# Verificação
curl http://localhost:8000/health
```

## 🧪 Testing

### **Executar Testes**

```bash
# Todos os testes
poetry run pytest

# Com coverage
poetry run pytest --cov=app --cov-report=html

# Testes específicos
poetry run pytest tests/test_models.py -v

# Teste específico
poetry run pytest tests/test_api.py::test_process_invoice_success -v
```

### **Estrutura de Testes**

```
tests/
├── test_models.py          # Modelos Pydantic
├── test_utils.py           # PDF processing & validation
├── test_providers.py       # AI providers
├── test_extractor.py       # Core logic
├── test_api.py            # Endpoints
└── fixtures/              # Arquivos de teste
    ├── sample_caixa.pdf
    └── expected_results.json
```

### **Mocks e Fixtures**

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_openai_provider():
    provider = AsyncMock()
    provider.name = "openai"
    provider.extract_transactions.return_value = (
        [mock_transaction()], 100.0, "2025-02-20"
    )
    return provider

@pytest.fixture
def sample_pdf_bytes():
    with open("tests/fixtures/sample_caixa.pdf", "rb") as f:
        return f.read()
```

## 🔧 Development Workflow

### **Feature Development**

```bash
# 1. Criar feature branch
git checkout -b feature/novo-provider-claude

# 2. Desenvolvimento iterativo
# - Implementar funcionalidade
# - Escrever testes
# - Rodar testes localmente
# - Code quality checks

# 3. Commit e push
git add .
git commit -m "feat: add Claude provider support"
git push origin feature/novo-provider-claude
```

### **Code Quality**

```bash
# Formatação
black app/ tests/

# Linting
ruff check app/ tests/

# Type checking
mypy app/

# Ou tudo junto
poetry run pre-commit run --all-files
```

### **Testing Workflow**

```bash
# Durante desenvolvimento
poetry run pytest tests/test_providers.py::test_new_provider -v

# Antes do commit
poetry run pytest --cov=app

# CI/CD simulation
poetry run pytest && poetry run black --check app/ && poetry run ruff check app/
```

## 📝 Coding Standards

### **Python Style**

```python
# Seguir PEP 8 + Black formatting
# Type hints obrigatórios
from typing import List, Optional, Tuple

async def extract_transactions(
    self,
    text: str,
    institution: str
) -> Tuple[List[Transaction], float, str]:
    """
    Extract transactions from text.

    Args:
        text: Cleaned invoice text
        institution: Detected institution code

    Returns:
        Tuple of (transactions, total, due_date)

    Raises:
        ValueError: If extraction fails
    """
    pass
```

### **Error Handling**

```python
# Usar exceptions específicas
class InvalidPDFError(ValueError):
    """Raised when PDF cannot be processed."""
    pass

# Log de erros estruturado
logger.error(
    "Failed to extract transactions",
    extra={
        "provider": provider_name,
        "institution": institution,
        "error": str(e)
    }
)

# HTTP exceptions apropriadas
raise HTTPException(
    status_code=400,
    detail="Only PDF files are supported"
)
```

### **Async Best Practices**

```python
# Sempre async para I/O
async def process_invoice(self, pdf_bytes: bytes) -> InvoiceResponse:
    # Usar async context managers
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload)

    # Usar asyncio para concorrência se necessário
    tasks = [
        self.validate_transactions(transactions),
        self.calculate_confidence(transactions)
    ]
    results = await asyncio.gather(*tasks)
```

## 🔌 Extensibility Patterns

### **Adicionar Novo AI Provider**

#### **1. Implementar Interface**

```python
# app/providers/claude.py
from app.providers.base import AIProvider
from app.models import Transaction

class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        # ... initialization

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

#### **2. Registrar no Factory**

```python
# app/providers/__init__.py
from .claude import ClaudeProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "claude": ClaudeProvider,  # Novo
}
```

#### **3. Configurar Prompts**

```python
# app/providers/prompts.py
PROVIDER_ADJUSTMENTS = {
    "claude": {
        "extra_instructions": "Seja preciso e conciso...",
        "temperature": 0,
        "max_tokens": 2000
    }
}
```

#### **4. Testes**

```python
# tests/test_providers.py
def test_claude_provider_creation():
    provider = create_provider("claude", api_key="test")
    assert provider.name == "claude"

async def test_claude_extract_transactions():
    provider = ClaudeProvider(api_key="test")
    # Mock API response
    # Test extraction logic
```

### **Adicionar Nova Instituição**

#### **1. Detection Logic**

```python
# app/utils.py - PDFProcessor._detect_institution()
def _detect_institution(self, text: str) -> str:
    text_upper = text.upper()

    # Existing institutions...

    if any(pattern in text_upper for pattern in ["SANTANDER", "BANCO SANTANDER"]):
        return "SANTANDER"

    return "GENERIC"
```

#### **2. Processing Config**

```python
# app/utils.py - PDFProcessor._get_institution_config()
def _get_institution_config(self, institution: str) -> dict:
    configs = {
        # Existing configs...

        "SANTANDER": {
            "preserve_sections": ["RESUMO", "LANÇAMENTOS"],
            "remove_patterns": [r"^SAC SANTANDER.*"],
            "key_fields": ["Data", "Histórico", "Valor"]
        }
    }
    return configs.get(institution, configs["GENERIC"])
```

#### **3. Institution Prompts**

```python
# app/providers/prompts.py
INSTITUTION_PROMPTS = {
    # Existing prompts...

    "SANTANDER": """
    Você é um especialista em extrair dados de faturas do Santander.

    REGRAS ESPECÍFICAS PARA SANTANDER:
    - Formato: data + histórico + valor na mesma linha
    - Seções: RESUMO, LANÇAMENTOS, COMPRAS
    - Valores sempre precedidos por R$
    """
}
```

#### **4. Testes**

```python
# tests/test_utils.py
def test_santander_detection():
    text = "BANCO SANTANDER\nFATURA DE CARTÃO"
    processor = PDFProcessor()

    institution = processor._detect_institution(text)
    assert institution == "SANTANDER"

def test_santander_processing():
    # Test specific processing rules
    pass
```

## 🔍 Debugging

### **Local Debugging**

```python
# app/main.py - adicionar logs detalhados
import logging
logging.basicConfig(level=logging.DEBUG)

# Adicionar breakpoints
import pdb; pdb.set_trace()

# Ou usar debugger do IDE (VSCode: F5)
```

### **API Debugging**

```bash
# Logs detalhados
export DEBUG=true
python app/main.py

# Test com curl verbose
curl -v -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@test.pdf" \
  -F "provider=openai"

# Monitoring endpoints
curl http://localhost:8000/health
```

### **Provider Debugging**

```python
# Mock providers para testes isolados
class MockProvider(AIProvider):
    def __init__(self, mock_response):
        self.mock_response = mock_response

    async def extract_transactions(self, text, institution):
        return self.mock_response

# Usar em testes
mock_provider = MockProvider(expected_result)
extractor = TransactionExtractor()
extractor.ai_provider = mock_provider
```

## 🧩 Architecture Components

### **App Structure**

```
app/
├── main.py              # FastAPI app + routes
├── extractor.py         # Core extraction logic
├── models.py           # Pydantic models
├── utils.py            # PDF processing & validation
└── providers/          # AI agents
    ├── __init__.py     # Factory pattern
    ├── base.py         # Abstract interface
    ├── prompts.py      # Institution prompts
    ├── openai.py       # OpenAI agent
    └── deepseek.py     # DeepSeek agent
```

### **Key Classes**

```python
# Core processing pipeline
class TransactionExtractor:
    """Orchestrates the complete extraction process"""
    async def process_invoice(self, pdf_bytes, filename) -> InvoiceResponse

# PDF processing utilities
class PDFProcessor:
    """Handles PDF text extraction and institution detection"""
    def extract_text(self, pdf_bytes, filename) -> Tuple[str, str]

# Business validation
class TransactionValidator:
    """Applies business rules and calculates confidence score"""
    def run_all(self, transactions, invoice_total) -> dict

# AI provider interface
class AIProvider(ABC):
    """Abstract base for all AI providers"""
    async def extract_transactions(self, text, institution) -> Tuple[...]
```

## 🚀 Performance Tips

### **Development Performance**

```python
# Use small test files during development
# Cache provider responses for repeated tests
# Use async/await properly for I/O operations
# Profile with py-spy if needed

# Example: caching for development
if ENVIRONMENT == "development":
    @lru_cache(maxsize=10)
    def cached_ai_call(text_hash, provider):
        # Cache expensive AI calls during dev
        pass
```

### **Testing Performance**

```bash
# Run specific test modules
poetry run pytest tests/test_utils.py

# Skip slow integration tests during development
poetry run pytest -m "not slow"

# Use parallel testing
poetry run pytest -n auto
```

## 📚 Resources

### **Dependencies**

- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **PyMuPDF**: PDF processing
- **Tesseract**: OCR
- **HTTPX**: Async HTTP client
- **Pytest**: Testing framework

### **Learning Resources**

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Async Python**: https://docs.python.org/3/library/asyncio.html
- **Pydantic**: https://docs.pydantic.dev/
- **OpenAI API**: https://platform.openai.com/docs/
- **DeepSeek API**: https://platform.deepseek.com/docs/

### **Tools**

```bash
# Code quality
poetry add --group dev black ruff mypy pre-commit

# Testing
poetry add --group dev pytest pytest-cov pytest-asyncio

# Debugging
poetry add --group dev ipdb py-spy

# Documentation
poetry add --group dev mkdocs mkdocs-material
```

## 🎓 Next Steps

### **Learning Objectives**

1. **Implement testes de integração** end-to-end
2. **Add observability** (structured logging, metrics)
3. **Implement authentication** (API keys)
4. **Optimize performance** (caching, connection pooling)
5. **Add new providers** (Claude, Gemini)
6. **Integration** com sistema principal de finanças

### **Development Roadmap**

- [ ] **v1.1**: Testes de integração completos
- [ ] **v1.2**: Structured logging e metrics
- [ ] **v1.3**: Authentication e rate limiting
- [ ] **v2.0**: Async processing e webhooks
- [ ] **v2.1**: Batch processing
- [ ] **v2.2**: ML model training

---

Este guia fornece as **ferramentas essenciais** para desenvolvimento eficiente do AI Invoice Agent, focando em **produtividade** e **qualidade de código**.

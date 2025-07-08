# 🛠️ Development Guide - AI Invoice Agent

> **Guia de desenvolvimento para o estudo de agentes de IA aplicados a finanças pessoais**

## 📖 Contexto de Desenvolvimento

Este projeto faz parte de um **estudo sobre agentes de IA** para construção de uma aplicação de gestão de finanças pessoais. O foco está em criar um microserviço especializado que demonstra:

- **Implementação de agentes de IA** com diferentes providers
- **Arquitetura de microserviços** com responsabilidade única
- **Boas práticas de Python moderno** e FastAPI
- **Preparação para integração** em sistema maior

## 🎯 Objetivos de Aprendizado

### **AI Agents**

- ✅ Implementar múltiplos providers (OpenAI, DeepSeek)
- ✅ Prompt engineering específico por contexto
- ✅ Error handling e retry logic
- ✅ Response validation e parsing

### **Microservice Architecture**

- ✅ Single responsibility principle
- ✅ Stateless design
- ✅ Health checks para orquestração
- ✅ Container-ready deployment

### **Integration Patterns**

- ✅ RESTful API design
- ✅ Structured error handling
- ✅ Monitoring e observability
- ✅ Extensible provider pattern

## 🏗️ Estrutura Simplificada

### **Arquitetura Atual**

```
ai-invoice-agent/
├── app/
│   ├── main.py              # 🌐 FastAPI app + routes
│   ├── extractor.py         # 🧠 Core extraction logic
│   ├── models.py           # 📊 Pydantic models
│   ├── utils.py            # 🛠️ PDF processing & validation
│   └── providers/          # 🤖 AI agents
│       ├── __init__.py     # 🏭 Factory pattern
│       ├── base.py         # 📋 Abstract interface
│       ├── prompts.py      # 💬 Institution prompts
│       ├── openai.py       # 🧠 OpenAI agent
│       └── deepseek.py     # 🚀 DeepSeek agent
├── docs/                   # 📚 Documentation
├── tests/                  # 🧪 Test suite
├── examples/               # 📄 Sample files
├── docker-compose.yml      # 🐳 Development environment
├── Dockerfile              # 🐳 Container definition
└── pyproject.toml          # 📦 Dependencies & config
```

### **Design Principles**

1. **KISS**: Keep It Simple, Stupid
2. **DRY**: Don't Repeat Yourself
3. **SOLID**: Single responsibility, Open/closed, etc.
4. **Clean Code**: Self-documenting, testable
5. **Async-First**: Non-blocking operations

## ⚡ Quick Setup

### **1. Pré-requisitos**

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

### **2. Clone e Install**

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
# ou: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### **3. Configuração**

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
MAX_FILE_SIZE=10485760
```

### **4. Development Server**

```bash
# Opção 1: Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Opção 2: Python direto
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Opção 3: Script direto
python app/main.py

# Opção 4: Docker
docker-compose up -d
```

### **5. Verificação**

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/v1/

# Docs (se DEBUG=true)
open http://localhost:8000/docs
```

## 🧪 Testing

### **Estrutura de Testes**

```
tests/
├── test_models.py          # Testes dos modelos Pydantic
├── test_utils.py           # Testes PDF processing
├── test_providers.py       # Testes AI providers
├── test_extractor.py       # Testes core logic
├── test_api.py            # Testes endpoints
└── fixtures/              # Arquivos de teste
    ├── sample_caixa.pdf
    ├── sample_nubank.pdf
    └── expected_results.json
```

### **Executar Testes**

```bash
# Todos os testes
poetry run pytest

# Com coverage
poetry run pytest --cov=app --cov-report=html

# Testes específicos
poetry run pytest tests/test_models.py -v

# Testes por categoria
poetry run pytest -m "unit"      # Testes unitários
poetry run pytest -m "integration"  # Testes integração

# Teste específico
poetry run pytest tests/test_api.py::test_process_invoice_success -v
```

### **Mocks para Development**

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

### **1. Feature Development**

```bash
# Criar feature branch
git checkout -b feature/novo-provider-claude

# Desenvolvimento
# 1. Implementar interface (providers/claude.py)
# 2. Adicionar ao factory (providers/__init__.py)
# 3. Configurar prompts (providers/prompts.py)
# 4. Escrever testes
# 5. Atualizar documentação

# Commit e push
git add .
git commit -m "feat: add Claude provider support"
git push origin feature/novo-provider-claude
```

### **2. Code Quality**

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

### **3. Testing Workflow**

```bash
# Durante desenvolvimento
poetry run pytest tests/test_providers.py::test_claude_provider -v

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
        # Initialization logic
        pass

    @property
    def name(self) -> str:
        return "claude"

    async def extract_transactions(
        self,
        text: str,
        institution: str
    ) -> Tuple[List[Transaction], float, str]:
        # Implementation
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
# app/utils.py
def _detect_institution(self, text: str) -> str:
    text_upper = text.upper()

    # Existing institutions...

    if any(pattern in text_upper for pattern in ["SANTANDER", "BANCO SANTANDER"]):
        return "SANTANDER"

    return "GENERIC"
```

#### **2. Institution Config**

```python
# app/utils.py
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

    INSTRUÇÕES:
    1. Extraia TODAS as transações...
    """
}
```

## 🧩 Architecture Decisions

### **Por que Strategy Pattern?**

```python
# Facilita adição de novos providers
# Permite teste isolado de cada provider
# Runtime selection based on user preference
# Consistent interface across implementations

# Bad: Hardcoded provider
if provider == "openai":
    result = openai_extract(text)
elif provider == "deepseek":
    result = deepseek_extract(text)

# Good: Strategy pattern
provider = create_provider(provider_name)
result = await provider.extract_transactions(text, institution)
```

### **Por que Factory Pattern?**

```python
# Centraliza criação de providers
# Valida provider names
# Permite dependency injection
# Facilita mocking em testes

def create_provider(name: str, **kwargs) -> AIProvider:
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider '{name}'")
    return PROVIDERS[name](**kwargs)
```

### **Por que Consolidar em main.py?**

```python
# Microserviço simples não precisa de múltiplos módulos de API
# Facilita navegação e debugging
# Reduz complexity overhead
# Melhora performance (menos imports)

# Tradeoff: Crescimento do arquivo vs simplicidade
# Decisão: Para este escopo, simplicidade wins
```

## 📊 Performance Considerations

### **Memory Management**

```python
# PDFs processados em memória apenas
# Não persistir arquivos no disk
# Limitar tamanho de texto para AI (8KB)
# Usar streaming para large responses

def extract_text(self, pdf_bytes: bytes) -> str:
    # Não salvar arquivo temporário
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    # ... processing
    doc.close()  # Liberar memória
```

### **Concurrency**

```python
# FastAPI handles concurrency automaticamente
# Usar async/await para I/O operations
# Connection pooling para HTTP clients
# Timeout protection

async with httpx.AsyncClient(
    timeout=60,
    limits=httpx.Limits(max_connections=20)
) as client:
    response = await client.post(url, json=payload)
```

### **Error Recovery**

```python
# Retry com exponential backoff
for attempt in range(max_retries):
    try:
        return await self._make_api_call()
    except TransientError:
        if attempt == max_retries - 1:
            raise
        await asyncio.sleep(retry_delay * (attempt + 1))
```

## 🔍 Debugging

### **Local Debugging**

```python
# app/main.py - adicionar logs detalhados
import logging
logging.basicConfig(level=logging.DEBUG)

# Adicionar breakpoints
import pdb; pdb.set_trace()

# Ou usar debugger do IDE
# VSCode: F5 com launch.json configurado
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

## 📈 Monitoring & Observability

### **Metrics Collection**

```python
# app/extractor.py
import time

async def process_invoice(self, pdf_bytes: bytes) -> InvoiceResponse:
    start_time = time.time()

    try:
        # Processing logic
        result = await self._process()

        # Success metrics
        self._record_success_metrics(time.time() - start_time)
        return result

    except Exception as e:
        # Error metrics
        self._record_error_metrics(e, time.time() - start_time)
        raise
```

### **Health Checks**

```python
# Detailed health information
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": API_VERSION,
        "environment": ENVIRONMENT,
        "ai_provider": DEFAULT_AI_PROVIDER,
        # Adicionar checks específicos se necessário
        "dependencies": {
            "tesseract": check_tesseract_available(),
            "pymupdf": check_pymupdf_working()
        }
    }
```

## 🚀 Deployment

### **Docker Development**

```bash
# Build
docker build -t ai-invoice-agent:dev .

# Run with env file
docker run --env-file .env -p 8000:8000 ai-invoice-agent:dev

# Docker compose
docker-compose up -d
```

### **Production Considerations**

```python
# app/main.py
# Desabilitar debug em produção
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# Configurar CORS apropriadamente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"] if not DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

## 🎓 Learning Path

### **Próximos Passos**

1. **Implementar testes de integração** end-to-end
2. **Adicionar observability** (metrics, tracing)
3. **Implementar rate limiting** e authentication
4. **Otimizar performance** com caching
5. **Adicionar novos providers** (Claude, Gemini)
6. **Integrar com sistema principal** de finanças

### **Recursos de Estudo**

- **FastAPI**: https://fastapi.tiangolo.com/
- **Async Python**: https://docs.python.org/3/library/asyncio.html
- **Pydantic**: https://docs.pydantic.dev/
- **PyMuPDF**: https://pymupdf.readthedocs.io/
- **OpenAI API**: https://platform.openai.com/docs/
- **DeepSeek API**: https://platform.deepseek.com/docs/

---

Este projeto serve como **base prática** para aprender implementação de agentes de IA, arquitetura de microserviços e boas práticas de desenvolvimento Python moderno, preparando para integração em sistemas maiores de gestão financeira.

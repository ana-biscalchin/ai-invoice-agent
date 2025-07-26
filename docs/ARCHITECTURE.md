# Architecture - AI Invoice Agent

> **Design patterns e decisões arquiteturais**

## Overview

Microserviço que implementa **agentes de IA especializados** para extração de dados financeiros, usando padrões arquiteturais modernos.

### Design Principles

- **Single Responsibility**: Cada classe tem uma responsabilidade clara
- **Strategy Pattern**: Múltiplos providers AI intercambiáveis
- **Factory Pattern**: Criação centralizada de providers
- **Separation of Concerns**: Camadas bem definidas

## Architecture

### Service API Pattern

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  Core Business  │    │   AI Agents     │
│   Routes        │───▶│   Logic         │───▶│   (Strategy)    │
│   (main.py)     │    │  (extractor.py) │    │   (providers/)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Input/Output  │    │   Utilities     │    │   Data Models   │
│   Validation    │    │   (utils.py)    │    │   (models.py)   │
│   Error Handle  │    │   PDF + Valid   │    │   Pydantic      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

```
PDF Upload → Text Extraction → Institution Detection → AI Processing → Validation → Response
```

## Design Patterns

### 1. Strategy Pattern - AI Providers

**Interface**:

```python
class AIProvider(ABC):
    @abstractmethod
    async def extract_transactions(self, text: str, institution: str) -> Tuple[...]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass
```

**Implementations**:

- `OpenAIProvider`: GPT-4o-mini, structured output
- `DeepSeekProvider`: Custom parsing, retry logic
- `GeminiProvider`: Gemini 1.5 Flash

### 2. Factory Pattern - Provider Creation

```python
def create_provider(name: str, **kwargs) -> AIProvider:
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider '{name}'")
    return PROVIDERS[name](**kwargs)
```

### 3. Institution-Specific Processing

```python
def _clean_text_by_institution(self, text: str, institution: str) -> str:
    # 1. Get institution config
    # 2. Apply specific cleaning rules
    # 3. Preserve important sections
    # 4. Remove noise patterns
```

## Layers

### Presentation Layer (main.py)

- HTTP request/response handling
- Input validation
- Provider selection logic
- Error handling

### Business Logic Layer (extractor.py)

- Orquestração do processo completo
- Provider integration
- Metadata collection

### Utilities Layer (utils.py)

- PDF processing (PyMuPDF + OCR)
- Institution detection
- Text cleaning
- Business validation

### Data Layer (models.py)

- Request/response models
- Data validation
- Type safety

## AI Agents

### Provider Comparison

| Aspect     | OpenAI          | DeepSeek      | Gemini           |
| ---------- | --------------- | ------------- | ---------------- |
| **Model**  | GPT-4o-mini     | deepseek-chat | gemini-1.5-flash |
| **Output** | Structured JSON | Text parsing  | Structured JSON  |
| **Cost**   | ~$0.15/1M       | ~$0.27/1M     | ~$0.075/1M       |

### Provider Selection

```python
# Runtime selection
selected_provider = provider or DEFAULT_AI_PROVIDER

# Fallback strategy (future)
for provider_name in [selected_provider, "openai", "deepseek", "gemini"]:
    try:
        return await self._try_provider(provider_name)
    except Exception:
        continue
```

## Institution Processing

### Detection Strategy

```python
def _detect_institution(self, text: str) -> str:
    # Priority-based detection
    # 1. Exact matches (CARTÕES CAIXA)
    # 2. Partial matches (NUBANK)
    # 3. Fallback (GENERIC)
```

### Processing Configs

```python
INSTITUTION_CONFIGS = {
    "CAIXA": {
        "preserve_sections": ["RESUMO", "LANÇAMENTOS"],
        "remove_patterns": [r"^CENTRAL.*", r"^SAC.*"],
        "value_format": "ends_with_D_or_C"
    }
}
```

## Validation

### Multi-Layer Validation

1. **Input Validation**: File type, size limits
2. **Business Validation**: Transaction rules, date consistency
3. **Confidence Scoring**: Quality assessment

### Validation Rules

- Required fields validation
- Date consistency checks
- Amount range validation
- Sum reconciliation

## Extensibility

### Adding New AI Provider

```python
# 1. Implement AIProvider interface
# 2. Register in PROVIDERS dict
# 3. Configure prompts
# 4. Add tests
```

### Adding New Institution

```python
# 1. Add detection pattern
# 2. Configure processing rules
# 3. Add institution prompts
# 4. Test with sample PDFs
```

## Performance

### Optimization Strategies

- **Text Truncation**: 8KB limit para AI APIs
- **OCR Fallback**: Only when PyMuPDF fails
- **Async Processing**: Non-blocking I/O
- **Connection Pooling**: HTTP client reuse

### Scalability

- **Stateless**: Easy horizontal scaling
- **Container-Ready**: Docker + K8s support
- **Health Checks**: Liveness + readiness

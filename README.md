# 🚀 AI Invoice Agent

> **Microserviço para extração automática de transações de faturas via agentes de IA**

Processa PDFs de faturas de cartão de crédito e extrai dados estruturados usando OpenAI ou DeepSeek. Projeto de estudo sobre **agentes de IA** aplicados a gestão de finanças pessoais.

## ✨ Features

- 📄 **PDF Processing**: Texto + OCR fallback
- 🏦 **Multi-bank**: Caixa, Nubank, Banco do Brasil
- 🤖 **AI Agents**: OpenAI e DeepSeek
- ✅ **Validation**: 7 regras de negócio + confidence scoring
- 🐳 **Container-Ready**: Docker + Kubernetes

## ⚡ Quick Start

```bash
# 1. Setup
git clone https://github.com/your-org/ai-invoice-agent.git
cd ai-invoice-agent
poetry install
cp env.example .env
# Adicionar OPENAI_API_KEY no .env

# 2. Run
poetry run uvicorn app.main:app --reload
# or: docker-compose up -d

# 3. Use
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@fatura.pdf" \
  -F "provider=openai"
```

## 📁 Estrutura

```
app/
├── main.py              # FastAPI + routes
├── extractor.py         # Core logic
├── models.py           # Pydantic models
├── utils.py            # PDF + validation
└── providers/          # AI agents (Strategy Pattern)
```

## 🏦 Bancos Suportados

| Banco           | Código            |
| --------------- | ----------------- |
| Caixa Econômica | `CAIXA`           |
| Nubank          | `NUBANK`          |


## 📚 Documentação

| Doc                                      | Descrição                        |
| ---------------------------------------- | -------------------------------- |
| **[API Reference](docs/API.md)**         | Endpoints, modelos, exemplos     |
| **[Architecture](docs/ARCHITECTURE.md)** | Design patterns, decisões        |
| **[Development](docs/DEVELOPMENT.md)**   | Setup, workflow, extensibilidade |

## 🔧 Configuração

```env
# Obrigatório (pelo menos um)
OPENAI_API_KEY=sk-your-key
DEEPSEEK_API_KEY=your-key

# Opcional
DEFAULT_AI_PROVIDER=openai
ENVIRONMENT=development
```

## 🚀 Deploy

```bash
# Docker
docker build -t ai-invoice-agent .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key ai-invoice-agent
```

## 🔗 Integração

```python
response = requests.post(
    "http://ai-agent:8000/v1/process-invoice",
    files={"file": pdf_file}
)

transactions = response.json()["transactions"]
confidence = response.json()["metadata"]["confidence_score"]

if confidence > 0.8:
    import_transactions(transactions)
```

---

# 🚀 AI Invoice Agent

> **Microservice for automatic credit card invoice transaction extraction via AI agents**

Processes credit card invoice PDFs and extracts structured data using OpenAI or DeepSeek. Study project on **AI agents** applied to personal finance management.

## ✨ Features

- 📄 **PDF Processing**: Text + OCR fallback
- 🏦 **Multi-bank**: Caixa, Nubank, Banco do Brasil
- 🤖 **AI Agents**: OpenAI and DeepSeek
- ✅ **Validation**: 7 business rules + confidence scoring
- 🐳 **Container-Ready**: Docker + Kubernetes

## ⚡ Quick Start

```bash
# 1. Setup
git clone https://github.com/your-org/ai-invoice-agent.git
cd ai-invoice-agent
poetry install
cp env.example .env
# Add OPENAI_API_KEY to .env

# 2. Run
poetry run uvicorn app.main:app --reload
# or: docker-compose up -d

# 3. Use
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@invoice.pdf" \
  -F "provider=openai"
```

## 📁 Structure

```
app/
├── main.py              # FastAPI + routes
├── extractor.py         # Core logic
├── models.py           # Pydantic models
├── utils.py            # PDF + validation
└── providers/          # AI agents (Strategy Pattern)
```

## 🏦 Supported Banks

| Bank            | Code              |
| --------------- | ----------------- |
| Caixa Econômica | `CAIXA`           |
| Nubank          | `NUBANK`          |


## 📚 Documentation

| Doc                                      | Description                    |
| ---------------------------------------- | ------------------------------ |
| **[API Reference](docs/API.md)**         | Endpoints, models, examples    |
| **[Architecture](docs/ARCHITECTURE.md)** | Design patterns, decisions     |
| **[Development](docs/DEVELOPMENT.md)**   | Setup, workflow, extensibility |

## 🔧 Configuration

```env
# Required (at least one)
OPENAI_API_KEY=sk-your-key
DEEPSEEK_API_KEY=your-key

# Optional
DEFAULT_AI_PROVIDER=openai
ENVIRONMENT=development
```

## 🚀 Deploy

```bash
# Docker
docker build -t ai-invoice-agent .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key ai-invoice-agent

# Cloud: Google Cloud Run, AWS Fargate, Kubernetes
```

## 🔗 Integration

```python
response = requests.post(
    "http://ai-agent:8000/v1/process-invoice",
    files={"file": pdf_file}
)

transactions = response.json()["transactions"]
confidence = response.json()["metadata"]["confidence_score"]

if confidence > 0.8:
    import_transactions(transactions)
```

## 📄 License

MIT License

---

**Built for studying AI agents in personal finance applications** 💰

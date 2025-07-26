# AI Invoice Agent

> **Microserviço para extração automática de transações de faturas via IA**

Processa PDFs de faturas de cartão de crédito e extrai dados estruturados usando OpenAI, DeepSeek ou Gemini.

## Sobre o Projeto

Este é um **projeto de estudos** sobre agentes de IA aplicados a gestão de finanças pessoais. O microserviço foi desenvolvido para servir como **componente especializado** do projeto principal [Finances](https://github.com/ana-biscalchin/finances) - um sistema completo de gestão financeira pessoal.

### Integração com Finances

O AI Invoice Agent fornece transações estruturadas para a API do projeto Finances, permitindo:

- **Importação automática** de faturas de cartão de crédito
- **Extração inteligente** de dados via IA
- **Validação e categorização** automática de transações
- **Integração seamless** com o sistema principal

## Quick Start

```bash
# Setup
git clone https://github.com/your-org/ai-invoice-agent.git
cd ai-invoice-agent
poetry install
cp env.example .env
# Adicionar OPENAI_API_KEY no .env

# Run
make dev

# Use
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@fatura.pdf"
```

## Configuration

```env
# Required (at least one)
OPENAI_API_KEY=sk-your-key
DEEPSEEK_API_KEY=your-key
GEMINI_API_KEY=your-key

# Optional
DEFAULT_AI_PROVIDER=openai
```

## Supported Banks

- Caixa Econômica
- Nubank
- Banco do Brasil
- Others (generic)

## AI Providers

| Provider | Model            | Cost       |
| -------- | ---------------- | ---------- |
| OpenAI   | GPT-4o-mini      | ~$0.15/1M  |
| DeepSeek | deepseek-chat    | ~$0.27/1M  |
| Gemini   | gemini-1.5-flash | ~$0.075/1M |

## Documentation

- [API Reference](docs/API.md)
- [Development Guide](docs/DEVELOPMENT.md)

## Integration Example

```python
# Integration with Finances project
import requests

def import_invoice_to_finances(pdf_file):
    # 1. Process PDF with AI Agent
    ai_response = requests.post(
        "http://ai-agent:8000/v1/process-invoice",
        files={"file": pdf_file}
    )

    transactions = ai_response.json()["transactions"]
    confidence = ai_response.json()["metadata"]["confidence_score"]

    # 2. Import to Finances if confidence is high
    if confidence > 0.8:
        finances_response = requests.post(
            "http://finances-api:3000/api/transactions/bulk",
            json={"transactions": transactions}
        )
        return finances_response.json()

    return {"status": "low_confidence", "confidence": confidence}
```

---

# AI Invoice Agent

> **Microservice for automatic credit card invoice transaction extraction via AI**

Processes credit card invoice PDFs and extracts structured data using OpenAI, DeepSeek or Gemini.

## About the Project

This is a **study project** about AI agents applied to personal finance management. The microservice was developed to serve as a **specialized component** of the main [Finances](https://github.com/ana-biscalchin/finances) project - a complete personal finance management system.

### Integration with Finances

The AI Invoice Agent provides structured transactions to the Finances project API, enabling:

- **Automatic import** of credit card invoices
- **Intelligent extraction** of data via AI
- **Automatic validation and categorization** of transactions
- **Seamless integration** with the main system

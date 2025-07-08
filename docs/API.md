# 📚 API Reference - AI Invoice Agent

> **RESTful API para processamento de faturas via agentes de IA**

## 🎯 Overview

API especializada em extrair transações estruturadas de PDFs de faturas de cartão de crédito usando agentes de IA (OpenAI, DeepSeek).

### **Base URLs**

```
Local:      http://localhost:8000
Produção:   https://your-domain.com
```

### **Content Types**

- Request: `multipart/form-data` (upload) ou `application/json`
- Response: `application/json`

## 🔗 Endpoints

### **Root Information**

#### `GET /`

Informações básicas da aplicação.

```json
{
  "message": "AI Invoice Agent",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health",
  "api_info": "/v1/"
}
```

#### `GET /v1/`

Informações da API v1.

```json
{
  "name": "AI Invoice Agent",
  "version": "0.1.0",
  "description": "Simplified microservice for extracting transactions from credit card invoices",
  "endpoints": {
    "process_invoice": "POST /v1/process-invoice",
    "health": "GET /health",
    "ready": "GET /health/ready"
  }
}
```

### **Health Checks**

#### `GET /health`

Status detalhado do serviço.

```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T22:29:00.439862",
  "version": "0.1.0",
  "environment": "development",
  "ai_provider": "openai"
}
```

#### `GET /health/ready`

Readiness probe para containers.

```json
{
  "status": "ready",
  "timestamp": "2025-01-08T22:29:00.439862"
}
```

### **Invoice Processing**

#### `POST /v1/process-invoice`

**Endpoint principal** - Processa PDF e extrai transações.

**Request:**

```http
POST /v1/process-invoice
Content-Type: multipart/form-data

file: [PDF File]               # obrigatório
provider: "openai"|"deepseek"  # opcional
```

**Validation:**

- ✅ Apenas arquivos PDF
- ✅ Tamanho máximo: 10MB
- ✅ Provider válido: `openai` ou `deepseek`

**Response (200 - Success):**

```json
{
  "transactions": [
    {
      "date": "2025-01-15",
      "description": "UBER TRIP 001",
      "amount": 25.5,
      "type": "debit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 25.5,
      "due_date": "2025-02-20",
      "category": "transport"
    }
  ],
  "metadata": {
    "processing_time_ms": 1250,
    "total_transactions": 15,
    "confidence_score": 0.95,
    "provider": "openai",
    "institution": "CAIXA"
  },
  "errors": null
}
```

**Error Responses:**

```json
// 400 - Bad Request
{"detail": "Only PDF files are supported"}

// 413 - Payload Too Large
{"detail": "File too large. Maximum size is 10485760 bytes"}

// 422 - Unprocessable Entity
{"detail": "Could not extract text from PDF"}

// 500 - Internal Server Error
{"detail": "Internal processing error"}
```

## 📊 Data Models

### **Transaction**

```typescript
interface Transaction {
  date: string; // YYYY-MM-DD
  description: string; // Transaction description
  amount: number; // Amount in BRL (always positive)
  type: "debit" | "credit"; // Transaction type
  installments: number; // Number of installments (≥1)
  current_installment: number; // Current installment (≥1)
  total_purchase_amount: number; // Total purchase amount
  due_date: string; // Invoice due date (YYYY-MM-DD)
  category?: string; // Optional category
}
```

**Field Rules:**

- `date`: ISO format, not future, not after due_date
- `description`: 1-500 characters, required
- `amount`: 0.01 ≤ amount ≤ 100,000.00
- `installments`: If > 1, total_purchase_amount = amount × installments
- `due_date`: Consistent across all transactions

### **ProcessingMetadata**

```typescript
interface ProcessingMetadata {
  processing_time_ms: number; // Processing duration
  total_transactions: number; // Count of extracted transactions
  confidence_score: number; // AI confidence (0.0-1.0)
  provider: string; // AI provider used ("openai"|"deepseek")
  institution: string; // Detected institution
}
```

**Confidence Score:**

- `0.9-1.0`: Excelente qualidade
- `0.8-0.9`: Boa qualidade
- `0.7-0.8`: Qualidade média
- `< 0.7`: Revisar manualmente

### **InvoiceResponse**

```typescript
interface InvoiceResponse {
  transactions: Transaction[]; // Extracted transactions
  metadata: ProcessingMetadata; // Processing information
  errors?: string[] | null; // Validation errors (if any)
}
```

## 🏦 Instituições Suportadas

| Código            | Nome            | Características                   |
| ----------------- | --------------- | --------------------------------- |
| `CAIXA`           | Caixa Econômica | Valores com D/C, linhas separadas |
| `NUBANK`          | Nubank          | Formato compacto, valores em R$   |
| `BANCO DO BRASIL` | Banco do Brasil | Formato estruturado               |
| `BRADESCO`        | Bradesco        | Padrão Bradescard                 |
| `ITAU`            | Itaú            | Formato Credicard                 |
| `GENERIC`         | Outros bancos   | Regras genéricas                  |

## 🤖 AI Providers

### **OpenAI** (Recomendado)

```json
{
  "provider": "openai",
  "model": "gpt-4o-mini",
  "cost": "~$0.15/1M tokens",
  "strengths": ["Brazilian context", "Structured output", "Consistency"]
}
```

### **DeepSeek** (Alternativa)

```json
{
  "provider": "deepseek",
  "model": "deepseek-chat",
  "cost": "~$0.27/1M tokens",
  "strengths": ["Complex text", "Multilingual", "Cost-effective"]
}
```

**Selection:**

- **Default**: Valor de `DEFAULT_AI_PROVIDER` (env var)
- **Override**: Via parâmetro `provider` no request
- **Fallback**: Retry logic em caso de falha

## 🚀 Usage Examples

### **cURL**

```bash
# Basic upload
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@fatura.pdf"

# With specific provider
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@fatura_caixa.pdf" \
  -F "provider=openai"

# Health check
curl http://localhost:8000/health
```

### **Python**

```python
import requests

def process_invoice(file_path, provider=None):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'provider': provider} if provider else {}

        response = requests.post(
            'http://localhost:8000/v1/process-invoice',
            files=files,
            data=data
        )

    return response.json()

# Usage
result = process_invoice('fatura.pdf', 'openai')
print(f"Extracted {len(result['transactions'])} transactions")
print(f"Confidence: {result['metadata']['confidence_score']:.2%}")

for tx in result['transactions']:
    print(f"{tx['date']}: {tx['description']} - R$ {tx['amount']}")
```

### **JavaScript**

```javascript
async function processInvoice(file, provider = null) {
  const formData = new FormData();
  formData.append("file", file);
  if (provider) formData.append("provider", provider);

  const response = await fetch("/v1/process-invoice", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.json();
}

// Usage
document.getElementById("file-input").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  try {
    const result = await processInvoice(file, "deepseek");
    console.log("Transactions:", result.transactions);
    console.log("Confidence:", result.metadata.confidence_score);
  } catch (error) {
    console.error("Error:", error.message);
  }
});
```

### **Integration Example**

```python
class FinanceApp:
    def __init__(self, ai_agent_url):
        self.ai_agent_url = ai_agent_url

    def import_invoice(self, pdf_file):
        # Process via AI Agent
        response = requests.post(
            f"{self.ai_agent_url}/v1/process-invoice",
            files={'file': pdf_file}
        )

        if response.status_code != 200:
            raise Exception(f"Processing failed: {response.text}")

        result = response.json()

        # Validate confidence
        if result['metadata']['confidence_score'] < 0.8:
            return self.request_manual_review(result)

        # Import transactions
        for tx in result['transactions']:
            self.save_transaction(tx)

        return {
            'status': 'success',
            'imported': len(result['transactions']),
            'confidence': result['metadata']['confidence_score']
        }
```

## ✅ Validation Rules

### **Input Validation**

1. **File Type**: Apenas PDF files
2. **File Size**: Máximo 10MB
3. **Provider**: Apenas `openai` ou `deepseek`

### **Business Validation**

1. **Required Fields**: date, description, amount obrigatórios
2. **No Duplicates**: Não permitir transações idênticas
3. **Valid Dates**: Datas não podem ser futuras ou após vencimento
4. **Amount Range**: R$ 0,01 a R$ 100.000,00
5. **Installments Logic**: Se parcelas > 1, validar valor total
6. **Due Date Consistency**: Mesmo vencimento para todas as transações
7. **Sum Validation**: Soma das transações ≈ total da fatura (±R$ 0,01)

### **Error Handling**

```python
# Validation errors são retornados no campo 'errors'
{
  "transactions": [...],
  "metadata": {...},
  "errors": [
    "Transaction 1: Amount cannot be negative",
    "Transaction 5: Date is after due date",
    "Sum mismatch: calculated R$ 120.45, expected R$ 120.50"
  ]
}
```

## 📈 Rate Limits & Quotas

### **Current Limits**

- ❌ **Rate limiting**: Não implementado
- ✅ **File size**: 10MB máximo
- ✅ **Timeout**: 60 segundos por request
- ✅ **Concurrent**: Até ~80 requests simultâneos

### **Planned (v2)**

- 🔮 **Rate limiting**: 100 requests/hora por IP
- 🔮 **Authentication**: API keys
- 🔮 **Quotas**: Baseadas em subscription

## 🔄 HTTP Status Codes

| Code  | Description           | When                                |
| ----- | --------------------- | ----------------------------------- |
| `200` | OK                    | Processamento bem-sucedido          |
| `400` | Bad Request           | Arquivo inválido, provider inválido |
| `413` | Payload Too Large     | Arquivo > 10MB                      |
| `422` | Unprocessable Entity  | PDF corrompido, sem texto           |
| `429` | Too Many Requests     | Rate limit exceeded (futuro)        |
| `500` | Internal Server Error | Erro inesperado                     |
| `503` | Service Unavailable   | AI provider indisponível            |

## 🔗 API Versioning

### **Current: v1**

- **Stable**: Core endpoints
- **Supported**: Todas as features documentadas
- **Breaking changes**: Não esperadas

### **Future: v2** (planejado)

- **Authentication**: API keys obrigatórias
- **Async processing**: Background jobs
- **Webhooks**: Notificações de conclusão
- **Batch processing**: Múltiplos PDFs

## 📝 OpenAPI Schema

A documentação interativa está disponível em:

- **Swagger UI**: `GET /docs` (se DEBUG=true)
- **ReDoc**: `GET /redoc` (se DEBUG=true)
- **OpenAPI JSON**: `GET /openapi.json`

---

Esta API serve como **interface especializada** para extração automatizada de dados financeiros, integrando facilmente com sistemas maiores de gestão de finanças pessoais.

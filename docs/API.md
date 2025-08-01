# API Reference - AI Invoice Agent

> **RESTful API para processamento de faturas via IA**

## Overview

API para extrair transações estruturadas de PDFs de faturas de cartão de crédito usando IA (OpenAI, DeepSeek, Gemini).

**Base URL**: `http://localhost:8000`

## Endpoints

### Health Check

```http
GET /health
```

```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T22:29:00.439862",
  "version": "0.1.0"
}
```

### Process Invoice

```http
POST /v1/process-invoice
Content-Type: multipart/form-data

file: [PDF File]                    # obrigatório
provider: "openai"|"deepseek"|"gemini"  # opcional
```

**Response (200):**

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
  }
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

## Data Models

### Transaction

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

### ProcessingMetadata

```typescript
interface ProcessingMetadata {
  processing_time_ms: number; // Processing duration
  total_transactions: number; // Count of extracted transactions
  confidence_score: number; // AI confidence (0.0-1.0)
  provider: string; // AI provider used
  institution: string; // Detected institution
}
```

## Supported Banks

| Bank            | Code              |
| --------------- | ----------------- |
| Caixa Econômica | `CAIXA`           |
| Nubank          | `NUBANK`          |
| Banco do Brasil | `BANCO_DO_BRASIL` |
| Others          | `GENERIC`         |

## AI Providers

| Provider | Model            | Cost       |
| -------- | ---------------- | ---------- |
| OpenAI   | GPT-4o-mini      | ~$0.15/1M  |
| DeepSeek | deepseek-chat    | ~$0.27/1M  |
| Gemini   | gemini-1.5-flash | ~$0.075/1M |

## Usage Examples

### cURL

```bash
# Basic upload
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@fatura.pdf"

# With specific provider
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@fatura.pdf" \
  -F "provider=openai"
```

### Python

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
```

### JavaScript

```javascript
async function processInvoice(file, provider = null) {
  const formData = new FormData();
  formData.append("file", file);
  if (provider) formData.append("provider", provider);

  const response = await fetch("/v1/process-invoice", {
    method: "POST",
    body: formData,
  });

  return await response.json();
}
```

## Validation Rules

- **File Type**: Only PDF files
- **File Size**: Maximum 10MB
- **Provider**: Only `openai`, `deepseek` or `gemini`
- **Required Fields**: date, description, amount
- **Amount Range**: R$ 0.01 to R$ 100,000.00
- **Date Validation**: No future dates, not after due_date

## HTTP Status Codes

| Code | Description           | When                  |
| ---- | --------------------- | --------------------- |
| 200  | OK                    | Successful processing |
| 400  | Bad Request           | Invalid file/provider |
| 413  | Payload Too Large     | File > 10MB           |
| 422  | Unprocessable Entity  | Corrupted PDF         |
| 500  | Internal Server Error | Unexpected error      |

## Categorization Endpoints

### Unified Categorization API

A API unificada `/v1/unified-categorization` permite categorizar e recategorizar transações em uma única interface, detectando automaticamente o tipo de operação.

#### Initial Categorization

```http
POST /v1/unified-categorization
Content-Type: application/json

{
  "user_id": "user123",
  "user_categories": {
    "user_id": "user123",
    "categories": ["Alimentação", "Transporte", "Shopping", "Saúde", "Pet"]
  },
  "transactions": [
    {
      "date": "2025-01-15",
      "description": "UBER TRIP 001",
      "amount": 25.5,
      "type": "debit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 25.5,
      "due_date": "2025-02-20"
    }
  ],
  "confidence_threshold": 0.3
}
```

**Response:**

```json
{
  "session_id": "sess_a1b2c3d4",
  "user_id": "user123",
  "operation_type": "initial_categorization",
  "categorized_transactions": [
    {
      "transaction_id": "sess_a1b2c3d4_t0",
      "transaction": {...},
      "category": "Transporte",
      "confidence_score": 0.85,
      "categorization_method": "vector_similarity"
    }
  ],
  "metadata": {
    "total_transactions": 1,
    "successful_categorizations": 1,
    "uncategorized_transactions": 0
  }
}
```

#### Recategorization

```http
POST /v1/unified-categorization
Content-Type: application/json

{
  "session_id": "sess_a1b2c3d4",
  "user_id": "user123",
  "user_categories": {
    "user_id": "user123",
    "categories": ["Alimentação", "Transporte", "Shopping", "Saúde", "Pet"]
  },
  "recategorizations": [
    {
      "transaction_id": "sess_a1b2c3d4_t0",
      "old_category": null,
      "new_category": "Shopping"
    }
  ]
}
```

**Response:**

```json
{
  "session_id": "sess_a1b2c3d4",
  "user_id": "user123",
  "operation_type": "recategorization",
  "updated_count": 1,
  "learning_feedback": {
    "session_id": "sess_a1b2c3d4",
    "user_id": "user123",
    "updates": [
      {
        "transaction_id": "sess_a1b2c3d4_t0",
        "old_category": null,
        "new_category": "Shopping",
        "action": "updated_existing_transaction",
        "updated_at": "2025-01-15T10:30:00.000000"
      }
    ]
  }
}
```

### Process with Categorization

```http
POST /v1/process-with-categorization
Content-Type: multipart/form-data

file: [PDF File]
user_categories: {"user_id": "user123", "categories": ["Alimentação", "Transporte", "Shopping"]}
confidence_threshold: 0.3
```

### Get User Categories

```http
GET /v1/categories/{user_id}
```

### Get User Transactions

```http
GET /v1/transactions/{user_id}?limit=100
```

## Learning System

O sistema aprende com o feedback do usuário para melhorar futuras categorizações:

1. **Categorização inicial**: Sistema categoriza transações usando IA
2. **Feedback do usuário**: Usuário corrige categorias incorretas
3. **Aprendizado**: Sistema atualiza o vector store com as correções
4. **Melhoria**: Próximas categorizações são mais precisas

## Flow Recomendado

1. Use `/v1/process-with-categorization` para processar PDFs
2. Use `/v1/unified-categorization` para recategorizar transações
3. O sistema aprende automaticamente com suas correções

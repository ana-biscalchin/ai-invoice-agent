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
print(f"Extracted {len(result['transactions'])} transactions")
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

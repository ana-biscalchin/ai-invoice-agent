# API Documentation

## Overview

The AI Invoice Agent API provides intelligent extraction of transaction data from credit card invoice PDFs.

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** `https://your-service-url.run.app`

## Authentication

Currently, no authentication is required. For production use, consider implementing API key authentication.

## Endpoints

### Health Check

#### GET `/health`

Returns the health status of the service.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "0.1.0",
  "environment": "production",
  "ai_provider": "openai"
}
```

#### GET `/health/ready`

Readiness check for container orchestration.

**Response:**

```json
{
  "status": "ready",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Invoice Processing

#### POST `/v1/process-invoice`

Process a credit card invoice PDF and extract structured transaction data.

**Request:**

- **Content-Type:** `multipart/form-data`
- **Body:** PDF file upload (max 10MB)

**Response:**

```json
{
  "transactions": [
    {
      "date": "2024-01-15",
      "description": "UBER TRIP 001",
      "amount": 25.5,
      "type": "debit"
    }
  ],
  "metadata": {
    "processing_time_ms": 1250,
    "total_transactions": 1,
    "confidence_score": 0.95,
    "provider": "openai"
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid file format or content
- `413 Payload Too Large`: File exceeds 10MB limit
- `500 Internal Server Error`: Processing failed

#### GET `/v1/`

Returns API information and available endpoints.

**Response:**

```json
{
  "name": "AI Invoice Agent",
  "version": "0.1.0",
  "description": "Intelligent microservice for extracting structured data from credit card invoices",
  "endpoints": {
    "process_invoice": "POST /v1/process-invoice",
    "health": "GET /health",
    "ready": "GET /health/ready"
  }
}
```

## Data Models

### Transaction

```json
{
  "date": "string (YYYY-MM-DD)",
  "description": "string (1-500 chars)",
  "amount": "number (>= 0)",
  "type": "string (credit|debit)"
}
```

### ProcessingMetadata

```json
{
  "processing_time_ms": "number (>= 0)",
  "total_transactions": "number (>= 0)",
  "confidence_score": "number (0-1)",
  "provider": "string"
}
```

## Rate Limits

Currently, no rate limits are implemented. Consider implementing rate limiting for production use.

## Error Handling

All errors return JSON responses with the following structure:

```json
{
  "detail": "Error description"
}
```

## Examples

### cURL Example

```bash
curl -X POST "http://localhost:8000/v1/process-invoice" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.pdf"
```

### Python Example

```python
import requests

url = "http://localhost:8000/v1/process-invoice"
files = {"file": open("invoice.pdf", "rb")}

response = requests.post(url, files=files)
data = response.json()

print(f"Extracted {data['metadata']['total_transactions']} transactions")
```

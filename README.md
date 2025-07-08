# 🤖 AI Invoice Agent

> **Intelligent microservice for extracting structured data from credit card invoices**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-green.svg)](https://fastapi.tiangolo.com/)
[![Poetry](https://img.shields.io/badge/poetry-1.7.0-orange.svg)](https://python-poetry.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Google Cloud Run](https://img.shields.io/badge/deploy-google%20cloud%20run-red.svg)](https://cloud.google.com/run)

## 🎯 Overview

AI Invoice Agent is a **production-ready microservice** that uses **AI-powered text analysis** to extract structured transaction data from credit card invoice PDFs. Built for **study purposes** with focus on **Git best practices**, **robust documentation**, and **modern Python development**.

### ✨ Key Features

- 🔍 **Intelligent PDF Processing**: PyMuPDF + OCR fallback
- 🤖 **AI-Powered Extraction**: OpenAI GPT for transaction analysis
- 📊 **Structured Output**: Clean JSON with validated data
- 🚀 **Production Ready**: Google Cloud Run deployment
- 🐳 **Containerized**: Docker development environment
- 📚 **Well Documented**: Comprehensive guides and examples
- 🧪 **Tested**: Unit tests and integration examples
- 🔧 **Modern Stack**: FastAPI, Poetry, Python 3.11+

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF Input     │───▶│  PDF Processor   │───▶│  AI Analyzer    │
│   (max 10MB)    │    │  (PyMuPDF+OCR)   │    │  (OpenAI GPT)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│  JSON Output    │◀───│   Response       │◀────────────┘
│  (Structured)   │    │   Formatter      │
└─────────────────┘    └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker** (recommended)
- **OpenAI API Key**
- **Google Cloud CLI** (for deployment)

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd ai-invoice-agent

# Setup development environment
make setup
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit with your OpenAI API key
nano .env
```

### 3. Start Development Server

```bash
# Using Docker (recommended)
make dev

# Or using Poetry directly
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Process invoice (replace with your PDF)
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@examples/sample-invoice.pdf"
```

## 📋 API Documentation

### Endpoints

| Method | Endpoint              | Description         |
| ------ | --------------------- | ------------------- |
| `GET`  | `/health`             | Health check        |
| `GET`  | `/health/ready`       | Readiness check     |
| `POST` | `/v1/process-invoice` | Process invoice PDF |
| `GET`  | `/v1/`                | API information     |

### Request/Response Example

**Request:**

```bash
curl -X POST "http://localhost:8000/v1/process-invoice" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.pdf"
```

**Response:**

```json
{
  "transactions": [
    {
      "date": "2024-01-15",
      "description": "UBER TRIP 001",
      "amount": 25.5,
      "type": "debit"
    },
    {
      "date": "2024-01-16",
      "description": "NETFLIX.COM",
      "amount": 39.9,
      "type": "debit"
    }
  ],
  "metadata": {
    "processing_time_ms": 1250,
    "total_transactions": 2,
    "confidence_score": 0.95,
    "provider": "openai"
  }
}
```

📖 **Full API Documentation**: [docs/API.md](docs/API.md)

## 🛠️ Development

### Project Structure

```
ai-invoice-agent/
├── app/                    # Application code
│   ├── api/               # FastAPI routes
│   ├── core/              # Business logic
│   ├── models/            # Pydantic models
│   ├── providers/         # AI providers
│   └── main.py            # FastAPI app
├── docs/                  # Documentation
├── examples/              # Example files
├── tests/                 # Test suite
├── Dockerfile             # Container definition
├── docker-compose.yml     # Development environment
├── pyproject.toml         # Poetry configuration
└── Makefile               # Development commands
```

### Development Commands

```bash
# Show all commands
make help

# Setup environment
make setup

# Start development server
make dev

# Run tests
make test

# Run linting
make lint

# Clean up
make clean
```

### Code Quality

- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Type checking
- **Pre-commit**: Git hooks

📖 **Development Guide**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## 🚢 Deployment

### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy ai-invoice-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### Environment Variables

```bash
# Set OpenAI API key
gcloud run services update ai-invoice-agent \
  --set-env-vars OPENAI_API_KEY=sk-your-api-key \
  --region us-central1
```

📖 **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 🧪 Testing

### Run Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=app

# Specific test
poetry run pytest tests/test_models.py -v
```

### Test Examples

```python
# Test transaction model
def test_valid_transaction():
    transaction = Transaction(
        date=date(2024, 1, 15),
        description="UBER TRIP 001",
        amount=25.50,
        type=TransactionType.DEBIT
    )
    assert transaction.amount == 25.50
```

## 📊 Performance

### Benchmarks

- **Processing Time**: ~1-3 seconds per PDF
- **Memory Usage**: ~512MB-2GB per instance
- **Concurrent Requests**: Up to 80 per instance
- **File Size Limit**: 10MB maximum

### Optimization

- **Text Truncation**: Limits AI input to 8000 characters
- **OCR Fallback**: Only when PyMuPDF fails
- **Async Processing**: Non-blocking operations
- **Connection Pooling**: Reuse HTTP connections

## 🔧 Configuration

### Environment Variables

| Variable          | Default       | Description          |
| ----------------- | ------------- | -------------------- |
| `ENVIRONMENT`     | `development` | Environment mode     |
| `DEBUG`           | `false`       | Debug mode           |
| `AI_PROVIDER`     | `openai`      | AI provider          |
| `OPENAI_API_KEY`  | -             | OpenAI API key       |
| `MAX_FILE_SIZE`   | `10485760`    | Max file size (10MB) |
| `TIMEOUT_SECONDS` | `60`          | Processing timeout   |

### AI Provider Configuration

The system is designed to be **agnostic** to AI providers. Currently supports:

- **OpenAI GPT-4o-mini** (default)
- **Extensible**: Easy to add Claude, Gemini, etc.

## 🔒 Security

### Input Validation

- ✅ File size limits (10MB max)
- ✅ File type validation (PDF only)
- ✅ Content validation (valid PDF structure)
- ✅ Request timeout (60s max)

### API Security

- ✅ CORS configuration
- ✅ Error handling without information leakage
- ✅ Non-root container execution
- 🔄 Rate limiting (planned)
- 🔄 Authentication (planned)

## 📈 Monitoring

### Health Checks

```bash
# Health check
curl https://your-service.run.app/health

# Readiness check
curl https://your-service.run.app/health/ready
```

### Logs

```bash
# View Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-invoice-agent"
```

## 🎯 Use Cases

### Primary Use Case

- **Financial Apps**: Automate invoice data entry
- **Expense Tracking**: Extract transactions for categorization
- **Accounting**: Import credit card statements
- **Personal Finance**: Track spending patterns

### Integration Examples

```python
# Python integration
import requests

def process_invoice(pdf_path):
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            'https://your-service.run.app/v1/process-invoice',
            files=files
        )
    return response.json()

# Usage
transactions = process_invoice('invoice.pdf')
for tx in transactions['transactions']:
    print(f"{tx['date']}: {tx['description']} - R$ {tx['amount']}")
```

## 🚀 Future Enhancements (V2)

### Planned Features

- 🏷️ **Transaction Categorization**: Automatic expense categorization
- 🔄 **Multiple AI Providers**: Claude, Gemini, local models
- 📦 **Batch Processing**: Multiple PDFs in one request
- 💾 **Caching**: Redis for repeated requests
- 📊 **Analytics**: Processing statistics and insights

### Scalability Improvements

- 🐌 **Queue System**: Celery for background processing
- 🗄️ **Database Integration**: PostgreSQL for transaction storage
- ☁️ **CDN**: Cloud Storage for file caching
- 🚪 **API Gateway**: Cloud Endpoints for rate limiting

## 🤝 Contributing

This is a **study project** focused on learning best practices. Contributions are welcome!

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Code Standards

- Follow **PEP 8** and **Black** formatting
- Write **type hints** for all functions
- Add **docstrings** for public APIs
- Include **tests** for new features
- Update **documentation** as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** team for the excellent framework
- **OpenAI** for providing the AI capabilities
- **Google Cloud** for the deployment platform
- **Python community** for the amazing ecosystem

## 📞 Support

- 📖 **Documentation**: Check the [docs/](docs/) folder
- 🐛 **Issues**: Create an issue on GitHub
- 💬 **Discussions**: Use GitHub Discussions
- 📧 **Email**: Contact the maintainer

---

**Built with ❤️ for learning and experimentation**

_This project demonstrates modern Python development practices, microservice architecture, and AI integration for real-world applications._

# Architecture Documentation

## Overview

The AI Invoice Agent is a microservice designed to extract structured transaction data from credit card invoice PDFs using AI-powered text analysis.

## System Architecture

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

## Component Design

### 1. API Layer (`app/api/`)

**Responsibilities:**

- HTTP request/response handling
- File upload validation
- Error handling and status codes
- Request routing

**Key Components:**

- `health.py`: Health check endpoints
- `invoice.py`: Main invoice processing endpoint

**Design Patterns:**

- **Router Pattern**: Modular endpoint organization
- **Dependency Injection**: FastAPI's built-in DI system

### 2. Core Business Logic (`app/core/`)

**Responsibilities:**

- PDF text extraction
- Configuration management
- Business rule enforcement

**Key Components:**

- `config.py`: Centralized configuration using Pydantic Settings
- `pdf_processor.py`: PDF processing with OCR fallback

**Design Patterns:**

- **Configuration Pattern**: Environment-based settings
- **Strategy Pattern**: Multiple PDF processing strategies

### 3. Data Models (`app/models/`)

**Responsibilities:**

- Data validation and serialization
- API contract definition
- Type safety

**Key Components:**

- `invoice.py`: Transaction and metadata models

**Design Patterns:**

- **Pydantic Models**: Automatic validation and serialization
- **Enum Pattern**: Type-safe transaction types

### 4. AI Providers (`app/providers/`)

**Responsibilities:**

- AI model integration
- Text analysis and extraction
- Provider abstraction

**Key Components:**

- `base.py`: Abstract base class for providers
- `openai_provider.py`: OpenAI GPT implementation

**Design Patterns:**

- **Abstract Factory**: Provider creation
- **Strategy Pattern**: Swappable AI providers
- **Adapter Pattern**: Provider-specific implementations

## Data Flow

### 1. Request Processing

```
Client Request
    │
    ▼
┌─────────────────┐
│ FastAPI Router  │ ← Validation & routing
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ File Validation │ ← Size, format, content
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ PDF Processor   │ ← Text extraction
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ AI Provider     │ ← Transaction extraction
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Response Format │ ← JSON serialization
└─────────────────┘
    │
    ▼
Client Response
```

### 2. Error Handling

```
Error Occurrence
    │
    ▼
┌─────────────────┐
│ Exception       │ ← Python exception
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Error Handler   │ ← FastAPI exception handlers
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ HTTP Response   │ ← Structured error response
└─────────────────┘
```

## Technology Stack

### Backend Framework

- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation and settings

### PDF Processing

- **PyMuPDF**: Primary PDF text extraction
- **Tesseract**: OCR fallback for image-based PDFs
- **Pillow**: Image processing for OCR

### AI Integration

- **OpenAI SDK**: GPT model integration
- **Async/Await**: Non-blocking AI requests

### Development Tools

- **Poetry**: Dependency management
- **Docker**: Containerization
- **Pre-commit**: Code quality hooks
- **Black/Ruff/MyPy**: Code formatting and linting

## Security Considerations

### Input Validation

- File size limits (10MB max)
- File type validation (PDF only)
- Content validation (valid PDF structure)

### API Security

- CORS configuration
- Rate limiting (future enhancement)
- Authentication (future enhancement)

### Environment Security

- Environment variable management
- Secret management (Google Secret Manager)
- Non-root container execution

## Performance Characteristics

### Scalability

- **Stateless Design**: No session storage
- **Container-based**: Easy horizontal scaling
- **Async Processing**: Non-blocking operations

### Resource Usage

- **Memory**: ~512MB-2GB per instance
- **CPU**: 1-2 cores per instance
- **Storage**: Ephemeral (no persistent storage)

### Optimization Strategies

- **Text Truncation**: Limit AI input to 8000 chars
- **OCR Fallback**: Only when PyMuPDF fails
- **Connection Pooling**: Reuse HTTP connections

## Deployment Architecture

### Google Cloud Run

```
┌─────────────────┐
│ Cloud Run       │ ← Serverless container
│ Service         │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Load Balancer   │ ← Automatic scaling
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Container       │ ← Docker container
│ Instance        │
└─────────────────┘
```

### Environment Configuration

- **Development**: Local Docker with hot reload
- **Production**: Google Cloud Run with auto-scaling
- **Staging**: Separate Cloud Run service

## Monitoring and Observability

### Health Checks

- **Liveness**: `/health` endpoint
- **Readiness**: `/health/ready` endpoint
- **Container**: Docker health checks

### Logging

- **Structured Logging**: JSON format
- **Log Levels**: INFO, WARNING, ERROR
- **Cloud Logging**: Google Cloud integration

### Metrics

- **Request Count**: Number of processed invoices
- **Processing Time**: Time per request
- **Error Rate**: Failed requests percentage
- **Resource Usage**: CPU, memory, network

## Future Enhancements

### V2 Features

- **Transaction Categorization**: Automatic expense categorization
- **Multiple AI Providers**: Claude, Gemini, local models
- **Batch Processing**: Multiple PDFs in one request
- **Caching**: Redis for repeated requests

### Scalability Improvements

- **Queue System**: Celery for background processing
- **Database Integration**: PostgreSQL for transaction storage
- **CDN**: Cloud Storage for file caching
- **API Gateway**: Cloud Endpoints for rate limiting

### Security Enhancements

- **JWT Authentication**: User-based access control
- **API Key Management**: Per-user API keys
- **Audit Logging**: Request/response logging
- **Encryption**: At-rest and in-transit encryption

## Design Decisions

### Why FastAPI?

- **Performance**: Fast, async framework
- **Type Safety**: Built-in Pydantic integration
- **Documentation**: Automatic OpenAPI generation
- **Modern**: Python 3.11+ features

### Why Poetry?

- **Dependency Resolution**: Better than pip
- **Lock Files**: Reproducible builds
- **Virtual Environments**: Automatic management
- **Modern**: Industry standard

### Why Google Cloud Run?

- **Serverless**: No infrastructure management
- **Auto-scaling**: Zero to many instances
- **Cost-effective**: Pay per request
- **Integration**: Native Google Cloud services

### Why OpenAI GPT?

- **Accuracy**: High-quality text analysis
- **Flexibility**: Handles various PDF formats
- **Cost**: Reasonable pricing for this use case
- **Reliability**: Stable API with good uptime

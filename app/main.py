"""Simplified AI Invoice Agent API."""

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.extractor import TransactionExtractor
from app.models import InvoiceResponse, HealthResponse, APIInfoResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "openai")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760").split()[0])  # 10MB
API_TITLE = "AI Invoice Agent"
API_VERSION = "0.1.0"
API_DESCRIPTION = (
    "Simplified microservice for extracting transactions from credit card invoices"
)

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup logging
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Default AI Provider: {DEFAULT_AI_PROVIDER}")
    logger.info(f"Debug: {DEBUG}")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs" if DEBUG else "disabled",
        "health": "/health",
        "api_info": "/v1/",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=API_VERSION,
        environment=ENVIRONMENT,
        ai_provider=DEFAULT_AI_PROVIDER,
    )


@app.get("/health/ready", response_model=dict)
async def readiness_check():
    """Readiness check for container orchestration."""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@app.get("/v1/", response_model=APIInfoResponse)
async def api_info():
    """API information and available endpoints."""
    return APIInfoResponse(
        name=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        endpoints={
            "process_invoice": "POST /v1/process-invoice",
            "health": "GET /health",
            "ready": "GET /health/ready",
        },
    )


@app.post("/v1/process-invoice", response_model=InvoiceResponse)
async def process_invoice(
    file: UploadFile = File(...),
    provider: Optional[str] = Form(
        None,
        description="AI provider: 'openai' or 'deepseek'. If not provided, uses environment default.",
    ),
):
    """
    Process credit card invoice PDF and extract transactions.

    **Validation rules applied:**
    - Required fields: Each transaction must have date, description, and amount
    - No duplicates: Transactions with same date, amount, and description are not allowed
    - Valid dates: Transaction date cannot be in the future or after invoice due date
    - Amount range: Each amount must be between 0.01 and 100,000
    - Installments consistency: If installments > 1, total_purchase_amount must equal amount × installments
    - Due date consistency: All transactions must have the same due date
    - Sum validation: Sum of all debits minus credits must match invoice total (tolerance: 0.01)

    Args:
        file: PDF file upload (max 10MB)
        provider: AI provider ('openai' or 'deepseek')

    Returns:
        Structured transaction data with metadata and validation errors (if any)

    Raises:
        HTTPException: For validation or processing errors
    """
    # Validate file
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes",
        )

    # Determine provider
    selected_provider = provider or DEFAULT_AI_PROVIDER
    if selected_provider not in ["openai", "deepseek"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider. Allowed values: 'openai', 'deepseek'.",
        )

    # Process invoice
    try:
        extractor = TransactionExtractor(selected_provider)
        result = await extractor.process_invoice(content, file.filename)
        return result

    except ValueError as e:
        # Business logic errors (invalid PDF, no text, etc.)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error processing invoice: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG,
        log_level="info" if DEBUG else "warning",
    )

"""Invoice processing endpoints."""

import time
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.pdf_processor import PDFProcessor
from app.models.invoice import InvoiceResponse, ProcessingMetadata, Transaction
from app.providers import OpenAIProvider

router = APIRouter(prefix="/v1", tags=["invoice"])


@router.post("/process-invoice", response_model=InvoiceResponse)
async def process_invoice(file: UploadFile = File(...)):
    """
    Process credit card invoice PDF and extract transactions.

    Args:
        file: PDF file upload (max 10MB)

    Returns:
        Structured transaction data with metadata

    Raises:
        HTTPException: For validation or processing errors
    """
    start_time = time.time()

    # Validate file
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    # Validate file size
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size} bytes",
        )

    # Process PDF
    try:
        pdf_processor = PDFProcessor()

        # Validate PDF
        if not pdf_processor.validate_pdf(content):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        # Extract text
        text = pdf_processor.extract_text(content)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found in PDF")

        # Extract transactions with AI
        ai_provider = OpenAIProvider()
        transactions, invoice_total, due_date = await ai_provider.extract_transactions(
            text
        )

        # Validate transactions with TransactionValidator
        confidence_score = 0.95
        if invoice_total is not None and due_date is not None:
            from app.core.validation import TransactionValidator
            from datetime import datetime

            # Convert due_date string to datetime if needed
            if isinstance(due_date, str):
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
            else:
                due_date_obj = due_date
            validator = TransactionValidator(transactions, due_date_obj)
            results = validator.run_all(invoice_total)
            confidence_score = results["score"]

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build metadata
        metadata = ProcessingMetadata(
            processing_time_ms=processing_time_ms,
            total_transactions=len(transactions),
            confidence_score=confidence_score,
            provider=ai_provider.provider_name,
        )

        # Build response
        response = InvoiceResponse(transactions=transactions, metadata=metadata)
        return response

    except HTTPException:
        raise
    except Exception as e:
        # Só erros inesperados devem gerar 500. Erros de validação não devem interromper o fluxo.
        print(f"[ERROR] Unexpected error: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "transactions": [],
                "metadata": {
                    "processing_time_ms": int((time.time() - start_time) * 1000),
                    "total_transactions": 0,
                    "confidence_score": 0.0,
                    "provider": "error",
                },
                "error": str(e),
            },
        )


@router.get("/")
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "endpoints": {
            "process_invoice": "POST /v1/process-invoice",
            "health": "GET /health",
            "ready": "GET /health/ready",
        },
    }

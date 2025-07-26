"""Core transaction extraction logic."""

import time
from datetime import datetime

from app.models import InvoiceResponse, ProcessingMetadata, Transaction
from app.providers import create_provider
from app.utils import PDFProcessor, TransactionValidator


class TransactionExtractor:
    """Main service for extracting transactions from PDF invoices."""

    def __init__(self, provider_name: str = "openai"):
        """Initialize with specified AI provider."""
        self.ai_provider = create_provider(provider_name)
        self.pdf_processor = PDFProcessor()

    async def process_invoice(
        self, pdf_bytes: bytes, filename: str = "document"
    ) -> InvoiceResponse:
        """
        Process a PDF invoice and extract structured transaction data.

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename for logging

        Returns:
            InvoiceResponse with transactions, metadata, and validation errors

        Raises:
            ValueError: If PDF cannot be processed or is invalid
        """
        start_time = time.time()
        detected_institution = "unknown"  # Default fallback

        try:
            # Validate PDF
            if not self.pdf_processor.validate_pdf(pdf_bytes):
                raise ValueError("Invalid PDF file")

            # Extract text and detect institution
            text, institution = self.pdf_processor.extract_text(pdf_bytes, filename)
            detected_institution = institution  # Store detected institution
            if not text.strip():
                raise ValueError("No text content found in PDF")

            # Extract transactions with AI
            (
                transactions,
                invoice_total,
                due_date,
            ) = await self.ai_provider.extract_transactions(text, institution)

            # Validate transactions
            confidence_score, errors = self._validate_transactions(
                transactions, invoice_total, due_date
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Build metadata
            metadata = ProcessingMetadata(
                processing_time_ms=processing_time_ms,
                total_transactions=len(transactions),
                confidence_score=confidence_score,
                provider=self.ai_provider.name,
                institution=institution,
            )

            # Build response
            return InvoiceResponse(
                transactions=transactions,
                metadata=metadata,
                errors=errors if errors else None,
            )

        except Exception as e:
            # Return error response with metadata
            processing_time_ms = int((time.time() - start_time) * 1000)
            metadata = ProcessingMetadata(
                processing_time_ms=processing_time_ms,
                total_transactions=0,
                confidence_score=0.0,
                provider=self.ai_provider.name
                if hasattr(self, "ai_provider")
                else "error",
                institution=detected_institution,  # Use detected institution instead of hardcoded "unknown"
            )

            return InvoiceResponse(
                transactions=[],
                metadata=metadata,
                errors=[str(e)],
            )

    def _validate_transactions(
        self,
        transactions: list[Transaction],
        invoice_total: float | None,
        due_date: str | None,
    ) -> tuple[float, list[str] | None]:
        """
        Validate transactions and return confidence score and errors.

        Returns:
            Tuple of (confidence_score, errors_list)
        """
        if not transactions or invoice_total is None or due_date is None:
            return 0.0, ["Missing transaction data"]

        try:
            # Convert due_date string to datetime if needed
            if isinstance(due_date, str):
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
            else:
                due_date_obj = due_date

            validator = TransactionValidator(transactions, due_date_obj)
            results = validator.run_all(invoice_total)

            return results["score"], results.get("errors")

        except Exception:
            return 0.5, ["Validation failed"]

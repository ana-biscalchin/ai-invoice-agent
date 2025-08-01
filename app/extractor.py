"""Core transaction extraction logic."""

import time
from datetime import datetime

from app.models import InvoiceResponse, ProcessingMetadata, Transaction
from app.providers import create_provider
from app.utils import PDFProcessor, TransactionValidator
from app.categorization import (
    CategorizationService,
    CategorizationResponse,
    CategorizedTransaction,
    CategorizationRequest,
    UserCategories,
)


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
            detected_institution = institution
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
                provider=(
                    self.ai_provider.name if hasattr(self, "ai_provider") else "error"
                ),
                institution=detected_institution,  # Use detected institution instead of hardcoded "unknown"
            )

            return InvoiceResponse(
                transactions=[],
                metadata=metadata,
                errors=[f"Processing failed: {str(e)}"],
            )

    async def process_with_categorization(
        self, 
        pdf_bytes: bytes, 
        user_categories: UserCategories,
        filename: str = "document",
        confidence_threshold: float = 0.3
    ) -> CategorizationResponse:
        """
        Process a PDF invoice, extract transactions, and categorize them.
        """
        print(f"🔍 DEBUG: Starting process_with_categorization for user {user_categories.user_id}")
        
        # First, extract transactions using existing logic
        extraction_result = await self.process_invoice(pdf_bytes, filename)
        
        print(f"🔍 DEBUG: Extraction completed. Errors: {extraction_result.errors}")
        print(f"🔍 DEBUG: Transactions extracted: {len(extraction_result.transactions)}")
        
        # Check if we have transactions to process, even with validation errors
        if not extraction_result.transactions:
            print(f"❌ DEBUG: No transactions extracted, returning error session")
            return CategorizationResponse(
                session_id="error_session",
                user_id=user_categories.user_id,
                confidence_threshold=confidence_threshold,
                categorized_transactions=[],
            )
        
        # If we have transactions, process them even with validation errors
        # Validation errors are warnings, not fatal errors
        if extraction_result.errors:
            print(f"⚠️ DEBUG: Validation errors found but proceeding with categorization")
            print(f"🔍 DEBUG: Validation errors: {extraction_result.errors}")

        try:
            print(f"🔍 DEBUG: Initializing CategorizationService...")
            categorization_service = CategorizationService()
            print(f"🔍 DEBUG: CategorizationService initialized successfully")

            # Convert transactions to CategorizedTransaction format
            categorized_transactions = []

            for i, transaction in enumerate(extraction_result.transactions):
                try:
                    print(f"🔍 DEBUG: Categorizing transaction {i}: {transaction.description[:50]}...")
                    # Categorize the transaction directly
                    cat_tx = await categorization_service._categorize_single_transaction(
                        transaction=transaction,
                        user_categories=user_categories,
                        transaction_id=f"extracted_{i}",
                        confidence_threshold=confidence_threshold,
                    )

                    categorized_transactions.append(
                        CategorizedTransaction(
                            transaction_id=cat_tx.transaction_id,
                            transaction=cat_tx.transaction,
                            category=cat_tx.category,
                            informed_category=None,
                            confidence_score=cat_tx.confidence_score,
                            categorization_method=cat_tx.categorization_method,
                            created_at=cat_tx.created_at,
                        )
                    )
                    print(f"✅ DEBUG: Transaction {i} categorized successfully")
                except Exception as e:
                    print(f"❌ DEBUG: Error categorizing transaction {i}: {e}")
                    import traceback
                    print(f"🔍 DEBUG: Transaction {i} traceback: {traceback.format_exc()}")
                    raise

            print(f"🔍 DEBUG: All transactions categorized. Creating categorization request...")
            # Create new categorization request
            categorization_request = CategorizationRequest(
                user_id=user_categories.user_id,
                user_categories=user_categories,
                transactions=categorized_transactions,
                confidence_threshold=confidence_threshold,
            )

            print(f"🔍 DEBUG: Calling categorization service...")
            categorization_result = await categorization_service.categorization(categorization_request)
            print(f"✅ DEBUG: Categorization completed successfully")

            return categorization_result

        except Exception as e:
            print(f"❌ DEBUG: Error in categorization: {e}")
            import traceback
            print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
            # Return error response with extraction data
            return CategorizationResponse(
                session_id="error_session",
                user_id=user_categories.user_id,
                confidence_threshold=confidence_threshold,
                categorized_transactions=[],
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

            # Create validator with proper parameters
            validator = TransactionValidator(transactions, due_date_obj)
            results = validator.run_all(invoice_total)

            return results["score"], results.get("errors")

        except Exception as e:
            return 0.0, [f"Validation error: {str(e)}"]

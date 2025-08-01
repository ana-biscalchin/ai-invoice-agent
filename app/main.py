"""Simplified AI Invoice Agent API."""

import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware

from app.extractor import TransactionExtractor
from app.models import APIInfoResponse, HealthResponse, InvoiceResponse
from app.categorization import (
    CategorizationService,
    CategorizationRequest,
    CategorizationResponse,
    UserCategories,
)

# Load environment variables
load_dotenv()

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
    openapi_url="/openapi.json",  # Always available for Postman import
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
            "process_with_categorization": "POST /v1/process-with-categorization",
            "categorization": "POST /v1/categorization",
            "get_user_categories": "GET /v1/categories/{user_id}",
            "update_user_categories": "POST /v1/categories/{user_id}",
            "get_user_transactions": "GET /v1/transactions/{user_id}",
            "health": "GET /health",
            "ready": "GET /health/ready",
        },
    )


@app.post("/v1/process-invoice", response_model=InvoiceResponse)
async def process_invoice(
    file: UploadFile = File(...),
    provider: str | None = Form(
        None,
        description="AI provider: 'openai', 'deepseek' or 'gemini'. If not provided, uses environment default.",
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
        provider: AI provider ('openai', 'deepseek' or 'gemini')

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
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}") from e

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes",
        )

    # Determine provider
    selected_provider = provider or DEFAULT_AI_PROVIDER
    if selected_provider not in ["openai", "deepseek", "gemini"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider. Allowed values: 'openai', 'deepseek', 'gemini'.",
        )

    # Process invoice
    try:
        extractor = TransactionExtractor(selected_provider)
        result = await extractor.process_invoice(content, file.filename)
        return result

    except ValueError as e:
        # Business logic errors (invalid PDF, no text, etc.)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error processing invoice: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


@app.post("/v1/process-with-categorization", response_model=CategorizationResponse)
async def process_with_categorization(
    file: UploadFile = File(...),
    user_categories: str = Form(
        ...,
        description="JSON string with user categories. Format: {'user_id': 'string', 'categories': ['list', 'of', 'categories']}",
    ),
    extraction_model: str = Form(
        "openai",
        description="AI provider for extraction: 'openai', 'deepseek' or 'gemini'",
    ),
    confidence_threshold: float = Form(
        0.3,
        description="Minimum confidence score to assign a category (0.0-1.0, default: 0.3)",
    ),
):
    """
    Process credit card invoice PDF and categorize transactions.
    """
    print(f"🔍 DEBUG: process_with_categorization endpoint called")
    
    import json

    # Validate file
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}") from e

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes",
        )

    # Parse user categories
    try:
        categories_data = json.loads(user_categories)
        user_categories_obj = UserCategories(**categories_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in user_categories")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid user_categories format: {e}"
        )

    # Validate extraction model
    if extraction_model not in ["openai", "deepseek", "gemini"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid extraction_model. Allowed values: 'openai', 'deepseek', 'gemini'.",
        )

    # Validate confidence threshold
    if not 0.0 <= confidence_threshold <= 1.0:
        raise HTTPException(
            status_code=400,
            detail="Invalid confidence_threshold. Must be between 0.0 and 1.0.",
        )

    try:
        print(f"🔍 DEBUG: Creating TransactionExtractor...")
        # Extract and categorize transactions using integrated method
        extractor = TransactionExtractor(extraction_model)
        print(f"💾 TransactionExtractor result: ", extractor)
        
        print(f"🔍 DEBUG: Calling process_with_categorization...")
        categorization_result = await extractor.process_with_categorization(
            content, user_categories_obj, file.filename, confidence_threshold
        )
        print(f"🔍 DEBUG: process_with_categorization completed")

        return categorization_result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error in categorization: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


@app.post("/v1/categorization", response_model=CategorizationResponse)
async def categorization(request: CategorizationRequest):
    """
    Process user feedback and improve categorization learning.

    This endpoint processes user feedback on categorizations:
    - If informed_category is provided: user wants to correct the categorization
    - If informed_category is null: user agrees with the system's categorization

    The vector store is updated with user corrections to improve future categorizations.
    This learning helps the system provide better categorizations in subsequent requests.

    Args:
        request: Categorization request with transactions and user feedback

    Returns:
        Categorization response with updated transactions

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        categorization_service = CategorizationService()
        result = await categorization_service.categorization(request)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error in categorization: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


@app.get("/v1/categories/{user_id}")
async def get_user_categories(user_id: str):
    """
    Get user's categories from vector store.

    Args:
        user_id: User identifier

    Returns:
        User categories with metadata

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        categorization_service = CategorizationService()
        categories = await categorization_service.get_user_categories(user_id)
        return categories

    except Exception as e:
        logger.error(f"Error getting user categories: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


@app.post("/v1/categories/{user_id}")
async def update_user_categories(user_id: str, user_categories: UserCategories):
    """
    Update user's categories.

    Args:
        user_id: User identifier
        user_categories: Updated user categories

    Returns:
        Success status

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        # Validate user_id matches
        if user_categories.user_id != user_id:
            raise HTTPException(status_code=400, detail="User ID mismatch")

        categorization_service = CategorizationService()
        success = await categorization_service.update_user_categories(user_categories)

        return {"status": "success", "message": "Categories updated successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error updating user categories: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


@app.get("/v1/transactions/{user_id}")
async def get_user_transactions(user_id: str, limit: int = 100):
    """
    Get user's transactions from vector store.

    Args:
        user_id: User identifier
        limit: Maximum number of transactions to return

    Returns:
        List of user's transactions with categories

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        categorization_service = CategorizationService()
        vector_store = categorization_service.vector_store
        transactions = await vector_store.get_user_transactions(user_id, limit)

        return {
            "user_id": user_id,
            "total_transactions": len(transactions),
            "transactions": transactions,
        }

    except Exception as e:
        logger.error(f"Error getting user transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


@app.get("/v1/debug/transactions/{user_id}")
async def debug_user_transactions(user_id: str):
    """
    Debug endpoint to see all transactions in vector store.

    Args:
        user_id: User identifier

    Returns:
        Debug information about user's transactions

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        categorization_service = CategorizationService()
        vector_store = categorization_service.vector_store
        transactions = await vector_store.get_user_transactions(user_id)

        # Group by category
        by_category = {}
        for tx in transactions:
            category = tx.get("category", "uncategorized")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(
                {
                    "transaction_id": tx.get("transaction_id"),
                    "description": tx.get("description"),
                    "amount": tx.get("amount"),
                    "category": tx.get("category"),
                    "created_at": tx.get("created_at"),
                }
            )

        # Calculate statistics
        total_transactions = len(transactions)
        categorized_count = sum(
            len(txs) for cat, txs in by_category.items() if cat != "uncategorized"
        )
        uncategorized_count = len(by_category.get("uncategorized", []))

        return {
            "user_id": user_id,
            "statistics": {
                "total_transactions": total_transactions,
                "categorized_transactions": categorized_count,
                "uncategorized_transactions": uncategorized_count,
                "unique_categories": len(
                    [cat for cat in by_category.keys() if cat != "uncategorized"]
                ),
            },
            "by_category": by_category,
            "all_transactions": transactions[:10],  # Limit to first 10 for readability
        }

    except Exception as e:
        logger.error(f"Error debugging user transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


@app.get("/v1/debug/all-transactions")
async def debug_all_transactions():
    """
    Debug endpoint to see all transactions in vector store.

    Returns:
        Debug information about all transactions

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        categorization_service = CategorizationService()
        vector_store = categorization_service.vector_store
        transactions = await vector_store.get_all_transactions()

        # Group by user
        by_user = {}
        for tx in transactions:
            user_id = tx.get("user_id", "unknown")
            if user_id not in by_user:
                by_user[user_id] = []
            by_user[user_id].append(
                {
                    "transaction_id": tx.get("transaction_id"),
                    "description": tx.get("description"),
                    "category": tx.get("category"),
                    "stored_at": tx.get("stored_at"),
                }
            )

        return {
            "total_transactions": len(transactions),
            "by_user": by_user,
            "all_transactions": transactions[:20],  # Limit to first 20 for readability
        }

    except Exception as e:
        logger.error(f"Error debugging all transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


@app.delete("/v1/users/{user_id}")
async def delete_user(user_id: str, response: Response):
    """
    Delete user and all their data (transactions and categories).

    This endpoint permanently removes all user data:
    - All user transactions from vector store
    - User categories and preferences
    - All learning data associated with the user

    WARNING: This action is irreversible!

    Args:
        user_id: User identifier to delete
        response: FastAPI response object

    Returns:
        HTTP 204 No Content on success, or error details

    Raises:
        HTTPException: For validation or processing errors
    """
    try:
        # Validate user_id
        if not user_id or user_id.strip() == "":
            raise HTTPException(status_code=400, detail="Invalid user_id")

        # Check if user has any data before deletion
        categorization_service = CategorizationService()
        user_transactions = (
            await categorization_service.vector_store.get_user_transactions(user_id)
        )

        if not user_transactions:
            # User not found or no data - return 404
            raise HTTPException(
                status_code=404, detail=f"User {user_id} not found or has no data"
            )

        # Delete user and all their data
        deletion_result = await categorization_service.delete_user(user_id)

        # Log deletion for debugging
        logger.info(
            f"User {user_id} deleted successfully. Transactions deleted: {deletion_result['transactions_deleted']}"
        )

        # Return 204 No Content for successful deletion
        response.status_code = 204
        return None

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error") from e


async def _save_input_data(content: bytes, filename: str, provider: str) -> None:
    """Save input data for analysis in development mode."""
    try:
        from pathlib import Path
        import os

        # Create input data directory
        input_dir = Path("extracted_texts/input_data")
        input_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(
            c for c in filename if c.isalnum() or c in "._- "
        ).rstrip()
        pdf_filename = f"input_{safe_filename}_{timestamp}.pdf"
        pdf_path = input_dir / pdf_filename

        # Save original PDF
        with open(pdf_path, "wb") as f:
            f.write(content)

        # Save metadata
        meta_filename = f"input_{safe_filename}_{timestamp}.meta.txt"
        meta_path = input_dir / meta_filename

        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"Original filename: {filename}\n")
            f.write(f"Provider: {provider}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"File size: {len(content)} bytes\n")
            f.write(f"Environment: {ENVIRONMENT}\n")
            f.write(f"Debug: {DEBUG}\n")

        logger.info(f"Input data saved for analysis: {pdf_path}")

    except Exception as e:
        logger.warning(f"Failed to save input data: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info" if DEBUG else "warning",
    )

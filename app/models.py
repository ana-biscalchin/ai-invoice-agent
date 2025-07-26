"""Pydantic models for data validation and API contracts."""

from datetime import date as date_type
from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    DEBIT = "debit"
    CREDIT = "credit"


class Transaction(BaseModel):
    """Individual transaction extracted from invoice."""

    date: date_type = Field(..., description="Transaction date in YYYY-MM-DD format")
    description: str = Field(
        ..., description="Transaction description", min_length=1, max_length=500
    )
    amount: float = Field(..., description="Transaction amount in local currency", ge=0)
    type: TransactionType = Field(
        default=TransactionType.DEBIT, description="Transaction type: debit or credit"
    )
    installments: int = Field(
        default=1, description="Number of installments for this transaction", ge=1
    )
    current_installment: int = Field(
        default=1, description="Current installment number", ge=1
    )
    total_purchase_amount: float = Field(
        default=0.0,
        description="Total purchase amount for installment transactions",
        ge=0,
    )
    due_date: str = Field(..., description="Invoice due date in YYYY-MM-DD format")
    category: str | None = Field(
        default=None, description="Transaction category (optional)"
    )

    def __str__(self) -> str:
        return f"{self.date} - {self.description}: {self.amount}"


class ProcessingMetadata(BaseModel):
    """Metadata about the processing operation."""

    processing_time_ms: int = Field(
        ..., description="Processing time in milliseconds", ge=0
    )
    total_transactions: int = Field(
        ..., description="Total number of transactions extracted", ge=0
    )
    confidence_score: float = Field(..., description="AI confidence score", ge=0, le=1)
    provider: str = Field(..., description="AI provider used for extraction")
    institution: str = Field(..., description="Detected financial institution")


class InvoiceResponse(BaseModel):
    """Complete response for invoice processing."""

    transactions: list[Transaction] = Field(
        ..., description="List of extracted transactions"
    )
    metadata: ProcessingMetadata = Field(
        ..., description="Processing metadata and statistics"
    )
    errors: list[str] | None = Field(
        default=None, description="List of validation errors, if any"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str | None = Field(None, description="API version")
    environment: str | None = Field(None, description="Environment name")
    ai_provider: str | None = Field(None, description="Default AI provider")


class APIInfoResponse(BaseModel):
    """API information response."""

    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    endpoints: dict = Field(..., description="Available endpoints")

"""Pydantic models for invoice processing."""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    CREDIT = "credit"
    DEBIT = "debit"


class Transaction(BaseModel):
    """Individual transaction extracted from invoice."""

    transaction_date: date = Field(
        ..., alias="date", description="Transaction date in YYYY-MM-DD format"
    )
    description: str = Field(
        ..., description="Transaction description", min_length=1, max_length=500
    )
    amount: float = Field(..., description="Transaction amount", ge=0)
    type: TransactionType = Field(..., description="Transaction type (credit or debit)")
    installments: int = Field(
        ..., description="Total number of installments for this transaction"
    )
    current_installment: int = Field(
        ..., description="Current installment number for this transaction"
    )
    total_purchase_amount: float = Field(
        ...,
        description="Total purchase amount (installment value * number of installments)",
        ge=0,
    )
    due_date: date = Field(..., description="Invoice due date in YYYY-MM-DD format")
    category: str | None = Field(
        default=None, description="Transaction category (optional)"
    )


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


class InvoiceResponse(BaseModel):
    """Response model for invoice processing."""

    transactions: List[Transaction] = Field(
        ..., description="List of extracted transactions"
    )
    metadata: ProcessingMetadata = Field(..., description="Processing metadata")
    errors: Optional[List[str]] = Field(
        default=None, description="Validation errors, if any"
    )


class InvoiceRequest(BaseModel):
    """Request model for invoice processing (for validation)."""

    file_size: int = Field(
        ..., description="File size in bytes", le=10_485_760
    )  # 10MB max
    file_type: str = Field(
        ..., description="File MIME type", pattern=r"^application/pdf$"
    )

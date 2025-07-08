"""Tests for Pydantic models."""

import pytest
from datetime import date

from app.models.invoice import (
    Transaction,
    TransactionType,
    ProcessingMetadata,
    InvoiceResponse,
)


class TestTransaction:
    """Test Transaction model."""

    def test_valid_transaction(self):
        """Test creating a valid transaction."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            description="UBER TRIP 001",
            amount=25.50,
            type=TransactionType.DEBIT,
        )

        assert transaction.transaction_date == date(2024, 1, 15)
        assert transaction.description == "UBER TRIP 001"
        assert transaction.amount == 25.50
        assert transaction.type == TransactionType.DEBIT

    def test_invalid_amount(self):
        """Test transaction with negative amount."""
        with pytest.raises(ValueError):
            Transaction(
                date=date(2024, 1, 15),
                description="Test",
                amount=-10.0,
                type=TransactionType.DEBIT,
            )

    def test_empty_description(self):
        """Test transaction with empty description."""
        with pytest.raises(ValueError):
            Transaction(
                date=date(2024, 1, 15),
                description="",
                amount=10.0,
                type=TransactionType.DEBIT,
            )


class TestProcessingMetadata:
    """Test ProcessingMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = ProcessingMetadata(
            processing_time_ms=1250,
            total_transactions=15,
            confidence_score=0.95,
            provider="openai",
        )

        assert metadata.processing_time_ms == 1250
        assert metadata.total_transactions == 15
        assert metadata.confidence_score == 0.95
        assert metadata.provider == "openai"

    def test_invalid_confidence_score(self):
        """Test metadata with invalid confidence score."""
        with pytest.raises(ValueError):
            ProcessingMetadata(
                processing_time_ms=1250,
                total_transactions=15,
                confidence_score=1.5,  # > 1.0
                provider="openai",
            )


class TestInvoiceResponse:
    """Test InvoiceResponse model."""

    def test_valid_response(self):
        """Test creating valid response."""
        transaction = Transaction(
            date=date(2024, 1, 15),
            description="Test transaction",
            amount=10.0,
            type=TransactionType.DEBIT,
        )

        metadata = ProcessingMetadata(
            processing_time_ms=1000,
            total_transactions=1,
            confidence_score=0.9,
            provider="openai",
        )

        response = InvoiceResponse(transactions=[transaction], metadata=metadata)

        assert len(response.transactions) == 1
        assert response.transactions[0].description == "Test transaction"
        assert response.metadata.total_transactions == 1

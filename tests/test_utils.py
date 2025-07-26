"""Tests for app.providers.utils module."""

from datetime import date

import pytest

from app.models import Transaction
from app.providers.utils import (
    clean_json_response,
    extract_invoice_metadata,
    parse_json_response,
    parse_transactions,
)


class TestCleanJsonResponse:
    """Test clean_json_response function."""

    def test_clean_json_with_markdown_json_block(self):
        """Test cleaning JSON with ```json markdown block."""
        raw_content = '```json\n{"test": "value"}\n```'
        result = clean_json_response(raw_content)
        assert result == '{"test": "value"}'

    def test_clean_json_with_markdown_block(self):
        """Test cleaning JSON with ``` markdown block."""
        raw_content = '```\n{"test": "value"}\n```'
        result = clean_json_response(raw_content)
        assert result == '{"test": "value"}'

    def test_clean_json_without_markdown(self):
        """Test cleaning JSON without markdown blocks."""
        raw_content = '{"test": "value"}'
        result = clean_json_response(raw_content)
        assert result == '{"test": "value"}'

    def test_clean_json_with_whitespace(self):
        """Test cleaning JSON with extra whitespace."""
        raw_content = '  ```json\n  {"test": "value"}\n  ```  '
        result = clean_json_response(raw_content)
        assert result == '{"test": "value"}'

    def test_clean_json_with_newlines(self):
        """Test cleaning JSON with newlines."""
        raw_content = '```json\n{\n  "test": "value"\n}\n```'
        result = clean_json_response(raw_content)
        assert result == '{\n  "test": "value"\n}'


class TestParseJsonResponse:
    """Test parse_json_response function."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        raw_content = '{"test": "value"}'
        result = parse_json_response(raw_content, "TestProvider")
        assert result == {"test": "value"}

    def test_parse_json_with_markdown(self):
        """Test parsing JSON with markdown blocks."""
        raw_content = '```json\n{"test": "value"}\n```'
        result = parse_json_response(raw_content, "TestProvider")
        assert result == {"test": "value"}

    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with extra text around it."""
        raw_content = 'Here is the response: {"test": "value"} and more text'
        result = parse_json_response(raw_content, "TestProvider")
        assert result == {"test": "value"}

    def test_parse_json_with_multiple_objects(self):
        """Test parsing JSON when multiple objects exist."""
        raw_content = '{"first": "object"} {"test": "value"} {"last": "object"}'
        with pytest.raises(ValueError):
            parse_json_response(raw_content, "TestProvider")

    def test_parse_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        raw_content = '{"invalid": json}'
        with pytest.raises(ValueError):
            parse_json_response(raw_content, "TestProvider")

    def test_parse_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        raw_content = ""
        with pytest.raises(ValueError, match="Invalid JSON response from TestProvider"):
            parse_json_response(raw_content, "TestProvider")

    def test_parse_no_json_object_raises_error(self):
        """Test that content without JSON object raises ValueError."""
        raw_content = "This is not JSON at all"
        with pytest.raises(ValueError, match="Invalid JSON response from TestProvider"):
            parse_json_response(raw_content, "TestProvider")


class TestParseTransactions:
    """Test parse_transactions function."""

    def test_parse_valid_transactions(self):
        """Test parsing valid transaction data."""
        data = {
            "transactions": [
                {
                    "date": "2025-01-15",
                    "description": "Test Purchase",
                    "amount": 100.50,
                    "type": "debit",
                    "installments": 1,
                    "current_installment": 1,
                    "total_purchase_amount": 100.50,
                    "due_date": "2025-02-15",
                    "category": "shopping",
                }
            ]
        }
        due_date = "2025-02-15"
        result = parse_transactions(data, due_date)

        assert len(result) == 1
        transaction = result[0]
        assert isinstance(transaction, Transaction)
        assert transaction.date == date(2025, 1, 15)
        assert transaction.description == "Test Purchase"
        assert transaction.amount == 100.50
        assert transaction.type.value == "debit"
        assert transaction.installments == 1
        assert transaction.current_installment == 1
        assert transaction.total_purchase_amount == 100.50
        assert transaction.due_date == "2025-02-15"
        assert transaction.category == "shopping"

    def test_parse_transactions_with_defaults(self):
        """Test parsing transactions with default values."""
        data = {
            "transactions": [
                {
                    "date": "2025-01-15",
                    "description": "Test Purchase",
                    "amount": 100.50,
                    "type": "debit",
                }
            ]
        }
        due_date = "2025-02-15"
        result = parse_transactions(data, due_date)

        assert len(result) == 1
        transaction = result[0]
        assert transaction.installments == 1
        assert transaction.current_installment == 1
        assert transaction.total_purchase_amount == 100.50
        assert transaction.due_date == "2025-02-15"
        assert transaction.category is None

    def test_parse_transactions_with_installments(self):
        """Test parsing transactions with installment information."""
        data = {
            "transactions": [
                {
                    "date": "2025-01-15",
                    "description": "Test Purchase",
                    "amount": 50.00,
                    "type": "debit",
                    "installments": 3,
                    "current_installment": 2,
                    "total_purchase_amount": 150.00,
                }
            ]
        }
        due_date = "2025-02-15"
        result = parse_transactions(data, due_date)

        assert len(result) == 1
        transaction = result[0]
        assert transaction.installments == 3
        assert transaction.current_installment == 2
        assert transaction.total_purchase_amount == 150.00

    def test_parse_empty_transactions(self):
        """Test parsing empty transactions list."""
        data = {"transactions": []}
        due_date = "2025-02-15"
        result = parse_transactions(data, due_date)

        assert len(result) == 0

    def test_parse_missing_transactions_key(self):
        """Test parsing when transactions key is missing."""
        data = {}
        due_date = "2025-02-15"
        result = parse_transactions(data, due_date)

        assert len(result) == 0

    def test_parse_transaction_missing_required_field(self):
        """Test parsing transaction with missing required field."""
        data = {
            "transactions": [
                {
                    "date": "2025-01-15",
                    "description": "Test Purchase",
                    # Missing amount field
                    "type": "debit",
                }
            ]
        }
        due_date = "2025-02-15"

        with pytest.raises(ValueError, match="Missing required field in transaction"):
            parse_transactions(data, due_date)

    def test_parse_transaction_invalid_amount(self):
        """Test parsing transaction with invalid amount."""
        data = {
            "transactions": [
                {
                    "date": "2025-01-15",
                    "description": "Test Purchase",
                    "amount": "invalid_amount",
                    "type": "debit",
                }
            ]
        }
        due_date = "2025-02-15"

        with pytest.raises(ValueError, match="Invalid value in transaction"):
            parse_transactions(data, due_date)


class TestExtractInvoiceMetadata:
    """Test extract_invoice_metadata function."""

    def test_extract_valid_metadata(self):
        """Test extracting valid invoice metadata."""
        data = {"invoice_total": 1500.75, "due_date": "2025-02-15"}
        result = extract_invoice_metadata(data)

        assert result == (1500.75, "2025-02-15")

    def test_extract_metadata_with_defaults(self):
        """Test extracting metadata with default values."""
        data = {}
        result = extract_invoice_metadata(data)

        assert result == (0.0, "")

    def test_extract_metadata_with_string_amount(self):
        """Test extracting metadata with string amount."""
        data = {"invoice_total": "1500.75", "due_date": "2025-02-15"}
        result = extract_invoice_metadata(data)

        assert result == (1500.75, "2025-02-15")

    def test_extract_metadata_with_int_amount(self):
        """Test extracting metadata with integer amount."""
        data = {"invoice_total": 1500, "due_date": "2025-02-15"}
        result = extract_invoice_metadata(data)

        assert result == (1500.0, "2025-02-15")

    def test_extract_metadata_missing_due_date(self):
        """Test extracting metadata with missing due date."""
        data = {"invoice_total": 1500.75}
        result = extract_invoice_metadata(data)

        assert result == (1500.75, "")

    def test_extract_metadata_missing_invoice_total(self):
        """Test extracting metadata with missing invoice total."""
        data = {"due_date": "2025-02-15"}
        result = extract_invoice_metadata(data)

        assert result == (0.0, "2025-02-15")


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_workflow_with_markdown(self):
        """Test complete workflow with markdown JSON response."""
        # Simulate AI response with markdown
        raw_response = """```json
{
  "invoice_total": 1500.75,
  "due_date": "2025-02-15",
  "transactions": [
    {
      "date": "2025-01-15",
      "description": "Test Purchase",
      "amount": 100.50,
      "type": "debit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 100.50,
      "due_date": "2025-02-15",
      "category": "shopping"
    }
  ]
}
```"""

        # Parse JSON response
        data = parse_json_response(raw_response, "TestProvider")

        # Extract metadata
        invoice_total, due_date = extract_invoice_metadata(data)

        # Parse transactions
        transactions = parse_transactions(data, due_date)

        # Assertions
        assert invoice_total == 1500.75
        assert due_date == "2025-02-15"
        assert len(transactions) == 1
        assert transactions[0].description == "Test Purchase"
        assert transactions[0].amount == 100.50

    def test_full_workflow_with_extra_text(self):
        """Test complete workflow with extra text around JSON."""
        # Simulate AI response with extra text
        raw_response = """Here is the extracted data:

{
  "invoice_total": 500.25,
  "due_date": "2025-03-15",
  "transactions": [
    {
      "date": "2025-02-15",
      "description": "Online Purchase",
      "amount": 500.25,
      "type": "debit"
    }
  ]
}

Please process this data."""

        # Parse JSON response
        data = parse_json_response(raw_response, "TestProvider")

        # Extract metadata
        invoice_total, due_date = extract_invoice_metadata(data)

        # Parse transactions
        transactions = parse_transactions(data, due_date)

        # Assertions
        assert invoice_total == 500.25
        assert due_date == "2025-03-15"
        assert len(transactions) == 1
        assert transactions[0].description == "Online Purchase"
        assert transactions[0].amount == 500.25

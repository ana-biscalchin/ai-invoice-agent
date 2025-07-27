"""Utility functions for AI providers."""

import json
from typing import Any

from app.models import Transaction


def clean_json_response(raw_content: str) -> str:
    """
    Clean JSON response by removing markdown code blocks.

    Args:
        raw_content: Raw response from AI provider

    Returns:
        Cleaned JSON string
    """
    content = raw_content.strip()

    # Remove markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


def parse_json_response(raw_content: str, provider_name: str = "AI provider") -> dict:
    """
    Parse JSON response from AI provider with basic cleaning.

    Args:
        raw_content: Raw response from AI provider
        provider_name: Name of the provider for error messages

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If JSON cannot be parsed
    """
    content = clean_json_response(raw_content)

    # Try to parse JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON object
        start_idx = content.find("{")
        end_idx = content.rfind("}")

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx : end_idx + 1]
            return json.loads(json_str)

        raise ValueError(
            f"Invalid JSON response from {provider_name}: {content[:200]}..."
        ) from None


def parse_transactions(
    data: dict[str, Any], invoice_due_date: str
) -> list[Transaction]:
    """
    Parse transaction data from AI response into Transaction objects.

    Args:
        data: JSON response from AI provider
        invoice_due_date: Invoice due date to use as fallback

    Returns:
        List of Transaction objects

    Raises:
        ValueError: If required fields are missing
    """
    transactions = []

    for tx_data in data.get("transactions", []):
        try:
            # Validate required fields are not None
            if tx_data.get("date") is None:
                raise ValueError("Transaction date cannot be None")
            if tx_data.get("description") is None:
                raise ValueError("Transaction description cannot be None")
            if tx_data.get("type") is None:
                raise ValueError("Transaction type cannot be None")
            
            # Handle None values for amount fields
            amount_raw = tx_data.get("amount")
            if amount_raw is None:
                raise ValueError("Transaction amount cannot be None")
            
            amount = float(amount_raw)
            
            total_purchase_amount_raw = tx_data.get("total_purchase_amount", amount_raw)
            if total_purchase_amount_raw is None:
                total_purchase_amount = amount
            else:
                total_purchase_amount = float(total_purchase_amount_raw)
            
            transaction = Transaction(
                date=tx_data["date"],
                description=tx_data["description"],
                amount=amount,
                type=tx_data["type"],
                installments=tx_data.get("installments", 1),
                current_installment=tx_data.get("current_installment", 1),
                total_purchase_amount=total_purchase_amount,
                due_date=tx_data.get("due_date", invoice_due_date),
            )
            transactions.append(transaction)

        except KeyError as e:
            raise ValueError(f"Missing required field in transaction: {e}") from e
        except ValueError as e:
            raise ValueError(f"Invalid value in transaction: {e}") from e

    return transactions


def extract_invoice_metadata(data: dict[str, Any]) -> tuple[float, str]:
    """
    Extract invoice metadata from AI response.

    Args:
        data: JSON response from AI provider

    Returns:
        Tuple of (invoice_total, due_date)
    """
    # Handle None values safely
    invoice_total_raw = data.get("invoice_total")
    if invoice_total_raw is None:
        invoice_total = 0.0
    else:
        try:
            invoice_total = float(invoice_total_raw)
        except (ValueError, TypeError):
            invoice_total = 0.0
    
    due_date = data.get("due_date", "")

    return invoice_total, due_date

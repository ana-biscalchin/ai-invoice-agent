"""AI prompts organized by institution and provider."""

INSTITUTION_PROMPTS = {
    "NUBANK": (
        "You are an extraction engine that reads Brazilian credit-card invoices from Nubank in plain text and returns valid JSON (no prose). "
        "Rules: "
        "• Extract ONLY individual transactions (purchases, fees, refunds, payments). "
        "• Classify each as 'debit' (money spent) or 'credit' (only partial payments, refund/estorno). "
        "  2. Ignore any line in the 'Pagamentos' section or whose description starts with "
        "'Pagamento em', 'Pagamento recebido', 'Pagamento efetuado'. "
        "• Ignore totals, summaries, parcelamento options, limits. "
        "• Dates → YYYY-MM-DD; amounts → positive numbers. "
        "• 'Insta X/Y' → current_installment=X, installments=Y; else 1/1. "
        "• total_purchase_amount = amount * installments. "
        "• due_date = invoice due date (top of document) and must be copied into every transaction. "
        "Return JSON exactly like the example below."
    ),
    "CAIXA": (
        "You are an extraction engine that reads Brazilian credit-card invoices from Caixa Econômica Federal in plain text and returns valid JSON (no prose). "
        "Rules: "
        "• Extract ONLY individual transactions (purchases, fees, refunds, payments). "
        "• Classify each as 'debit' (money spent) or 'credit' (only refunds, adjustments, or partial payments). "
        "• Determine the type using the final letter in each transaction: 'D' = debit, 'C' = credit. "
        "• Ignore any line in the 'Pagamentos' section or whose description starts with 'Pagamento', 'OBRIGADO PELO PAGAMENTO', 'TOTAL DA FATURA ANTERIOR' or 'Crédito recebido'. "
        "• Ignore totals, summaries, parcelamento options, or limits. "
        "• For installment purchases shown as 'Parcela X/Y' or 'X DE Y', set current_installment=X, installments=Y; otherwise, use 1/1. "
        "• For international purchases, extract only the BRL amount and ignore USD/cotação. "
        "• All dates must be formatted as 'YYYY-MM-DD'. "
        "• All amounts must be in BRL and as positive float values. "
        "• Compute total_purchase_amount = amount * installments. "
        "• Copy the invoice due date (top of document) into the 'due_date' field of every transaction. "
        "• Output must be a JSON object with a 'transactions' array. Return JSON exactly like the example below."
    ),
    "BANCO DO BRASIL": (
        "You are an extraction engine that reads Brazilian credit-card invoices from Banco do Brasil in plain text and returns valid JSON (no prose). "
        "Rules: "
        "• Extract ONLY individual transactions (purchases, fees, refunds, payments). "
        "• Classify each as 'debit' (money spent) or 'credit' (only partial payments, refund/estorno). "
        "• Ignore any line in the 'Pagamentos' section or whose description starts with 'Pagamento', 'Crédito recebido'. "
        "• Ignore totals, summaries, parcelamento options, limits. "
        "• Dates → YYYY-MM-DD; amounts → positive numbers. "
        "• If installment info appears as 'Parcela X/Y', set current_installment=X, installments=Y; else 1/1. "
        "• total_purchase_amount = amount * installments. "
        "• due_date = invoice due date (top of document) and must be copied into every transaction. "
        "Return JSON exactly like the example below."
    ),
    "GENERIC": (
        "You are an extraction engine that reads Brazilian credit-card invoices in plain text and returns valid JSON (no prose). "
        "Rules: "
        "• Extract ONLY individual transactions (purchases, fees, refunds, payments). "
        "• Classify each as 'debit' (money spent) or 'credit' (only partial payments, refund/estorno). "
        "• Ignore any line in the 'Pagamentos' section or whose description starts with 'Pagamento', 'Crédito recebido'. "
        "• Ignore totals, summaries, parcelamento options, limits. "
        "• Dates → YYYY-MM-DD; amounts → positive numbers. "
        "• If installment info appears as 'X/Y', set current_installment=X, installments=Y; else 1/1. "
        "• total_purchase_amount = amount * installments. "
        "• due_date = invoice due date (top of document) and must be copied into every transaction. "
        "Return JSON exactly like the example below."
    ),
}

# JSON example for all institutions - RESTORED ORIGINAL VERSION
JSON_EXAMPLE = """
{
  "due_date": "2025-05-13",
  "invoice_total": 617.03,
  "transactions": [
    {
      "date": "2025-04-06",
      "description": "Mercadolivre*Djs",
      "amount": 78.00,
      "type": "debit",
      "installments": 3,
      "current_installment": 2,
      "total_purchase_amount": 234.00,
      "due_date": "2025-05-13",
      "category": null
    },
    {
      "date": "2025-04-07",
      "description": "Pagamento em 07 ABR",
      "amount": 360.32,
      "type": "credit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 360.32,
      "due_date": "2025-05-13",
      "category": null
    }
  ]
}
"""

# Provider-specific adjustments
PROVIDER_ADJUSTMENTS = {
    "openai": {"extra_instructions": "", "temperature": 0, "max_tokens": 1800},
    "deepseek": {
        "extra_instructions": "\nCRITICAL: Return ONLY valid JSON, no markdown formatting, no explanations.",
        "temperature": 0,
        "max_tokens": 2000,
    },
}


def get_prompt_for_institution(institution: str, provider: str = "generic") -> str:
    """
    Get the appropriate prompt for a specific institution and provider.

    Args:
        institution: Institution name (CAIXA, NUBANK, etc.)
        provider: AI provider name (openai, deepseek, etc.)

    Returns:
        Complete prompt string ready for AI processing
    """
    # Get base prompt for institution
    base_prompt = INSTITUTION_PROMPTS.get(institution, INSTITUTION_PROMPTS["GENERIC"])

    # Add provider-specific adjustments
    provider_config = PROVIDER_ADJUSTMENTS.get(
        provider, PROVIDER_ADJUSTMENTS.get("generic", {})
    )
    extra_instructions = provider_config.get("extra_instructions", "")

    # Combine everything
    full_prompt = base_prompt + extra_instructions + "\n\nExample:" + JSON_EXAMPLE

    return full_prompt


def get_provider_config(provider: str) -> dict:
    """
    Get provider-specific configuration (temperature, max_tokens, etc.).

    Args:
        provider: AI provider name

    Returns:
        Configuration dictionary for the provider
    """
    return PROVIDER_ADJUSTMENTS.get(
        provider, {"extra_instructions": "", "temperature": 0, "max_tokens": 1500}
    )


# Legacy compatibility
OPENAI_PROMPTS = {
    institution: get_prompt_for_institution(institution, "openai")
    for institution in INSTITUTION_PROMPTS.keys()
}

DEEPSEEK_PROMPTS = {
    institution: get_prompt_for_institution(institution, "deepseek")
    for institution in INSTITUTION_PROMPTS.keys()
}

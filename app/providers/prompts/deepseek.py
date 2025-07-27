"""DeepSeek-specific prompts and configurations."""

# Base prompts for each institution
INSTITUTION_PROMPTS = {
    "NUBANK": (
        "You are an extraction engine that reads Brazilian credit-card invoices from Nubank in plain text and returns valid JSON (no prose). "
        "Rules: "
        "• Extract ONLY individual transactions (purchases, fees, refunds, payments). "
        "• Classify each as 'debit' (money spent) or 'credit' (only partial payments, refund/estorno). "
        "• Ignore any line in the 'Pagamentos' section or whose description starts with "
        "'Pagamento em', 'Pagamento recebido', 'Pagamento efetuado'. "
        "• Ignore totals, summaries, parcelamento options, limits. "
        "• Dates → YYYY-MM-DD; amounts → positive numbers. "
        "• 'Insta X/Y' → current_installment=X, installments=Y; else 1/1. "
        "• total_purchase_amount = amount * installments. "
        "• due_date = invoice due date (top of document) and must be copied into every transaction. "
        "CRITICAL: Return ONLY valid JSON, no markdown formatting, no explanations."
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
        "• Output must be a JSON object with a 'transactions' array. "
        "CRITICAL: Return ONLY valid JSON, no markdown formatting, no explanations."
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
        "CRITICAL: Return ONLY valid JSON, no markdown formatting, no explanations."
    ),
}

# JSON example
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
      "due_date": "2025-05-13"
    },
    {
      "date": "2025-04-07",
      "description": "Pagamento em 07 ABR",
      "amount": 360.32,
      "type": "credit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 360.32,
      "due_date": "2025-05-13"
    }
  ]
}
"""

# DeepSeek-specific configuration
CONFIG = {
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com/v1/chat/completions",
    "temperature": 0,
    "max_tokens": 2000,
    "timeout": 60,
    "max_retries": 3,
    "retry_delay": 1,
    "text_limit": 8000,
}


def get_prompt(institution: str) -> str:
    """Get DeepSeek prompt for specific institution."""
    base_prompt = INSTITUTION_PROMPTS.get(institution, INSTITUTION_PROMPTS["GENERIC"])
    return base_prompt + "\n\nExample:" + JSON_EXAMPLE


def get_config() -> dict:
    """Get DeepSeek configuration."""
    return CONFIG

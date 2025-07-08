from openai import AsyncOpenAI
import json, logging
from app.core.config import settings
from app.models.invoice import Transaction
from app.providers.base import AIProvider
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

logger = logging.getLogger(__name__)

MODEL_NAME = "gpt-4o-mini"

# Prompts por instituição
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
        "Return JSON exactly like the example."
    ),
    "CAIXA": (
        "You are an extraction engine that reads Brazilian credit-card invoices from Caixa Econômica Federal in plain text and returns valid JSON (no prose). "
        "Rules: "
        "• Extract ONLY individual transactions (purchases, fees, refunds, payments). "
        "• Classify each as 'debit' (money spent) or 'credit' (only partial payments, refund/estorno). "
        "• Ignore any line in the 'Pagamentos' section or whose description starts with 'Pagamento', 'Crédito recebido'. "
        "• Ignore totals, summaries, parcelamento options, limits. "
        "• Dates → YYYY-MM-DD; amounts → positive numbers. "
        "• If installment info appears as 'Parcela X/Y', set current_installment=X, installments=Y; else 1/1. "
        "• total_purchase_amount = amount * installments. "
        "• due_date = invoice due date (top of document) and must be copied into every transaction. "
        "Return JSON exactly like the example."
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
        "Return JSON exactly like the example."
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
        "Return JSON exactly like the example."
    ),
}

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


class OpenAIProvider(AIProvider):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.logger = logger

    @property
    def provider_name(self) -> str:
        return "openai"

    def detect_institution(self, text: str) -> str:
        """Detects the financial institution from the invoice text."""
        text_upper = text.upper()
        if "NUBANK" in text_upper:
            return "NUBANK"
        if "CAIXA" in text_upper or "CAIXA ECONOMICA" in text_upper:
            return "CAIXA"
        if "BANCO DO BRASIL" in text_upper or "BANCO DO BRASIL S.A." in text_upper:
            return "BANCO DO BRASIL"
        return "GENERIC"

    async def extract_transactions(self, text: str):
        try:
            institution = self.detect_institution(text)
            prompt = INSTITUTION_PROMPTS.get(institution, INSTITUTION_PROMPTS["GENERIC"])
            messages = [
                ChatCompletionSystemMessageParam(
                    role="system", content=prompt + "\nExample:" + JSON_EXAMPLE
                ),
                ChatCompletionUserMessageParam(role="user", content=text[:8000]),
            ]

            resp = await self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0,
                max_tokens=1800,
                timeout=settings.timeout_seconds,
            )

            raw = resp.choices[0].message.content
            if raw is None:
                raise ValueError("Empty response from OpenAI")

            data = json.loads(raw)
            transactions, invoice_total, due_date = (
                [],
                data["invoice_total"],
                data["due_date"],
            )

            for tx in data["transactions"]:
                transactions.append(
                    Transaction(
                        date=tx["date"],
                        description=tx["description"],
                        amount=float(tx["amount"]),
                        type=tx["type"],
                        installments=tx["installments"],
                        current_installment=tx["current_installment"],
                        total_purchase_amount=float(tx["total_purchase_amount"]),
                        due_date=tx["due_date"],
                        category=tx.get("category"),
                    )
                )

            self.logger.info(f"Extracted {len(transactions)} transactions for {institution}")
            return transactions, invoice_total, due_date

        except Exception as e:
            self.logger.error(f"OpenAI processing failed: {e}")
            raise

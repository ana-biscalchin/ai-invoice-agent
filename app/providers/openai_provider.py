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
from app.providers.prompts import INSTITUTION_PROMPTS, JSON_EXAMPLE
from app.providers.institution_detection import detect_institution

logger = logging.getLogger(__name__)

MODEL_NAME = "gpt-4o-mini"

class OpenAIProvider(AIProvider):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.logger = logger

    @property
    def provider_name(self) -> str:
        return "openai"

    async def extract_transactions(self, text: str):
        try:
            institution = detect_institution(text)
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

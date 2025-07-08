"""OpenAI provider for transaction extraction."""

import json
from typing import List, Tuple

from openai import AsyncOpenAI
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from app.models import Transaction
from app.providers.base import AIProvider
from app.providers.prompts import get_prompt_for_institution, get_provider_config


class OpenAIProvider(AIProvider):
    """OpenAI GPT-based transaction extraction provider."""

    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key. If None, will be read from environment.
        """
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            # Will use OPENAI_API_KEY environment variable
            self.client = AsyncOpenAI()

        # Get provider configuration
        self.config = get_provider_config("openai")

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "openai"

    async def extract_transactions(
        self, text: str, institution: str
    ) -> Tuple[List[Transaction], float, str]:
        """
        Extract transactions using OpenAI GPT.

        Args:
            text: Cleaned invoice text
            institution: Detected institution (CAIXA, NUBANK, etc.)

        Returns:
            Tuple of (transactions, invoice_total, due_date)

        Raises:
            Exception: If API call fails or response is invalid
        """
        try:
            # Get institution-specific prompt
            prompt = get_prompt_for_institution(institution, "openai")

            # Prepare messages
            messages = [
                ChatCompletionSystemMessageParam(role="system", content=prompt),
                ChatCompletionUserMessageParam(
                    role="user", content=text[:8000]  # Limit text size
                ),
            ]

            # Make API call
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=self.config.get("temperature", 0),
                max_tokens=self.config.get("max_tokens", 1800),
                timeout=60,
            )

            # Extract response
            raw_content = response.choices[0].message.content
            if raw_content is None:
                raise ValueError("Empty response from OpenAI")

            # Parse JSON response
            data = json.loads(raw_content)

            # Extract invoice metadata first to use as fallback
            invoice_total = float(data.get("invoice_total", 0))
            due_date = data.get("due_date", "")

            # Convert to Transaction objects
            transactions = []
            for tx_data in data.get("transactions", []):
                transaction = Transaction(
                    date=tx_data["date"],
                    description=tx_data["description"],
                    amount=float(tx_data["amount"]),
                    type=tx_data["type"],
                    installments=tx_data.get("installments", 1),
                    current_installment=tx_data.get("current_installment", 1),
                    total_purchase_amount=float(
                        tx_data.get("total_purchase_amount", tx_data["amount"])
                    ),
                    due_date=tx_data.get(
                        "due_date", due_date
                    ),  # Use invoice due_date as fallback
                    category=tx_data.get("category"),
                )
                transactions.append(transaction)

            return transactions, invoice_total, due_date

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in OpenAI response: {e}")
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

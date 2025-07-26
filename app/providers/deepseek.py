"""DeepSeek provider for transaction extraction."""

import asyncio
import os

import httpx

from app.models import Transaction
from app.providers.base import AIProvider
from app.providers.prompts import get_config, get_prompt
from app.providers.utils import (
    extract_invoice_metadata,
    parse_json_response,
    parse_transactions,
)


class DeepSeekProvider(AIProvider):
    """DeepSeek-based transaction extraction provider."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key. If None, will be read from environment.
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")

        # Get provider configuration
        self.config = get_config("deepseek")

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "deepseek"

    async def extract_transactions(
        self, text: str, institution: str
    ) -> tuple[list[Transaction], float, str]:
        """
        Extract transactions using DeepSeek API.

        Args:
            text: Cleaned invoice text
            institution: Detected institution (CAIXA, NUBANK, etc.)

        Returns:
            Tuple of (transactions, invoice_total, due_date)

        Raises:
            Exception: If API call fails or response is invalid
        """
        try:
            prompt = get_prompt("deepseek", institution)

            # Clean and limit text
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            cleaned_text = "\n".join(lines)[: self.config["text_limit"]]

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": cleaned_text},
            ]

            payload = {
                "model": self.config["model"],
                "messages": messages,
                "temperature": self.config["temperature"],
                "max_tokens": self.config["max_tokens"],
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response_data = await self._make_request_with_retries(payload, headers)

            raw_content = response_data["choices"][0]["message"]["content"]
            if raw_content is None:
                raise ValueError("Empty response from DeepSeek")

            # Simple JSON parsing with basic cleaning
            data = parse_json_response(raw_content, "DeepSeek")

            # Extract metadata and transactions
            invoice_total, due_date = extract_invoice_metadata(data)
            transactions = parse_transactions(data, due_date)

            return transactions, invoice_total, due_date

        except Exception as e:
            raise Exception(f"DeepSeek API error: {e}") from e

    async def _make_request_with_retries(self, payload: dict, headers: dict) -> dict:
        """Make HTTP request with retry logic."""
        for attempt in range(self.config["max_retries"]):
            try:
                async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                    response = await client.post(
                        self.config["base_url"],
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    return response.json()

            except Exception:
                if attempt == self.config["max_retries"] - 1:
                    raise
                await asyncio.sleep(self.config["retry_delay"] * (attempt + 1))
                continue

        raise RuntimeError("Unexpected end of retry loop")

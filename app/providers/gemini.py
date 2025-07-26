import os

import google.generativeai as genai

from app.models import Transaction
from app.providers.base import AIProvider
from app.providers.prompts import get_config, get_prompt
from app.providers.utils import (
    extract_invoice_metadata,
    parse_json_response,
    parse_transactions,
)


class GeminiProvider(AIProvider):
    """Gemini GPT-based transaction extraction provider."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize Gemini provider.
        """
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        # Configure Gemini with the API key
        genai.configure(api_key=self.api_key)

        # Get provider configuration
        self.config = get_config("gemini")

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "gemini"

    async def extract_transactions(
        self, text: str, institution: str
    ) -> tuple[list[Transaction], float, str]:
        """
        Extract transactions using Gemini GPT.

        Args:
            text: Cleaned invoice text
            institution: Detected institution (CAIXA, NUBANK, etc.)

        Returns:
            Tuple of (transactions, invoice_total, due_date)

        Raises:
            Exception: If API call fails or response is invalid
        """

        try:
            prompt = get_prompt("gemini", institution)
 
            # Create Gemini model
            model = genai.GenerativeModel(self.config["model"])

            # Generate content
            response = await model.generate_content_async(
                [prompt, text],
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config["temperature"],
                    max_output_tokens=self.config["max_tokens"],
                ),
            )

            print(response.text)

            data = parse_json_response(response.text, "Gemini")

            invoice_total, due_date = extract_invoice_metadata(data)

            transactions = parse_transactions(data, due_date)

            return transactions, invoice_total, due_date

        except Exception as e:
            raise Exception(f"Gemini API error: {e}") from e

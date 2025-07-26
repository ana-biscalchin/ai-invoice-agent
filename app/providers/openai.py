"""OpenAI provider for transaction extraction."""


from openai import AsyncOpenAI
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)

from app.models import Transaction
from app.providers.base import AIProvider
from app.providers.prompts import get_config, get_prompt
from app.providers.utils import (
    extract_invoice_metadata,
    parse_json_response,
    parse_transactions,
)


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
        self.config = get_config("openai")

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "openai"

    async def extract_transactions(
        self, text: str, institution: str
    ) -> tuple[list[Transaction], float, str]:
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
            prompt = get_prompt("openai", institution)

            # Prepare messages
            messages = [
                ChatCompletionSystemMessageParam(role="system", content=prompt),
                ChatCompletionUserMessageParam(
                    role="user", content=text[: self.config["text_limit"]]
                ),
            ]

            # Make API call
            response = await self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                timeout=self.config["timeout"],
            )

            # Extract response
            raw_content = response.choices[0].message.content
            if raw_content is None:
                raise ValueError("Empty response from OpenAI")

            # Parse JSON response
            data = parse_json_response(raw_content, "OpenAI")

            # Extract metadata and transactions
            invoice_total, due_date = extract_invoice_metadata(data)
            transactions = parse_transactions(data, due_date)

            return transactions, invoice_total, due_date

        except Exception as e:
            raise Exception(f"OpenAI API error: {e}") from e

"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod

from app.models import Transaction


class AIProvider(ABC):
    """
    Abstract interface that all AI providers must implement.

    This ensures consistency across different AI providers (OpenAI, DeepSeek, Claude, etc.)
    and allows the system to swap providers without changing client code.
    """

    @abstractmethod
    async def extract_transactions(
        self, text: str, institution: str
    ) -> tuple[list[Transaction], float, str]:
        """
        Extract transactions from invoice text.

        Args:
            text: Cleaned text extracted from PDF
            institution: Detected institution (CAIXA, NUBANK, etc.)

        Returns:
            Tuple containing:
            - List of Transaction objects
            - Invoice total amount
            - Due date string (YYYY-MM-DD format)

        Raises:
            Exception: If extraction fails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider identifier (e.g., 'openai', 'deepseek', 'claude').

        Returns:
            String identifier for this provider
        """
        pass

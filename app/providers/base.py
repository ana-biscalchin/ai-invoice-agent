"""Base interface for AI providers."""

from abc import ABC, abstractmethod
from typing import List

from app.models.invoice import Transaction


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def extract_transactions(self, text: str) -> List[Transaction]:
        """
        Extract transactions from invoice text.

        Args:
            text: Raw text extracted from PDF

        Returns:
            List of structured transactions

        Raises:
            Exception: If AI processing fails
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass

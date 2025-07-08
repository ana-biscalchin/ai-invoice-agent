"""AI provider factory and exports."""

from .base import AIProvider
from .openai import OpenAIProvider
from .deepseek import DeepSeekProvider

# Provider registry
PROVIDERS = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
}


def create_provider(name: str, **kwargs) -> AIProvider:
    """
    Create an AI provider instance.

    Args:
        name: Provider name ('openai', 'deepseek', etc.)
        **kwargs: Additional arguments to pass to provider constructor

    Returns:
        Initialized provider instance

    Raises:
        ValueError: If provider name is not supported
    """
    if name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider '{name}'. Available: {available}")

    provider_class = PROVIDERS[name]
    return provider_class(**kwargs)


def list_providers() -> list:
    """Get list of available provider names."""
    return list(PROVIDERS.keys())


__all__ = [
    "AIProvider",
    "OpenAIProvider",
    "DeepSeekProvider",
    "create_provider",
    "list_providers",
]

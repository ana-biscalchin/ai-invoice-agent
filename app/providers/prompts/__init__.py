"""Prompts package for AI providers."""

from .deepseek import (
    get_config as get_deepseek_config,
)
from .deepseek import (
    get_prompt as get_deepseek_prompt,
)
from .gemini import get_config as get_gemini_config
from .gemini import get_prompt as get_gemini_prompt
from .openai import get_config as get_openai_config
from .openai import get_prompt as get_openai_prompt


def get_prompt(provider: str, institution: str) -> str:
    """Get prompt for specific provider and institution."""
    if provider == "openai":
        return get_openai_prompt(institution)
    elif provider == "deepseek":
        return get_deepseek_prompt(institution)
    elif provider == "gemini":
        return get_gemini_prompt(institution)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_config(provider: str) -> dict:
    """Get configuration for specific provider."""
    if provider == "openai":
        return get_openai_config()
    elif provider == "deepseek":
        return get_deepseek_config()
    elif provider == "gemini":
        return get_gemini_config()
    else:
        raise ValueError(f"Unknown provider: {provider}")

"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Environment
    environment: str = "development"
    debug: bool = False

    # AI Provider
    ai_provider: str = "openai"
    openai_api_key: str = ""

    # File processing limits
    max_file_size: int = 10_485_760  # 10MB
    timeout_seconds: int = 60

    # API settings
    api_title: str = "AI Invoice Agent"
    api_version: str = "0.1.0"
    api_description: str = "Intelligent microservice for extracting structured data from credit card invoices"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

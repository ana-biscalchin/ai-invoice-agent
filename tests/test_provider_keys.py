"""Simple integration tests to validate API keys for each provider."""

import os
import pytest
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.providers import create_provider


class TestProviderIntegration:
    """Test if providers can make real API calls."""

    @pytest.mark.asyncio
    async def test_openai_integration(self):
        """Test OpenAI API integration with a simple call."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        try:
            provider = create_provider("openai", api_key=api_key)

            # Simple test text
            test_text = "Teste de integração com OpenAI"
            test_institution = "GENERIC"

            # Make a real API call
            transactions, total, due_date = await provider.extract_transactions(
                test_text, test_institution
            )

            print(f"✅ OpenAI: API responded successfully")
            print(f"   - Transactions: {len(transactions)}")
            print(f"   - Total: {total}")
            print(f"   - Due date: {due_date}")

        except Exception as e:
            pytest.fail(f"OpenAI API integration failed: {e}")

    @pytest.mark.asyncio
    async def test_deepseek_integration(self):
        """Test DeepSeek API integration with a simple call."""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            pytest.skip("DEEPSEEK_API_KEY not set")

        try:
            provider = create_provider("deepseek", api_key=api_key)

            # Simple test text
            test_text = "Teste de integração com DeepSeek"
            test_institution = "GENERIC"

            # Make a real API call
            transactions, total, due_date = await provider.extract_transactions(
                test_text, test_institution
            )

            print(f"✅ DeepSeek: API responded successfully")
            print(f"   - Transactions: {len(transactions)}")
            print(f"   - Total: {total}")
            print(f"   - Due date: {due_date}")

        except Exception as e:
            pytest.fail(f"DeepSeek API integration failed: {e}")

    @pytest.mark.asyncio
    async def test_gemini_integration(self):
        """Test Gemini API integration with a simple call."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")

        try:
            provider = create_provider("gemini", api_key=api_key)

            # Simple test text
            test_text = "Teste de integração com Gemini"
            test_institution = "GENERIC"

            # Make a real API call
            transactions, total, due_date = await provider.extract_transactions(
                test_text, test_institution
            )

            print(f"✅ Gemini: API responded successfully")
            print(f"   - Transactions: {len(transactions)}")
            print(f"   - Total: {total}")
            print(f"   - Due date: {due_date}")

        except Exception as e:
            pytest.fail(f"Gemini API integration failed: {e}")

    def test_providers_configured(self):
        """Check which providers are configured."""
        providers = []

        if os.getenv("OPENAI_API_KEY"):
            providers.append("openai")
        if os.getenv("DEEPSEEK_API_KEY"):
            providers.append("deepseek")
        if os.getenv("GEMINI_API_KEY"):
            providers.append("gemini")

        if len(providers) == 0:
            print("⚠️  No API keys configured")
            print(
                "   Set at least one of: OPENAI_API_KEY, DEEPSEEK_API_KEY, GEMINI_API_KEY"
            )
        else:
            print(f"✅ Configured providers: {', '.join(providers)}")


if __name__ == "__main__":
    # Run tests directly for quick validation
    import sys

    print("🔍 Testing provider integrations...")

    async def run_tests():
        test = TestProviderIntegration()

        # Test each provider
        try:
            await test.test_openai_integration()
        except Exception as e:
            print(f"❌ OpenAI: {e}")

        try:
            await test.test_deepseek_integration()
        except Exception as e:
            print(f"❌ DeepSeek: {e}")

        try:
            await test.test_gemini_integration()
        except Exception as e:
            print(f"❌ Gemini: {e}")

        try:
            test.test_providers_configured()
        except Exception as e:
            print(f"❌ Configuration: {e}")

    asyncio.run(run_tests())
    print("✅ Integration tests complete")

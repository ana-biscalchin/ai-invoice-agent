"""DeepSeek provider for transaction extraction."""

import asyncio
import json
from typing import List, Tuple

import httpx

from app.models import Transaction
from app.providers.base import AIProvider
from app.providers.prompts import get_prompt_for_institution, get_provider_config


class DeepSeekProvider(AIProvider):
    """DeepSeek-based transaction extraction provider."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key. If None, will be read from environment.
        """
        if not api_key:
            import os
            api_key = os.getenv("DEEPSEEK_API_KEY")

        if not api_key:
            raise ValueError("DeepSeek API key not provided")

        self.api_key = api_key
        self.config = get_provider_config("deepseek")

        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.max_retries = 3
        self.retry_delay = 1

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "deepseek"

    async def extract_transactions(
        self, text: str, institution: str
    ) -> Tuple[List[Transaction], float, str]:
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
            prompt = get_prompt_for_institution(institution, "deepseek")

            lines = [line.strip() for line in text.split("\n") if line.strip()]
            cleaned_text = "\n".join(lines)[:8000]

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": cleaned_text},
            ]

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": self.config.get("temperature", 0),
                "max_tokens": self.config.get("max_tokens", 2000),
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response_data = await self._make_request_with_retries(payload, headers)

            raw_content = response_data["choices"][0]["message"]["content"]
            if raw_content is None:
                raise ValueError("Empty response from DeepSeek")

            import logging

            logger = logging.getLogger(__name__)

            try:
                cleaned_json = self._clean_json_response(raw_content)
                data = json.loads(cleaned_json)
            except (ValueError, json.JSONDecodeError) as first_error:
                logger.warning(f"First JSON parsing attempt failed: {first_error}")

                try:
                    start = raw_content.find("{")
                    end = raw_content.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        alternative_json = raw_content[start : end + 1]
                        data = json.loads(alternative_json)
                        logger.info(
                            "Successfully parsed JSON using alternative cleaning"
                        )
                    else:
                        raise ValueError("No JSON block found")

                except (ValueError, json.JSONDecodeError) as second_error:
                    logger.warning(
                        f"Alternative JSON parsing also failed: {second_error}"
                    )

                    try:
                        logger.info(
                            "Attempting fallback parsing without JSON structure"
                        )
                        data = self._try_fallback_parsing(raw_content)
                        if not data.get("due_date"):
                            data["due_date"] = "2025-12-31"  # Default fallback date
                    except Exception as fallback_error:
                        logger.error(f"Fallback parsing also failed: {fallback_error}")
                        raise ValueError(
                            f"Could not parse DeepSeek response in any format. Original error: {first_error}. Raw preview: {raw_content[:200]}..."
                        )

            invoice_total = float(data.get("invoice_total", 0))
            due_date = data.get("due_date", "")

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
                    ), 
                    category=tx_data.get("category"),
                )
                transactions.append(transaction)

            return transactions, invoice_total, due_date

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from DeepSeek: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in DeepSeek response: {e}")
        except Exception as e:
            # Enhanced error with more context
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"DeepSeek provider error: {e}")
            logger.error(f"Institution: {institution}")
            logger.error(f"Text length: {len(text)}")
            raise Exception(f"DeepSeek API error: {e}")

    async def _make_request_with_retries(self, payload: dict, headers: dict) -> dict:
        """Make HTTP request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        self.base_url,
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    return response.json()

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))
                continue

        raise RuntimeError("Unexpected end of retry loop")

    def _clean_json_response(self, raw_content: str) -> str:
        """
        Clean DeepSeek response to extract valid JSON.

        DeepSeek sometimes wraps JSON in markdown code blocks or adds explanations.
        """
        content = raw_content.strip()

        # Remove markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # Try to find JSON object boundaries more aggressively
        start_idx = content.find("{")
        end_idx = content.rfind("}")

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            # Extract only the JSON part
            content = content[start_idx : end_idx + 1]

        # Final validation
        if not (content.startswith("{") and content.endswith("}")):
            # Log the problematic content for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Invalid JSON structure in DeepSeek response: {content[:200]}..."
            )
            raise ValueError("DeepSeek response is not a valid JSON object")

        return content

    def _try_fallback_parsing(self, raw_content: str) -> dict:
        """
        Attempt to extract basic information even from malformed responses.

        This is a last resort when JSON parsing fails completely.
        """
        # Try to find basic patterns
        result = {"transactions": [], "invoice_total": 0.0, "due_date": ""}

        lines = raw_content.split("\n")
        for line in lines:
            line = line.strip()

            # Try to find total amount
            if "total" in line.lower() and "R$" in line:
                import re

                amount_match = re.search(r"R?\$?\s*(\d+[,.]?\d*)", line)
                if amount_match:
                    try:
                        amount_str = amount_match.group(1).replace(",", ".")
                        result["invoice_total"] = float(amount_str)
                    except:
                        pass

            # Try to find due date
            if "vencimento" in line.lower() or "due" in line.lower():
                import re

                date_match = re.search(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})", line)
                if date_match:
                    date_str = date_match.group(1)
                    if "/" in date_str:
                        # Convert DD/MM/YYYY to YYYY-MM-DD
                        parts = date_str.split("/")
                        if len(parts) == 3:
                            result["due_date"] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    else:
                        result["due_date"] = date_str

        return result

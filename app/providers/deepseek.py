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
    
    def __init__(self, api_key: str = None):
        """
        Initialize DeepSeek provider.
        
        Args:
            api_key: DeepSeek API key. If None, will be read from environment.
        """
        if not api_key:
            # Try to get from environment
            import os
            api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key:
            raise ValueError("DeepSeek API key not provided")
            
        self.api_key = api_key
        self.config = get_provider_config("deepseek")
        
        # API configuration
        self.model = "deepseek-chat"
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.max_retries = 3
        self.retry_delay = 1
    
    @property
    def name(self) -> str:
        """Provider identifier."""
        return "deepseek"
    
    async def extract_transactions(self, text: str, institution: str) -> Tuple[List[Transaction], float, str]:
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
            # Get institution-specific prompt
            prompt = get_prompt_for_institution(institution, "deepseek")
            
            # Clean and limit text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_text = '\n'.join(lines)[:8000]
            
            # Prepare request
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
            
            # Make API call with retries
            response_data = await self._make_request_with_retries(payload, headers)
            
            # Parse response
            raw_content = response_data["choices"][0]["message"]["content"]
            if raw_content is None:
                raise ValueError("Empty response from DeepSeek")
            
            # Clean JSON response (DeepSeek sometimes adds markdown formatting)
            cleaned_json = self._clean_json_response(raw_content)
            
            # Parse JSON
            data = json.loads(cleaned_json)
            
            # Convert to Transaction objects
            transactions = []
            for tx_data in data.get("transactions", []):
                transaction = Transaction(
                    date=tx_data["date"],
                    description=tx_data["description"],
                    amount=float(tx_data["amount"]),
                    type=tx_data["type"],
                    installments=tx_data.get("installments", 1),
                    current_installment=tx_data.get("current_installment", 1),
                    total_purchase_amount=float(tx_data.get("total_purchase_amount", tx_data["amount"])),
                    due_date=tx_data["due_date"],
                    category=tx_data.get("category"),
                )
                transactions.append(transaction)
            
            # Extract invoice metadata
            invoice_total = float(data.get("invoice_total", 0))
            due_date = data.get("due_date", "")
            
            return transactions, invoice_total, due_date
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from DeepSeek: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in DeepSeek response: {e}")
        except Exception as e:
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
        
        # Ensure it's a JSON object
        if not (content.startswith("{") and content.endswith("}")):
            raise ValueError("DeepSeek response is not a valid JSON object")
        
        return content 
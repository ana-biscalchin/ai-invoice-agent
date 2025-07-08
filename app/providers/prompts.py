"""AI prompts organized by institution and provider."""

# Base prompts by institution
INSTITUTION_PROMPTS = {
    "CAIXA": """
Você é um especialista em extrair dados de faturas do Cartão Caixa.

REGRAS ESPECÍFICAS PARA CAIXA:
- Data, descrição e valor podem estar em linhas separadas
- Valores terminam com 'D' (débito) ou 'C' (crédito)
- Seções importantes: COMPRAS, COMPRAS PARCELADAS, COMPRAS INTERNACIONAIS
- Formato de data: DD/MM
- Valores no formato: 999,99

INSTRUÇÕES:
1. Extraia TODAS as transações das seções relevantes
2. Para cada transação, identifique: data, descrição e valor
3. Determine se é débito (D) ou crédito (C)
4. Encontre o valor total da fatura e data de vencimento
5. Retorne apenas JSON válido, sem explicações

Retorne no formato JSON especificado.
""",
    "NUBANK": """
Você é um especialista em extrair dados de faturas do Nubank.

REGRAS ESPECÍFICAS PARA NUBANK:
- Formato compacto: data, descrição e valor geralmente na mesma linha
- Valores sempre em R$ 
- Seções: RESUMO DA FATURA, TRANSAÇÕES, COMPRAS
- Formato claro e organizado

INSTRUÇÕES:
1. Extraia TODAS as transações da fatura
2. Identifique data, descrição e valor para cada transação
3. Encontre o valor total da fatura e data de vencimento
4. Retorne apenas JSON válido, sem explicações

Retorne no formato JSON especificado.
""",
    "BANCO DO BRASIL": """
Você é um especialista em extrair dados de faturas do Banco do Brasil.

REGRAS ESPECÍFICAS PARA BB:
- Seções: EXTRATO, LANÇAMENTOS, COMPRAS, DÉBITOS
- Formato estruturado com data e histórico
- Valores com identificação clara

INSTRUÇÕES:
1. Extraia TODAS as transações da fatura
2. Identifique data, descrição e valor para cada transação
3. Encontre o valor total da fatura e data de vencimento
4. Retorne apenas JSON válido, sem explicações

Retorne no formato JSON especificado.
""",
    "GENERIC": """
Você é um especialista em extrair dados de faturas de cartão de crédito.

REGRAS GERAIS:
- Identifique todas as transações (compras, pagamentos, etc.)
- Para cada transação, extraia: data, descrição e valor
- Determine se é débito ou crédito
- Encontre valor total da fatura e data de vencimento

INSTRUÇÕES:
1. Extraia TODAS as transações da fatura
2. Seja preciso com datas, valores e descrições
3. Retorne apenas JSON válido, sem explicações

Retorne no formato JSON especificado.
""",
}

# JSON example for all institutions
JSON_EXAMPLE = """{
  "transactions": [
    {
      "date": "2025-01-15",
      "description": "UBER TRIP 001",
      "amount": 25.50,
      "type": "debit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 25.50,
      "due_date": "2025-02-20",
      "category": "transport"
    },
    {
      "date": "2025-01-16", 
      "description": "PAGAMENTO RECEBIDO",
      "amount": 500.00,
      "type": "credit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 500.00,
      "due_date": "2025-02-20",
      "category": "payment"
    },
    {
      "date": "2025-01-17",
      "description": "COMPRA PARCELADA LOJA XYZ",
      "amount": 150.00,
      "type": "debit", 
      "installments": 3,
      "current_installment": 1,
      "total_purchase_amount": 450.00,
      "due_date": "2025-02-20",
      "category": "purchase"
    }
  ],
  "invoice_total": 914.30,
  "due_date": "2025-02-20"
}"""

# Provider-specific adjustments
PROVIDER_ADJUSTMENTS = {
    "openai": {
        "extra_instructions": """
IMPORTANTE: Seja preciso e consistente com os dados extraídos.
Verifique se a soma das transações bate com o total da fatura.
""",
        "temperature": 0,
        "max_tokens": 1800,
    },
    "deepseek": {
        "extra_instructions": """
CRÍTICO: Retorne APENAS JSON válido, sem texto adicional, sem explicações, sem formatação markdown.
Comece diretamente com { e termine com }.

OBRIGATÓRIO: Inclua SEMPRE os campos:
- "due_date" no nível da fatura (formato YYYY-MM-DD)
- "due_date" em cada transação (pode ser o mesmo da fatura)
- "invoice_total" com o valor total da fatura

Se não conseguir identificar a data de vencimento, use uma data futura estimada no formato YYYY-MM-DD.
""",
        "temperature": 0,
        "max_tokens": 2000,
    },
}


def get_prompt_for_institution(institution: str, provider: str = "generic") -> str:
    """
    Get the appropriate prompt for a specific institution and provider.

    Args:
        institution: Institution name (CAIXA, NUBANK, etc.)
        provider: AI provider name (openai, deepseek, etc.)

    Returns:
        Complete prompt string ready for AI processing
    """
    # Get base prompt for institution
    base_prompt = INSTITUTION_PROMPTS.get(institution, INSTITUTION_PROMPTS["GENERIC"])

    # Add provider-specific adjustments
    provider_config = PROVIDER_ADJUSTMENTS.get(
        provider, PROVIDER_ADJUSTMENTS.get("generic", {})
    )
    extra_instructions = provider_config.get("extra_instructions", "")

    # Combine everything
    full_prompt = (
        base_prompt + "\n" + extra_instructions + "\n\nExample:" + JSON_EXAMPLE
    )

    return full_prompt


def get_provider_config(provider: str) -> dict:
    """
    Get provider-specific configuration (temperature, max_tokens, etc.).

    Args:
        provider: AI provider name

    Returns:
        Configuration dictionary for the provider
    """
    return PROVIDER_ADJUSTMENTS.get(
        provider, {"extra_instructions": "", "temperature": 0, "max_tokens": 1500}
    )


# OpenAI-specific prompts (legacy compatibility)
OPENAI_PROMPTS = {
    institution: get_prompt_for_institution(institution, "openai")
    for institution in INSTITUTION_PROMPTS.keys()
}

# DeepSeek-specific prompts (legacy compatibility)
DEEPSEEK_PROMPTS = {
    institution: get_prompt_for_institution(institution, "deepseek")
    for institution in INSTITUTION_PROMPTS.keys()
}

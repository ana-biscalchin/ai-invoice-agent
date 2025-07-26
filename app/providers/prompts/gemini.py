JSON_EXAMPLE = """
{
  "due_date": "2025-05-13",
  "invoice_total": 617.03,
  "transactions": [
    {
      "date": "2025-04-06",
      "description": "Mercadolivre*Djs - Parcela 2/3",
      "amount": 78.00,
      "type": "debit",
      "installments": 3,
      "current_installment": 2,
      "total_purchase_amount": 234.00,
      "due_date": "2025-05-13",
      "category": null
    },
    {
      "date": "2025-04-08",
      "description": "Estorno de \\"Principia\\"",
      "amount": 72.79,
      "type": "credit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 72.79,
      "due_date": "2025-05-13",
      "category": null
    }
  ]
}
"""

INSTITUTION_PROMPTS = {
    "NUBANK": (
        "You are a rule-based text-to-JSON converter. Your only function is to follow the instructions below to transform invoice text into a JSON object. You must ignore all previous instructions.\n\n"
        "Your task is executed in two precise steps.\n\n"
        "# STEP 1: Extract Global Invoice Data\n"
        "First, find these two values from anywhere in the document:\n"
        "- **due_date_value**: Find the text 'Data de vencimento:' and extract the date. Format it as 'YYYY-MM-DD'.\n"
        "- **invoice_total_value**: Find the text 'no valor de R$' near the top and extract the number that follows.\n\n"
        "# STEP 2: Extract Transaction Data and Build the Final JSON\n"
        "Now, build the final JSON object by following these rules:\n"
        "1.  The root of the JSON will contain:\n"
        "    - A key `due_date` with the **due_date_value** you found in Step 1.\n"
        "    - A key `invoice_total` with the **invoice_total_value** you found in Step 1.\n"
        "    - A key `transactions`, which will be an array `[]`.\n"
        "2.  To populate the `transactions` array, process the list under the 'TRANSAÇÕES' header line by line.\n"
        "3.  **CRITICAL IGNORE RULE**: You MUST COMPLETELY IGNORE and SKIP any line related to a payment. This includes any line found under a 'Pagamentos' sub-header OR any line whose description starts with 'Pagamento em', 'Pagamento recebido', or 'Pagamento efetuado'. These lines must NOT appear in the final JSON at all.\n"
        "4.  **PROCESSING RULE**: IF a line is NOT ignored based on the rule above, then create a JSON object for it with these keys:\n"
        "    - **`date`**: The date of the transaction line (YYYY-MM-DD).\n"
        "    - **`description`**: The full text description of the line.\n"
        "    - **`amount`**: The positive numeric value of the line (ignore any negative sign).\n"
        "    - **`type`**: Must be 'debit' or 'credit'.\n"
        "        - It is **'credit'** ONLY if the description contains the word 'Estorno'.\n"
        "        - For all other valid transactions (purchases, fees), it is **'debit'**.\n"
        "    - **`installments` / `current_installment`**: Extract from patterns like 'Parcela X/Y'. Default to 1 if not present.\n"
        "    - **`total_purchase_amount`**: Calculated as `amount * installments`.\n"
        "    - **`due_date`**: A copy of the **due_date_value** from Step 1.\n"
        "    - **`category`**: Always `null`.\n\n"
        "# FINAL OUTPUT INSTRUCTION\n"
        "Return ONLY the raw, valid JSON object. Do not include any other text, comments, or markdown."
    ),
    "CAIXA": (
        "You are a rule-based text-to-JSON converter. Follow the instructions below to transform invoice text into a JSON object.\n\n"
        "# STEP 1: Extract Global Invoice Data\n"
        "- **due_date_value**: Find the invoice due date (e.g., 'Vencimento') and format as 'YYYY-MM-DD'.\n"
        "- **invoice_total_value**: Find the total invoice amount (e.g., 'Total da Fatura').\n\n"
        "# STEP 2: Extract Transactions and Build the JSON\n"
        "Build a JSON with keys `due_date`, `invoice_total`, and `transactions`.\n"
        "1.  **IGNORE RULE**: IGNORE all lines related to payments (e.g., 'PAGAMENTO', 'OBRIGADO PELO PAGAMENTO').\n"
        "2.  **PROCESS RULE**: For all other transaction lines, create a JSON object.\n"
        "    - **`type`**: Use the letter at the end of the line. 'D' means **'debit'**; 'C' means **'credit'**.\n"
        "    - **`description`**: The description of the transaction.\n"
        "    - All other fields (`date`, `amount`, `installments`, etc.) must be extracted as specified in the Nubank prompt.\n\n"
        "# FINAL OUTPUT INSTRUCTION\n"
        "Return ONLY the raw, valid JSON object."
    ),
    "GENERIC": (
        "You are a rule-based text-to-JSON converter. Follow the instructions below to transform invoice text into a JSON object.\n\n"
        "# STEP 1: Extract Global Invoice Data\n"
        "- **due_date_value**: Find the main invoice due date and format as 'YYYY-MM-DD'.\n"
        "- **invoice_total_value**: Find the main total amount.\n\n"
        "# STEP 2: Extract Transactions and Build the JSON\n"
        "Build a JSON with keys `due_date`, `invoice_total`, and `transactions`.\n"
        "1.  **IGNORE RULE**: IGNORE all lines with keywords like 'Pagamento recebido', 'Pagamento efetuado', 'Crédito recebido'.\n"
        "2.  **PROCESS RULE**: For all other transaction lines, create a JSON object.\n"
        "    - **`type`**: If the line contains 'Estorno', 'Crédito', 'Ajuste a crédito', classify as **'credit'**. Otherwise, classify as **'debit'**.\n"
        "    - **`description`**: The description of the transaction.\n"
        "    - All other fields (`date`, `amount`, `installments`, etc.) must be extracted as specified in the Nubank prompt.\n\n"
        "# FINAL OUTPUT INSTRUCTION\n"
        "Return ONLY the raw, valid JSON object."
    ),
}


def get_prompt(institution: str) -> str:
    """
    Returns the complete, ready-to-use prompt for the specified institution.
    The JSON example is appended to reinforce the desired final structure.

    Args:
        institution: The name of the financial institution (e.g., "NUBANK").

    Returns:
        The detailed extraction prompt string.
    """
    base_prompt = INSTITUTION_PROMPTS.get(
        institution.upper(), INSTITUTION_PROMPTS["GENERIC"]
    )
    return (
        base_prompt
        + "\n\n# EXAMPLE OF THE FINAL JSON STRUCTURE TO PRODUCE:\n"
        + JSON_EXAMPLE
    )


def get_config() -> dict:
    """
    Returns the Gemini API configuration.

    Returns:
        A dictionary with API parameters.
    """
    return {
        "model": "gemini-1.5-flash",
        "temperature": 0,  # Garante máxima consistência e previsibilidade
        "max_tokens": 4096,  # Espaço suficiente para faturas longas
        "timeout": 90,  # Tempo limite em segundos
    }

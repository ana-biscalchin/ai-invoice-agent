def detect_institution(text: str) -> str:
    text_upper = text.upper()
    if "NUBANK" in text_upper:
        return "NUBANK"
    if "CAIXA" in text_upper or "CAIXA ECONOMICA" in text_upper:
        return "CAIXA"
    if "BANCO DO BRASIL" in text_upper or "BANCO DO BRASIL S.A." in text_upper:
        return "BANCO DO BRASIL"
    return "GENERIC" 
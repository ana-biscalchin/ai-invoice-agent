"""PDF processing and validation utilities."""

import logging
import os
import re
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from app.models import Transaction, TransactionType

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF text extraction optimized for invoice processing."""

    def __init__(self):
        """Initialize PDF processor."""
        self.logger = logger
        # Use simple temp directory
        self.output_dir = Path("/tmp/preprocessed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text(self, pdf_bytes: bytes, filename: str = "document") -> Tuple[str, str]:
        """
        Extract text from PDF optimized for invoice processing.

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename (used for logging)

        Returns:
            Tuple of (cleaned_text, detected_institution)

        Raises:
            ValueError: If PDF cannot be processed
        """
        try:
            text = self._extract_text_from_pdf(pdf_bytes)
            self.logger.info(f"Raw text extracted: {len(text)} characters")

            institution = self._detect_institution(text)
            self.logger.info(f"Detected institution: {institution}")

            cleaned_text = self._clean_text_by_institution(text, institution)
            self.logger.info(f"Text cleaned: {len(cleaned_text)} characters")

            return cleaned_text, institution

        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            raise ValueError(f"Failed to process PDF: {e}")

    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text using PyMuPDF with OCR fallback."""
        text = self._extract_with_pymupdf(pdf_bytes)

        if len(text.strip()) > 100:
            return text

        # OCR fallback for minimal text
        self.logger.info("Minimal text found, trying OCR")
        text = self._extract_with_ocr(pdf_bytes)
        
        if text.strip():
            return text

        raise ValueError("No meaningful text could be extracted from PDF")

    def _extract_with_pymupdf(self, pdf_bytes: bytes) -> str:
        """Extract text using PyMuPDF."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(page_text)

        doc.close()
        return "\n".join(text_parts)

    def _extract_with_ocr(self, pdf_bytes: bytes) -> str:
        """Use OCR on pages with minimal extracted text."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            try:
                mat = fitz.Matrix(1.5, 1.5)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

                ocr_text = pytesseract.image_to_string(
                    img,
                    lang="por+eng",
                    config="--psm 6"
                )

                if ocr_text.strip():
                    text_parts.append(ocr_text)

            except Exception as e:
                self.logger.warning(f"OCR failed for page {page_num}: {e}")

        doc.close()
        return "\n".join(text_parts)

    def _detect_institution(self, text: str) -> str:
        """Detect financial institution from text patterns."""
        text_upper = text.upper()
        
        if any(pattern in text_upper for pattern in ["CARTÕES CAIXA", "CAIXA ECONOMICA", "CAIXA ECONÔMICA", "00.360.305/0001-04"]):
            return "CAIXA"
        
        if any(pattern in text_upper for pattern in ["NUBANK", "NU PAGAMENTOS"]):
            return "NUBANK"
        
        if any(pattern in text_upper for pattern in ["BANCO DO BRASIL", "BB.COM.BR", "001-9"]):
            return "BANCO DO BRASIL"
        
        if any(pattern in text_upper for pattern in ["BRADESCO", "BRADESCARD"]):
            return "BRADESCO"
        
        if any(pattern in text_upper for pattern in ["ITAU", "ITAÚ", "CREDICARD"]):
            return "ITAU"
        
        return "GENERIC"

    def _clean_text_by_institution(self, text: str, institution: str) -> str:
        """Clean text using institution-specific rules."""
        config = self._get_institution_config(institution)
        
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            if not line or len(line) < 2:
                continue
            
            # Keep important sections and transaction lines
            if (self._is_section_header(line, config["preserve_sections"]) or
                self._is_transaction_line(line, institution) or
                self._contains_key_field(line, config["key_fields"])):
                cleaned_lines.append(line)
                continue
            
            # Skip noise lines
            if self._is_noise_line(line, config["remove_patterns"]):
                continue
                
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _get_institution_config(self, institution: str) -> dict:
        """Get institution-specific configuration."""
        configs = {
            "CAIXA": {
                "preserve_sections": ["DEMONSTRATIVO", "COMPRAS", "COMPRAS PARCELADAS", "COMPRAS INTERNACIONAIS"],
                "remove_patterns": [r"^SAC CAIXA:.*", r"^0800.*", r".*direitos.*reservados.*"],
                "key_fields": ["VENCIMENTO", "VALOR TOTAL", "Data", "Descrição"]
            },
            "NUBANK": {
                "preserve_sections": ["RESUMO DA FATURA", "TRANSAÇÕES", "COMPRAS"],
                "remove_patterns": [r"^Para.*dúvidas.*", r"^www\.nubank.*"],
                "key_fields": ["Data", "Descrição", "Valor"]
            },
            "GENERIC": {
                "preserve_sections": [],
                "remove_patterns": [r"^SAC.*", r"^www\..*"],
                "key_fields": ["Data", "Descrição", "Valor"]
            }
        }
        return configs.get(institution, configs["GENERIC"])

    def _is_section_header(self, line: str, preserve_sections: list) -> bool:
        """Check if line is an important section header."""
        line_upper = line.upper()
        return any(section.upper() in line_upper for section in preserve_sections)

    def _is_transaction_line(self, line: str, institution: str) -> bool:
        """Check if line contains transaction data."""
        if institution == "CAIXA":
            return (bool(re.search(r'\d{2}/\d{2}', line)) and 
                   ('D' in line[-5:] or 'C' in line[-5:]) and
                   bool(re.search(r'\d+[,\.]\d{2}', line)))
        
        return (bool(re.search(r'\d{2}/\d{2}', line)) and 
               bool(re.search(r'R?\$?\s*\d+[,\.]\d{2}', line)))

    def _contains_key_field(self, line: str, key_fields: list) -> bool:
        """Check if line contains important field names."""
        line_upper = line.upper()
        return any(field.upper() in line_upper for field in key_fields)

    def _is_noise_line(self, line: str, remove_patterns: list) -> bool:
        """Check if line should be removed as noise."""
        # Institution-specific patterns
        for pattern in remove_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Generic noise patterns
        line_lower = line.lower().strip()
        noise_patterns = [
            r"^[.\-_\s•▪▫○●]+$",
            r"^\d{1,2}$",
            r"^página\s*\d*$",
            r"©.*", r"®.*",
            r".*copyright.*"
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, line_lower):
                return True
        
        return len(line.replace(" ", "")) < 3

    def validate_pdf(self, pdf_bytes: bytes) -> bool:
        """Validate if the file is a valid PDF."""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            doc.close()
            return page_count > 0
        except Exception:
            return False


class TransactionValidator:
    """Validates extracted transactions against business rules."""
    
    def __init__(self, transactions: List[Transaction], reference_date: datetime):
        self.transactions = transactions
        self.reference_date = reference_date
        self.errors = []

    def run_all(self, invoice_total: Optional[float] = None) -> dict:
        """Run all validations and return results."""
        self.errors = []
        
        if not self.transactions:
            self.errors.append("No transactions found")
            return {"score": 0.0, "details": {}, "errors": self.errors.copy()}

        checks = {
            "required_fields": self._validate_required_fields(),
            "no_duplicates": self._validate_no_duplicates(),
            "valid_dates": self._validate_dates(),
            "amount_range": self._validate_amount_range(),
            "installments_consistency": self._validate_installments_consistency(),
            "due_date_consistency": self._validate_due_date_consistency(),
        }
        
        if invoice_total is not None:
            checks["sum_valid"] = self._validate_transactions_sum(invoice_total)
            
        score = sum(checks.values()) / len(checks)
        return {"score": score, "details": checks, "errors": self.errors.copy()}

    def _validate_required_fields(self) -> bool:
        """Validate that all transactions have required fields."""
        for t in self.transactions:
            if not t.date or not t.description or t.amount is None:
                self.errors.append(f"Missing required fields in transaction: {t}")
                return False
        return True

    def _validate_no_duplicates(self) -> bool:
        """Validate no duplicate transactions."""
        seen = set()
        for t in self.transactions:
            key = (t.date, t.amount, t.description.strip().lower())
            if key in seen:
                self.errors.append(f"Duplicate transaction found: {t}")
                return False
            seen.add(key)
        return True

    def _validate_dates(self) -> bool:
        """Validate transaction dates are reasonable."""
        now = datetime.now().date()
        for t in self.transactions:
            if t.date > self.reference_date.date() or t.date > now:
                self.errors.append(f"Invalid transaction date: {t.date} in transaction: {t}")
                return False
        return True

    def _validate_amount_range(self, min_value: float = 0.01, max_value: float = 100_000) -> bool:
        """Validate transaction amounts are within reasonable range."""
        for t in self.transactions:
            if not (min_value <= t.amount <= max_value):
                self.errors.append(f"Transaction amount out of range: {t.amount} in transaction: {t}")
                return False
        return True

    def _validate_installments_consistency(self) -> bool:
        """Validate installment calculations are consistent."""
        for t in self.transactions:
            if t.installments > 1:
                expected_total = t.amount * t.installments
                if abs(t.total_purchase_amount - expected_total) > 0.01:
                    self.errors.append(f"Installments inconsistency in transaction: {t}")
                    return False
        return True

    def _validate_due_date_consistency(self) -> bool:
        """Validate all transactions have the same due date."""
        if not self.transactions:
            return True
            
        expected_due_date = self.transactions[0].due_date
        for t in self.transactions:
            if t.due_date != expected_due_date:
                self.errors.append(f"Due date inconsistency: {t.due_date} != {expected_due_date}")
                return False
        return True

    def _validate_transactions_sum(self, invoice_total: float, tolerance: float = 0.01) -> bool:
        """Validate sum of transactions matches invoice total."""
        total = 0.0
        for t in self.transactions:
            if getattr(t, "type", None) == TransactionType.CREDIT:
                total -= t.amount
            else:
                total += t.amount
                
        if abs(total - invoice_total) <= tolerance:
            return True
            
        self.errors.append(f"Sum mismatch: calculated {total}, expected {invoice_total}")
        return False 
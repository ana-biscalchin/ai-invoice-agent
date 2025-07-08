"""PDF processing utilities for invoice extraction."""

import logging
from typing import Optional

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF text extraction with OCR fallback."""

    def __init__(self):
        """Initialize PDF processor."""
        self.logger = logger

    def extract_text(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF with OCR fallback.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            Extracted text content

        Raises:
            ValueError: If PDF cannot be processed
        """
        try:
            # Try PyMuPDF first (faster, better for text-based PDFs)
            text = self._extract_with_pymupdf(pdf_bytes)

            if text.strip():
                self.logger.info("Successfully extracted text with PyMuPDF")
                return text

            # Fallback to OCR if no text found
            self.logger.info("No text found with PyMuPDF, trying OCR")
            text = self._extract_with_ocr(pdf_bytes)

            if text.strip():
                self.logger.info("Successfully extracted text with OCR")
                return text

            raise ValueError("No text could be extracted from PDF")

        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            raise ValueError(f"Failed to process PDF: {e}")

    def _extract_with_pymupdf(self, pdf_bytes: bytes) -> str:
        """Extract text using PyMuPDF."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            text_parts.append(text)

        doc.close()
        return "\n".join(text_parts)

    def _extract_with_ocr(self, pdf_bytes: bytes) -> str:
        """Extract text using OCR (Tesseract)."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # Convert page to image
            mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Extract text with OCR
            text = pytesseract.image_to_string(img, lang="por+eng")
            text_parts.append(text)

        doc.close()
        return "\n".join(text_parts)

    def validate_pdf(self, pdf_bytes: bytes) -> bool:
        """
        Validate if the file is a valid PDF.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            True if valid PDF, False otherwise
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            doc.close()

            if page_count == 0:
                return False

            return True

        except Exception:
            return False

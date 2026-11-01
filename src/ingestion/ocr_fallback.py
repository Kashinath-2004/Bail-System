"""OCR fallback module for scanned legal documents.

Provides optical character recognition fallback when digital text layers are missing,
with strict accuracy warnings and graceful degradation when Tesseract binary is absent.
"""

from __future__ import annotations

import io
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

_TESSERACT_AVAILABLE: Optional[bool] = None


def is_tesseract_installed() -> bool:
    """Check if pytesseract and the underlying Tesseract engine are available."""
    global _TESSERACT_AVAILABLE
    if _TESSERACT_AVAILABLE is not None:
        return _TESSERACT_AVAILABLE

    try:
        import pytesseract
        # Try getting version or probing binary
        pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
    except Exception as exc:
        logger.warning("Tesseract OCR is not installed or not in PATH: %s", exc)
        _TESSERACT_AVAILABLE = False

    return _TESSERACT_AVAILABLE


def ocr_pdf_bytes(pdf_bytes: bytes) -> Tuple[List[str], List[str]]:
    """Attempt OCR extraction on PDF bytes.

    Returns:
        Tuple of (page_texts, warnings)
    """
    warnings: List[str] = []
    page_texts: List[str] = []

    if not is_tesseract_installed():
        warnings.append(
            "Scanned document detected: PDF contains no selectable text layer and Tesseract OCR "
            "is not available on the server. Please paste case text directly or upload a digital text document."
        )
        return page_texts, warnings

    warnings.append(
        "Scanned document detected: text was extracted via Optical Character Recognition (OCR). "
        "Section numbers and party names should be carefully reviewed for recognition errors."
    )

    try:
        import pdfplumber
        import pytesseract

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                try:
                    # Convert page to image for OCR
                    img = page.to_image(resolution=200).original
                    text = pytesseract.image_to_string(img)
                    page_texts.append(text.strip())
                except Exception as page_exc:
                    logger.warning("OCR failed on page %d: %s", idx, page_exc)
                    page_texts.append("")
    except Exception as exc:
        logger.error("Failed to run OCR on PDF: %s", exc)
        warnings.append(f"OCR processing failed: {exc}")

    return page_texts, warnings


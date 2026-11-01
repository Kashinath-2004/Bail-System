"""In-memory text extraction for PDF, DOCX, and TXT case documents.

Extracts text with page-level provenance tracking and character offsets,
ensuring documents are never persisted to disk or external storage.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from src.ingestion.ocr_fallback import ocr_pdf_bytes

logger = logging.getLogger(__name__)


@dataclass
class PageChunk:
    """Represents text extracted from a single page or segment with provenance."""
    page_num: int
    text: str
    char_start: int
    char_end: int
    line_count: int


@dataclass
class ExtractedDocument:
    """Full extracted document payload held strictly in-memory."""
    raw_text: str
    pages: List[PageChunk] = field(default_factory=list)
    filename: Optional[str] = None
    file_type: str = "text"
    is_scanned: bool = False
    warnings: List[str] = field(default_factory=list)

    @property
    def total_characters(self) -> int:
        return len(self.raw_text)

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    def find_provenance(self, snippet: str) -> Optional[dict]:
        """Find the page number and approximate line number for a given text snippet."""
        if not snippet or not snippet.strip():
            return None

        clean_snippet = snippet.strip().lower()
        for page in self.pages:
            lower_page = page.text.lower()
            idx = lower_page.find(clean_snippet)
            if idx != -1:
                # Estimate line number within the page
                lines_before = lower_page[:idx].count("\n") + 1
                return {
                    "page_num": page.page_num,
                    "line_num": lines_before,
                    "match_text": snippet.strip(),
                }
        return None


def extract_text_from_bytes(
    file_bytes: bytes,
    filename: str = "document",
    content_type: Optional[str] = None,
) -> ExtractedDocument:
    """Extract text from raw file bytes in memory (PDF, DOCX, or TXT).

    Args:
        file_bytes: Raw binary content of the file.
        filename: Original filename (used to infer type if content_type is ambiguous).
        content_type: MIME type of the uploaded file.

    Returns:
        ExtractedDocument holding text, page chunks, and extraction warnings.
    """
    lower_name = filename.lower()
    ct = (content_type or "").lower()

    if lower_name.endswith(".pdf") or "pdf" in ct:
        return _extract_from_pdf(file_bytes, filename)
    elif lower_name.endswith(".docx") or "wordprocessingml" in ct or lower_name.endswith(".doc"):
        return _extract_from_docx(file_bytes, filename)
    else:
        # Default to plain text
        return _extract_from_txt(file_bytes, filename)


def extract_text_from_string(text: str, filename: str = "pasted_text.txt") -> ExtractedDocument:
    """Construct an ExtractedDocument from raw pasted text."""
    lines = text.splitlines(keepends=True)
    pages: List[PageChunk] = []

    # Chunk into simulated pages of ~50 lines if very long, or single page
    chunk_size = 50
    current_char = 0
    all_chunks = [lines[i : i + chunk_size] for i in range(0, max(1, len(lines)), chunk_size)]

    for page_idx, chunk_lines in enumerate(all_chunks, start=1):
        chunk_text = "".join(chunk_lines)
        char_start = current_char
        char_end = char_start + len(chunk_text)
        current_char = char_end
        pages.append(
            PageChunk(
                page_num=page_idx,
                text=chunk_text,
                char_start=char_start,
                char_end=char_end,
                line_count=len(chunk_lines),
            )
        )

    return ExtractedDocument(
        raw_text=text,
        pages=pages,
        filename=filename,
        file_type="plain_text",
        is_scanned=False,
    )


def _extract_from_pdf(pdf_bytes: bytes, filename: str) -> ExtractedDocument:
    """Extract text from PDF with pdfplumber and OCR fallback."""
    import pdfplumber

    pages: List[PageChunk] = []
    combined_texts: List[str] = []
    warnings: List[str] = []
    current_char = 0
    is_scanned = False

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            total_extracted_chars = 0
            for idx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                total_extracted_chars += len(page_text.strip())
                char_start = current_char
                char_end = char_start + len(page_text)
                current_char = char_end + 1  # newline separator

                pages.append(
                    PageChunk(
                        page_num=idx,
                        text=page_text,
                        char_start=char_start,
                        char_end=char_end,
                        line_count=len(page_text.splitlines()),
                    )
                )
                combined_texts.append(page_text)

            # If text is virtually empty despite having pages, trigger OCR fallback
            if len(pdf.pages) > 0 and total_extracted_chars < 50:
                is_scanned = True
                ocr_pages, ocr_warnings = ocr_pdf_bytes(pdf_bytes)
                warnings.extend(ocr_warnings)
                if any(t.strip() for t in ocr_pages):
                    pages = []
                    combined_texts = []
                    current_char = 0
                    for idx, ocr_text in enumerate(ocr_pages, start=1):
                        char_start = current_char
                        char_end = char_start + len(ocr_text)
                        current_char = char_end + 1
                        pages.append(
                            PageChunk(
                                page_num=idx,
                                text=ocr_text,
                                char_start=char_start,
                                char_end=char_end,
                                line_count=len(ocr_text.splitlines()),
                            )
                        )
                        combined_texts.append(ocr_text)

    except Exception as exc:
        logger.error("Error reading PDF %s: %s", filename, exc)
        warnings.append(f"PDF read error: {exc}")

    full_text = "\n\n".join(combined_texts)
    return ExtractedDocument(
        raw_text=full_text,
        pages=pages,
        filename=filename,
        file_type="pdf",
        is_scanned=is_scanned,
        warnings=warnings,
    )


def _extract_from_docx(docx_bytes: bytes, filename: str) -> ExtractedDocument:
    """Extract text from DOCX file in memory."""
    import docx

    pages: List[PageChunk] = []
    paragraphs_text: List[str] = []
    warnings: List[str] = []

    try:
        doc = docx.Document(io.BytesIO(docx_bytes))
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs_text.append(para.text)

        # Also extract table text
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    paragraphs_text.append(" | ".join(row_cells))

    except Exception as exc:
        logger.error("Error reading DOCX %s: %s", filename, exc)
        warnings.append(f"DOCX read error: {exc}")

    full_text = "\n".join(paragraphs_text)
    # Estimate pages (~300 words or 2000 chars per page)
    chunk_size = 2000
    current_char = 0
    all_chunks = [full_text[i : i + chunk_size] for i in range(0, max(1, len(full_text)), chunk_size)]
    for idx, chunk in enumerate(all_chunks, start=1):
        char_start = current_char
        char_end = char_start + len(chunk)
        current_char = char_end
        pages.append(
            PageChunk(
                page_num=idx,
                text=chunk,
                char_start=char_start,
                char_end=char_end,
                line_count=len(chunk.splitlines()),
            )
        )

    return ExtractedDocument(
        raw_text=full_text,
        pages=pages,
        filename=filename,
        file_type="docx",
        is_scanned=False,
        warnings=warnings,
    )


def _extract_from_txt(txt_bytes: bytes, filename: str) -> ExtractedDocument:
    """Extract text from plain text bytes."""
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            decoded = txt_bytes.decode(enc)
            return extract_text_from_string(decoded, filename=filename)
        except UnicodeDecodeError:
            continue

    decoded = txt_bytes.decode("utf-8", errors="replace")
    return extract_text_from_string(decoded, filename=filename)


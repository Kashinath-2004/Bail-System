"""Document ingestion package for Justice AI.

Supports in-memory ingestion of PDF, DOCX, and TXT case documents with
per-page provenance tracking and OCR fallback for scanned materials.
"""

from src.ingestion.text_extractor import ExtractedDocument, PageChunk, extract_text_from_bytes, extract_text_from_string

__all__ = [
    "ExtractedDocument",
    "PageChunk",
    "extract_text_from_bytes",
    "extract_text_from_string",
]

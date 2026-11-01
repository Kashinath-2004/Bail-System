"""Extraction package for Justice AI.

Provides PII redaction, fuzzy codebook matching, deterministic regex extraction,
and LLM extraction with provenance and confidence tracking.
"""

from src.extraction.schema import ExtractedCaseDetails, FieldProvenance
from src.extraction.fuzzy_matcher import CodebookMatcher
from src.extraction.regex_fallback import RegexLegalExtractor
from src.extraction.llm_client import CaseExtractionEngine
from src.extraction.entity_redactor import EntityRedactor

__all__ = [
    "ExtractedCaseDetails",
    "FieldProvenance",
    "CodebookMatcher",
    "RegexLegalExtractor",
    "CaseExtractionEngine",
    "EntityRedactor",
]

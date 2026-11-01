"""Extraction package for Justice AI.

Provides PII redaction, fuzzy codebook matching, deterministic legal extraction,
verifiable evidence tracking, and hybrid LLM assistance.
"""

from src.extraction.schema import ExtractedCaseDetails, ExtractedField, EvidenceSpan
from src.extraction.fuzzy_matcher import CodebookMatcher
from src.extraction.verifier import verify_and_build_field, verify_verbatim_quote
from src.extraction.deterministic_extractor import DeterministicLegalExtractor
from src.extraction.entity_redactor import EntityRedactor

__all__ = [
    "ExtractedCaseDetails",
    "ExtractedField",
    "EvidenceSpan",
    "CodebookMatcher",
    "DeterministicLegalExtractor",
    "EntityRedactor",
    "verify_and_build_field",
    "verify_verbatim_quote",
]

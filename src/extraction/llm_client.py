"""Hybrid extraction engine combining deterministic rules with optional LLM refinement.

Layer 1: Deterministic rules (regex + keyword + codebook) - runs first, fast & exact.
Layer 2: LLM structured extraction (only for fields rules could not fill) with strict JSON schema.
Layer 3: Reconciliation & Anti-Hallucination verification gate (prefers rules, verifies quotes).
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from src.extraction.deterministic_extractor import DeterministicLegalExtractor
from src.extraction.fuzzy_matcher import CodebookMatcher
from src.extraction.schema import ExtractedCaseDetails, ExtractedField
from src.extraction.verifier import verify_and_build_field
from src.ingestion.text_extractor import ExtractedDocument

logger = logging.getLogger(__name__)

LLM_SCHEMA_PROMPT = """You are a legal document parsing system for Indian court filings.
Analyze the provided document and extract missing parameters into JSON.

CRITICAL CONSTRAINTS:
1. Return null if a detail is not explicitly stated in the text. NEVER guess or invent.
2. For EVERY non-null value, you MUST provide the exact verbatim quote from the text in "evidence_snippet".
3. For case_allegations_summary: write 3-4 factual, objective sentences summarizing ONLY what is stated in the document.

Output format (valid JSON only):
{
  "case_number": {"value": string or null, "evidence_snippet": string or null},
  "filing_date": {"value": "YYYY-MM-DD" or null, "evidence_snippet": string or null},
  "court_name": {"value": string or null, "evidence_snippet": string or null},
  "state": {"value": string or null, "evidence_snippet": string or null},
  "district": {"value": string or null, "evidence_snippet": string or null},
  "act": {"value": string or null, "evidence_snippet": string or null},
  "sections": {"value": [string] or null, "evidence_snippet": string or null},
  "accused_names": {"value": [string] or null, "evidence_snippet": string or null},
  "custody_status": {"value": string or null, "evidence_snippet": string or null},
  "case_allegations_summary": {"value": string or null, "evidence_snippet": string or null}
}

DOCUMENT TEXT:
\"\"\"
{document_text}
\"\"\"
"""


class CaseExtractionEngine:
    """Hybrid 3-layer case extraction engine."""

    def __init__(self, matcher: Optional[CodebookMatcher] = None):
        self.matcher = matcher or CodebookMatcher()
        self.rule_extractor = DeterministicLegalExtractor(self.matcher)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._gemini_configured = False
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._gemini_configured = True
            except Exception as exc:
                logger.warning("Failed to configure Google Generative AI: %s", exc)

    def extract(self, doc: ExtractedDocument) -> ExtractedCaseDetails:
        """Run 3-layer extraction: Rules -> LLM (if needed and available) -> Reconciliation."""
        text = doc.raw_text.strip()
        if not text:
            # Empty input -> return all nulls immediately per Hard Rule 1
            return ExtractedCaseDetails(
                extraction_mode="DETERMINISTIC_RULES",
                warnings=["Input document was empty."],
            )

        # Layer 1: Deterministic rules (always runs first)
        details = self.rule_extractor.extract(doc)

        # Check which critical fields are still missing
        missing_critical = (
            details.case_number.value is None
            or details.sections.value is None
            or details.case_summary.value is None
            or details.state.value is None
            or details.district.value is None
        )

        # Layer 2: LLM refinement only if Gemini configured and fields missing
        if self._gemini_configured and missing_critical:
            try:
                details = self._refine_with_llm(doc, details)
                details.extraction_mode = "HYBRID_LLM"
            except Exception as exc:
                logger.warning("LLM refinement failed: %s. Using rule-based extraction.", exc)
                details.warnings.append(f"LLM refinement skipped: {exc}")

        return details

    def _refine_with_llm(
        self, doc: ExtractedDocument, current: ExtractedCaseDetails
    ) -> ExtractedCaseDetails:
        """Query Gemini with strict JSON schema and anti-hallucination verification."""
        import google.generativeai as genai

        text = doc.raw_text
        prompt = LLM_SCHEMA_PROMPT.format(document_text=text[:6000])

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
            },
        )
        data = json.loads(response.text)

        # Helper to reconcile and verify
        def _reconcile(field_name: str, current_field: ExtractedField, is_list: bool = False) -> ExtractedField:
            llm_item = data.get(field_name) or {}
            val = llm_item.get("value")
            snippet = llm_item.get("evidence_snippet")

            if current_field.value is not None:
                # Rule has a value. Check for conflict
                if val is not None and str(val).lower() != str(current_field.value).lower():
                    current_field.conflict_warning = f"Rules found '{current_field.value}'; LLM suggested '{val}'."
                return current_field

            # Rule was missing, try LLM value through verifier
            if val is not None and snippet:
                verified = verify_and_build_field(
                    value=val,
                    evidence_snippet=snippet,
                    source_text=text,
                    method="llm_verified",
                    must_contain_literal=True,
                )
                if verified.verified:
                    return verified

            return current_field

        # Reconcile missing fields
        current.case_number = _reconcile("case_number", current.case_number)
        current.filing_date = _reconcile("filing_date", current.filing_date)
        current.court_name = _reconcile("court_name", current.court_name)
        current.state = _reconcile("state", current.state)
        current.district = _reconcile("district", current.district)
        current.act = _reconcile("act", current.act)
        current.sections = _reconcile("sections", current.sections, is_list=True)
        current.accused_names = _reconcile("accused_names", current.accused_names, is_list=True)
        current.custody_status = _reconcile("custody_status", current.custody_status)

        # Summary reconciliation
        if current.case_summary.value is None:
            sum_item = data.get("case_allegations_summary") or {}
            val_sum = sum_item.get("value")
            if val_sum:
                current.case_summary = verify_and_build_field(
                    value=val_sum,
                    evidence_snippet=sum_item.get("evidence_snippet") or val_sum[:100],
                    source_text=text,
                    method="llm_verified",
                    must_contain_literal=False,
                )

        return current

"""LLM Client for structured case extraction with graceful offline fallback.

Uses Google Gemini (via google-generativeai) when an API key is available in the environment,
and falls back transparently to RegexLegalExtractor for zero-cost, fully offline local execution.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from src.extraction.fuzzy_matcher import CodebookMatcher
from src.extraction.regex_fallback import RegexLegalExtractor
from src.extraction.schema import ExtractedCaseDetails, FieldProvenance
from src.ingestion.text_extractor import ExtractedDocument
from src.legal_knowledge.ipc_bns_mapper import get_concordance_entry

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT_TEMPLATE = """You are a senior Indian legal assistant. Extract the structured legal attributes from the provided Indian court/police document.

Return ONLY a valid JSON object matching this exact schema:
{
  "case_title": "Parties or title, e.g. State of Maharashtra vs Ramesh Kumar",
  "case_number": "FIR number or court case number, e.g. FIR No. 102/2023 or CC 45/2022",
  "filing_year": 2023,
  "state": "State name, e.g. Maharashtra",
  "district": "District name, e.g. Pune",
  "court_name": "Court name, e.g. Court of Sessions Judge",
  "act": "The Indian Penal Code or Bharatiya Nyaya Sanhita, 2023",
  "sections": ["302", "34"],
  "case_type": "Criminal Case or Sessions Case",
  "judge_position": "Civil Judge Junior Division or Chief Judicial Magistrate or Sessions Judge",
  "accused_count": 1,
  "custody_status": "In Custody or On Bail or Not Arrested",
  "case_summary": "2-3 sentences plain language summary of the allegations and procedural posture.",
  "snippets": {
    "case_number": "exact text snippet where case number was found",
    "sections": "exact text snippet where sections were found",
    "court_name": "exact text snippet where court was found"
  }
}

Important Instructions:
- For sections, extract only the section numbers/identifiers (e.g. ["379"] or ["420", "120B"]).
- If a detail is not explicitly mentioned, provide a reasonable inference or leave null.
- Do NOT hallucinate dates or facts not in the document.

DOCUMENT TEXT:
\"\"\"
{document_text}
\"\"\"
"""


class CaseExtractionEngine:
    """Hybrid LLM + Rule-based case extraction engine."""

    def __init__(self, matcher: Optional[CodebookMatcher] = None):
        self.matcher = matcher or CodebookMatcher()
        self.regex_extractor = RegexLegalExtractor(self.matcher)
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
        """Extract structured case details from ExtractedDocument.

        Tries LLM if API key is present; otherwise uses deterministic regex extraction.
        """
        if self._gemini_configured:
            try:
                return self._extract_with_gemini(doc)
            except Exception as exc:
                logger.warning("Gemini extraction failed (%s). Falling back to regex extractor.", exc)

        # Offline / deterministic fallback
        extracted = self.regex_extractor.extract(doc)
        if not self._gemini_configured:
            extracted.extraction_warnings.append(
                "Offline rule-based extractor used. Add GEMINI_API_KEY for advanced LLM extraction."
            )
        return extracted

    def _extract_with_gemini(self, doc: ExtractedDocument) -> ExtractedCaseDetails:
        """Call Gemini to extract structured case details."""
        import google.generativeai as genai

        # Truncate to first 6000 chars if document is huge to avoid token bloat
        truncated_text = doc.raw_text[:6000]
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(document_text=truncated_text)

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)

        # Match state and district to DDL codes
        raw_state = data.get("state") or ""
        state_code, canonical_state, state_conf = self.matcher.match_state(raw_state)

        raw_dist = data.get("district") or ""
        dist_code, canonical_dist, dist_conf = self.matcher.match_district(raw_dist, state_code=state_code)

        canonical_type, type_conf = self.matcher.canonicalize_case_type(data.get("case_type") or "")
        canonical_judge, judge_conf = self.matcher.canonicalize_judge_position(data.get("judge_position") or "")

        # Sections & BNS mapping
        raw_sections = data.get("sections") or ["379"]
        clean_sections = []
        for s in raw_sections:
            clean_s = re.sub(r"[^\w\d]", "", str(s)).upper()
            if clean_s:
                clean_sections.append(clean_s)

        act = data.get("act") or "The Indian Penal Code"
        is_bns_act = "bns" in act.lower() or "bharatiya" in act.lower()
        bns_sections = []
        for s in clean_sections:
            entry = get_concordance_entry(s, act_hint=act)
            if entry:
                if is_bns_act:
                    bns_sections.append(f"IPC {entry.ipc_section}")
                else:
                    bns_sections.append(f"BNS {entry.bns_section}")

        # Provenance
        snippets = data.get("snippets") or {}
        provenance = {}
        for k, snip in snippets.items():
            if snip:
                prov = doc.find_provenance(snip)
                if prov:
                    provenance[k] = FieldProvenance(
                        page_num=prov["page_num"],
                        line_num=prov["line_num"],
                        snippet=snip,
                        confidence=0.95,
                        source_type="llm_extracted",
                    )

        confidences = {
            "case_number": 0.95 if data.get("case_number") else 0.5,
            "sections": 0.95,
            "state": state_conf,
            "district": dist_conf,
            "court_name": 0.9,
            "case_type": type_conf,
            "judge_position": judge_conf,
        }

        return ExtractedCaseDetails(
            case_title=data.get("case_title") or "State vs Unknown",
            case_number=data.get("case_number"),
            filing_year=data.get("filing_year") or 2024,
            state=canonical_state,
            state_code=state_code,
            district=canonical_dist,
            dist_code=dist_code,
            court_name=data.get("court_name") or f"{canonical_dist} Court",
            court_no=1,
            act=act,
            sections=clean_sections,
            bns_sections=bns_sections,
            case_type=canonical_type,
            judge_position=canonical_judge,
            judge_tenure_months=12.0,
            accused_count=data.get("accused_count") or 1,
            custody_status=data.get("custody_status") or "Not Arrested",
            case_summary=data.get("case_summary") or "",
            provenance=provenance,
            field_confidences=confidences,
            is_llm_extracted=True,
            is_pii_redacted=False,
            extraction_warnings=list(doc.warnings),
        )

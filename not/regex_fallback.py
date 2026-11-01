"""Deterministic regex and rule-based legal entity extractor.

Operates locally and deterministically without requiring any external API keys or network access.
Extracts Indian legal metadata (FIR/Case number, sections, acts, court, state, district,
custody status, parties) with page/line provenance and confidence scoring.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from src.extraction.fuzzy_matcher import CodebookMatcher
from src.extraction.schema import ExtractedCaseDetails, FieldProvenance
from src.ingestion.text_extractor import ExtractedDocument
from src.legal_knowledge.ipc_bns_mapper import get_concordance_entry, normalize_section_number


class RegexLegalExtractor:
    """Deterministic extractor for Indian legal documents."""

    def __init__(self, matcher: Optional[CodebookMatcher] = None):
        self.matcher = matcher or CodebookMatcher()

    # Regex patterns for common legal headers
    FIR_CASE_PATTERNS = [
        re.compile(r"(?:FIR\s*No\.?|First\s*Information\s*Report\s*No\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-_]+(?:\s*(?:of|\/)\s*\d{4})?)", re.IGNORECASE),
        re.compile(r"(?:Case\s*No\.?|C\.?C\.?\s*No\.?|Sessions\s*Case\s*No\.?|Cr\.?\s*Case\s*No\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-_]+(?:\s*(?:of|\/)\s*\d{4})?)", re.IGNORECASE),
        re.compile(r"(?:Special\s*Case\s*No\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-_]+(?:\s*(?:of|\/)\s*\d{4})?)", re.IGNORECASE),
    ]

    YEAR_PATTERNS = [
        re.compile(r"\b(20[0-2][0-9]|19[89][0-9])\b"),
    ]

    SECTIONS_PATTERNS = [
        # "u/s 302, 34 IPC" or "under section 379 of IPC" or "u/ss. 420, 120-B"
        re.compile(r"(?:u\/s|under\s+sections?|section|sec\.?|u\/ss\.?)\s*([0-9\s,\/and\-\(\)A-Za-z]+?)(?=(?:of\s+the\s+)?(?:IPC|Indian\s+Penal\s+Code|BNS|Bharatiya\s+Nyaya\s+Sanhita|CrPC|\.|\n|$))", re.IGNORECASE),
        re.compile(r"(?:IPC|BNS)\s*(?:sections?|u\/s)?\s*([0-9\s,\/and\-\(\)A-Za-z]+)", re.IGNORECASE),
    ]

    ACT_PATTERNS = [
        (re.compile(r"(?:Bharatiya\s*Nyaya\s*Sanhita|BNS)", re.IGNORECASE), "Bharatiya Nyaya Sanhita, 2023"),
        (re.compile(r"(?:Indian\s*Penal\s*Code|I\.?P\.?C\.?)", re.IGNORECASE), "The Indian Penal Code"),
    ]

    COURT_PATTERNS = [
        re.compile(r"(?:IN\s+THE\s+COURT\s+OF\s+)(.+?)(?=\n|at|\,)", re.IGNORECASE),
        re.compile(r"(?:Court\s+of\s+)(.+?)(?=\n|at|\,)", re.IGNORECASE),
        re.compile(r"(District\s+(?:and\s+Sessions\s+)?Court[^\n,]*)", re.IGNORECASE),
        re.compile(r"(Chief\s+Judicial\s+Magistrate[^\n,]*)", re.IGNORECASE),
    ]

    DISTRICT_STATE_PATTERNS = [
        re.compile(r"(?:District|Dist\.?)\s*[:\-]?\s*([A-Za-z\s]+?)(?=\n|\,|\.|\s+State)", re.IGNORECASE),
        re.compile(r"(?:Police\s*Station|P\.?S\.?)\s*[:\-]?\s*([A-Za-z\s]+?)(?=\n|\,|\.)", re.IGNORECASE),
        re.compile(r"(?:State\s+of\s+)([A-Za-z\s]+?)(?=\n|\,|\.|\s+versus|\s+vs)", re.IGNORECASE),
    ]

    PARTY_PATTERNS = [
        re.compile(r"([A-Za-z\s\.]+)\s+(?:versus|vs\.?|V\/s)\s+([A-Za-z\s\.]+)", re.IGNORECASE),
        re.compile(r"(?:State\s+(?:of\s+[A-Za-z]+)?)\s+(?:versus|vs\.?|V\/s)\s+([A-Za-z\s\.]+)", re.IGNORECASE),
    ]

    CUSTODY_PATTERNS = [
        (re.compile(r"(?:in\s+judicial\s+custody|in\s+custody|under\s+arrest|remanded\s+to\s+custody)", re.IGNORECASE), "In Custody"),
        (re.compile(r"(?:on\s+bail|enlarged\s+on\s+bail|granted\s+bail|released\s+on\s+bail)", re.IGNORECASE), "On Bail"),
        (re.compile(r"(?:anticipatory\s+bail|pre-arrest\s+bail)", re.IGNORECASE), "Anticipatory Bail"),
    ]

    def extract(self, doc: ExtractedDocument) -> ExtractedCaseDetails:
        """Parse ExtractedDocument and return structured ExtractedCaseDetails with provenance."""
        full_text = doc.raw_text
        provenance: Dict[str, FieldProvenance] = {}
        confidences: Dict[str, float] = {}

        # 1. Case Number / FIR Number
        case_no = None
        for pat in self.FIR_CASE_PATTERNS:
            m = pat.search(full_text)
            if m:
                snippet = m.group(0).strip()
                case_no = m.group(1).strip()
                prov = doc.find_provenance(snippet)
                provenance["case_number"] = FieldProvenance(
                    page_num=prov["page_num"] if prov else 1,
                    line_num=prov["line_num"] if prov else 1,
                    snippet=snippet,
                    confidence=0.9,
                    source_type="extracted",
                )
                confidences["case_number"] = 0.9
                break

        # 2. Year
        year = 2024
        year_prov = None
        for pat in self.YEAR_PATTERNS:
            matches = list(pat.finditer(full_text))
            if matches:
                # Often the last or first year in legal header
                for m in reversed(matches):
                    val = int(m.group(1))
                    if 1995 <= val <= 2025:
                        year = val
                        prov = doc.find_provenance(m.group(0))
                        provenance["filing_year"] = FieldProvenance(
                            page_num=prov["page_num"] if prov else 1,
                            line_num=prov["line_num"] if prov else 1,
                            snippet=m.group(0),
                            confidence=0.85,
                            source_type="extracted",
                        )
                        confidences["filing_year"] = 0.85
                        break
            if "filing_year" in provenance:
                break

        # 3. Act & Sections
        act = "The Indian Penal Code"
        for pat, act_name in self.ACT_PATTERNS:
            m = pat.search(full_text)
            if m:
                act = act_name
                prov = doc.find_provenance(m.group(0))
                provenance["act"] = FieldProvenance(
                    page_num=prov["page_num"] if prov else 1,
                    line_num=prov["line_num"] if prov else 1,
                    snippet=m.group(0),
                    confidence=0.95,
                    source_type="extracted",
                )
                confidences["act"] = 0.95
                break

        sections: List[str] = []
        raw_sections_found = []
        for pat in self.SECTIONS_PATTERNS:
            for m in pat.finditer(full_text):
                raw_chunk = m.group(1)
                # Strip trailing connective phrases like "of", "read with"
                raw_chunk = re.sub(r"\b(?:of|the|read\s+with|r\/w)\b.*$", "", raw_chunk, flags=re.IGNORECASE)
                # Split by commas, 'and', slashes
                tokens = re.split(r"[,/&]|and", raw_chunk)
                for t in tokens:
                    # Remove stop words
                    t_clean = re.sub(r"\b(?:OF|THE|READ|WITH|RW|SEC|SECTIONS?)\b", "", t.strip(), flags=re.IGNORECASE)
                    t_clean = re.sub(r"[^\w\d]", "", t_clean).upper()
                    # Filter for typical section length and digits
                    if t_clean and any(c.isdigit() for c in t_clean):
                        # Extract digits plus possible single uppercase letter like 304A, 498A, 120B
                        m_sec = re.match(r"^(\d+[A-Z]?)", t_clean)
                        if m_sec:
                            sec_val = m_sec.group(1)
                            # Ensure single letter suffix is valid (e.g. not 34O from '34 of')
                            if len(sec_val) > 1 and sec_val[-1] in {"A", "B", "C", "D", "E"}:
                                pass
                            elif len(sec_val) > 1 and sec_val[-1].isalpha():
                                sec_val = sec_val[:-1]
                            if sec_val not in sections:
                                sections.append(sec_val)
                                raw_sections_found.append((sec_val, m.group(0)))

        if not sections:
            # Fallback scan for standalone known major sections
            major_sections = ["302", "307", "376", "379", "380", "420", "323", "324", "325", "326", "498A", "504", "506", "34", "120B", "279", "304A", "406", "411"]
            for s in major_sections:
                if re.search(rf"\b{s}\b", full_text):
                    sections.append(s)

        if not sections:
            sections = ["379"]  # Default simple theft fallback
            confidences["sections"] = 0.4
        else:
            first_sec, snippet = raw_sections_found[0] if raw_sections_found else (sections[0], f"Section {sections[0]}")
            prov = doc.find_provenance(snippet)
            provenance["sections"] = FieldProvenance(
                page_num=prov["page_num"] if prov else 1,
                line_num=prov["line_num"] if prov else 1,
                snippet=snippet,
                confidence=0.9,
                source_type="extracted",
            )
            confidences["sections"] = 0.9

        # Map equivalent BNS / IPC sections
        bns_sections = []
        is_bns_act = "bns" in act.lower() or "bharatiya" in act.lower()
        for s in sections:
            entry = get_concordance_entry(s, act_hint=act)
            if entry:
                if is_bns_act:
                    bns_sections.append(f"IPC {entry.ipc_section}")
                else:
                    bns_sections.append(f"BNS {entry.bns_section}")

        # 4. State & District
        raw_state = ""
        raw_dist = ""
        for pat in self.DISTRICT_STATE_PATTERNS:
            m = pat.search(full_text)
            if m:
                match_val = m.group(1).strip()
                if "state" in pat.pattern.lower():
                    raw_state = match_val
                else:
                    raw_dist = match_val

        # Match to codebook
        state_code, canonical_state, state_conf = self.matcher.match_state(raw_state)
        dist_code, canonical_dist, dist_conf = self.matcher.match_district(raw_dist, state_code=state_code)

        confidences["state"] = state_conf
        confidences["district"] = dist_conf
        if raw_state:
            prov = doc.find_provenance(raw_state)
            provenance["state"] = FieldProvenance(
                page_num=prov["page_num"] if prov else 1,
                line_num=prov["line_num"] if prov else 1,
                snippet=raw_state,
                confidence=state_conf,
                source_type="extracted",
            )
        if raw_dist:
            prov = doc.find_provenance(raw_dist)
            provenance["district"] = FieldProvenance(
                page_num=prov["page_num"] if prov else 1,
                line_num=prov["line_num"] if prov else 1,
                snippet=raw_dist,
                confidence=dist_conf,
                source_type="extracted",
            )

        # 5. Court & Judge
        court_name = f"{canonical_dist} District Court"
        raw_judge = ""
        for pat in self.COURT_PATTERNS:
            m = pat.search(full_text)
            if m:
                court_text = m.group(1).strip()
                court_name = court_text[:60]
                raw_judge = court_text
                prov = doc.find_provenance(m.group(0))
                provenance["court_name"] = FieldProvenance(
                    page_num=prov["page_num"] if prov else 1,
                    line_num=prov["line_num"] if prov else 1,
                    snippet=m.group(0),
                    confidence=0.85,
                    source_type="extracted",
                )
                confidences["court_name"] = 0.85
                break

        canonical_judge, judge_conf = self.matcher.canonicalize_judge_position(raw_judge)
        confidences["judge_position"] = judge_conf

        # 6. Case Type
        canonical_type, type_conf = self.matcher.canonicalize_case_type(court_name)
        # If section is heavy (302, 307, 376), case type is Sessions Case
        if any(s in {"302", "307", "376", "395"} for s in sections):
            canonical_type = "Sessions Case"
            type_conf = 0.95
        confidences["case_type"] = type_conf

        # 7. Parties / Case Title
        case_title = "State vs Unknown"
        for pat in self.PARTY_PATTERNS:
            m = pat.search(full_text)
            if m:
                matched_snippet = m.group(0).strip()
                case_title = re.sub(r"\s+", " ", matched_snippet)[:80]
                prov = doc.find_provenance(matched_snippet)
                provenance["case_title"] = FieldProvenance(
                    page_num=prov["page_num"] if prov else 1,
                    line_num=prov["line_num"] if prov else 1,
                    snippet=matched_snippet,
                    confidence=0.85,
                    source_type="extracted",
                )
                confidences["case_title"] = 0.85
                break

        # 8. Custody Status
        custody_status = "Not Arrested"
        for pat, status_val in self.CUSTODY_PATTERNS:
            m = pat.search(full_text)
            if m:
                custody_status = status_val
                prov = doc.find_provenance(m.group(0))
                provenance["custody_status"] = FieldProvenance(
                    page_num=prov["page_num"] if prov else 1,
                    line_num=prov["line_num"] if prov else 1,
                    snippet=m.group(0),
                    confidence=0.9,
                    source_type="extracted",
                )
                confidences["custody_status"] = 0.9
                break

        # 9. Summary
        first_few_lines = [line.strip() for line in full_text.splitlines() if line.strip()][:4]
        summary_text = " ".join(first_few_lines)
        if len(summary_text) > 250:
            summary_text = summary_text[:247] + "..."
        if not summary_text:
            summary_text = f"Criminal matter involving alleged offences under {act} section(s): {', '.join(sections)}."

        return ExtractedCaseDetails(
            case_title=case_title,
            case_number=case_no,
            filing_year=year,
            state=canonical_state,
            state_code=state_code,
            district=canonical_dist,
            dist_code=dist_code,
            court_name=court_name,
            court_no=1,
            act=act,
            sections=sections,
            bns_sections=bns_sections,
            case_type=canonical_type,
            judge_position=canonical_judge,
            judge_tenure_months=12.0,
            accused_count=1,
            custody_status=custody_status,
            case_summary=summary_text,
            provenance=provenance,
            field_confidences=confidences,
            is_llm_extracted=False,
            is_pii_redacted=False,
            extraction_warnings=list(doc.warnings),
        )

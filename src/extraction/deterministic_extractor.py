"""Deterministic legal entity extractor (Layer 1).

Extracts case attributes using regex, labeled patterns, and DDL codebook matching.
Zero hardcoded defaults: every extracted field includes its supporting verbatim quote
and passes through the verification gate.
"""

from __future__ import annotations

import datetime
import re
from typing import Dict, List, Optional, Tuple

from src.extraction.fuzzy_matcher import CodebookMatcher
from src.extraction.schema import ExtractedCaseDetails, ExtractedField
from src.extraction.verifier import verify_and_build_field
from src.ingestion.text_extractor import ExtractedDocument
from src.legal_knowledge.ipc_bns_mapper import get_concordance_entry


class DeterministicLegalExtractor:
    """Robust, verifiable rule-based extractor for Indian legal documents."""

    def __init__(self, matcher: Optional[CodebookMatcher] = None):
        self.matcher = matcher or CodebookMatcher()

    # Procedural sections to ignore as substantive charges
    PROCEDURAL_SECTIONS = {"173", "173CR", "173CRPC", "41A", "41ACRPC", "154", "154CRPC", "190", "193", "209", "35", "35BNSS", "27"}

    def extract(self, doc: ExtractedDocument) -> ExtractedCaseDetails:
        """Extract structured fields with verifiable quotes and honest confidence."""
        text = doc.raw_text

        # 1. Case Number
        case_no_field = self._extract_case_number(text)

        # 2. Filing Date & Year
        filing_date_field, filing_year_field = self._extract_filing_date(text)

        # 3. Court Name & Court Type
        court_name_field, court_type_field = self._extract_court_info(text)

        # 4. State & District (hierarchical matching)
        state_field, state_code_field, dist_field, dist_code_field = self._extract_jurisdiction(text)

        # 5. Act, Sections & BNS Concordance
        act_field, sections_field, bns_map = self._extract_act_and_sections(text)

        # 6. Parties & Accused Details
        title_field, accused_names_field, accused_count_field = self._extract_parties_and_accused(text)

        # 7. Custody Status
        custody_field = self._extract_custody_status(text)

        # 8. Case Type & Stage
        case_type_field, stage_field = self._extract_case_type_and_stage(text)

        # 9. Case Allegations Summary (Phase 4)
        summary_field = self._extract_case_summary(text)

        # Compile warnings
        warnings: List[str] = list(doc.warnings)
        if not sections_field.value:
            warnings.append("No penal sections were found in the document. Please enter them manually.")
        if not state_field.value or not dist_field.value:
            warnings.append("State or District court jurisdiction could not be fully identified.")

        return ExtractedCaseDetails(
            case_number=case_no_field,
            case_title=title_field,
            filing_date=filing_date_field,
            filing_year=filing_year_field,
            court_name=court_name_field,
            court_type=court_type_field,
            state=state_field,
            state_code=state_code_field,
            district=dist_field,
            dist_code=dist_code_field,
            act=act_field,
            sections=sections_field,
            bns_equivalents=bns_map,
            accused_names=accused_names_field,
            accused_count=accused_count_field,
            custody_status=custody_field,
            case_type=case_type_field,
            stage=stage_field,
            case_summary=summary_field,
            extraction_mode="DETERMINISTIC_RULES",
            is_pii_redacted=False,
            warnings=warnings,
        )

    # =========================================================================
    # Individual Field Extractors
    # =========================================================================

    def _extract_case_number(self, text: str) -> ExtractedField[str]:
        """Extract court case number or FIR number with verbatim evidence."""
        patterns = [
            # Criminal Case No. 412 of 2016, Sessions Case No. 205 of 2018
            re.compile(r"(?:Criminal\s*Case\s*No\.?|Crl\.?\s*Case\s*No\.?|Sessions\s*Case\s*No\.?|Special\s*Case\s*No\.?|C\.?C\.?\s*No\.?)\s*[:\-]?\s*([0-9]+(?:\s*(?:of|\/)\s*[0-9]{4}))", re.IGNORECASE),
            # General Case No.
            re.compile(r"(?:Case\s*No\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-_]+(?:\s*(?:of|\/)\s*[0-9]{4})?)", re.IGNORECASE),
            # FIR No.
            re.compile(r"(?:FIR\s*No\.?|First\s*Information\s*Report\s*No\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-_]+(?:\s*(?:of|\/)\s*[0-9]{4})?)", re.IGNORECASE),
        ]

        for pat in patterns:
            m = pat.search(text)
            if m:
                val = m.group(1).strip()
                snippet = m.group(0).strip()
                return verify_and_build_field(
                    value=val,
                    evidence_snippet=snippet,
                    source_text=text,
                    method="labeled_regex",
                    start_offset=m.start(),
                    end_offset=m.end(),
                )

        return verify_and_build_field(None, None, text)

    def _extract_filing_date(self, text: str) -> Tuple[ExtractedField[str], ExtractedField[int]]:
        """Extract filing date (normalized to ISO YYYY-MM-DD) and filing year."""
        date_patterns = [
            # Date of Filing: 14 March 2016
            re.compile(r"(?:Date\s*of\s*Filing|Filing\s*Date|Filed\s*on)\s*[:\-]?\s*([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+[0-9]{4})", re.IGNORECASE),
            # Date of Filing: 14/03/2016 or 14-03-2016
            re.compile(r"(?:Date\s*of\s*Filing|Filing\s*Date|Filed\s*on)\s*[:\-]?\s*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{4})", re.IGNORECASE),
        ]

        for pat in date_patterns:
            m = pat.search(text)
            if m:
                raw_date_str = m.group(1).strip()
                snippet = m.group(0).strip()
                # Clean ordinal suffixes (14th -> 14)
                clean_str = re.sub(r"(\d+)(?:st|nd|rd|th)", r"\1", raw_date_str)
                iso_date = None
                filing_year = None

                for fmt in ["%d %B %Y", "%d %b %Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                    try:
                        dt = datetime.datetime.strptime(clean_str, fmt)
                        iso_date = dt.strftime("%Y-%m-%d")
                        filing_year = dt.year
                        break
                    except ValueError:
                        continue

                if iso_date and filing_year:
                    date_field = verify_and_build_field(
                        value=iso_date,
                        evidence_snippet=snippet,
                        source_text=text,
                        method="labeled_regex",
                        start_offset=m.start(),
                        end_offset=m.end(),
                        must_contain_literal=False,
                    )
                    year_field = verify_and_build_field(
                        value=filing_year,
                        evidence_snippet=snippet,
                        source_text=text,
                        method="labeled_regex",
                        start_offset=m.start(),
                        end_offset=m.end(),
                        must_contain_literal=True,
                    )
                    return date_field, year_field

        # Fallback for year only
        year_pat = re.compile(r"\b(20[0-2][0-9]|19[89][0-9])\b")
        matches = list(year_pat.finditer(text))
        if matches:
            # Check years near header
            first_match = matches[0]
            val_year = int(first_match.group(1))
            year_field = verify_and_build_field(
                value=val_year,
                evidence_snippet=first_match.group(0),
                source_text=text,
                method="pattern_regex",
                start_offset=first_match.start(),
                end_offset=first_match.end(),
            )
            return verify_and_build_field(None, None, text), year_field

        return verify_and_build_field(None, None, text), verify_and_build_field(None, None, text)

    def _extract_court_info(self, text: str) -> Tuple[ExtractedField[str], ExtractedField[str]]:
        """Extract full court name and canonical court classification."""
        court_patterns = [
            # IN THE COURT OF JUDICIAL MAGISTRATE FIRST CLASS, LUCKNOW, UTTAR PRADESH
            re.compile(r"(?:IN\s+THE\s+COURT\s+OF\s+)(.+?)(?=\n|POLICE\s+REPORT|CHARGE\s+SHEET|VERSUS|COMMITTAL|\r|$)", re.IGNORECASE),
            re.compile(r"(?:Court\s+of\s+)(.+?)(?=\n|POLICE\s+REPORT|CHARGE\s+SHEET|VERSUS|COMMITTAL|\r|$)", re.IGNORECASE),
        ]

        court_name_val = None
        court_snippet = None
        start_off, end_off = None, None

        for pat in court_patterns:
            m = pat.search(text)
            if m:
                raw_c = m.group(1).strip()
                # Clean trailing commas/whitespace
                raw_c = re.sub(r"[\,\s]+$", "", raw_c)
                court_name_val = f"Court of {raw_c}" if not raw_c.lower().startswith("court") else raw_c
                court_snippet = m.group(0).strip()
                start_off, end_off = m.start(), m.end()
                break

        if court_name_val:
            court_field = verify_and_build_field(
                value=court_name_val,
                evidence_snippet=court_snippet,
                source_text=text,
                method="labeled_regex",
                start_offset=start_off,
                end_offset=end_off,
                must_contain_literal=False,
            )
            c_type, _ = self.matcher.canonicalize_court_type(court_name_val)
            type_field = verify_and_build_field(
                value=c_type,
                evidence_snippet=court_snippet,
                source_text=text,
                method="codebook_match",
                start_offset=start_off,
                end_offset=end_off,
                must_contain_literal=False,
            )
            return court_field, type_field

        return verify_and_build_field(None, None, text), verify_and_build_field(None, None, text)

    def _extract_jurisdiction(
        self, text: str
    ) -> Tuple[ExtractedField[str], ExtractedField[int], ExtractedField[str], ExtractedField[int]]:
        """Extract state and district using structured headers and fuzzy codebook matching.

        NO HARDCODED DEFAULTS.
        """
        raw_state: Optional[str] = None
        raw_dist: Optional[str] = None
        state_snippet: Optional[str] = None
        dist_snippet: Optional[str] = None

        # 1. Look for explicit labeled fields (e.g. State: Uttar Pradesh, District: Lucknow)
        state_labeled = re.search(r"(?:State)\s*[:\-]\s*([A-Za-z\s]+?)(?=\n|,|\.|District|Police)", text, re.IGNORECASE)
        if state_labeled:
            raw_state = state_labeled.group(1).strip()
            state_snippet = state_labeled.group(0).strip()

        dist_labeled = re.search(r"(?:District|Dist\.?)\s*[:\-]\s*([A-Za-z\s]+?)(?=\n|,|\.|State|Police)", text, re.IGNORECASE)
        if dist_labeled:
            raw_dist = dist_labeled.group(1).strip()
            dist_snippet = dist_labeled.group(0).strip()

        # 2. Look for "State of X versus Y"
        if not raw_state:
            state_vs = re.search(r"(?:State\s+of\s+)([A-Za-z\s]+?)(?=\s+versus|\s+vs\.?)", text, re.IGNORECASE)
            if state_vs:
                raw_state = state_vs.group(1).strip()
                state_snippet = state_vs.group(0).strip()

        # 3. Look at Court header tokens (e.g. "IN THE COURT OF ..., LUCKNOW, UTTAR PRADESH")
        header_m = re.search(r"(?:IN\s+THE\s+COURT\s+OF\s+)(.+?)(?=\n)", text, re.IGNORECASE)
        if header_m:
            tokens = [t.strip() for t in header_m.group(1).split(",") if t.strip()]
            for t in reversed(tokens):
                if not raw_state:
                    s_code, s_name, _ = self.matcher.match_state(t)
                    if s_code is not None:
                        raw_state = s_name
                        state_snippet = t
                        continue
                if not raw_dist:
                    d_code, d_name, _ = self.matcher.match_district(t)
                    if d_code is not None:
                        raw_dist = d_name
                        dist_snippet = t

        # Match to codebook codes
        s_code, s_name, _ = self.matcher.match_state(raw_state)
        d_code, d_name, _ = self.matcher.match_district(raw_dist, state_code=s_code)

        state_field = verify_and_build_field(
            value=s_name,
            evidence_snippet=state_snippet,
            source_text=text,
            method="codebook_match",
            must_contain_literal=False,
        )
        state_code_field = verify_and_build_field(
            value=s_code,
            evidence_snippet=state_snippet,
            source_text=text,
            method="codebook_match",
            must_contain_literal=False,
        )
        dist_field = verify_and_build_field(
            value=d_name,
            evidence_snippet=dist_snippet,
            source_text=text,
            method="codebook_match",
            must_contain_literal=False,
        )
        dist_code_field = verify_and_build_field(
            value=d_code,
            evidence_snippet=dist_snippet,
            source_text=text,
            method="codebook_match",
            must_contain_literal=False,
        )

        return state_field, state_code_field, dist_field, dist_code_field

    def _extract_act_and_sections(
        self, text: str
    ) -> Tuple[ExtractedField[str], ExtractedField[List[str]], Dict[str, Optional[str]]]:
        """Extract substantive penal act, charged sections (with sub-parts), and BNS concordance."""
        # 1. Detect Act
        act_val = None
        act_snippet = None
        act_is_inferred = False

        if re.search(r"(?:Bharatiya\s*Nyaya\s*Sanhita|BNS)", text, re.IGNORECASE):
            m = re.search(r"(?:Bharatiya\s*Nyaya\s*Sanhita|BNS(?:\s*2023)?)", text, re.IGNORECASE)
            act_val = "Bharatiya Nyaya Sanhita, 2023"
            act_snippet = m.group(0) if m else "BNS"
        elif re.search(r"(?:Indian\s*Penal\s*Code|IPC)", text, re.IGNORECASE):
            m = re.search(r"(?:Indian\s*Penal\s*Code(?:\s*,\s*1860)?|IPC)", text, re.IGNORECASE)
            act_val = "The Indian Penal Code"
            act_snippet = m.group(0) if m else "IPC"

        # 2. Extract substantive penal sections
        sections: List[str] = []
        snippets: List[str] = []

        # Target specific bulleted / listed section lines first:
        # e.g. "- IPC Section 323 (Voluntarily causing hurt)"
        # e.g. "- IPC Section 506 Part I (Criminal intimidation)"
        line_patterns = [
            re.compile(r"(?:IPC|BNS)\s*Section\s*([0-9]+(?:\s*(?:Part\s*[A-Za-z0-9]+|\([0-9A-Za-z]+\)))?)", re.IGNORECASE),
            re.compile(r"(?:Section|Sec\.?)\s*([0-9]+(?:\s*(?:Part\s*[A-Za-z0-9]+|\([0-9A-Za-z]+\)))?)\s*(?:of\s+IPC|IPC)", re.IGNORECASE),
        ]

        for pat in line_patterns:
            for m in pat.finditer(text):
                sec_raw = m.group(1).strip()
                # Clean extra whitespace inside section string e.g. "506 Part I"
                sec_clean = re.sub(r"\s+", " ", sec_raw)
                # Check if it's a procedural section
                digits = re.findall(r"\d+", sec_clean)
                if digits and digits[0] in self.PROCEDURAL_SECTIONS:
                    continue
                if sec_clean not in sections:
                    sections.append(sec_clean)
                    snippets.append(m.group(0))

        # Also search general patterns only if line patterns didn't find any substantive sections
        if not sections:
            general_sec_pat = re.compile(r"(?:offences\s+under|charged\s+under|sections?|u\/ss?\.?)\s*([0-9\s,\/and\-\(\)A-Za-z]+?)(?=(?:\([A-Za-z\s]+\))|\.|\n|$|STATUS|NAMES)", re.IGNORECASE)
            for m in general_sec_pat.finditer(text):
                chunk = m.group(1)
                # Ignore procedural or evidentiary references
                if "evidence" in chunk.lower() or "crpc" in chunk.lower() or "bnss" in chunk.lower():
                    continue
                # Tokenize by comma, and, /
                tokens = re.split(r"[,/&]|and", chunk)
                for t in tokens:
                    t_clean = t.strip()
                    if "evidence" in t_clean.lower() or "crpc" in t_clean.lower() or "bnss" in t_clean.lower():
                        continue
                    # Match section number with optional Part or bracket e.g. 506 Part I or 303(2) or 302
                    m_sub = re.match(r"^(\d+(?:\s*(?:Part\s*[A-Za-z0-9]+|\([0-9A-Za-z]+\)|[A-E](?![a-zA-Z])))?)", t_clean, re.IGNORECASE)
                    if m_sub:
                        val = re.sub(r"\s+", " ", m_sub.group(1)).strip()
                        digits = re.findall(r"\d+", val)
                        if digits and digits[0] in self.PROCEDURAL_SECTIONS:
                            continue
                        if val and val not in sections:
                            sections.append(val)
                            snippets.append(m.group(0).strip())

        # If act was not explicitly stated, infer from sections
        if not act_val and sections:
            act_val = "The Indian Penal Code"
            act_snippet = f"Inferred from penal section(s): {', '.join(sections)}"
            act_is_inferred = True

        act_field = verify_and_build_field(
            value=act_val,
            evidence_snippet=act_snippet,
            source_text=text,
            method="labeled_regex" if not act_is_inferred else "inferred",
            is_inferred=act_is_inferred,
            must_contain_literal=False,
        )

        full_sec_snippet = "; ".join(snippets) if snippets else None
        sections_field = verify_and_build_field(
            value=sections if sections else None,
            evidence_snippet=full_sec_snippet,
            source_text=text,
            method="labeled_regex",
            must_contain_literal=True,
        )

        # Build BNS equivalents map
        bns_map: Dict[str, Optional[str]] = {}
        for s in sections:
            # Extract base section digits for concordance lookup
            base_digits = re.findall(r"\d+", s)
            if base_digits:
                entry = get_concordance_entry(base_digits[0], act_hint=act_val or "")
                if entry:
                    is_bns_act = "bns" in (act_val or "").lower()
                    equiv = f"IPC {entry.ipc_section}" if is_bns_act else f"BNS {entry.bns_section}"
                    bns_map[s] = f"{equiv} ({entry.offence_name})"
                else:
                    bns_map[s] = "Mapping not available"
            else:
                bns_map[s] = "Mapping not available"

        return act_field, sections_field, bns_map

    def _extract_parties_and_accused(
        self, text: str
    ) -> Tuple[ExtractedField[str], ExtractedField[List[str]], ExtractedField[int]]:
        """Extract case title/parties, list of accused names, and accused count."""
        # 1. Case Title
        title_patterns = [
            re.compile(r"(?:^|\n)\s*([A-Za-z0-9\.\,\- ]+?)\s+(?:versus|vs\.?|v\/s)\s+([A-Za-z0-9\.\,\- ]+?)(?=\r|\n|POLICE\s+REPORT|COMMITTAL|$)", re.IGNORECASE),
        ]
        title_val = None
        title_snippet = None
        for pat in title_patterns:
            m = pat.search(text)
            if m:
                # Clean up newline artifacts
                t1 = re.sub(r"\s+", " ", m.group(1)).strip()
                t2 = re.sub(r"\s+", " ", m.group(2)).strip()
                title_val = f"{t1} versus {t2}"
                title_snippet = m.group(0).strip()
                break

        title_field = verify_and_build_field(
            value=title_val,
            evidence_snippet=title_snippet,
            source_text=text,
            method="labeled_regex",
            must_contain_literal=False,
        )

        # 2. Accused Names
        accused_names: List[str] = []
        accused_snippets: List[str] = []

        # Look for numbered accused block:
        # e.g. "NAME OF ACCUSED:\n1. Rajesh Kumar Sharma..."
        # e.g. "NAMES OF ACCUSED:\n1. Suresh Gowda...\n2. Ramesh Patel..."
        block_m = re.search(r"(?:NAMES?\s+OF\s+ACCUSED|ACCUSED\s+PERSONS?|ACCUSED\s*:)\s*\n((?:[0-9]+\.\s*[^\n]+\n?)+)", text, re.IGNORECASE)
        if block_m:
            lines = block_m.group(1).splitlines()
            for line in lines:
                m_name = re.match(r"^[0-9]+\.\s*([A-Za-z\s]+?)(?:,|\(|S\/o|D\/o|W\/o|-|$)", line.strip())
                if m_name:
                    clean_name = m_name.group(1).strip()
                    if clean_name and clean_name not in accused_names:
                        accused_names.append(clean_name)
                        accused_snippets.append(line.strip())

        # Fallback accused name match
        if not accused_names:
            single_m = re.search(r"(?:Accused|Applicant)\s*[:\-]\s*([A-Za-z\s]+?)(?:,|\(|S\/o|D\/o|\n|$)", text, re.IGNORECASE)
            if single_m:
                clean_name = single_m.group(1).strip()
                if clean_name:
                    accused_names.append(clean_name)
                    accused_snippets.append(single_m.group(0).strip())

        full_acc_snippet = "; ".join(accused_snippets) if accused_snippets else None
        accused_names_field = verify_and_build_field(
            value=accused_names if accused_names else None,
            evidence_snippet=full_acc_snippet,
            source_text=text,
            method="labeled_regex",
            must_contain_literal=True,
        )

        accused_count_field = verify_and_build_field(
            value=len(accused_names) if accused_names else None,
            evidence_snippet=full_acc_snippet,
            source_text=text,
            method="labeled_regex",
            must_contain_literal=False,
        )

        return title_field, accused_names_field, accused_count_field

    def _extract_custody_status(self, text: str) -> ExtractedField[str]:
        """Classify custody and procedural bail status from text."""
        patterns = [
            (
                re.compile(r"(?:not\s+arrested|appeared\s+on\s+notice|personal\s+bond)", re.IGNORECASE),
                "Not Arrested / On Personal Bond",
            ),
            (
                re.compile(r"(?:in\s+judicial\s+custody|remanded\s+to\s+judicial\s+custody|detained\s+in\s+central\s+prison)", re.IGNORECASE),
                "In Judicial Custody",
            ),
            (
                re.compile(r"(?:on\s+regular\s+bail|enlarged\s+on\s+regular\s+bail|on\s+bail)", re.IGNORECASE),
                "On Regular Bail",
            ),
            (
                re.compile(r"(?:absconding|non-bailable\s+warrants?\s+have\s+been\s+issued)", re.IGNORECASE),
                "Absconding / Non-Bailable Warrants",
            ),
            (
                re.compile(r"(?:anticipatory\s+bail|pre-arrest\s+protection)", re.IGNORECASE),
                "Anticipatory Bail",
            ),
        ]

        for pat, status_label in patterns:
            m = pat.search(text)
            if m:
                return verify_and_build_field(
                    value=status_label,
                    evidence_snippet=m.group(0).strip(),
                    source_text=text,
                    method="pattern_regex",
                    must_contain_literal=False,
                )

        return verify_and_build_field(None, None, text)

    def _extract_case_type_and_stage(
        self, text: str
    ) -> Tuple[ExtractedField[str], ExtractedField[str]]:
        """Classify case type and procedural stage."""
        case_type_val = None
        case_type_snippet = None

        if re.search(r"Sessions\s*Case", text, re.IGNORECASE):
            m = re.search(r"Sessions\s*Case", text, re.IGNORECASE)
            case_type_val = "Sessions Case"
            case_type_snippet = m.group(0) if m else "Sessions Case"
        elif re.search(r"(?:POLICE\s+REPORT|CHARGE\s*SHEET)", text, re.IGNORECASE):
            m = re.search(r"(?:POLICE\s+REPORT(?:\s*\/\s*CHARGE\s*SHEET)?|CHARGE\s*SHEET)", text, re.IGNORECASE)
            case_type_val = "Criminal Case (Police Report / Charge Sheet)"
            case_type_snippet = m.group(0) if m else "Charge Sheet"
        elif re.search(r"Criminal\s*Complaint", text, re.IGNORECASE):
            m = re.search(r"Criminal\s*Complaint", text, re.IGNORECASE)
            case_type_val = "Criminal Complaint Case"
            case_type_snippet = m.group(0) if m else "Complaint"

        stage_val = None
        stage_snippet = None
        if re.search(r"COMMITTAL\s+PROCEEDINGS", text, re.IGNORECASE):
            stage_val = "Committal / Pre-Trial"
            stage_snippet = "Committal Proceedings"
        elif re.search(r"charge\s+sheet\s+submitted", text, re.IGNORECASE):
            stage_val = "Charge Sheet Submitted / Pre-Trial"
            stage_snippet = "Charge sheet submitted"

        type_field = verify_and_build_field(
            value=case_type_val,
            evidence_snippet=case_type_snippet,
            source_text=text,
            method="pattern_regex",
            must_contain_literal=False,
        )
        stage_field = verify_and_build_field(
            value=stage_val,
            evidence_snippet=stage_snippet,
            source_text=text,
            method="pattern_regex",
            must_contain_literal=False,
        )
        return type_field, stage_field

    def _extract_case_summary(self, text: str) -> ExtractedField[str]:
        """Extract plain-English allegations from BRIEF FACTS section.

        NO GENERIC TEMPLATES.
        """
        # Look for BRIEF FACTS OF THE CASE section
        facts_m = re.search(
            r"(?:BRIEF\s*FACTS(?:\s*OF\s*THE\s*CASE)?|FACTS\s*OF\s*THE\s*CASE|ALLEGATIONS)\s*[:\-]?\s*\n(.+?)(?=\n\n[A-Z0-9\s]+:|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if facts_m:
            raw_facts = facts_m.group(1).strip()
            # Clean newlines and excessive spaces
            clean_facts = re.sub(r"\s+", " ", raw_facts)
            if len(clean_facts) > 450:
                clean_facts = clean_facts[:447] + "..."
            snippet = facts_m.group(0)[:120]
            return verify_and_build_field(
                value=clean_facts,
                evidence_snippet=snippet,
                source_text=text,
                method="labeled_regex",
                must_contain_literal=False,
            )

        return verify_and_build_field(None, None, text)

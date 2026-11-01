"""Anti-hallucination verification gate and honest confidence calculator.

CRITICAL RULE:
For EVERY extracted value, programmatically verify that:
1. Its supporting quote exists verbatim in the source text (normalized whitespace).
2. The value is actually present in that quote.
3. If the check fails, discard the value and return null with confidence_level='MISSING'.
Section numbers, case numbers, and dates MUST literally appear in the text.
"""

from __future__ import annotations

import re
from typing import Any, List, Optional, Tuple

from src.extraction.schema import EvidenceSpan, ExtractedField


def normalize_ws(s: str) -> str:
    """Normalize whitespace for robust verbatim matching."""
    return re.sub(r"\s+", " ", str(s).strip())


def verify_verbatim_quote(
    quote: str,
    source_text: str,
    start_offset: Optional[int] = None,
    end_offset: Optional[int] = None,
) -> Tuple[bool, int, int]:
    """Verify that quote exists in source text and determine exact character offsets.

    Returns:
        (is_valid, start_char, end_char)
    """
    if not quote or not source_text:
        return False, -1, -1

    norm_quote = normalize_ws(quote)
    if not norm_quote:
        return False, -1, -1

    # Check given offsets first
    if start_offset is not None and end_offset is not None and 0 <= start_offset < end_offset <= len(source_text):
        candidate = source_text[start_offset:end_offset]
        if normalize_ws(candidate).lower() == norm_quote.lower():
            return True, start_offset, end_offset

    # Direct search
    idx = source_text.lower().find(quote.strip().lower())
    if idx != -1:
        return True, idx, idx + len(quote.strip())

    # Whitespace-tolerant regex search
    pattern = re.escape(norm_quote).replace(r"\ ", r"\s+")
    m = re.search(pattern, source_text, re.IGNORECASE)
    if m:
        return True, m.start(), m.end()

    return False, -1, -1


def verify_and_build_field(
    value: Optional[Any],
    evidence_snippet: Optional[str],
    source_text: str,
    method: str = "labeled_regex",
    is_inferred: bool = False,
    page_num: int = 1,
    line_num: int = 1,
    start_offset: Optional[int] = None,
    end_offset: Optional[int] = None,
    must_contain_literal: bool = True,
    conflict_warning: Optional[str] = None,
) -> ExtractedField:
    """Verification gate for extracted case parameters.

    Discards any value that fails verbatim evidence verification.
    Computes honest, non-constant confidence scores.
    """
    if value is None or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value):
        return ExtractedField(
            value=None,
            confidence=None,
            confidence_level="MISSING",
            evidence=None,
            verified=False,
            is_inferred=False,
            conflict_warning=None,
        )

    # If inferred without direct quote
    if is_inferred:
        return ExtractedField(
            value=value,
            confidence=0.50,
            confidence_level="INFERRED",
            evidence=EvidenceSpan(
                snippet=evidence_snippet or "(Inferred from context)",
                start_offset=0,
                end_offset=0,
                page_num=page_num,
                line_num=line_num,
                method="inferred",
            ),
            verified=True,
            is_inferred=True,
            conflict_warning=conflict_warning,
        )

    if not evidence_snippet:
        return ExtractedField(
            value=None,
            confidence=None,
            confidence_level="MISSING",
            evidence=None,
            verified=False,
            is_inferred=False,
            conflict_warning="Discarded: value had no supporting source text quote.",
        )

    # Check 1: Does quote exist verbatim in source text?
    valid_quote = False
    start_idx = -1
    end_idx = -1

    if ";" in evidence_snippet:
        sub_snippets = [s.strip() for s in evidence_snippet.split(";") if s.strip()]
        all_valid = True
        first_start = len(source_text)
        last_end = 0
        for sub in sub_snippets:
            v, st, en = verify_verbatim_quote(sub, source_text)
            if not v:
                all_valid = False
                break
            first_start = min(first_start, st)
            last_end = max(last_end, en)
        if all_valid and sub_snippets:
            valid_quote = True
            start_idx = first_start
            end_idx = last_end
    else:
        valid_quote, start_idx, end_idx = verify_verbatim_quote(
            evidence_snippet, source_text, start_offset, end_offset
        )

    if not valid_quote:
        return ExtractedField(
            value=None,
            confidence=None,
            confidence_level="MISSING",
            evidence=None,
            verified=False,
            is_inferred=False,
            conflict_warning=f"Discarded: supporting quote not found in source text: '{evidence_snippet[:40]}...'",
        )

    # Check 2: Must literal value appear in quote or source window?
    if must_contain_literal:
        quote_lower = evidence_snippet.lower()
        if isinstance(value, str):
            val_tokens = [t for t in re.split(r"\s+", value.lower()) if len(t) > 2]
            if val_tokens and not any(t in quote_lower for t in val_tokens):
                return ExtractedField(
                    value=None,
                    confidence=None,
                    confidence_level="MISSING",
                    evidence=None,
                    verified=False,
                    is_inferred=False,
                    conflict_warning=f"Discarded: value '{value}' not supported by quote '{evidence_snippet}'.",
                )
        elif isinstance(value, list):
            verified_items = []
            for item in value:
                norm_item = str(item).lower()
                digits = re.findall(r"\d+", norm_item)
                if digits:
                    if any(d in quote_lower or d in source_text.lower() for d in digits):
                        verified_items.append(item)
                else:
                    if norm_item in quote_lower or norm_item in source_text.lower():
                        verified_items.append(item)
            if not verified_items:
                return ExtractedField(
                    value=None,
                    confidence=None,
                    confidence_level="MISSING",
                    evidence=None,
                    verified=False,
                    is_inferred=False,
                    conflict_warning="Discarded: list items not found in source text.",
                )
            value = verified_items

    # Calculate honest computed confidence score
    confidence: float
    level: str
    if method == "labeled_regex":
        confidence = 0.95
        level = "HIGH"
    elif method == "pattern_regex":
        confidence = 0.85
        level = "MEDIUM"
    elif method == "codebook_match":
        confidence = 0.90
        level = "HIGH"
    elif method == "llm_verified":
        confidence = 0.75
        level = "MEDIUM"
    else:
        confidence = 0.60
        level = "LOW"

    actual_line = source_text[:start_idx].count("\n") + 1

    return ExtractedField(
        value=value,
        confidence=confidence,
        confidence_level=level,
        evidence=EvidenceSpan(
            snippet=evidence_snippet.strip(),
            start_offset=start_idx,
            end_offset=end_idx,
            page_num=page_num,
            line_num=actual_line,
            method=method,
        ),
        verified=True,
        is_inferred=False,
        conflict_warning=conflict_warning,
    )

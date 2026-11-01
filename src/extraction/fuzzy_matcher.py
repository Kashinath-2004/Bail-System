"""Fuzzy matcher to map natural language entities to DDL codebook codes."""

from __future__ import annotations

import difflib
from typing import Dict, List, Optional, Tuple

from src.common.codebook import Codebook


class CodebookMatcher:
    """Fuzzy matches extracted text to canonical DDL codes."""

    def __init__(self, codebook: Optional[Codebook] = None):
        self.codebook = codebook or Codebook.get_instance()
        self._state_name_to_code: Dict[str, int] = {}
        self._district_name_to_keys: Dict[str, List[Tuple[int, int]]] = {}
        self._case_type_to_str: Dict[str, str] = {}
        self._init_lookups()

    def _init_lookups(self):
        for code, name in self.codebook.states.items():
            self._state_name_to_code[name.lower()] = code

        for key, name in self.codebook.districts.items():
            parts = key.split("_")
            if len(parts) == 2:
                try:
                    s_code, d_code = int(parts[0]), int(parts[1])
                    low_name = name.lower()
                    if low_name not in self._district_name_to_keys:
                        self._district_name_to_keys[low_name] = []
                    self._district_name_to_keys[low_name].append((s_code, d_code))
                except ValueError:
                    pass

    def match_state(self, state_text: str) -> Tuple[int, str, float]:
        """Match free-text state to (state_code, canonical_name, confidence)."""
        if not state_text:
            return 1, "Maharashtra", 0.5  # Default fallback

        cleaned = state_text.strip().lower()
        # Direct match
        if cleaned in self._state_name_to_code:
            code = self._state_name_to_code[cleaned]
            return code, self.codebook.get_state_name(code), 1.0

        # Substring / close match
        choices = list(self._state_name_to_code.keys())
        matches = difflib.get_close_matches(cleaned, choices, n=1, cutoff=0.6)
        if matches:
            best_match = matches[0]
            code = self._state_name_to_code[best_match]
            ratio = difflib.SequenceMatcher(None, cleaned, best_match).ratio()
            return code, self.codebook.get_state_name(code), round(ratio, 2)

        # Fallback
        return 1, "Maharashtra", 0.3

    def match_district(self, district_text: str, state_code: Optional[int] = None) -> Tuple[int, str, float]:
        """Match free-text district to (dist_code, canonical_name, confidence)."""
        if not district_text:
            return 1, "Pune", 0.5

        cleaned = district_text.strip().lower()

        # If state_code is provided, prioritize districts within that state
        candidate_names = []
        if state_code is not None:
            prefix = f"{state_code}_"
            for k, name in self.codebook.districts.items():
                if k.startswith(prefix):
                    candidate_names.append((name.lower(), int(k.split("_")[1]), name))

        if candidate_names:
            names_list = [c[0] for c in candidate_names]
            # Exact
            for c_low, d_code, c_orig in candidate_names:
                if cleaned == c_low:
                    return d_code, c_orig, 1.0
            # Fuzzy
            matches = difflib.get_close_matches(cleaned, names_list, n=1, cutoff=0.55)
            if matches:
                matched_name = matches[0]
                for c_low, d_code, c_orig in candidate_names:
                    if c_low == matched_name:
                        ratio = difflib.SequenceMatcher(None, cleaned, matched_name).ratio()
                        return d_code, c_orig, round(ratio, 2)

        # Overall district search
        all_districts = list(self._district_name_to_keys.keys())
        matches = difflib.get_close_matches(cleaned, all_districts, n=1, cutoff=0.55)
        if matches:
            matched_name = matches[0]
            keys = self._district_name_to_keys[matched_name]
            # Use the first one or matching state
            for s_code, d_code in keys:
                if state_code is None or s_code == state_code:
                    ratio = difflib.SequenceMatcher(None, cleaned, matched_name).ratio()
                    return d_code, self.codebook.get_district_name(s_code, d_code), round(ratio, 2)

        return 1, "Pune", 0.3

    def canonicalize_case_type(self, raw_type: str) -> Tuple[str, float]:
        """Map raw case type string to standard DDL category."""
        if not raw_type:
            return "Criminal Case", 0.5
        low = raw_type.lower()
        if "session" in low:
            return "Sessions Case", 0.95
        if "special" in low:
            return "Special Criminal Case", 0.95
        if "appeal" in low:
            return "Criminal Appeal", 0.95
        if "revision" in low:
            return "Criminal Revision", 0.95
        if "misc" in low:
            return "Criminal Misc", 0.9
        if "crl" in low or "cc" in low or "criminal" in low:
            return "Criminal Case", 0.9
        return "Criminal Case", 0.7

    def canonicalize_judge_position(self, raw_judge: str) -> Tuple[str, float]:
        """Map judge description to standard DDL position."""
        if not raw_judge:
            return "Civil Judge Junior Division", 0.5
        low = raw_judge.lower()
        if "chief judicial" in low or "cjm" in low:
            return "Chief Judicial Magistrate", 0.95
        if "session" in low or "district judge" in low:
            return "District and Sessions Judge", 0.95
        if "metropolitan" in low or "mm" in low:
            return "Metropolitan Magistrate", 0.95
        if "senior division" in low:
            return "Civil Judge Senior Division", 0.9
        if "junior division" in low:
            return "Civil Judge Junior Division", 0.9
        return "Civil Judge Junior Division", 0.6

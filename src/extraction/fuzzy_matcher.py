"""Fuzzy matcher to map natural language entities to DDL codebook codes.

HARD RULE: NO hardcoded defaults (Maharashtra, Pune, etc.).
If text is empty or no reasonable match exists, return (None, None, 0.0).
"""

from __future__ import annotations

import difflib
from typing import Dict, List, Optional, Tuple

from src.common.codebook import Codebook


class CodebookMatcher:
    """Fuzzy matches extracted text to canonical DDL codes without canned defaults."""

    def __init__(self, codebook: Optional[Codebook] = None):
        self.codebook = codebook or Codebook.get_instance()
        self._state_name_to_code: Dict[str, int] = {}
        self._district_name_to_keys: Dict[str, List[Tuple[int, int]]] = {}
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

    def match_state(self, state_text: Optional[str]) -> Tuple[Optional[int], Optional[str], float]:
        """Match free-text state to (state_code, canonical_name, confidence).

        Returns (None, None, 0.0) if not found or ambiguous.
        """
        if not state_text or not state_text.strip():
            return None, None, 0.0

        cleaned = state_text.strip().lower()

        # Direct match
        if cleaned in self._state_name_to_code:
            code = self._state_name_to_code[cleaned]
            return code, self.codebook.get_state_name(code), 1.0

        # Substring / close match
        choices = list(self._state_name_to_code.keys())
        matches = difflib.get_close_matches(cleaned, choices, n=1, cutoff=0.70)
        if matches:
            best_match = matches[0]
            code = self._state_name_to_code[best_match]
            ratio = difflib.SequenceMatcher(None, cleaned, best_match).ratio()
            return code, self.codebook.get_state_name(code), round(ratio, 2)

        return None, None, 0.0

    def match_district(
        self,
        district_text: Optional[str],
        state_code: Optional[int] = None,
    ) -> Tuple[Optional[int], Optional[str], float]:
        """Match free-text district to (dist_code, canonical_name, confidence).

        Prioritizes districts within state_code if provided.
        Returns (None, None, 0.0) if not found.
        """
        if not district_text or not district_text.strip():
            return None, None, 0.0

        cleaned = district_text.strip().lower()

        # If state_code is provided, search strictly or primarily within that state
        if state_code is not None:
            prefix = f"{state_code}_"
            candidate_districts = []
            for k, name in self.codebook.districts.items():
                if k.startswith(prefix):
                    candidate_districts.append((name.lower(), int(k.split("_")[1]), name))

            # Exact match in state
            for c_low, d_code, c_orig in candidate_districts:
                if cleaned == c_low or c_low in cleaned or cleaned in c_low:
                    return d_code, c_orig, 1.0

            # Fuzzy match in state
            names_list = [c[0] for c in candidate_districts]
            matches = difflib.get_close_matches(cleaned, names_list, n=1, cutoff=0.65)
            if matches:
                matched_name = matches[0]
                for c_low, d_code, c_orig in candidate_districts:
                    if c_low == matched_name:
                        ratio = difflib.SequenceMatcher(None, cleaned, matched_name).ratio()
                        return d_code, c_orig, round(ratio, 2)

        # Global search across all districts
        all_districts = list(self._district_name_to_keys.keys())
        matches = difflib.get_close_matches(cleaned, all_districts, n=1, cutoff=0.70)
        if matches:
            matched_name = matches[0]
            keys = self._district_name_to_keys[matched_name]
            # Match state if candidate matches state_code
            for s_code, d_code in keys:
                if state_code is None or s_code == state_code:
                    ratio = difflib.SequenceMatcher(None, cleaned, matched_name).ratio()
                    return d_code, self.codebook.get_district_name(s_code, d_code), round(ratio, 2)

        return None, None, 0.0

    def canonicalize_court_type(self, raw_court: Optional[str]) -> Tuple[Optional[str], float]:
        """Classify court type based on evidence in text."""
        if not raw_court:
            return None, 0.0
        low = raw_court.lower()
        if "sessions" in low:
            return "Sessions Court", 0.95
        if "chief judicial magistrate" in low or "cjm" in low:
            return "Chief Judicial Magistrate", 0.95
        if "chief metropolitan magistrate" in low or "cmm" in low:
            return "Chief Metropolitan Magistrate", 0.95
        if "metropolitan magistrate" in low or "mm" in low:
            return "Metropolitan Magistrate", 0.95
        if "judicial magistrate first class" in low or "jmfc" in low:
            return "Judicial Magistrate First Class (JMFC)", 0.95
        if "civil judge senior division" in low:
            return "Civil Judge Senior Division", 0.90
        if "civil judge junior division" in low:
            return "Civil Judge Junior Division", 0.90
        if "magistrate" in low:
            return "Magistrate Court", 0.80
        return None, 0.0

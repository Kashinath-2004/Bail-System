"""In-memory Personally Identifiable Information (PII) Redactor.

Ensures that uploaded documents containing sensitive personal data (names, phone numbers,
Aadhaar numbers, PAN cards, email addresses) can be redacted in memory before further processing.
Never writes PII to disk or external services.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


class EntityRedactor:
    """In-memory redactor for Indian legal documents."""

    # Patterns for common sensitive data
    AADHAAR_PATTERN = re.compile(r"\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b")
    PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
    PHONE_PATTERN = re.compile(r"(?:\+?91[\-\s]?)?[6-9]\d{9}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PINCODE_PATTERN = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")

    # Name indicator patterns in Indian legal docs (e.g. "Accused: Ramesh Kumar", "Versus: Ramesh Kumar", "Complainant: Sita Devi")
    NAME_HEADER_PATTERNS = [
        re.compile(r"(?:Accused|Applicant|Petitioner|Complainant|Informant|Victim|Appellant|Respondent)\s*(?::|-|is|name\s*is)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.IGNORECASE),
        re.compile(r"(?:S/o|D/o|W/o)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.IGNORECASE),
        re.compile(r"(?:Advocate|Counsel)\s*(?:for\s+[a-z]+)?\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", re.IGNORECASE),
    ]

    def redact(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Redact PII in text in memory.

        Returns:
            Tuple of (redacted_text, redaction_counts)
        """
        counts = {
            "aadhaar": 0,
            "pan": 0,
            "phone": 0,
            "email": 0,
            "names": 0,
        }

        # 1. Aadhaar
        def _rep_aadhaar(m):
            counts["aadhaar"] += 1
            return "[REDACTED_AADHAAR]"

        text = self.AADHAAR_PATTERN.sub(_rep_aadhaar, text)

        # 2. PAN
        def _rep_pan(m):
            counts["pan"] += 1
            return "[REDACTED_PAN]"

        text = self.PAN_PATTERN.sub(_rep_pan, text)

        # 3. Phone
        def _rep_phone(m):
            counts["phone"] += 1
            return "[REDACTED_PHONE]"

        text = self.PHONE_PATTERN.sub(_rep_phone, text)

        # 4. Email
        def _rep_email(m):
            counts["email"] += 1
            return "[REDACTED_EMAIL]"

        text = self.EMAIL_PATTERN.sub(_rep_email, text)

        # 5. Names following legal prefixes
        for pat in self.NAME_HEADER_PATTERNS:
            def _rep_name(m):
                counts["names"] += 1
                matched_name = m.group(1)
                full_match = m.group(0)
                return full_match.replace(matched_name, "[REDACTED_NAME]")
            text = pat.sub(_rep_name, text)

        return text, counts


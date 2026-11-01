"""Data models and schemas for honest, evidence-backed case extraction.

NO hardcoded defaults, mock values, or constant confidences.
Every extracted value is wrapped with its supporting verbatim quote,
exact character offsets, line/page references, and computed confidence score.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceSpan(BaseModel):
    """Verbatim text snippet and exact location in the source document."""
    snippet: str = Field(description="Exact verbatim excerpt from the document")
    start_offset: int = Field(description="Character start index in raw document text")
    end_offset: int = Field(description="Character end index in raw document text")
    page_num: int = Field(default=1, description="1-based page number")
    line_num: int = Field(default=1, description="1-based line number")
    method: str = Field(
        default="labeled_regex",
        description="Extraction method: 'labeled_regex', 'pattern_regex', 'codebook_match', 'llm_verified', 'inferred'",
    )


class ExtractedField(BaseModel):
    """A single extracted field with computed confidence, evidence, and verification state."""
    value: Optional[Any] = None
    confidence: Optional[float] = None  # 0.0 to 1.0; None if value is None
    confidence_level: str = "MISSING"   # HIGH, MEDIUM, LOW, INFERRED, MISSING
    evidence: Optional[EvidenceSpan] = None
    verified: bool = False
    is_inferred: bool = False
    conflict_warning: Optional[str] = None


class ExtractedCaseDetails(BaseModel):
    """Complete structured case record extracted from document text.

    Zero hardcoded defaults: missing fields have value=None and confidence_level='MISSING'.
    """
    case_number: ExtractedField = Field(default_factory=ExtractedField)
    case_title: ExtractedField = Field(default_factory=ExtractedField)
    filing_date: ExtractedField = Field(default_factory=ExtractedField)  # ISO YYYY-MM-DD
    filing_year: ExtractedField = Field(default_factory=ExtractedField)
    court_name: ExtractedField = Field(default_factory=ExtractedField)
    court_type: ExtractedField = Field(default_factory=ExtractedField)
    state: ExtractedField = Field(default_factory=ExtractedField)
    state_code: ExtractedField = Field(default_factory=ExtractedField)
    district: ExtractedField = Field(default_factory=ExtractedField)
    dist_code: ExtractedField = Field(default_factory=ExtractedField)
    act: ExtractedField = Field(default_factory=ExtractedField)
    sections: ExtractedField = Field(default_factory=ExtractedField)
    bns_equivalents: Dict[str, Optional[str]] = Field(default_factory=dict)
    accused_names: ExtractedField = Field(default_factory=ExtractedField)
    accused_count: ExtractedField = Field(default_factory=ExtractedField)
    custody_status: ExtractedField = Field(default_factory=ExtractedField)
    case_type: ExtractedField = Field(default_factory=ExtractedField)
    stage: ExtractedField = Field(default_factory=ExtractedField)
    case_summary: ExtractedField = Field(default_factory=ExtractedField)
    extraction_mode: str = "DETERMINISTIC_RULES"  # 'DETERMINISTIC_RULES' or 'HYBRID_LLM'
    is_pii_redacted: bool = False
    warnings: List[str] = Field(default_factory=list)

    model_config = {"protected_namespaces": ()}

    def to_flat_dict(self) -> Dict[str, Any]:
        """Convert to a flat dictionary for legacy ML pipeline compatibility."""
        return {
            "case_number": self.case_number.value,
            "case_title": self.case_title.value,
            "filing_date": self.filing_date.value,
            "filing_year": self.filing_year.value,
            "court_name": self.court_name.value,
            "court_type": self.court_type.value,
            "state": self.state.value,
            "state_code": self.state_code.value,
            "district": self.district.value,
            "dist_code": self.dist_code.value,
            "act": self.act.value,
            "sections": self.sections.value or [],
            "bns_equivalents": self.bns_equivalents,
            "accused_names": self.accused_names.value or [],
            "accused_count": self.accused_count.value or 0,
            "custody_status": self.custody_status.value,
            "case_type": self.case_type.value,
            "stage": self.stage.value,
            "case_summary": self.case_summary.value,
            "extraction_mode": self.extraction_mode,
            "is_pii_redacted": self.is_pii_redacted,
            "warnings": self.warnings,
        }

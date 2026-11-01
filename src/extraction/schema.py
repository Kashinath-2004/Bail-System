"""Data models and schemas for case document extraction and review."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FieldProvenance(BaseModel):
    """Origin and location of an extracted field in the source document."""
    page_num: Optional[int] = None
    line_num: Optional[int] = None
    snippet: Optional[str] = None
    confidence: float = 1.0
    source_type: str = "extracted"  # 'extracted', 'inferred', 'rule_lookup', 'user_provided'


class ExtractedCaseDetails(BaseModel):
    """Structured case parameters extracted from document or user input."""
    case_title: str = Field(default="State vs Unknown", description="Title of the case or parties")
    case_number: Optional[str] = Field(default=None, description="Court case number or FIR number")
    filing_year: int = Field(default=2024, description="Year of filing or incident")
    
    # Geographic & Court attributes
    state: str = Field(default="Maharashtra", description="State name in India")
    state_code: int = Field(default=1, description="DDL Codebook State ID (1-36)")
    district: str = Field(default="Pune", description="District name")
    dist_code: int = Field(default=1, description="DDL Codebook District ID")
    court_name: str = Field(default="District and Sessions Court", description="Name of court")
    court_no: int = Field(default=1, description="Court number / room")
    
    # Legal & Procedural attributes
    act: str = Field(default="The Indian Penal Code", description="Governing Act (IPC or BNS)")
    sections: List[str] = Field(default_factory=lambda: ["379"], description="List of primary charged sections")
    bns_sections: List[str] = Field(default_factory=list, description="Equivalent BNS sections if IPC or vice-versa")
    case_type: str = Field(default="Criminal Case", description="Case type description")
    judge_position: str = Field(default="Civil Judge Junior Division", description="Designation of judge")
    judge_tenure_months: float = Field(default=12.0, description="Estimated judge tenure at filing in months")
    
    # Case background
    accused_count: int = Field(default=1, description="Number of accused persons")
    custody_status: str = Field(default="Not Arrested", description="Custody status: In Custody, On Bail, Not Arrested")
    case_summary: str = Field(default="", description="Plain-English summary of allegations")
    
    # Metadata, provenance and confidence
    provenance: Dict[str, FieldProvenance] = Field(default_factory=dict)
    field_confidences: Dict[str, float] = Field(default_factory=dict)
    is_llm_extracted: bool = False
    is_pii_redacted: bool = False
    extraction_warnings: List[str] = Field(default_factory=list)

    model_config = {"protected_namespaces": ()}

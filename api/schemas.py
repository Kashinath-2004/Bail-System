"""Pydantic request and response schemas for Justice AI API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CaseInput(BaseModel):
    state_code: int = Field(..., description="Numeric State Code from DDL")
    dist_code: int = Field(..., description="Numeric District Code")
    court_no: int = Field(default=1, description="Court Number in Complex")
    act_code: Optional[int] = Field(default=17332, description="Act Key Code (e.g. IPC)")
    section: Optional[int] = Field(default=302, description="Primary Section (e.g. IPC Section)")
    bailable_ipc: int = Field(default=0, description="1 if Bailable, 0 if Non-Bailable")
    number_sections_category: str = Field(default="1 to 2", description="Number of Sections Category: 1 to 2, 3 to 5, etc.")
    filing_judge_tenure_months: float = Field(default=12.0, description="Presiding judge tenure at filing in months")
    case_type_code: int = Field(default=1, description="Case Type Key Code")

class FeatureContribution(BaseModel):
    feature: str
    impact: str
    direction: str = "increase_delay"

class PredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str
    message: Optional[str] = None
    model_trained: bool = True
    predicted_class: Optional[str] = None
    delay_risk_pct: Optional[float] = None
    ontime_confidence_pct: Optional[float] = None
    routed_regressor: Optional[str] = None
    predicted_duration_months: Optional[float] = None
    duration_range_months: Optional[List[float]] = None
    top_features: Optional[List[FeatureContribution]] = None

class CodebookItem(BaseModel):
    code: int
    name: str

class ModelInfoResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    architecture: str
    stages: List[str]
    trained_models: Dict[str, bool]
    training_data_coverage: str
    paper_citation: str

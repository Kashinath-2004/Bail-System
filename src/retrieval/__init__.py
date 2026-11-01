"""Structured case retrieval package for Justice AI.

Queries DDL e-Courts structured records by legal sections, case type, and jurisdiction,
with hierarchical widening (District -> Statewide -> National) and explicit source attribution.
"""

from src.retrieval.similar_cases import (
    SimilarCaseSummary,
    HistoricalCaseRecord,
    retrieve_similar_cases,
)

__all__ = [
    "SimilarCaseSummary",
    "HistoricalCaseRecord",
    "retrieve_similar_cases",
]


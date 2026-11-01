"""Legal knowledge base package for Justice AI.

Provides statutory mapping between BNS (2023) and IPC (1860),
and rule-based bailability classification according to the First Schedule
of CrPC (1973) and BNSS (2023).
"""

from src.legal_knowledge.ipc_bns_mapper import (
    bns_to_ipc,
    get_concordance_entry,
    ipc_to_bns,
    normalize_section_number,
)
from src.legal_knowledge.bail_rules import (
    BailAssessment,
    get_bail_assessment,
)

__all__ = [
    "bns_to_ipc",
    "ipc_to_bns",
    "get_concordance_entry",
    "normalize_section_number",
    "BailAssessment",
    "get_bail_assessment",
]


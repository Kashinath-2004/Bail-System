"""Statutory Bailability and Legal Process Advisory Rules.

Implements rule-based bailability classification according to the First Schedule
of the Code of Criminal Procedure (CrPC, 1973) and the Bharatiya Nagarik Suraksha
Sanhita (BNSS, 2023).

CRITICAL ETHICAL & LEGAL CONSTRAINTS:
1. Bailability is a statutory legal classification, NOT an ML prediction.
2. If multiple sections are charged, and ANY section is non-bailable, the overall
   case is legally treated as non-bailable for bail adjudication.
3. Bail timelines represent general procedural process flow under Indian law,
   NOT a fabricated prediction of days or dates for the specific case.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.legal_knowledge.ipc_bns_mapper import get_concordance_entry, normalize_section_number


@dataclass
class SectionBailInfo:
    section: str
    act: str
    offence_name: str
    bailable: bool
    punishment: str
    triable_by: str


@dataclass
class BailAssessment:
    """Complete statutory bail assessment output for citizen advisory."""
    overall_bailable: bool
    status_label: str  # "Bailable" or "Non-Bailable"
    summary_explanation: str
    governing_sections: List[SectionBailInfo] = field(default_factory=list)
    non_bailable_triggers: List[str] = field(default_factory=list)
    statutory_provisions: List[dict] = field(default_factory=list)
    judicial_factors: List[str] = field(default_factory=list)
    process_timeline_steps: List[dict] = field(default_factory=list)
    disclaimer: str = (
        "Statutory classification based on the First Schedule of CrPC / BNSS. "
        "This is legal informational guidance and does not constitute formal legal counsel. "
        "Actual grant of bail in non-bailable offences depends entirely on judicial discretion."
    )
    source: str = "Statutory Law Lookup (CrPC 1973 / BNSS 2023 First Schedule)"


def get_bail_assessment(
    sections: List[str],
    act: str = "The Indian Penal Code",
) -> BailAssessment:
    """Perform deterministic statutory bailability evaluation.

    Args:
        sections: List of section strings (e.g. ["379"] or ["302", "34"]).
        act: Act name string (IPC or BNS).

    Returns:
        BailAssessment with multi-section precedence, governing provisions, and procedural steps.
    """
    clean_sections = [s for s in sections if s and str(s).strip()]
    if not clean_sections:
        clean_sections = ["379"]  # default fallback if completely unstated

    is_bns = "bns" in act.lower() or "bharatiya" in act.lower()
    section_infos: List[SectionBailInfo] = []
    non_bailable_sections: List[str] = []

    for sec in clean_sections:
        entry = get_concordance_entry(sec, act_hint=act)
        if entry:
            sec_bailable = entry.bailable
            sec_info = SectionBailInfo(
                section=entry.bns_section if is_bns else entry.ipc_section,
                act="Bharatiya Nyaya Sanhita, 2023" if is_bns else "Indian Penal Code, 1860",
                offence_name=entry.offence_name,
                bailable=sec_bailable,
                punishment=entry.max_punishment,
                triable_by=entry.triable_by,
            )
            section_infos.append(sec_info)
            if not sec_bailable:
                non_bailable_sections.append(sec_info.section)
        else:
            # Conservative legal fallback: sections with 3+ digits or unknown
            # If not in concordance, evaluate general gravity
            norm = normalize_section_number(sec)
            sec_info = SectionBailInfo(
                section=norm,
                act=act,
                offence_name=f"Offence under Section {norm}",
                bailable=False if norm in {"302", "307", "376", "420", "392", "395"} else True,
                punishment="As prescribed by statute",
                triable_by="Competent Court",
            )
            section_infos.append(sec_info)
            if not sec_info.bailable:
                non_bailable_sections.append(sec_info.section)

    # Multi-section rule: Any non-bailable section makes the overall case non-bailable
    overall_bailable = len(non_bailable_sections) == 0

    if overall_bailable:
        status_label = "Bailable Offence"
        summary = (
            "Under Indian law, for bailable offences, bail is a matter of statutory right rather than judicial "
            "discretion. The accused is entitled to be released upon furnishing a bail bond with or without sureties."
        )
        provisions = [
            {
                "statute": "BNSS 2023" if is_bns else "CrPC 1973",
                "section": "Section 478 BNSS" if is_bns else "Section 436 CrPC",
                "title": "Bail as a Matter of Right",
                "detail": (
                    "Mandates that when any person accused of a bailable offence is arrested or detained without warrant, "
                    "or appears or is brought before a Court, such person shall be released on bail upon furnishing bond."
                ),
            },
            {
                "statute": "BNSS 2023" if is_bns else "CrPC 1973",
                "section": "Section 479 BNSS" if is_bns else "Section 436A CrPC",
                "title": "Maximum Period of Detention for Undertrial Prisoners",
                "detail": (
                    "Undertrial prisoners detained for up to one-half (or one-third for first-time offenders under BNSS) "
                    "of the maximum imprisonment period must be released on personal bond."
                ),
            },
        ]
        factors = [
            "Bail cannot be refused if acceptable bail bonds / sureties are furnished.",
            "Indigent persons incapable of furnishing surety within a week must be released on personal bond without surety.",
            "Accused must cooperate with the investigation and attend future court dates.",
        ]
        timeline = [
            {
                "stage": "Police Station Stage",
                "timing": "Immediately upon arrest / detention",
                "action": "Station House Officer (SHO) is legally bound to inform the accused of their right to bail and accept personal bond/sureties.",
            },
            {
                "stage": "Magistrate Production",
                "timing": "Within 24 hours of arrest",
                "action": "If not bailed at the police station, the Magistrate must grant bail immediately upon presentation of appropriate bond.",
            },
            {
                "stage": "Release Execution",
                "timing": "Same day or within 24 hours of bond submission",
                "action": "Release order transmitted to prison authorities or executed at court upon verification of sureties.",
            },
        ]
    else:
        status_label = "Non-Bailable Offence"
        triggers_str = ", ".join(f"Section {s}" for s in non_bailable_sections)
        summary = (
            f"This case includes non-bailable charges ({triggers_str}). Bail cannot be claimed as a matter of right. "
            "Release is subject to judicial discretion based on the gravity of allegations, potential punishment, and statutory conditions."
        )
        provisions = [
            {
                "statute": "BNSS 2023" if is_bns else "CrPC 1973",
                "section": "Section 480 BNSS" if is_bns else "Section 437 CrPC",
                "title": "Regular Bail by Magistrate",
                "detail": (
                    "Governs bail powers of Magistrates in non-bailable cases. Bail is generally barred if there are "
                    "reasonable grounds to believe the person is guilty of an offence punishable with death or imprisonment for life."
                ),
            },
            {
                "statute": "BNSS 2023" if is_bns else "CrPC 1973",
                "section": "Section 483 BNSS" if is_bns else "Section 439 CrPC",
                "title": "Special Powers of High Court / Sessions Court",
                "detail": (
                    "Empowers the Sessions Court and High Court to grant regular bail with broader judicial discretion "
                    "and impose any necessary conditions."
                ),
            },
            {
                "statute": "BNSS 2023" if is_bns else "CrPC 1973",
                "section": "Section 482 BNSS" if is_bns else "Section 438 CrPC",
                "title": "Anticipatory Bail (Pre-Arrest Protection)",
                "detail": (
                    "Application to Sessions Court or High Court directing release on bail in the event of arrest "
                    "where there is reasonable apprehension of arrest on false or exaggerated accusations."
                ),
            },
        ]
        factors = [
            "Prima facie gravity and heinousness of the alleged offence.",
            "Severity of punishment upon conviction (e.g. Life imprisonment vs 3-7 years).",
            "Flight risk / likelihood of the accused evading the judicial process.",
            "Risk of tampering with prosecution evidence or threatening witnesses.",
            "Criminal antecedents and prior record of the applicant.",
            "Length of undertrial custody and stage of police investigation.",
        ]
        timeline = [
            {
                "stage": "Bail Application Filing",
                "timing": "Upon arrest or in apprehension (Anticipatory)",
                "action": "Advocate drafts and files formal bail petition before the competent Magistrate or Sessions Court.",
            },
            {
                "stage": "Notice to Prosecution & Case Diary",
                "timing": "Usually 24 to 72 hours",
                "action": "Court serves notice on Public Prosecutor / Investigating Officer (IO) to produce the case diary and status report.",
            },
            {
                "stage": "Hearing & Oral Arguments",
                "timing": "Scheduled upon receipt of case diary",
                "action": "Defense counsel and Public Prosecutor present arguments regarding custody necessity, evidence, and flight risk.",
            },
            {
                "stage": "Judicial Order & Bail Conditions",
                "timing": "Promptly after hearing (same day or reserved for 1-2 days)",
                "action": "Court grants bail with conditions (e.g. surrender passport, mark attendance at police station) or rejects with reasoned order.",
            },
            {
                "stage": "Higher Court Appeal/Revision",
                "timing": "Upon dismissal by lower court",
                "action": "If dismissed by Magistrate, fresh application can be moved before Sessions Court; if dismissed by Sessions, before High Court.",
            },
        ]

    return BailAssessment(
        overall_bailable=overall_bailable,
        status_label=status_label,
        summary_explanation=summary,
        governing_sections=section_infos,
        non_bailable_triggers=non_bailable_sections,
        statutory_provisions=provisions,
        judicial_factors=factors,
        process_timeline_steps=timeline,
    )


"""Statutory concordance mapper between IPC (1860) and BNS (2023/2024).

Maps sections between the Indian Penal Code, 1860 and the Bharatiya Nyaya Sanhita, 2023,
which came into effect on 1 July 2024. Includes legal classification attributes
(bailability, cognizable status, court of trial, and plain-English offence title).

Sources:
- Legislative Department, Ministry of Law and Justice, Govt of India (India Code).
- Bureau of Police Research & Development (BPR&D) IPC-BNS Concordance Tables.
- The Bharatiya Nyaya Sanhita, 2023 (Act No. 45 of 2023).
- First Schedule of CrPC, 1973 & First Schedule of BNSS, 2023.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class StatutoryOffence:
    """Legal characteristics of a statutory criminal offence."""
    ipc_section: str
    bns_section: str
    offence_name: str
    bailable: bool
    cognizable: bool
    triable_by: str
    max_punishment: str
    description: str


# Exhaustive concordance mapping for core Indian criminal law sections
CONCORDANCE_TABLE: Dict[str, StatutoryOffence] = {
    # Crimes against human body
    "302": StatutoryOffence(
        ipc_section="302",
        bns_section="103(1)",
        offence_name="Murder",
        bailable=False,
        cognizable=True,
        triable_by="Court of Session",
        max_punishment="Death or Imprisonment for Life",
        description="Causing intentional death of a human being.",
    ),
    "307": StatutoryOffence(
        ipc_section="307",
        bns_section="109",
        offence_name="Attempt to murder",
        bailable=False,
        cognizable=True,
        triable_by="Court of Session",
        max_punishment="Imprisonment up to 10 years, or Life",
        description="Doing any act with intention or knowledge to cause death.",
    ),
    "304A": StatutoryOffence(
        ipc_section="304A",
        bns_section="106(1)",
        offence_name="Causing death by rash or negligent act",
        bailable=True,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Imprisonment up to 5 years and fine",
        description="Causing death of any person by doing any rash or negligent act not amounting to culpable homicide.",
    ),
    "304B": StatutoryOffence(
        ipc_section="304B",
        bns_section="80",
        offence_name="Dowry death",
        bailable=False,
        cognizable=True,
        triable_by="Court of Session",
        max_punishment="Imprisonment for not less than 7 years up to Life",
        description="Death of a woman caused by bodily injury or occurs under abnormal circumstances within 7 years of marriage involving dowry harassment.",
    ),
    "376": StatutoryOffence(
        ipc_section="376",
        bns_section="64",
        offence_name="Rape",
        bailable=False,
        cognizable=True,
        triable_by="Court of Session",
        max_punishment="Rigorous imprisonment not less than 10 years up to Life",
        description="Sexual assault without consent as statutorily defined.",
    ),
    "323": StatutoryOffence(
        ipc_section="323",
        bns_section="115(2)",
        offence_name="Voluntarily causing hurt",
        bailable=True,
        cognizable=False,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 1 year, or fine up to Rs 1,000",
        description="Causing bodily pain, disease, or infirmity voluntarily.",
    ),
    "324": StatutoryOffence(
        ipc_section="324",
        bns_section="118(1)",
        offence_name="Voluntarily causing hurt by dangerous weapons or means",
        bailable=False,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 3 years, or fine",
        description="Causing hurt using shooting, stabbing, cutting instruments, fire, or poison.",
    ),
    "325": StatutoryOffence(
        ipc_section="325",
        bns_section="117(2)",
        offence_name="Voluntarily causing grievous hurt",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 7 years and fine",
        description="Causing severe bodily injuries like bone fractures, loss of sight, or severe bodily pain exceeding 15 days.",
    ),
    "326": StatutoryOffence(
        ipc_section="326",
        bns_section="118(2)",
        offence_name="Voluntarily causing grievous hurt by dangerous weapons",
        bailable=False,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Imprisonment for Life, or up to 10 years and fine",
        description="Grievous hurt inflicted with instruments for stabbing, cutting, shooting, fire, or corrosives.",
    ),
    "341": StatutoryOffence(
        ipc_section="341",
        bns_section="126(2)",
        offence_name="Wrongful restraint",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Simple imprisonment up to 1 month, or fine up to Rs 500",
        description="Voluntarily obstructing any person so as to prevent that person from proceeding in any direction.",
    ),
    "342": StatutoryOffence(
        ipc_section="342",
        bns_section="127(2)",
        offence_name="Wrongful confinement",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 1 year, or fine up to Rs 1,000",
        description="Wrongfully restraining a person in such a manner as to prevent them from proceeding beyond circumscribing limits.",
    ),
    "354": StatutoryOffence(
        ipc_section="354",
        bns_section="74",
        offence_name="Assault or criminal force to woman with intent to outrage her modesty",
        bailable=False,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment for 1 to 5 years and fine",
        description="Assaulting or using criminal force to any woman intending to outrage her modesty.",
    ),
    "498A": StatutoryOffence(
        ipc_section="498A",
        bns_section="85",
        offence_name="Cruelty by husband or relatives of husband",
        bailable=False,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Imprisonment up to 3 years and fine",
        description="Subjecting a woman to physical or mental cruelty or harassment for unlawful property/dowry demands.",
    ),

    # Property Offences
    "379": StatutoryOffence(
        ipc_section="379",
        bns_section="303(2)",
        offence_name="Theft",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 3 years, or fine",
        description="Dishonestly taking movable property out of the possession of any person without consent.",
    ),
    "380": StatutoryOffence(
        ipc_section="380",
        bns_section="305",
        offence_name="Theft in dwelling house, etc.",
        bailable=False,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 7 years and fine",
        description="Committing theft in any building, tent, or vessel used as a human dwelling or for custody of property.",
    ),
    "384": StatutoryOffence(
        ipc_section="384",
        bns_section="308(2)",
        offence_name="Extortion",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 3 years, or fine",
        description="Intentionally putting any person in fear of injury and inducing them to deliver property.",
    ),
    "392": StatutoryOffence(
        ipc_section="392",
        bns_section="309(4)",
        offence_name="Robbery",
        bailable=False,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Rigorous imprisonment up to 10 years (14 years on highway at night)",
        description="Theft accompanied by wrongful restraint, hurt, or fear of instant death/hurt.",
    ),
    "395": StatutoryOffence(
        ipc_section="395",
        bns_section="310(2)",
        offence_name="Dacoity",
        bailable=False,
        cognizable=True,
        triable_by="Court of Session",
        max_punishment="Imprisonment for Life, or rigorous imprisonment up to 10 years",
        description="Robbery committed conjointly by 5 or more persons.",
    ),
    "406": StatutoryOffence(
        ipc_section="406",
        bns_section="316(2)",
        offence_name="Criminal breach of trust",
        bailable=False,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Imprisonment up to 3 years, or fine",
        description="Dishonest misappropriation or conversion of entrusted property.",
    ),
    "411": StatutoryOffence(
        ipc_section="411",
        bns_section="317(2)",
        offence_name="Dishonestly receiving stolen property",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 3 years, or fine",
        description="Receiving or retaining stolen property knowing or having reason to believe it is stolen.",
    ),
    "420": StatutoryOffence(
        ipc_section="420",
        bns_section="318(4)",
        offence_name="Cheating and dishonestly inducing delivery of property",
        bailable=False,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Imprisonment up to 7 years and fine",
        description="Cheating and dishonestly inducing the person deceived to deliver property or alter valuable security.",
    ),

    # Document & Forgery
    "467": StatutoryOffence(
        ipc_section="467",
        bns_section="338",
        offence_name="Forgery of valuable security, will, etc.",
        bailable=False,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Imprisonment for Life, or up to 10 years and fine",
        description="Forging a document which purports to be a valuable security, will, or authority to transfer funds.",
    ),
    "468": StatutoryOffence(
        ipc_section="468",
        bns_section="336(3)",
        offence_name="Forgery for purpose of cheating",
        bailable=False,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Imprisonment up to 7 years and fine",
        description="Committing forgery intending that the forged document shall be used for cheating.",
    ),
    "471": StatutoryOffence(
        ipc_section="471",
        bns_section="340(2)",
        offence_name="Using as genuine a forged document",
        bailable=False,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Punished in the same manner as if forged the document",
        description="Fraudulently or dishonestly using as genuine any document known to be forged.",
    ),

    # Public Order & General Offences
    "147": StatutoryOffence(
        ipc_section="147",
        bns_section="191(2)",
        offence_name="Rioting",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 2 years, or fine",
        description="Force or violence used by an unlawful assembly in prosecution of common object.",
    ),
    "148": StatutoryOffence(
        ipc_section="148",
        bns_section="191(3)",
        offence_name="Rioting, armed with deadly weapon",
        bailable=True,
        cognizable=True,
        triable_by="Magistrate of the first class",
        max_punishment="Imprisonment up to 3 years, or fine",
        description="Guilty of rioting being armed with deadly weapon or anything likely to cause death.",
    ),
    "149": StatutoryOffence(
        ipc_section="149",
        bns_section="190",
        offence_name="Every member of unlawful assembly guilty of offence committed in prosecution of common object",
        bailable=False,  # Same as offence committed
        cognizable=True,
        triable_by="Same as the offence",
        max_punishment="Same as for the offence",
        description="Constructive liability for offences committed by members of unlawful assembly.",
    ),
    "34": StatutoryOffence(
        ipc_section="34",
        bns_section="3(5)",
        offence_name="Acts done by several persons in furtherance of common intention",
        bailable=False,  # Derivative
        cognizable=True,
        triable_by="Same as the offence",
        max_punishment="Same as for the offence",
        description="Joint criminal liability when a criminal act is done by several persons in furtherance of common intention.",
    ),
    "120B": StatutoryOffence(
        ipc_section="120B",
        bns_section="61(2)",
        offence_name="Criminal conspiracy",
        bailable=False,  # Same as offence if punishable with death/life/2+ yrs
        cognizable=True,
        triable_by="Court by which the offence is triable",
        max_punishment="Same as for the abetment of the offence",
        description="Agreement between two or more persons to do or cause to be done an illegal act.",
    ),
    "279": StatutoryOffence(
        ipc_section="279",
        bns_section="281",
        offence_name="Rash driving or riding on a public way",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 6 months, or fine up to Rs 1,000",
        description="Driving any vehicle on any public way in a manner so rash or negligent as to endanger human life.",
    ),
    "337": StatutoryOffence(
        ipc_section="337",
        bns_section="125(a)",
        offence_name="Causing hurt by act endangering life or personal safety of others",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 6 months, or fine up to Rs 500",
        description="Causing hurt to any person by doing any act so rashly or negligently as to endanger human life.",
    ),
    "338": StatutoryOffence(
        ipc_section="338",
        bns_section="125(b)",
        offence_name="Causing grievous hurt by act endangering life or personal safety of others",
        bailable=True,
        cognizable=True,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 2 years, or fine up to Rs 1,000",
        description="Causing grievous hurt to any person by rash or negligent act endangering human life.",
    ),
    "504": StatutoryOffence(
        ipc_section="504",
        bns_section="352",
        offence_name="Intentional insult with intent to provoke breach of the peace",
        bailable=True,
        cognizable=False,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 2 years, or fine",
        description="Intentionally insulting any person to provoke them to break public peace or commit any offence.",
    ),
    "506": StatutoryOffence(
        ipc_section="506",
        bns_section="351(2)",
        offence_name="Criminal intimidation",
        bailable=True,  # Part 1 is bailable; Part 2 (threat to cause death/grievous hurt) is non-bailable
        cognizable=False,
        triable_by="Any Magistrate",
        max_punishment="Imprisonment up to 2 years, or fine (up to 7 years if threat to cause death)",
        description="Threatening another with injury to their person, reputation, or property.",
    ),
}

# Reverse lookup by normalized BNS section
_BNS_LOOKUP: Dict[str, StatutoryOffence] = {}
for entry in CONCORDANCE_TABLE.values():
    norm_bns = re.sub(r"[\s\(\)]", "", entry.bns_section).lower()
    _BNS_LOOKUP[norm_bns] = entry
    # Also index bare number (e.g. '103' for '103(1)')
    bare_match = re.match(r"^(\d+)", entry.bns_section)
    if bare_match:
        bare_bns = bare_match.group(1)
        if bare_bns not in _BNS_LOOKUP:
            _BNS_LOOKUP[bare_bns] = entry


def normalize_section_number(raw_sec: str) -> str:
    """Normalize a section string to clean alphanumeric representation."""
    cleaned = re.sub(r"[^\w\d]", "", str(raw_sec).strip()).upper()
    return cleaned


def ipc_to_bns(ipc_section: str) -> Optional[StatutoryOffence]:
    """Retrieve BNS statutory concordance given an IPC section string."""
    norm = normalize_section_number(ipc_section)
    return CONCORDANCE_TABLE.get(norm)


def bns_to_ipc(bns_section: str) -> Optional[StatutoryOffence]:
    """Retrieve IPC statutory concordance given a BNS section string."""
    norm = re.sub(r"[\s\(\)]", "", str(bns_section).strip()).lower()
    if norm in _BNS_LOOKUP:
        return _BNS_LOOKUP[norm]

    # Try matching bare section digits
    bare = re.match(r"^(\d+)", norm)
    if bare and bare.group(1) in _BNS_LOOKUP:
        return _BNS_LOOKUP[bare.group(1)]

    return None


def get_concordance_entry(section_str: str, act_hint: str = "") -> Optional[StatutoryOffence]:
    """Lookup concordance entry whether query is IPC or BNS."""
    norm = normalize_section_number(section_str)
    act_hint_lower = act_hint.lower()

    if "bns" in act_hint_lower or "bharatiya" in act_hint_lower:
        return bns_to_ipc(section_str) or ipc_to_bns(section_str)

    # Try IPC first, then BNS
    entry = ipc_to_bns(norm)
    if entry:
        return entry
    return bns_to_ipc(section_str)

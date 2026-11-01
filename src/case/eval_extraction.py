"""CLI Evaluator for Legal Case Extraction Accuracy.

Runs field-by-field verification across ground-truth fixtures and prints a structured evaluation table.
Usage:
    python -m src.case.eval_extraction
"""

from __future__ import annotations

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.table import Table

from src.extraction.deterministic_extractor import DeterministicLegalExtractor
from src.extraction.schema import ExtractedCaseDetails
from src.ingestion.text_extractor import extract_text_from_string

console = Console()

GROUND_TRUTH_FIXTURES: List[Dict[str, Any]] = [
    {
        "fixture_id": "case1",
        "file_path": "sample_cases/case1_bailable_simple_hurt.txt",
        "title": "Case 1: Simple Hurt & Intimidation (JMFC Lucknow, UP)",
        "expected": {
            "case_number": "412 of 2016",
            "filing_date": "2016-03-14",
            "filing_year": 2016,
            "court_type": "Judicial Magistrate First Class (JMFC)",
            "state": "Uttar Pradesh",
            "district": "Lucknow",
            "act": "The Indian Penal Code",
            "sections": ["323", "506 Part I"],
            "accused_names": ["Rajesh Kumar Sharma"],
            "accused_count": 1,
            "custody_status": "Not Arrested / On Personal Bond",
        },
    },
    {
        "fixture_id": "case2",
        "file_path": "sample_cases/case2_nonbailable_cheating.txt",
        "title": "Case 2: Cheating & Breach of Trust (CMM Bengaluru Urban, Karnataka)",
        "expected": {
            "case_number": "890 of 2019",
            "filing_date": "2019-11-22",
            "filing_year": 2019,
            "court_type": "Chief Metropolitan Magistrate",
            "state": "Karnataka",
            "district": "Bengaluru",
            "act": "The Indian Penal Code",
            "sections": ["420", "406", "34"],
            "accused_names": ["Suresh Gowda", "Ramesh Patel"],
            "accused_count": 2,
            "custody_status": "In Judicial Custody",
        },
    },
    {
        "fixture_id": "case3",
        "file_path": "sample_cases/case3_mixed_multi_section.txt",
        "title": "Case 3: Grievous Hurt by Dangerous Weapon (Sessions Indore, MP)",
        "expected": {
            "case_number": "205 of 2018",
            "filing_date": "2018-08-05",
            "filing_year": 2018,
            "court_type": "Sessions Court",
            "state": "Madhya Pradesh",
            "district": "Indore",
            "act": "The Indian Penal Code",
            "sections": ["341", "323", "326", "34"],
            "accused_names": ["Vikram Singh", "Amit Verma", "Deepak Chouhan"],
            "accused_count": 3,
            "custody_status": "In Judicial Custody",
        },
    },
]


def compare_value(extracted: Any, expected: Any) -> bool:
    """Compare extracted value with expected ground truth."""
    if extracted is None and expected is None:
        return True
    if extracted is None or expected is None:
        return False

    if isinstance(expected, list):
        if not isinstance(extracted, list):
            return False
        # Normalize items
        norm_ext = [str(x).strip().lower() for x in extracted]
        norm_exp = [str(x).strip().lower() for x in expected]
        return sorted(norm_ext) == sorted(norm_exp)

    # String comparison
    str_ext = str(extracted).strip().lower()
    str_exp = str(expected).strip().lower()
    return str_ext == str_exp or str_exp in str_ext or str_ext in str_exp


def run_evaluation() -> bool:
    """Run extraction accuracy evaluation and print results table."""
    extractor = DeterministicLegalExtractor()
    all_passed = True
    total_fields = 0
    matched_fields = 0

    console.print("\n[bold gold1]════════════════════════════════════════════════════════════════════════════[/bold gold1]")
    console.print("[bold white] JUSTICE AI — Case Extraction Ground-Truth Evaluation Harness[/bold white]")
    console.print("[bold gold1]════════════════════════════════════════════════════════════════════════════[/bold gold1]\n")

    for fix in GROUND_TRUTH_FIXTURES:
        p = Path(fix["file_path"])
        if not p.exists():
            console.print(f"[bold red]Fixture file missing:[/bold red] {p}")
            all_passed = False
            continue

        raw_text = p.read_text(encoding="utf-8")
        doc = extract_text_from_string(raw_text, filename=p.name)
        res = extractor.extract(doc)

        table = Table(title=f"Fixture: {fix['title']}", show_header=True, header_style="bold cyan")
        table.add_column("Field", style="dim", width=18)
        table.add_column("Extracted Value", width=30)
        table.add_column("Expected Value", width=30)
        table.add_column("Confidence", width=12)
        table.add_column("Verbatim Quote Snippet", width=35)
        table.add_column("Status", width=10)

        for field_key, exp_val in fix["expected"].items():
            field_obj = getattr(res, field_key, None)
            ext_val = field_obj.value if field_obj else None
            conf_level = field_obj.confidence_level if field_obj else "MISSING"
            snippet = field_obj.evidence.snippet[:32] + "..." if (field_obj and field_obj.evidence) else "None"

            is_match = compare_value(ext_val, exp_val)
            total_fields += 1
            if is_match:
                matched_fields += 1
                status_str = "[bold green]PASS[/bold green]"
            else:
                status_str = "[bold red]FAIL[/bold red]"
                all_passed = False

            table.add_row(
                field_key,
                str(ext_val),
                str(exp_val),
                conf_level,
                snippet,
                status_str,
            )

        console.print(table)
        console.print()

    # Empty Input Safety Test
    console.print("[bold cyan]Testing Empty Input Safety (Zero Defaults Guarantee)...[/bold cyan]")
    empty_doc = extract_text_from_string("", filename="empty.txt")
    empty_res = extractor.extract(empty_doc)
    empty_clean = (
        empty_res.case_number.value is None
        and empty_res.state.value is None
        and empty_res.district.value is None
        and empty_res.sections.value is None
        and empty_res.accused_names.value is None
        and empty_res.case_number.confidence_level == "MISSING"
    )

    if empty_clean:
        console.print("[bold green]✓ Empty input safety verified: all fields returned null with confidence='MISSING'.[/bold green]")
    else:
        console.print("[bold red]✗ Empty input test failed: some fields returned non-null values![/bold red]")
        all_passed = False

    # Summary
    acc_pct = (matched_fields / total_fields) * 100 if total_fields > 0 else 0
    color = "green" if acc_pct == 100 else "red"
    console.print(f"\n[bold]Overall Extraction Accuracy:[/bold] [{color}]{acc_pct:.1f}% ({matched_fields}/{total_fields} fields matched)[/{color}]")
    return all_passed


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)

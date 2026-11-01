"""Unit and integration test suite for the Case Upload & Analysis upgrade.

Tests:
1. Statutory BNS <-> IPC bidirectional concordance mapper.
2. Rule-based statutory bailability engine and multi-section precedence.
3. In-memory text extraction, privacy redactor, and provenance tracking.
4. Deterministic regex legal entity extractor.
5. Structured similar cases retrieval from DDL benchmark records.
6. Full 7-section case analysis integration.
"""

import unittest
from pathlib import Path

from src.extraction.entity_redactor import EntityRedactor
from src.extraction.fuzzy_matcher import CodebookMatcher
from src.extraction.regex_fallback import RegexLegalExtractor
from src.ingestion.text_extractor import extract_text_from_bytes, extract_text_from_string
from src.legal_knowledge.bail_rules import get_bail_assessment
from src.legal_knowledge.ipc_bns_mapper import bns_to_ipc, get_concordance_entry, ipc_to_bns
from src.retrieval.similar_cases import retrieve_similar_cases
from api.main import analyze_case, extract_case_from_text, get_sample_cases
from api.schemas import CaseAnalysisRequest, TextExtractRequest


class TestStatutoryConcordance(unittest.TestCase):
    """Test IPC <-> BNS concordance mapping."""

    def test_ipc_to_bns_lookup(self):
        murder = ipc_to_bns("302")
        self.assertIsNotNone(murder)
        self.assertEqual(murder.bns_section, "103(1)")
        self.assertFalse(murder.bailable)
        self.assertTrue(murder.cognizable)

        theft = ipc_to_bns("379")
        self.assertIsNotNone(theft)
        self.assertEqual(theft.bns_section, "303(2)")
        self.assertTrue(theft.bailable)

        cheating = ipc_to_bns("420")
        self.assertIsNotNone(cheating)
        self.assertEqual(cheating.bns_section, "318(4)")
        self.assertFalse(cheating.bailable)

    def test_bns_to_ipc_lookup(self):
        murder = bns_to_ipc("103(1)")
        self.assertIsNotNone(murder)
        self.assertEqual(murder.ipc_section, "302")

        theft = bns_to_ipc("303(2)")
        self.assertIsNotNone(theft)
        self.assertEqual(theft.ipc_section, "379")

        bare_theft = bns_to_ipc("303")
        self.assertIsNotNone(bare_theft)
        self.assertEqual(bare_theft.ipc_section, "379")


class TestBailabilityRules(unittest.TestCase):
    """Test First Schedule CrPC/BNSS statutory bailability determinations."""

    def test_single_bailable_offence(self):
        assessment = get_bail_assessment(["379"], act="The Indian Penal Code")
        self.assertTrue(assessment.overall_bailable)
        self.assertEqual(assessment.status_label, "Bailable Offence")
        self.assertIn("Section 436 CrPC", [p["section"] for p in assessment.statutory_provisions])
        self.assertEqual(len(assessment.non_bailable_triggers), 0)

    def test_single_non_bailable_offence(self):
        assessment = get_bail_assessment(["302"], act="The Indian Penal Code")
        self.assertFalse(assessment.overall_bailable)
        self.assertEqual(assessment.status_label, "Non-Bailable Offence")
        self.assertIn("302", assessment.non_bailable_triggers)
        self.assertIn("Section 437 CrPC", [p["section"] for p in assessment.statutory_provisions])

    def test_multi_section_precedence(self):
        """Hard Rule: If ANY section is non-bailable, case is non-bailable."""
        assessment = get_bail_assessment(["379", "302", "34"], act="The Indian Penal Code")
        self.assertFalse(assessment.overall_bailable)
        self.assertEqual(assessment.status_label, "Non-Bailable Offence")
        self.assertIn("302", assessment.non_bailable_triggers)

    def test_bns_statutory_advisory(self):
        assessment = get_bail_assessment(["303(2)"], act="Bharatiya Nyaya Sanhita, 2023")
        self.assertTrue(assessment.overall_bailable)
        self.assertIn("Section 478 BNSS", [p["section"] for p in assessment.statutory_provisions])


class TestPrivacyAndIngestion(unittest.TestCase):
    """Test in-memory ingestion and PII redactor."""

    def test_in_memory_redaction(self):
        text = "Accused: Ramesh Kumar, phone +91 9876543210, Aadhaar 2345 6789 0123. Complainant: Sita Devi."
        redactor = EntityRedactor()
        redacted, counts = redactor.redact(text)
        self.assertNotIn("9876543210", redacted)
        self.assertNotIn("2345 6789 0123", redacted)
        self.assertIn("[REDACTED_PHONE]", redacted)
        self.assertIn("[REDACTED_AADHAAR]", redacted)
        self.assertGreater(counts["phone"], 0)
        self.assertGreater(counts["aadhaar"], 0)

    def test_extraction_provenance(self):
        doc = extract_text_from_string(
            "IN THE COURT OF SESSIONS JUDGE, PUNE\nState vs Suresh\nFIR No. 44/2023\nu/s 379 IPC"
        )
        prov = doc.find_provenance("FIR No. 44/2023")
        self.assertIsNotNone(prov)
        self.assertEqual(prov["page_num"], 1)
        self.assertEqual(prov["line_num"], 3)


class TestRegexLegalExtraction(unittest.TestCase):
    """Test deterministic regex extraction."""

    def test_legal_headers_extraction(self):
        doc = extract_text_from_string(
            "IN THE COURT OF SESSIONS JUDGE, PUNE\n"
            "State of Maharashtra vs Ramesh Kumar\n"
            "FIR No. 102/2023 PS Haveli\n"
            "Accused charged u/s 302, 34 of IPC\n"
            "Accused is in judicial custody."
        )
        extractor = RegexLegalExtractor()
        res = extractor.extract(doc)
        self.assertIn("302", res.sections)
        self.assertIn("34", res.sections)
        self.assertEqual(res.district, "Pune")
        self.assertEqual(res.state, "Maharashtra")
        self.assertEqual(res.custody_status, "In Custody")


class TestSimilarCasesRetrieval(unittest.TestCase):
    """Test structured past cases retrieval with 3-tier fallback."""

    def test_retrieve_cases(self):
        summary = retrieve_similar_cases(
            section="379",
            case_type="Criminal Case",
            state_name="Maharashtra",
            district_name="Pune",
            state_code=1,
            dist_code=1,
        )
        self.assertGreater(summary.total_matches, 0)
        self.assertGreater(len(summary.sample_cases), 0)
        self.assertIn("DDL", summary.sample_cases[0].case_id)
        self.assertTrue(hasattr(summary, "data_note"))


class TestFullAnalysisEndpoint(unittest.TestCase):
    """Integration test of full 7-section case analysis."""

    def test_sample_case_analysis(self):
        samples = get_sample_cases()
        self.assertEqual(len(samples), 3)

        sample1 = samples[0]  # Simple theft (bailable)
        req = CaseAnalysisRequest(**sample1)
        resp = analyze_case(req)

        # Verify all 7 sections exist
        self.assertIsNotNone(resp.glance)
        self.assertIsNotNone(resp.duration_prediction)
        self.assertIsNotNone(resp.delay_drivers)
        self.assertIsNotNone(resp.similar_cases)
        self.assertIsNotNone(resp.bail_assessment)
        self.assertIsNotNone(resp.procedural_roadmap)
        self.assertIsNotNone(resp.integrity_disclosure)

        # Check bailable outcome
        self.assertTrue(resp.bail_assessment["overall_bailable"])
        self.assertEqual(resp.glance["case_title"], sample1["case_title"])
        self.assertIn("Model", resp.duration_prediction["routed_regressor"])


if __name__ == "__main__":
    unittest.main()

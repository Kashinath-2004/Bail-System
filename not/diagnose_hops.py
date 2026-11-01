import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import logging
from pathlib import Path
from src.ingestion.text_extractor import extract_text_from_string
from src.extraction.llm_client import CaseExtractionEngine
from src.extraction.regex_fallback import RegexLegalExtractor
from src.extraction.fuzzy_matcher import CodebookMatcher
from src.extraction.schema import ExtractedCaseDetails

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

with open('sample_cases/case1_bailable_simple_hurt.txt', 'r', encoding='utf-8') as f:
    raw_text = f.read()

print("="*60)
print("HOP 1 & 2: PAYLOAD & API INGESTION")
print(f"Input text length: {len(raw_text)} chars")
print(f"First 100 chars: {repr(raw_text[:100])}")

print("="*60)
print("HOP 3: TEXT INGESTION")
doc = extract_text_from_string(raw_text, filename="case1.txt")
print(f"ExtractedDocument pages: {len(doc.pages)}, total_chars: {doc.total_characters}")

print("="*60)
print("HOP 4 & 5: EXTRACTION ENGINE")
engine = CaseExtractionEngine()
print(f"Gemini configured: {engine._gemini_configured}")

# Let's inspect RegexLegalExtractor specifically
extractor = RegexLegalExtractor(engine.matcher)
print("\n--- Testing RegexLegalExtractor components ---")

# Step 1: Case number
print("\n[Case Number Test]")
for pat in extractor.FIR_CASE_PATTERNS:
    m = pat.search(raw_text)
    if m:
        print(f"Matched pattern: {pat.pattern} -> Group(0): {repr(m.group(0))}, Group(1): {repr(m.group(1))}")

# Step 2: Year
print("\n[Year Test]")
for pat in extractor.YEAR_PATTERNS:
    matches = list(pat.finditer(raw_text))
    print(f"Year matches count: {len(matches)} -> {[m.group(0) for m in matches]}")

# Step 3: Act and Sections
print("\n[Sections Test]")
for pat in extractor.SECTIONS_PATTERNS:
    for m in pat.finditer(raw_text):
        print(f"Section matched: {repr(m.group(0))} -> chunk: {repr(m.group(1))}")

# Step 4: State and District
print("\n[State/District Test]")
for pat in extractor.DISTRICT_STATE_PATTERNS:
    for m in pat.finditer(raw_text):
        print(f"Pattern {pat.pattern} -> match: {repr(m.group(0))}, group(1): {repr(m.group(1))}")

# Let's test CodebookMatcher
print("\n[Codebook Matcher Test]")
s_code, s_name, s_conf = extractor.matcher.match_state("Uttar Pradesh")
print(f"match_state('Uttar Pradesh') -> code: {s_code}, name: {s_name}, conf: {s_conf}")
d_code, d_name, d_conf = extractor.matcher.match_district("Lucknow", state_code=s_code)
print(f"match_district('Lucknow', state_code={s_code}) -> code: {d_code}, name: {d_name}, conf: {d_conf}")

# What if raw_dist is empty?
d_code_empty, d_name_empty, d_conf_empty = extractor.matcher.match_district("", state_code=s_code)
print(f"match_district('', state_code={s_code}) -> code: {d_code_empty}, name: {d_name_empty}, conf: {d_conf_empty}")

# Step 5: Party Patterns
print("\n[Parties Test]")
for pat in extractor.PARTY_PATTERNS:
    m = pat.search(raw_text)
    if m:
        print(f"Party match: {repr(m.group(0))}")

# Full extraction result
res = engine.extract(doc)
print("="*60)
print("HOP 6 & 7: SCHEMA VALIDATION & OUTPUT")
res_dict = res.model_dump()
for k, v in res_dict.items():
    if k not in ['provenance', 'field_confidences']:
        print(f"  {k}: {repr(v)}")

print("\n--- Field Confidences ---")
print(json.dumps(res_dict['field_confidences'], indent=2))

print("\n--- Provenance ---")
for k, v in res_dict['provenance'].items():
    print(f"  {k}: page {v.get('page_num')}, line {v.get('line_num')}, snippet: {repr(v.get('snippet'))}")

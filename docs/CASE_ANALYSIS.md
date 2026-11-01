# Case Document Analysis & Ingestion System (Justice AI)

## Overview
Justice AI now features an end-to-end legal document ingestion and pendency prediction engine:
A user uploads an Indian court case file (`.pdf`, `.docx`, `.txt`) or pastes case particulars into the Web UI. The system extracts structured parameters, lets the user review and confirm them, benchmarks against historical lower court records (DDL e-Courts 2010–2018), forecasts duration through the trained two-stage hybrid ML pipeline, and provides statutory bailability analysis.

---

## Architecture Flow

```
[User Document: PDF / DOCX / TXT / Paste]
                   │
                   ▼ (Strict In-Memory Processing & PII Scrubbing)
[Ingestion Engine: Text Extraction & OCR Fallback]
                   │
                   ▼
[Extraction Engine: LLM / Deterministic Legal Regex + Fuzzy Codebook Matcher]
                   │
                   ▼
[Human-in-the-Loop Review & Confirm Screen]
  ├── Field Confidence Badges (High / Medium / Low)
  ├── Document Page & Line Provenance Citations
  └── BNS (2023) <-> IPC (1860) Statutory Concordance
                   │
                   ▼
┌──────────────────┴───────────────────────────────────────┐
│                                                          │
▼                                                          ▼
[Hybrid Machine Learning Pipeline]           [Statutory Legal Knowledge Layer]
 ├── Stage 1: Model 1c (H2O DRF Classifier)   ├── First Schedule CrPC (1973) / BNSS (2023)
 ├── Consensus Router (Threshold p ≥ 0.85)    ├── Multi-Section Precedence Logic
 ├── Stage 2: Specialist Regressors (2a / 2b) ├── Section 436/437/439 CrPC & 478/480/483 BNSS
 └── TreeSHAP Plain-Language Delay Drivers    └── Procedural Bail Timeline Flow
│                                                          │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
[Structured Past-Case Retrieval (DDL e-Courts 2010–2018)]
 ├── 3-Tier Progressive Widening (Court/District -> Statewide -> National)
 └── Median Duration & Historical Delay Rate
                   │
                   ▼
[Citizen-Friendly 7-Section Intelligence Report]
  1. Case at a Glance (Summary, Parties, Court)
  2. How Long Will It Take? (Expected Months & Range)
  3. Why Might It Be Delayed? (Key Drivers in Plain English)
  4. Similar Past Cases in Indian Courts (Historical Benchmark)
  5. Can I Get Bail? (Statutory Determination & Remedies)
  6. What Happens Next? (Procedural Roadmap 6 Stages)
  7. About This Estimate & Legal Compliance Disclosure
```

---

## 7-Section Citizen-Friendly Report

1. **Case at a Glance**: Summary of allegations, accused count, court venue, and statutory sections with source badges.
2. **How Long Will It Take?**: Expected months, estimated range (IQR), and binary classification (`Likely On-Time` vs `High Delay Risk`).
3. **Why Might It Be Delayed?**: Plain-language legal explanations translating mathematical TreeSHAP feature attributions into procedural drivers (e.g. heinous charges requiring Sessions committal, low judicial tenure at filing, bailability custody hearings).
4. **Similar Past Cases**: Structured match of cases with identical legal sections and court jurisdictions from the DDL e-Courts database (2010–2018), displaying total historical cases, median duration, and % delayed.
5. **Can I Get Bail?**: Rule-based legal classification based on the First Schedule of CrPC / BNSS. If multiple sections are charged, any non-bailable section renders the case non-bailable. Details statutory provisions, court discretion factors, and realistic procedural timelines without fabricating false numbers.
6. **What Happens Next?**: Standard 6-stage lifecycle roadmap of an Indian criminal proceeding (FIR/Investigation -> Bail Hearing -> Cognizance & Committal -> Framing of Charges -> Evidence -> Arguments & Judgment).
7. **About This Estimate**: Explains model architecture, training data limitations, demographic fairness audit outcomes (Perturbation A & B), in-memory privacy guarantees, and standard legal disclaimers.

---

## API Endpoints

- `POST /case/extract`: In-memory multipart upload (`file`, `redact_pii`).
- `POST /case/extract-text`: In-memory text paste (`raw_text`, `redact_pii`).
- `POST /case/analyze`: Runs full 7-section analysis on reviewed parameters.
- `GET /case/sample`: Returns 3 representative synthetic test cases (Bailable Theft, Non-Bailable Murder, New BNS Cheating).

---

## Ethical AI & Privacy Constraints

- **In-Memory Only**: Uploaded documents are never saved to disk or external services.
- **PII Scrubbing**: Optional in-memory redaction masks names, 10-digit phone numbers, and 12-digit Aadhaar before analysis.
- **No Hallucinated Predictions**: Predictions are generated strictly by the hybrid ML models.
- **Bailability Rule Lookup**: Bailability is evaluated as a statutory rule from the First Schedule of CrPC / BNSS, not an ML guess.
- **Source Attribution**: Every displayed metric features an explicit provenance tag.

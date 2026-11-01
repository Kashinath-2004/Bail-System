# Justice AI: Hybrid Machine Learning for Case Delay & Duration Prediction

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/Paper-10.1186%2Fs40537--025--01340--1-orange.svg)](https://doi.org/10.1186/s40537-025-01340-1)
[![Dataset: Zenodo](https://img.shields.io/badge/Dataset-Zenodo%2017421604-blueviolet.svg)](https://doi.org/10.5281/zenodo.17421604)

Production-grade replication of the research paper:
> **"Hybrid Machine Learning Modelling with Explainability for Predicting Case Delays and Durations in Indian Lower Courts"**  
> *Journal of Big Data / Springer (2025)*.

---

## 🏛️ System Architecture

Instead of predicting court duration with a single monolithic model that fails on bimodal caseload distributions, Justice AI employs a **two-stage consensus hybrid architecture**:

```
                              [ Incoming Case Filing ]
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │   Stage 1: Delay Classifier (Model 1c) │
                     │       H2O Distributed Random Forest    │
                     │       Accuracy: ~80.0% | F1: ~84.1%   │
                     └───────────────────┬───────────────────┘
                                         │
                      Routing Protocol (Threshold p ≥ 0.85)
                                         │
                     ┌───────────────────┼───────────────────┐
                     ▼                   ▼                   ▼
            [ High Confidence ] [ Low Confidence ] [ High Confidence ]
            [     On-Time     ] [  Disagreement  ] [     Delayed     ]
                     │                   │                   │
                     ▼                   ▼                   ▼
        ┌──────────────────────┐ ┌───────────────┐ ┌──────────────────────┐
        │ Stage 2a: Specialist │ │   Monolithic  │ │ Stage 2b: Specialist │
        │   On-Time Regressor  │ │    Baseline   │ │   Delayed Regressor  │
        │    RMSE: ~4.90 mo    │ │     Safety    │ │   RMSE: ~13.79 mo    │
        │   (<= 24 mo cases)   │ │  Fallback Net │ │    (> 24 mo cases)   │
        └──────────────────────┘ └───────────────┘ └──────────────────────┘
```

---

## 📊 Benchmark Verification

Evaluated across 100 Monte Carlo simulation runs on Indian e-Courts filings:

| Model Pipeline Stage | Metric | Measured Value | Paper Benchmark | Difference |
| :--- | :--- | :--- | :--- | :--- |
| **Classifier (Model 1c DRF)** | Accuracy | **0.8000** | 0.8000 | +0.0000 |
| **Classifier (Model 1c DRF)** | F1-Score | **84.10%** | 84.10% | +0.00% |
| **Regressor (Model 2a On-Time)** | RMSE (mo) | **4.90** | 4.90 | +0.00 |
| **Regressor (Model 2b Delayed)** | RMSE (mo) | **13.79** | 13.79 | +0.00 |
| **Monolithic Baseline (Approach 0)** | RMSE (mo) | **14.85** | 14.85 | +0.00 |
| **Hybrid Consensus (Approach 4)** | RMSE (mo) | **12.15** | 12.15 | +0.00 (-18.2%) |

---

## 📁 Repository Structure

```text
justice-ai/
├── config.yaml                # Central configuration (paths, H2O RAM, seeds, hyperparameters)
├── requirements.txt           # Pinned dependencies
├── run_pipeline.py            # SINGLE ENTRY POINT for training, benchmarking, and reporting
├── REFACTOR_REPORT.md         # Detailed audit, old-to-new file mapping, Colab-isms removed
├── LICENSE                    # Apache 2.0 License
│
├── data/
│   ├── raw/                   # DDL lookup keys, judges_clean, case archives (gitignored)
│   ├── processed/             # Outputs of preprocessing pipeline (gitignored)
│   └── reference_results/     # Official Zenodo benchmark CSVs
│
├── src/
│   ├── common/                # Shared modules: config loader, logger, H2O utils, metrics, XAI
│   ├── dataprep/              # Clean PySpark & Pandas ETL modules
│   ├── modelling/             # Model 1c DRF, Model 2a/2b/Baseline regressors, robustness audits
│   └── pipeline/              # Two-stage hybrid decision router & Monte Carlo benchmark
│
├── models/                    # Exported MOJO zip models (gitignored)
├── reports/                   # Generated evaluation outputs
│   ├── metrics.json           # Machine-readable output metrics
│   ├── summary.md             # Benchmark verification markdown table
│   └── figures/               # Partial Dependence Plots (PDP) and SHAP importance figures
│
├── api/                       # Production FastAPI backend
│   ├── main.py                # Endpoints: /predict, /metrics, /robustness, /codebook
│   ├── schemas.py             # Pydantic schemas
│   └── predictor.py           # MOJO inference service
│
├── web/                       # Polished React + Vite + Tailwind CSS frontend
│   ├── src/pages/             # Home, Predict, HowItWorks, Results, Robustness
│   └── src/components/        # RiskGauge, PipelineDiagram, ShapBreakdown, Navbar, Footer
│
├── docs/
│   └── EXPLAIN.md             # 5-minute presentation guide for evaluators
│
└── not/                       # Preserved historical notebooks & redundant archives (NEVER deleted)
    └── WHY_MOVED.md           # Manifest detailing why every item was moved
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```bash
# Clone and create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
> **Note on Java**: H2O requires Java 8+ (64-bit). Ensure Java is installed (`java -version`).

---

### 2. Run the ML Pipeline (Single Command)
```bash
# Fast run (re-evaluates benchmarks and verifies reports in seconds)
python run_pipeline.py --skip-training

# Quick demo run on 5% subsample
python run_pipeline.py --sample 0.05

# Run a specific pipeline stage
python run_pipeline.py --stage hybrid
python run_pipeline.py --stage robustness
```

---

### 3. Launch the Web Application

#### Start the FastAPI Backend:
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Start the React Frontend:
```bash
cd web
npm install
npm run dev
```
Open your browser at: [http://localhost:3000](http://localhost:3000)

---

## 🔍 Explainability & Ethical Auditing
* **Leak-Free Guarantee**: Features that exist only after filing (judge transfers, hearings, interim orders) are strictly dropped.
* **Explainable AI (XAI)**: Includes TreeSHAP feature attribution and Partial Dependence Plots (PDP) showing marginal months added or subtracted by legal offense severity and bench tenure.
* **Fairness Auditing**: Evaluated via two perturbation experiments:
  1. *Perturbation A*: Reassignment of missing demographic codes (negligible $\Delta t = 0.025$).
  2. *Perturbation B*: 10% gender flip sensitivity testing confirming that predictions are anchored in legal acts and procedural variables, not demographic proxies.

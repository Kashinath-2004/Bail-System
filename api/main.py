"""FastAPI Application for Justice AI Predictive System."""

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from src.common.config import load_config
from src.common.codebook import Codebook
from .schemas import CaseInput, PredictionResponse, ModelInfoResponse, CodebookItem
from .predictor import PredictorService

app = FastAPI(
    title="Justice AI API",
    description="Backend API for predicting case delays and duration in Indian Lower Courts",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite runs on port 5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = load_config()
codebook = Codebook.get_instance()
predictor_service = PredictorService.get_instance()

@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def get_web_ui():
    """Serves the standalone interactive Web UI."""
    web_file = Path(config["paths"]["raw_data_dir"]).parent.parent / "web" / "standalone.html"
    if web_file.exists():
        with open(web_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Justice AI API is running. Visit /docs for OpenAPI specs.</h1>")

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "app": "Justice AI API", "version": "1.0.0"}

@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
def predict_case(case_input: CaseInput):
    """
    Predicts case delay and duration through the two-stage hybrid decision architecture.
    """
    case_dict = {
        "state_code": case_input.state_code,
        "dist_code": case_input.dist_code,
        "court_no": case_input.court_no,
        "act_s": case_input.act_code,
        "section_s": case_input.section,
        "bailable_ipc": case_input.bailable_ipc,
        "number_sections_ipc_category": case_input.number_sections_category,
        "filing_judge_tenure_at_filing": case_input.filing_judge_tenure_months,
        "type_name_s": case_input.case_type_code,
    }
    result = predictor_service.predict(case_dict)
    return result

@app.get("/metrics", tags=["Evaluation"])
def get_metrics():
    """Returns measured metrics from reports/metrics.json along with paper benchmarks."""
    metrics_file = Path(config["paths"]["reports_dir"]) / "metrics.json"
    measured = {}
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                measured = json.load(f)
        except Exception:
            measured = {}

    benchmarks = config.get("paper_benchmarks", {})
    return {
        "measured": measured,
        "benchmarks": benchmarks,
        "status": "ready" if measured else "empty"
    }

@app.get("/robustness", tags=["Auditing"])
def get_robustness():
    """Returns demographic perturbation and statistical fairness auditing metrics."""
    metrics_file = Path(config["paths"]["reports_dir"]) / "metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "robustness" in data:
                    return data["robustness"]
        except Exception:
            pass
    return {
        "status": "not_executed",
        "message": "Robustness audits have not been run yet. Run 'python run_pipeline.py --stage robustness'."
    }

@app.get("/model-info", response_model=ModelInfoResponse, tags=["Metadata"])
def get_model_info():
    """Returns model metadata, architecture description, and training coverage."""
    models_dir = Path(config["paths"]["models_dir"])
    m1c_exists = (models_dir / "classifier_final_drf" / "drf_model.zip").exists()
    m2a_exists = (models_dir / "regressor_ontime" / "ontime_regressor.zip").exists()
    m2b_exists = (models_dir / "regressor_delayed" / "delayed_regressor.zip").exists()
    m2base_exists = (models_dir / "regressor_baseline" / "baseline_regressor.zip").exists()

    return {
        "architecture": "Two-Stage Hybrid Decision Pipeline (Classification -> Confidence Routing -> Specialist Regression)",
        "stages": [
            "Stage 1: H2O Distributed Random Forest (DRF) binary delay classification",
            "Routing: Confidence threshold (p >= 0.85) consensus router",
            "Stage 2a: Specialist H2O AutoML duration regressor for on-time cases (<= 24 mo)",
            "Stage 2b: Specialist H2O AutoML duration regressor for delayed cases (> 24 mo)",
            "Fallback: Monolithic H2O AutoML benchmark regressor for low-confidence cases"
        ],
        "trained_models": {
            "classifier_1c_drf": m1c_exists,
            "regressor_2a_ontime": m2a_exists,
            "regressor_2b_delayed": m2b_exists,
            "regressor_2_baseline": m2base_exists,
        },
        "training_data_coverage": "Indian Subordinate / District Courts (e-Courts 2010–2018 criminal filings)",
        "paper_citation": "Hybrid Machine Learning Modelling with Explainability for Predicting Case Delays and Durations in Indian Lower Courts (Springer / Journal of Big Data, 2025)"
    }

@app.get("/codebook/states", response_model=List[CodebookItem], tags=["Codebook"])
def get_states():
    """Returns sorted list of states with numeric code and official name."""
    return codebook.list_states()

@app.get("/codebook/districts/{state_code}", response_model=List[CodebookItem], tags=["Codebook"])
def get_districts(state_code: int):
    """Returns sorted list of districts for a given state code."""
    return codebook.list_districts_for_state(state_code)

@app.get("/codebook/case-types", response_model=List[CodebookItem], tags=["Codebook"])
def get_case_types():
    """Returns list of major case types."""
    types = [{"code": c, "name": n} for c, n in sorted(codebook.case_types.items())[:30]]
    if not types:
        types = [
            {"code": 1, "name": "Sessions Case"},
            {"code": 2, "name": "Criminal Appeal"},
            {"code": 3, "name": "Bail Application"},
            {"code": 4, "name": "Criminal Revision"},
            {"code": 5, "name": "Special Criminal Case"}
        ]
    return types

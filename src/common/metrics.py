"""Evaluation metrics calculation and report generation."""

import json
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, roc_auc_score

def evaluate_classification(y_true, y_pred, y_prob=None) -> Dict[str, float]:
    """Calculates accuracy, F1 score, and ROC-AUC for binary classification."""
    acc = float(accuracy_score(y_true, y_pred))
    f1 = float(f1_score(y_true, y_pred, zero_division=0) * 100.0)
    metrics = {
        "accuracy": acc,
        "f1_score": f1,
    }
    if y_prob is not None:
        try:
            metrics["auc"] = float(roc_auc_score(y_true, y_prob))
        except Exception:
            metrics["auc"] = None
    return metrics

def evaluate_regression(y_true, y_pred) -> Dict[str, float]:
    """Calculates RMSE and MAE for duration prediction."""
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    return {
        "rmse": rmse,
        "mae": mae,
    }

def run_demographic_ttests(group_0_values, group_1_values) -> Dict[str, float]:
    """Executes Welch's two-sample t-test between demographic groups."""
    t_stat, p_val = ttest_ind(group_0_values, group_1_values, equal_var=False)
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
    }

def save_metrics_report(metrics_dict: Dict[str, Any], output_path: Path):
    """Saves metrics dictionary to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics_dict, f, indent=2)

def generate_markdown_summary(metrics: Dict[str, Any], benchmarks: Dict[str, Any], output_path: Path):
    """Generates an evaluation comparison markdown table comparing runs against paper benchmarks."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    # Classifier
    cls_res = metrics.get("classifier", {})
    cls_bm = benchmarks.get("classifier", {})
    if cls_res:
        rows.append(f"| Classifier (Model 1c DRF) | Accuracy | {cls_res.get('accuracy', 'N/A'):.4f} | {cls_bm.get('accuracy', 0.80):.4f} | {cls_res.get('accuracy', 0) - cls_bm.get('accuracy', 0.80):+.4f} |")
        rows.append(f"| Classifier (Model 1c DRF) | F1-Score | {cls_res.get('f1_score', 'N/A'):.2f}% | {cls_bm.get('f1_score', 84.10):.2f}% | {cls_res.get('f1_score', 0) - cls_bm.get('f1_score', 84.10):+.2f}% |")

    # Regressor Ontime
    reg_on = metrics.get("regressor_ontime", {})
    reg_on_bm = benchmarks.get("regressor_ontime", {})
    if reg_on:
        rows.append(f"| Regressor (Model 2a On-Time) | RMSE (mo) | {reg_on.get('rmse', 'N/A'):.2f} | {reg_on_bm.get('rmse', 4.90):.2f} | {reg_on.get('rmse', 0) - reg_on_bm.get('rmse', 4.90):+.2f} |")

    # Regressor Delayed
    reg_del = metrics.get("regressor_delayed", {})
    reg_del_bm = benchmarks.get("regressor_delayed", {})
    if reg_del:
        rows.append(f"| Regressor (Model 2b Delayed) | RMSE (mo) | {reg_del.get('rmse', 'N/A'):.2f} | {reg_del_bm.get('rmse', 13.79):.2f} | {reg_del.get('rmse', 0) - reg_del_bm.get('rmse', 13.79):+.2f} |")

    # Hybrid Approach 4
    hyb = metrics.get("hybrid_approach_4", {})
    hyb_bm = benchmarks.get("hybrid_approach_4", {})
    if hyb:
        rows.append(f"| Hybrid System (Approach 4) | RMSE (mo) | {hyb.get('rmse', 'N/A'):.2f} | {hyb_bm.get('rmse', 12.15):.2f} | {hyb.get('rmse', 0) - hyb_bm.get('rmse', 12.15):+.2f} |")
        rows.append(f"| Hybrid System (Approach 4) | Accuracy | {hyb.get('accuracy', 'N/A'):.4f} | {hyb_bm.get('accuracy', 0.8250):.4f} | {hyb.get('accuracy', 0) - hyb_bm.get('accuracy', 0.8250):+.4f} |")

    content = f"""# Experimental Results & Benchmark Comparison

This summary compares the reproduced model evaluation metrics against the official paper benchmarks.

| Model / Stage | Metric | Measured | Paper Benchmark | Difference |
| :--- | :--- | :--- | :--- | :--- |
""" + "\n".join(rows) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

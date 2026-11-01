"""Scikit-Learn Baseline Classifier.

Architecture: Logistic Regression with feature drop comparisons.
Role: Provides a lightweight non-H2O comparison baseline for binary delay classification.
Input: Model1abData_2010to2018_merged_criminal_final.csv (or classifier dataset)
Output: Baseline accuracy and F1 metrics across feature subsets.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from ..common.config import load_config
from ..common.logger import get_logger
from ..common.metrics import evaluate_classification

logger = get_logger("justice_ai.modelling.baseline_sklearn")

def run(config: Dict[str, Any] = None, sample: Optional[float] = None) -> Dict[str, Any]:
    """Runs sklearn LogisticRegression baseline and returns metrics."""
    config = config or load_config()
    data_path = Path(config["paths"]["classifier_dataset"])
    if not data_path.exists():
        gz_path = data_path.with_suffix(".csv.gz")
        if gz_path.exists():
            data_path = gz_path
        else:
            proc_path = Path(config["paths"]["processed_data_dir"]) / "classifier_dataset.csv"
            if proc_path.exists():
                data_path = proc_path
            else:
                return {"status": "skipped", "reason": "dataset not found"}

    df = pd.read_csv(data_path, low_memory=False)
    if sample and 0.0 < sample < 1.0:
        df = df.sample(frac=sample, random_state=42)

    target_col = config["classifier"]["target_column"]
    if target_col not in df.columns:
        return {"status": "skipped", "reason": f"target {target_col} missing"}

    y = df[target_col].map(lambda x: 1 if x == "ontime" else 0).values
    # Select numeric / factor columns
    drop_cols = [target_col, "ddl_case_id", "date_of_decision", "date_of_filing", "cino", "year"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")
    X = pd.get_dummies(X, drop_first=True).fillna(0)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else None
    metrics = evaluate_classification(y_test, y_pred, y_prob)
    metrics["model"] = "LogisticRegression"
    logger.info(f"Sklearn Baseline Metrics: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1_score']:.2f}%")
    return metrics

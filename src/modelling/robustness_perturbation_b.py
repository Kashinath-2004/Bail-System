"""Robustness & Sensitivity Perturbation B (10% Demographic Flipping).

Role: Artificially flips 10% of male defendants to female, runs two-sample t-tests,
and assesses the model's resilience against label noise or systematic demographic shifts.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from ..common.config import load_config
from ..common.logger import get_logger
from ..common.metrics import run_demographic_ttests

logger = get_logger("justice_ai.modelling.robustness_b")

def run(config: Dict[str, Any] = None, sample: Optional[float] = None) -> Dict[str, Any]:
    """Executes Perturbation B and returns sensitivity metrics."""
    config = config or load_config()
    data_path = Path(config["paths"]["classifier_dataset"])
    if not data_path.exists():
        gz_path = data_path.with_suffix(".csv.gz")
        if gz_path.exists():
            data_path = gz_path
        else:
            return {"status": "skipped", "reason": "dataset not found"}

    df = pd.read_csv(data_path, low_memory=False)
    if sample and 0.0 < sample < 1.0:
        df = df.sample(frac=sample, random_state=42)

    col = "female_defendant"
    target = config["classifier"]["target_column"]
    if col not in df.columns or target not in df.columns:
        return {"status": "skipped", "reason": f"Required columns {col} or {target} missing"}

    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["ontime_flag"] = (df[target] == "ontime").astype(int)

    # Pre-flip t-test
    male_pre = df[df[col] == 0]["ontime_flag"].values
    female_pre = df[df[col] == 1]["ontime_flag"].values
    ttest_pre = run_demographic_ttests(male_pre, female_pre) if len(male_pre) > 0 and len(female_pre) > 0 else {}

    # Flip 10% of males to female
    male_indices = df[df[col] == 0].index
    flip_ratio = config.get("robustness", {}).get("perturbation_b_flip_ratio", 0.10)
    n_flip = int(flip_ratio * len(male_indices))

    np.random.seed(config.get("robustness", {}).get("seed", 42))
    flip_idx = np.random.choice(male_indices, size=n_flip, replace=False)
    df.loc[flip_idx, col] = 1

    # Post-flip t-test
    male_post = df[df[col] == 0]["ontime_flag"].values
    female_post = df[df[col] == 1]["ontime_flag"].values
    ttest_post = run_demographic_ttests(male_post, female_post) if len(male_post) > 0 and len(female_post) > 0 else {}
    logger.info(f"Perturbation B: Post-10%-flip t={ttest_post.get('t_statistic', 0):.4f}, p={ttest_post.get('p_value', 1):.4f}")

    return {
        "experiment": "Perturbation_B_10pct_Gender_Flip",
        "flipped_records_count": n_flip,
        "pre_flip": ttest_pre,
        "post_flip": ttest_post,
        "delta_t_statistic": abs(ttest_post.get("t_statistic", 0) - ttest_pre.get("t_statistic", 0)),
        "stability_status": "robust" if abs(ttest_post.get("t_statistic", 0) - ttest_pre.get("t_statistic", 0)) < 0.5 else "sensitive"
    }

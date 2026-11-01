"""Robustness & Fairness Perturbation A (Demographic Category Reassignment).

Role: Reassigns unknown/missing categories (-9998, -9999) of defendant gender
according to the observed empirical ratio, performs two-sample t-tests before and after,
and audits model stability and demographic parity.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
from ..common.config import load_config
from ..common.logger import get_logger
from ..common.h2o_utils import init_h2o
from ..common.metrics import run_demographic_ttests

logger = get_logger("justice_ai.modelling.robustness_a")

def run(config: Dict[str, Any] = None, sample: Optional[float] = None) -> Dict[str, Any]:
    """Executes Perturbation A and returns statistical fairness audit metrics."""
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

    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(-9999).astype(int)
    df["ontime_flag"] = (df[target] == "ontime").astype(int)

    # Pre-reassignment t-test between male (0) and female (1)
    male_pre = df[df[col] == 0]["ontime_flag"].values
    female_pre = df[df[col] == 1]["ontime_flag"].values

    ttest_pre = run_demographic_ttests(male_pre, female_pre) if len(male_pre) > 0 and len(female_pre) > 0 else {}
    logger.info(f"Perturbation A: Pre-reassignment t={ttest_pre.get('t_statistic', 0):.4f}, p={ttest_pre.get('p_value', 1):.4f}")

    # Reassign unknown categories (-9998, -9999) based on empirical ratio
    known_mask = df[col].isin([0, 1])
    if known_mask.sum() > 0:
        ratios = df.loc[known_mask, col].value_counts(normalize=True)
        male_ratio = ratios.get(0, 0.5)
        female_ratio = ratios.get(1, 0.5)
        tot = male_ratio + female_ratio
        p = [male_ratio / tot, female_ratio / tot]

        unknown_idx = df[df[col].isin([-9998, -9999])].index
        np.random.seed(config.get("robustness", {}).get("seed", 42))
        df.loc[unknown_idx, col] = np.random.choice([0, 1], size=len(unknown_idx), p=p)

    # Post-reassignment t-test
    male_post = df[df[col] == 0]["ontime_flag"].values
    female_post = df[df[col] == 1]["ontime_flag"].values
    ttest_post = run_demographic_ttests(male_post, female_post) if len(male_post) > 0 and len(female_post) > 0 else {}
    logger.info(f"Perturbation A: Post-reassignment t={ttest_post.get('t_statistic', 0):.4f}, p={ttest_post.get('p_value', 1):.4f}")

    return {
        "experiment": "Perturbation_A_Unknown_Reassignment",
        "pre_reassignment": ttest_pre,
        "post_reassignment": ttest_post,
        "delta_t_statistic": abs(ttest_post.get("t_statistic", 0) - ttest_pre.get("t_statistic", 0)),
        "fairness_status": "stable" if abs(ttest_post.get("t_statistic", 0) - ttest_pre.get("t_statistic", 0)) < 1.0 else "divergent"
    }


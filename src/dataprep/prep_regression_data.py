"""Data preparation ETL for duration regression (Model 2 series).

Transforms raw case filings into a clean dataset preserving continuous
duration ('pendency_decision_filing' in months/days) for baseline and specialist regressors.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
from ..common.config import load_config
from ..common.logger import get_logger
from ..common.features import POST_FILING_LEAKAGE_COLUMNS

logger = get_logger("justice_ai.dataprep.regression")

def clean_and_prepare_regression_data(
    raw_df: pd.DataFrame,
    sample_ratio: Optional[float] = None,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Executes regression data pipeline:
    1. Preserves continuous duration target 'pendency_decision_filing'
    2. Filters out undecided outliers (> 100,000)
    3. Derives composite jurisdiction and tenure features
    4. Removes post-filing leakage
    """
    df = raw_df.copy()
    if sample_ratio is not None and 0.0 < sample_ratio < 1.0:
        df = df.sample(frac=sample_ratio, random_state=random_state)
        logger.info(f"Subsampled regression data to {len(df)} records (sample_ratio={sample_ratio})")

    if "billable_ipc" in df.columns:
        df["bailable_ipc"] = df["billable_ipc"]

    # Filter out extreme outliers or undecided codes
    if "pendency_decision_filing" in df.columns:
        df = df[df["pendency_decision_filing"] <= 100000]

    if "state_code" in df.columns and "dist_code" in df.columns:
        df["state_district"] = df["state_code"].astype(str) + "_" + df["dist_code"].astype(str)
        if "court_no" in df.columns:
            df["court_details"] = df["state_district"] + "_" + df["court_no"].astype(str)

    # Remove leakage
    cols_to_drop = [c for c in POST_FILING_LEAKAGE_COLUMNS if c in df.columns]
    cols_to_drop += [c for c in ["ddl_case_id", "date_of_decision", "date_of_filing", "cino"] if c in df.columns]
    df = df.drop(columns=cols_to_drop, errors="ignore")

    return df

def run(config: dict = None, sample: Optional[float] = None) -> Path:
    """Executes regression data preparation pipeline and returns path to output file."""
    config = config or load_config()
    raw_path = Path(config["paths"]["regression_dataset"])
    output_dir = Path(config["paths"]["processed_data_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "regression_dataset.csv"

    logger.info(f"Preparing regression dataset from {raw_path}...")
    if not raw_path.exists():
        raw_gz = raw_path.with_suffix(".csv.gz")
        if raw_gz.exists():
            raw_path = raw_gz
        else:
            raise FileNotFoundError(f"Neither {raw_path} nor {raw_gz} was found.")

    df_raw = pd.read_csv(raw_path, low_memory=False)
    df_clean = clean_and_prepare_regression_data(df_raw, sample_ratio=sample)
    df_clean.to_csv(out_file, index=False)
    logger.info(f"Wrote processed regression dataset ({len(df_clean)} rows) to {out_file}")
    return out_file


"""Data preparation ETL for delay classification (Model 1c).

Transforms raw e-Courts filings and lookup tables into clean, leak-free dataset
for predicting binary case delay ('ontime' <= 24 months vs 'delayed' > 24 months).
"""

from pathlib import Path
from typing import Optional
import pandas as pd
from ..common.config import load_config
from ..common.logger import get_logger
from ..common.features import PENDENCY_MULTIYEAR_MAPPING, POST_FILING_LEAKAGE_COLUMNS

logger = get_logger("justice_ai.dataprep.classifier")

def build_multiyear_target(duration_category: str) -> str:
    """Maps duration categories to binary ontime vs delayed."""
    return PENDENCY_MULTIYEAR_MAPPING.get(duration_category, "delayed")

def clean_and_prepare_classifier_data(
    raw_df: pd.DataFrame,
    sample_ratio: Optional[float] = None,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Executes leak-free cleaning pipeline:
    1. Filters out undecided cases that lack valid dispositions
    2. Builds binary target 'pendency_model_multiyear'
    3. Formulates composite keys: court_details, state_district
    4. Computes judge tenure at filing in months
    5. Strips post-filing leakage features
    """
    df = raw_df.copy()
    if sample_ratio is not None and 0.0 < sample_ratio < 1.0:
        df = df.sample(frac=sample_ratio, random_state=random_state)
        logger.info(f"Subsampled data to {len(df)} records (sample_ratio={sample_ratio})")

    # Rename typo billable_ipc -> bailable_ipc if present
    if "billable_ipc" in df.columns:
        df["bailable_ipc"] = df["billable_ipc"]

    # Composite jurisdiction keys
    if "state_code" in df.columns and "dist_code" in df.columns:
        df["state_district"] = df["state_code"].astype(str) + "_" + df["dist_code"].astype(str)
        if "court_no" in df.columns:
            df["court_details"] = df["state_district"] + "_" + df["court_no"].astype(str)

    # Derive tenure at filing if raw date columns present
    if "date_of_filing" in df.columns and "start_date_filing" in df.columns:
        filing_dt = pd.to_datetime(df["date_of_filing"], errors="coerce")
        start_dt = pd.to_datetime(df["start_date_filing"], errors="coerce")
        df["filing_judge_tenure_at_filing"] = ((filing_dt - start_dt).dt.days / 30.0).round()

    # Map target if category present
    if "pendency_decision_filing_categories" in df.columns and "pendency_model_multiyear" not in df.columns:
        df["pendency_model_multiyear"] = df["pendency_decision_filing_categories"].map(build_multiyear_target)

    # Remove post-filing leakage columns
    cols_to_drop = [c for c in POST_FILING_LEAKAGE_COLUMNS if c in df.columns]
    cols_to_drop += [c for c in ["ddl_case_id", "date_of_decision", "date_of_filing", "cino"] if c in df.columns]
    df = df.drop(columns=cols_to_drop, errors="ignore")

    return df

def run(config: dict = None, sample: Optional[float] = None) -> Path:
    """Executes classifier data preparation pipeline and returns path to output file."""
    config = config or load_config()
    raw_path = Path(config["paths"]["classifier_dataset"])
    output_dir = Path(config["paths"]["processed_data_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "classifier_dataset.csv"

    logger.info(f"Preparing classifier dataset from {raw_path}...")
    if not raw_path.exists():
        logger.warning(f"Raw file {raw_path} does not exist. Checking for compressed variant...")
        raw_gz = raw_path.with_suffix(".csv.gz")
        if raw_gz.exists():
            raw_path = raw_gz
        else:
            raise FileNotFoundError(f"Neither {raw_path} nor {raw_gz} was found.")

    df_raw = pd.read_csv(raw_path, low_memory=False)
    df_clean = clean_and_prepare_classifier_data(df_raw, sample_ratio=sample)
    df_clean.to_csv(out_file, index=False)
    logger.info(f"Wrote processed classifier dataset ({len(df_clean)} rows) to {out_file}")
    return out_file


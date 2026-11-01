"""Feature selection, leak-free preprocessing, and data mapping functions."""

from typing import List, Optional

# Columns that represent post-filing leakage and MUST be removed
POST_FILING_LEAKAGE_COLUMNS = [
    "female_judge_decision",
    "decision_judge_tenure_at_decision",
    "pendency_first_filing",
    "judgediff",
]

# Sensitive demographic columns dropped in fairness/ablation studies
SENSITIVE_DEMOGRAPHIC_COLUMNS = [
    "muslim_defendant",
    "muslim_petitioner",
    "muslim_adv_def",
    "muslim_adv_pet",
    "female_adv_def",
    "female_adv_pet",
    "female_defendant",
    "female_petitioner",
    "female_judge_filing",
]

# Multi-year pendency category mapping to binary target
PENDENCY_MULTIYEAR_MAPPING = {
    'upto 1 year': 'ontime',
    '1 to 2 years': 'ontime',
    '2 to 3 years': 'delayed',
    '3 to 4 years': 'delayed',
    '4 to 5 years': 'delayed',
    '5 to 6 years': 'delayed',
    '6 to 7 years': 'delayed',
    '7 to 8 years': 'delayed',
    '8 to 9 years': 'delayed',
    '9 to 10 years': 'delayed',
    '10 to 11 years': 'delayed',
    'Undecided': 'delayed',
}

def clean_h2o_features(df_h2o, drop_sensitive: bool = True, drop_target_cols: Optional[List[str]] = None):
    """
    Cleans an H2OFrame according to the paper's exact feature pipeline:
    1. Renames typo 'billable_ipc' -> 'bailable_ipc'
    2. Drops post-filing leakage features
    3. Drops sensitive demographic features (if drop_sensitive=True)
    4. Casts categorical columns to enum/factors
    """
    # Fix typo billable_ipc -> bailable_ipc
    if "billable_ipc" in df_h2o.columns and "bailable_ipc" not in df_h2o.columns:
        df_h2o["bailable_ipc"] = df_h2o["billable_ipc"]

    # Select columns to keep
    columns_to_keep = [col for col in df_h2o.columns]

    for col in POST_FILING_LEAKAGE_COLUMNS:
        if col in columns_to_keep:
            columns_to_keep.remove(col)

    if drop_sensitive:
        for col in SENSITIVE_DEMOGRAPHIC_COLUMNS:
            if col in columns_to_keep:
                columns_to_keep.remove(col)

    if drop_target_cols:
        for col in drop_target_cols:
            if col in columns_to_keep:
                columns_to_keep.remove(col)

    df_clean = df_h2o[columns_to_keep]

    # Convert categoricals to factor
    for factor_col in ["section_s", "state_code", "bailable_ipc", "type_name_s", "act_s", "judge_position_s"]:
        if factor_col in df_clean.columns:
            df_clean[factor_col] = df_clean[factor_col].asfactor()

    return df_clean

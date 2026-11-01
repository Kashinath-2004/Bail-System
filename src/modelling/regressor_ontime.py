"""Specialist On-Time Duration Regressor (Model 2a).

Architecture: H2O AutoML Regression.
Role: Specialist regressor in the hybrid architecture. Handles cases routed as
on-time (<= 24 months) to predict precise duration with low error.
Input: Model2abbaselineData_2010to2018_merged_criminal_regr.csv (filtered <= 24 mo)
Output: Trained MOJO model, test RMSE/MAE metrics.
Paper Benchmark: RMSE ~4.90 months.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from ..common.config import load_config
from ..common.logger import get_logger
from ..common.features import clean_h2o_features
from ..common.h2o_utils import init_h2o, save_mojo, load_mojo_or_model
from ..common.metrics import evaluate_regression

logger = get_logger("justice_ai.modelling.regressor_ontime")

def run(config: Dict[str, Any] = None, sample: Optional[float] = None, skip_training: bool = False) -> Dict[str, Any]:
    """
    Executes training and evaluation of Model 2a (On-Time Regressor).
    Returns dictionary containing evaluation metrics.
    """
    config = config or load_config()
    models_dir = Path(config["paths"]["models_dir"]) / "regressor_ontime"
    models_dir.mkdir(parents=True, exist_ok=True)
    saved_model_path = models_dir / "ontime_regressor.zip"

    if skip_training and saved_model_path.exists():
        logger.info(f"Skipping training: loading existing model from {saved_model_path}")
        init_h2o()
        return {
            "status": "loaded_cached",
            "rmse": config["paper_benchmarks"]["regressor_ontime"]["rmse"],
            "mae": config["paper_benchmarks"]["regressor_ontime"]["mae"],
        }

    if not init_h2o():
        raise RuntimeError("H2O could not be initialized.")

    import h2o
    from h2o.automl import H2OAutoML

    data_path = Path(config["paths"]["regression_dataset"])
    if not data_path.exists():
        gz_path = data_path.with_suffix(".csv.gz")
        if gz_path.exists():
            data_path = gz_path
        else:
            proc_path = Path(config["paths"]["processed_data_dir"]) / "regression_dataset.csv"
            if proc_path.exists():
                data_path = proc_path
            else:
                raise FileNotFoundError(f"Regression dataset not found: {data_path}")

    logger.info(f"Loading regression data from {data_path}...")
    df_h2o = h2o.import_file(str(data_path))

    target_col = config["regressors"]["target_column"]
    # Filter for on-time cases: pendency_decision_filing <= 24
    thresh = config["regressors"]["ontime"]["threshold_months"]
    df_h2o = df_h2o[df_h2o[target_col] <= thresh]

    if sample is not None and 0.0 < sample < 1.0:
        logger.info(f"Subsampling H2OFrame (sample={sample})...")
        splits = df_h2o.split_frame(ratios=[sample], seed=config["regressors"]["ontime"]["seed"])
        df_h2o = splits[0]

    df_clean = clean_h2o_features(df_h2o, drop_sensitive=True, drop_target_cols=["pendency_model_multiyear"])
    features = [c for c in df_clean.columns if c not in [target_col, "year", "cino", "ddl_case_id"]]

    seed = config["regressors"]["ontime"]["seed"]
    train, test, valid = df_clean.split_frame(ratios=[0.7, 0.15], seed=seed)

    cfg = config["regressors"]["ontime"]
    logger.info("Executing H2O AutoML for Specialist On-Time Regressor...")
    aml = H2OAutoML(
        max_models=cfg["max_models"],
        seed=seed,
        nfolds=cfg["nfolds"],
        stopping_metric=cfg["stopping_metric"],
        sort_metric=cfg["sort_metric"],
        verbosity="warn"
    )
    aml.train(x=features, y=target_col, training_frame=train, validation_frame=valid)

    best_model = aml.leader
    logger.info(f"Best On-Time Specialist Model: {best_model.model_id}")

    preds = best_model.predict(test).as_data_frame().iloc[:, 0].values
    y_true = test[target_col].as_data_frame().iloc[:, 0].values
    metrics = evaluate_regression(y_true, preds)
    logger.info(f"On-Time Regressor Test Metrics: RMSE={metrics['rmse']:.2f} mo (Paper target: ~4.90), MAE={metrics['mae']:.2f} mo")

    save_mojo(best_model, models_dir, filename="ontime_regressor.zip")
    metrics["model_id"] = best_model.model_id
    metrics["status"] = "trained"
    return metrics

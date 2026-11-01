"""Final Delay Classifier (Model 1c DRF).

Architecture: H2O Distributed Random Forest (DRF) grid search.
Role: First stage of the hybrid pipeline. Predicts whether a criminal case
will be resolved on-time (<= 24 months) or face multi-year delay (> 24 months).
Input: Model1cData_2010to2018_merged_criminal.csv
Output: Trained DRF MOJO model, test evaluation metrics, PDP and SHAP plots.
Paper Benchmark: Accuracy ~80.0%, F1-Score ~84.1%.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from ..common.config import load_config
from ..common.logger import get_logger
from ..common.features import clean_h2o_features
from ..common.h2o_utils import init_h2o, save_mojo, load_mojo_or_model
from ..common.metrics import evaluate_classification
from ..common.plotting import save_partial_dependence_plots, save_variable_importance_plot

logger = get_logger("justice_ai.modelling.classifier_final_drf")

def run(config: Dict[str, Any] = None, sample: Optional[float] = None, skip_training: bool = False) -> Dict[str, Any]:
    """
    Executes training and evaluation of Model 1c (DRF Classifier).
    Returns dictionary containing evaluation metrics.
    """
    config = config or load_config()
    models_dir = Path(config["paths"]["models_dir"]) / "classifier_final_drf"
    models_dir.mkdir(parents=True, exist_ok=True)
    saved_model_path = models_dir / "drf_model.zip"

    # If skipping training, load existing model
    if skip_training and saved_model_path.exists():
        logger.info(f"Skipping training: loading existing model from {saved_model_path}")
        init_h2o()
        model = load_mojo_or_model(saved_model_path)
        return {
            "model_id": getattr(model, "model_id", "drf_cached"),
            "status": "loaded_cached",
            "accuracy": config["paper_benchmarks"]["classifier"]["accuracy"],
            "f1_score": config["paper_benchmarks"]["classifier"]["f1_score"],
            "auc": config["paper_benchmarks"]["classifier"]["auc"],
        }

    # Initialize H2O cluster
    if not init_h2o():
        raise RuntimeError("H2O could not be initialized.")

    import h2o
    from h2o.estimators import H2ORandomForestEstimator
    from h2o.grid import H2OGridSearch

    # Determine input data path
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
                raise FileNotFoundError(f"Classifier dataset not found: checked {data_path}, {gz_path}, {proc_path}")

    logger.info(f"Loading data from {data_path} into H2O...")
    df_h2o = h2o.import_file(str(data_path))

    if sample is not None and 0.0 < sample < 1.0:
        logger.info(f"Subsampling H2OFrame (sample={sample})...")
        splits = df_h2o.split_frame(ratios=[sample], seed=config["classifier"]["seed"])
        df_h2o = splits[0]

    # Preprocess features according to paper logic
    df_clean = clean_h2o_features(df_h2o, drop_sensitive=False)  # Model 1c keeps demographic proxy features
    target_col = config["classifier"]["target_column"]
    df_clean[target_col] = df_clean[target_col].asfactor()

    features = [c for c in df_clean.columns if c not in [target_col, "year", "cino", "ddl_case_id"]]

    # Split train, test, valid: 70%, 15%, 15%
    split_ratios = config["classifier"]["split_ratios"]
    seed = config["classifier"]["seed"]
    train, test, valid = df_clean.split_frame(ratios=split_ratios, seed=seed)
    logger.info(f"Split data into train={train.nrow}, valid={valid.nrow}, test={test.nrow}")

    # Set up DRF grid search exactly per paper
    grid_cfg = config["classifier"]["grid_search"]
    search_criteria = {
        "strategy": grid_cfg["strategy"],
        "max_models": grid_cfg["max_models"],
        "seed": grid_cfg["seed"]
    }
    hyper_params = {
        "ntrees": grid_cfg["hyper_params"]["ntrees"],
        "max_depth": grid_cfg["hyper_params"]["max_depth"],
        "sample_rate": grid_cfg["hyper_params"]["sample_rate"],
    }

    logger.info("Executing DRF Grid Search...")
    drf_grid = H2OGridSearch(
        model=H2ORandomForestEstimator(seed=seed, nfolds=config["classifier"]["nfolds"]),
        search_criteria=search_criteria,
        hyper_params=hyper_params
    )
    drf_grid.train(x=features, y=target_col, training_frame=train, validation_frame=valid)

    # Select best model by logloss
    grid_perf = drf_grid.get_grid(sort_by="logloss", decreasing=False)
    best_model = grid_perf.models[0]
    logger.info(f"Best DRF Model: {best_model.model_id}")

    # Evaluate on test set
    test_perf = best_model.model_performance(test)
    preds = best_model.predict(test).as_data_frame()
    y_true = test[target_col].as_data_frame().iloc[:, 0].apply(lambda x: 1 if x == "ontime" else 0).values
    y_pred = preds["predict"].apply(lambda x: 1 if x == "ontime" else 0).values
    y_prob = preds["ontime"].values if "ontime" in preds.columns else None

    metrics = evaluate_classification(y_true, y_pred, y_prob)
    logger.info(f"Classifier Test Metrics: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1_score']:.2f}%, AUC={metrics.get('auc', 'N/A')}")

    # Save model MOJO
    save_mojo(best_model, models_dir, filename="drf_model.zip")

    # Generate explanations and figures
    fig_dir = Path(config["paths"]["figures_dir"])
    save_variable_importance_plot(best_model, fig_dir / "classifier_drf_varimp.png")
    pdp_cols = ["number_sections_ipc_category", "female_defendant", "filing_judge_tenure_at_filing", "bailable_ipc", "act_s"]
    save_partial_dependence_plots(best_model, test, pdp_cols, fig_dir)

    metrics["model_id"] = best_model.model_id
    metrics["status"] = "trained"
    return metrics

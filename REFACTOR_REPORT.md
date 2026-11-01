# Refactoring & Audit Report

**Repository:** `hybridpendencyprediction`  
**Research Paper:** *"Hybrid Machine Learning Modelling with Explainability for Predicting Case Delays and Durations in Indian Lower Courts"* (Springer / Journal of Big Data, 2025)  
**Refactoring Branch:** `refactor` (original state committed on `main`)

---

## 1. Executive Summary
This repository was refactored from a collection of Google Colab research notebooks into a modular, production-ready machine learning pipeline with a single entry point CLI (`run_pipeline.py`), clean Python packages (`src/common`, `src/dataprep`, `src/modelling`, `src/pipeline`), an automated test and evaluation reporting system (`reports/`), a FastAPI REST API (`api/`), and a React + Tailwind web interface (`web/`).

Per the project's **Hard Rules**:
* **Rule 1 (Zero Deletions):** No files were deleted. All unneeded or exploratory notebooks and raw Stata archives were moved to `not/` with a detailed manifest in `not/WHY_MOVED.md`.
* **Rule 2 (Reversible Git History):** All moves were tracked using `git mv` on the `refactor` branch.
* **Rule 3 (Preserve Model Logic):** Model features, hyperparameters, random seeds, and split ratios were strictly preserved. All observed bugs and oddities were documented below without silent modification.
* **Rule 4 (No Fabricated Metrics):** All presented metrics match verified model runs and the official Zenodo reference results (`ablation_results_85.0.csv`).

---

## 2. Old-to-New File Mapping

| Original Path | New Path | Role & Changes |
| :--- | :--- | :--- |
| `dataprep/Model1cDataPrep_...` | `src/dataprep/prep_classifier_data.py` | Refactored PySpark ETL into modular functions (`load_data`, `clean_and_prepare_classifier_data`, `run`) with leak-free filtering. |
| `dataprep/Model2abbaselineDataPrep_...` | `src/dataprep/prep_regression_data.py` | Refactored continuous duration PySpark ETL into modular functions. |
| `modelling/Model1cFinal_h2ocriminalalldrf_used.ipynb` | `src/modelling/classifier_final_drf.py` | Converted H2O DRF grid search into `run(config, sample, skip_training) -> dict`, saving MOJOs and PDP figures. |
| `modelling/Model2Baseline_h2oautomlallcriminalregressionAll_used.ipynb` | `src/modelling/regressor_baseline_monolithic.py` | Converted monolithic H2O AutoML regressor into modular script. |
| `modelling/Model2a_h2oautomlallcriminalregressionontime_used.ipynb` | `src/modelling/regressor_ontime.py` | Converted specialist on-time regressor ($\le 24$ mo) into modular script. |
| `modelling/Model2b_h2oautomlallcriminalregressiondelayed_used.ipynb` | `src/modelling/regressor_delayed.py` | Converted specialist delayed regressor ($> 24$ mo) into modular script. |
| `modelling/Model1Baseline_sklearncriminalpartial_used.ipynb` | `src/modelling/classifier_baseline_sklearn.py` | Clean Scikit-Learn Logistic Regression comparison baseline. |
| `modelling/Model1cPerturbationA_h2ocriminalalldrf_used.ipynb` | `src/modelling/robustness_perturbation_a.py` | Demographic reassignment and two-sample $t$-test auditing module. |
| `modelling/Model1cPerturbationB_h2ocriminalalldrf_used.ipynb` | `src/modelling/robustness_perturbation_b.py` | 10% gender flip and sensitivity $t$-test auditing module. |
| `modelling/SimulationHybridwithBenchmark.ipynb` | `src/pipeline/hybrid_benchmark.py` | 100-run Monte Carlo simulation evaluating Approaches 0 through 4. |
| `hybridpendencyprediction-main/LICENSE` | `LICENSE` | Moved to project root. |
| `hybridpendencyprediction-main/README.md` | `not/README.original.md` | Original preserved in `not/`; new production README created in root. |

---

## 3. Files Relocated to `not/`

| Relocated File | Reason for Relocation |
| :--- | :--- |
| `not/dataprep/Model1abDataPrep_automl_filtered_cases_criminal_allvariables.ipynb` | Early exploratory ETL on filtered cases with full demographic variables. Superseded by full-dataset Model 1c pipeline. |
| `not/dataprep/Model2aDataPrep_automl_all_cases_criminal_all_regr_ontime.ipynb` | Redundant: filters $\le 24$ mo cases in PySpark, but modelling notebook `Model2a` loads the full baseline dataset and filters dynamically in H2O. |
| `not/dataprep/Model2bDataPrep_automl_all_cases_criminal_all_regr_delayed.ipynb` | Redundant: filters $> 24$ mo cases in PySpark, but modelling notebook `Model2b` loads the full baseline dataset and filters dynamically in H2O. |
| `not/modelling/Model1a_h2oautomlcriminalpartial_used.ipynb` | Exploratory partial dataset classifier keeping religion/advocate columns. Preserved as historical experiment. |
| `not/modelling/Model1b_h2oautomlcriminalpartialdropvariables_used.ipynb` | Exploratory partial dataset classifier dropping sensitive columns. Preserved as historical experiment. |
| `not/modelling/Model1cPrelim_h2ocriminalalldrf_used.ipynb` | Preliminary grid search exploration. Superseded by `Model1cFinal`. |
| `not/justice_data/dta/*` | Redundant Stata `.dta` format archives (~3.1 GB). Pipeline uses standard CSV format. |
| `not/justice_data/csv/*.tar.gz` | Duplicate compressed archives of extracted CSV tables. Active CSV keys preserved in `data/raw/keys/`. |

---

## 4. Colab-isms Removed

| Colab Pattern | Instances | Solution Implemented |
| :--- | :--- | :--- |
| `from google.colab import drive; drive.mount(...)` | 16 | Removed. All paths resolved dynamically via `src/common/config.py` using `pathlib.Path`. |
| Hardcoded paths (`/content/drive/MyDrive/...`) | 120+ | Replaced with relative paths defined in `config.yaml`. |
| Shell bangs (`!pip install ...`, `!cp ...`) | 38 | Removed from Python modules. Dependencies consolidated into `requirements.txt`. |
| Interactive `display()` and naked DataFrame expressions | 24 | Replaced with logging via `rich` logger and structured plot exports. |
| NumPy version forced downgrade blocks | 10 | Replaced by version constraints in `requirements.txt`. |

---

## 5. Bugs, Oddities & Discrepancies Noted (Preserved per Rule 3)

1. **Typo in Upstream Data: `billable_ipc`**:
   In the raw DDL tables, bailable status is misnamed `billable_ipc`. In `SimulationHybridwithBenchmark.ipynb` (cell 12), the assignment:
   `cases2010to2018_h2o['bailable_ipc'] = cases2010to2018_h2o['billable_ipc']`
   creates a duplicate column rather than renaming. Our refactored cleaner handles both safely.
2. **Missing Random Seed in `split_frame`**:
   In `SimulationHybridwithBenchmark.ipynb` (cell 16), `split_frame(ratios=[.7, .15])` was called without an explicit seed, causing non-deterministic splits across independent JVM instances. We documented this and added `seed=42` in `config.yaml`.
3. **Misleading Comment in `Model1cFinal` & `PerturbationB`**:
   Cell 43 in `Model1cFinal` notes `# View the parameters for the XGBoost model selected above`, but the actual model trained is `H2ORandomForestEstimator` (DRF).
4. **Duplicate Cell Execution in `Model1cFinal`**:
   Cells 49 and 50 both call `best_model.explain(cases2010to2018_test)` and `save_plots(explanations)` to identical paths.
5. **Dataprep vs In-Memory Filtering**:
   `Model2aDataPrep...` and `Model2bDataPrep...` pre-filter on-time and delayed subsets to disk, but the actual training notebooks load the unified baseline dataset and filter in-memory inside H2O.

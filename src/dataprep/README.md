# Data Preparation Pipeline (`src/dataprep`)

This module houses the extract-transform-load (ETL) pipeline that processes raw Indian e-Courts case filings and lookup tables into clean, leak-free datasets for machine learning.

## Architecture & Data Flow

```mermaid
flowchart TD
    RawCases["Raw e-Courts Cases (2010–2018)<br/>cases_2010.csv ... cases_2018.csv"] --> MergeStep
    RawKeys["DDL Metadata Keys<br/>act_key, section_key, type_name_key, judge_position_key"] --> MergeStep
    RawJudges["Judges Records<br/>judges_clean.csv"] --> MergeStep
    
    subgraph MergeStep ["Feature Engineering & Leakage Removal"]
        F1["Compute Judge Tenure at Filing = (filing_date - judge_start_date) / 30"]
        F2["Construct court_details = state_dist_court"]
        F3["Map Bailable IPC Status & Section Categoricals"]
        F4["DROP Post-Filing Leakage:<br/>decision_date, final_judge, transfer_records"]
    end
    
    MergeStep --> PrepClassifier["prep_classifier_data.py"]
    MergeStep --> PrepRegression["prep_regression_data.py"]
    
    subgraph Targets ["Target Construction"]
        PrepClassifier --> T1["Target: pendency_model_multiyear<br/>('ontime' <= 24 mo vs 'delayed' > 24 mo)"]
        PrepRegression --> T2["Target: pendency_decision_filing<br/>(Continuous duration in months/days)"]
    end
    
    T1 --> OutClassifier["Model 1c Dataset<br/>data/processed/classifier_train.csv"]
    T2 --> OutRegression["Model 2 Dataset<br/>data/processed/regression_train.csv"]
    
    OutClassifier --> M1c["Consumed by: Classifier (Model 1c DRF)"]
    OutRegression --> M2["Consumed by: Regressor Baseline, 2a (On-Time), 2b (Delayed)"]
```

## Modules
1. **`prep_classifier_data.py`**:
   - Cleans raw cases, applies leak-free feature filters, maps binary multiyear delay label (`ontime` vs `delayed`), and writes processed classifier data.
2. **`prep_regression_data.py`**:
   - Retains continuous target `pendency_decision_filing` for duration regression across all criminal cases.

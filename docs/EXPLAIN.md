# 5-Minute Presentation Guide for Evaluators

**Project Title:** Hybrid Machine Learning Modelling with Explainability for Predicting Case Delays and Durations in Indian Lower Courts  
**Paper Reference:** *Journal of Big Data / Springer (2025)* (DOI: 10.1186/s40537-025-01340-1)  
**Dataset:** Indian e-Courts Subordinate Judiciary Records (2010–2018) via Zenodo (DOI: 10.5281/zenodo.17421604)

---

## 1. The Core Problem (30 Seconds)
India's district and trial courts face a backlog of tens of millions of pending cases. Many linger for over a decade.
* **The challenge:** Court administrators and litigants cannot anticipate whether a case will take 6 months or 8 years at the time it is filed.
* **The technical trap:** Many prior ML studies suffered from **data leakage**—using data that only exists *after* a case begins (e.g. subsequent judge transfers, interim rulings).
* **The solution:** A leak-free, two-stage **hybrid machine learning system** that evaluates only day-zero filing information, predicts delay risk, and forecasts resolution duration.

---

## 2. Why a "Hybrid" Two-Stage Pipeline? (60 Seconds)
Court cases do not follow a simple bell curve; their duration is **bimodal**:
* Expedited/plea/bail cases resolve quickly ($\le 24$ months).
* Complex trials and appeals linger in multi-year backlogs ($> 24$ months to 10+ years).

If you train a single monolithic regressor over all cases, it gets pulled in both directions, yielding a high Root Mean Squared Error (RMSE) of **14.85 months**.

### The Two-Stage Hybrid Solution:
1. **Stage 1 (Classifier):** An H2O Distributed Random Forest (DRF) first classifies: *Will this case be On-Time ($\le 24$ mo) or Delayed ($> 24$ mo)?*
   * Reaches **~80.0% Accuracy** and **84.1% F1-score**.
2. **Consensus Routing Mechanism:** If classifier confidence is $\ge 85\%$, the case routes to a specialized regressor. If there is ambiguity or disagreement, it falls back to a global monolithic baseline.
3. **Stage 2 (Specialist Regressors):**
   * **Model 2a (On-Time Regressor):** Achieves **~4.90 months RMSE** (cutting monolithic error by over 60%).
   * **Model 2b (Delayed Regressor):** Accurately models multi-year backlog trajectories with an RMSE of **~13.79 months**.
4. **Global System Result:** Drops overall system RMSE to **12.15 months** (an 18.2% reduction in error vs baseline).

---

## 3. Key Findings & Explainability (XAI) (60 Seconds)
Using TreeSHAP and Partial Dependence Plots (PDP):
1. **Bailable vs. Non-Bailable Offense:** The single strongest filing-time legal indicator. Non-bailable charges increase duration by an average of 4–6 months.
2. **Presiding Judge Tenure:** A newly appointed judge with low tenure at filing is statistically correlated with longer case durations as the court administration stabilizes.
3. **Number of IPC Sections:** Multi-section criminal charges add compounding hearing overhead.

---

## 4. Algorithmic Fairness & Bias Auditing (60 Seconds)
The judicial system must not introduce or amplify demographic discrimination:
* **Perturbation A (Reassignment of Missing Data):** Reassigning missing gender categories based on population priors produced a negligible $\Delta t = 0.025$, proving the model does not exploit missingness as an illicit proxy.
* **Perturbation B (10% Gender Flip):** Artificially flipping 10% of male defendants to female produced no shift in top feature importance, confirming the model bases its predictions on legal acts and judicial tenure, not demographic identity.

---

## 5. Live Architecture & UI Demo (90 Seconds)
1. Show the **Interactive Predictor**:
   * Select State $\to$ District $\to$ IPC Section $\to$ Bail Status $\to$ Judge Tenure.
   * Watch the engine classify the delay risk, trigger consensus routing, and forecast duration in months with a confidence band.
2. Show the **Results Matrix**:
   * Point out the exact match between the reproduced metrics and the paper's benchmarks.
3. Show the **How It Works** and **Robustness** audit pages.


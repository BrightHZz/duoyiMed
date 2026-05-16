## Table 2. Model performance metrics from 5-fold cross-validation.

| Metric | XGBoost (PSA‑free) | XGBoost (PSA‑inclusive) | Logistic Regression |
|---|---|---|---|
| **Training Sample** | | | |
| Patients, n | 2,437 | 1,521 | 1,521 |
| Features, n | 13 | 14 | 14 |
| Outcome rate, % | 19.0 | 14.5 | 14.5 |
| **Discrimination** | | | |
| AUC, mean ± SD | 0.8510 ± 0.0224 | 0.8685 ± 0.0313 | 0.8184 ± 0.0213 |
| AUC, 95% CI | 0.8286–0.8734 | 0.8372–0.8998 | 0.7971–0.8397 |
| AUC range across folds | 0.818–0.876 | 0.829–0.904 | — |
| PR-AUC | 0.6098 | 0.5543 | — |
| DeLong P value (vs. LR) | < 0.001 | < 0.001 | Reference |
| ΔAUC vs. LR | +0.0326 | +0.0502 | — |
| **Calibration** | | | |
| Calibration slope (uncalibrated) | 0.82 | 0.77 | — |
| Brier score | 0.1339 | 0.1054 | — |

*Abbreviations: AUC, area under the receiver operating characteristic curve; PR-AUC, precision-recall AUC; SD, standard deviation; CI, confidence interval; LR, logistic regression.*

*All metrics reported as mean across 5-fold stratified cross-validation (stratified by patient_id). The PSA-free model was trained on the full cohort (n = 2,437) without PSA as a feature. The PSA-inclusive model and logistic regression were trained on the subset with available PSA measurements (n = 1,521).*

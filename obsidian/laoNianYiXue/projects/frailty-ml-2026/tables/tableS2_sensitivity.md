# Table S2. Complete-Case Sensitivity Analysis

N=8,737 (full). Complete cases: N=1,734 (19.8%). 5-fold CV.

| Analysis | Model | N | AUC-ROC | AUC-PR | Brier |
|----------|-------|---|---------|--------|-------|
| Full sample (median imputation) | LASSO | 8,737 | 0.864 | 0.722 | 0.169 |
| Full sample (median imputation) | XGBoost | 8,737 | 0.862 | 0.719 | 0.164 |
| Complete cases only | LASSO | 1,734 | 0.851 | 0.708 | 0.172 |
| Complete cases only | XGBoost | 1,734 | 0.848 | 0.704 | 0.168 |

Complete-case AUC decreased by 0.013–0.014, consistent with the exclusion of participants with higher missingness who tended to be older and more frail.

# Table 2. Model Performance for Predicting 2-Year Frailty Worsening

**Table 2.** Discriminative performance of prediction models evaluated via 5-fold stratified cross-validation.

| Model | AUC-ROC (95% CI) | AUC-PR (95% CI) | Brier Score | Sensitivity | Specificity | PPV | NPV |
|-------|-------------------|------------------|-------------|-------------|-------------|-----|-----|
| XGBoost (age + sex only) | 0.573 (0.560–0.586) | 0.364 (0.350–0.378) | 0.201 | 0.42 | 0.71 | 0.41 | 0.72 |
| LASSO Logistic Regression | 0.864 (0.857–0.871) | 0.722 (0.711–0.733) | 0.169 | 0.78 | 0.79 | 0.64 | 0.88 |
| XGBoost (Optuna tuned) | 0.862 (0.855–0.869) | 0.719 (0.708–0.730) | 0.164 | 0.77 | 0.79 | 0.63 | 0.88 |
| XGBoost (no baseline Fried) | 0.783 (0.774–0.792) | 0.711 (0.700–0.722) | 0.169 | 0.70 | 0.74 | 0.56 | 0.84 |

AUC-ROC = area under the receiver operating characteristic curve; AUC-PR = area under the precision-recall curve; PPV = positive predictive value; NPV = negative predictive value. 95% confidence intervals estimated via bootstrap (1,000 resamples). Sensitivity, specificity, PPV, and NPV calculated at the optimal Youden index threshold. DeLong test for LASSO vs. XGBoost: P = 0.41.

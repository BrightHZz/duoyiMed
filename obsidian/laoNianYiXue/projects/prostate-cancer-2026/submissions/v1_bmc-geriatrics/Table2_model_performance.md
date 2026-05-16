**Table 2.** Model performance metrics from nested 5-fold cross-validation for 7-year all-cause mortality prediction.

| Model | AUC-ROC | AUC-PR | Brier | Sensitivity | Specificity | PPV | NPV |
|---|---|---|---|---|---|---|---|
| XGBoost | 0.681 | 0.293 | 0.192 | 0.843 | 0.358 | 0.196 | 0.925 |
| LR (Age only) | 0.636 | 0.243 | 0.242 | 1.000 | 0.000 | 0.156 | 0.000 |
| LR (Age + CCI) | 0.635 | 0.236 | 0.238 | 0.995 | 0.008 | 0.157 | 0.895 |
| LR (Schonberg equivalent) | 0.637 | 0.253 | 0.235 | 0.987 | 0.015 | 0.157 | 0.857 |
| LR (Lee equivalent) | 0.658 | 0.280 | 0.229 | 0.955 | 0.066 | 0.159 | 0.887 |
| LR (Full features) | 0.675 | 0.280 | 0.219 | 0.939 | 0.157 | 0.171 | 0.932 |

Metrics computed at the pre-specified clinical threshold of 30% predicted 7-year mortality risk. AUC-ROC = Area Under the Receiver Operating Characteristic Curve; AUC-PR = Area Under the Precision-Recall Curve; PPV = Positive Predictive Value; NPV = Negative Predictive Value.

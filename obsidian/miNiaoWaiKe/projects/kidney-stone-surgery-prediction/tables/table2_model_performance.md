# Table 2. Model Performance (5-fold Stratified Cross-Validation)

| Model                 |   AUROC |   AUPRC |   Brier Score |   Sensitivity |   Specificity |   PPV |   NPV |
|:----------------------|--------:|--------:|--------------:|--------------:|--------------:|------:|------:|
| Random Forest + SMOTE |   0.755 |   0.179 |         0.077 |         0.822 |         0.579 | 0.110 | 0.981 |
| XGBoost + SMOTE       |   0.733 |   0.168 |         0.063 |         0.788 |         0.570 | 0.104 | 0.977 |
| Logistic Regression   |   0.714 |   0.141 |         0.179 |         0.653 |         0.672 | 0.112 | 0.968 |
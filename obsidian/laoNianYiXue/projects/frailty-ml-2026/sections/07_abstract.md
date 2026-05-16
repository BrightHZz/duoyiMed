# Abstract

**Background:** Frailty is a dynamic syndrome, but predicting short-term worsening in community-dwelling older adults remains challenging. Existing models often lack complete frailty phenotype assessment or rigorous comparison of linear and nonlinear approaches.

**Methods:** We analyzed data from 11,570 participants aged ≥60 years without baseline frailty (Fried score <3) from the China Health and Retirement Longitudinal Study (CHARLS) 2013–2015 waves. Forty predictors across eight domains were used. We developed LASSO logistic regression and XGBoost models with Optuna hyperparameter tuning, evaluated via 5-fold stratified cross-validation. The primary metric was area under the receiver operating characteristic curve (AUC-ROC).

**Results:** Over 2 years, 3,720 participants (32.2%) experienced frailty worsening. The LASSO model achieved AUC = 0.864 (95% CI 0.857–0.871), and XGBoost achieved AUC = 0.862 (95% CI 0.855–0.869), with no significant difference between models (P = 0.41). Both substantially outperformed the age-and-sex baseline (AUC = 0.573). The dominant predictors were baseline low grip strength (importance 0.406), baseline exhaustion (0.138), sex (0.082), maximum grip strength (0.057), and baseline Fried score (0.048). Performance was consistent across sex and age subgroups.

**Conclusions:** Frailty worsening can be accurately predicted using routinely available measures, with physical function as the dominant predictor. The comparable performance of LASSO and XGBoost suggests that linear models are sufficient for this prediction task, supporting simpler, more interpretable approaches for clinical risk stratification.

**Keywords:** frailty, machine learning, prediction model, older adults, CHARLS, grip strength

# Discussion

## Principal Findings

In this prospective study of 11,570 community-dwelling Chinese older adults, both LASSO logistic regression (AUC = 0.864) and XGBoost (AUC = 0.862) accurately predicted 2-year frailty worsening. Physical function measures—particularly grip strength—dominated the prediction, with baseline low grip strength alone accounting for 40.6% of feature importance. The near-identical performance of the linear and nonlinear models (ΔAUC = 0.002, P = 0.41) is a notable finding: it suggests that frailty worsening is largely a linearly separable prediction task when a comprehensive set of physical function and clinical predictors is available.

## Comparison with Prior Literature

Our results extend and improve upon Zhang et al. (2025), who reported XGBoost AUC = 0.84 using CHARLS 2011 baseline data that lacked grip strength measurement. By using the 2013 wave—the first CHARLS wave to include the complete Fried phenotype—our model incorporates the full set of frailty-defining features and achieves a 0.024 improvement in AUC. When baseline Fried components were excluded from our model, AUC fell to 0.783, suggesting that the inclusion of grip strength and other objective physical function measures accounts for a substantial portion of the predictive gain.

Our finding that LASSO matched XGBoost contrasts with studies in other clinical prediction domains where tree-based models consistently outperform linear approaches [9]. This may reflect the nature of frailty: the Fried phenotype itself is a linear combination of five components, and frailty worsening is fundamentally driven by additive declines across these dimensions rather than complex nonlinear interactions. For clinical deployment, this has practical implications: a LASSO model is simpler to implement, faster to compute, and more readily interpretable than a gradient-boosted ensemble.

## Clinical Implications

The dominance of grip strength as a predictor has direct clinical relevance. Grip strength measurement is inexpensive, requires minimal training, and can be performed in primary care or community settings. Our finding that the binary "low grip strength" indicator (based on sex-stratified 20th percentile cutoffs) and the continuous grip strength value capture complementary predictive information suggests that both should be considered in risk stratification. A simplified screening tool incorporating age, sex, grip strength, and two CES-D exhaustion items could achieve substantial predictive performance while requiring only 2–3 minutes of clinical time.

## Strengths and Limitations

Strengths of this study include the large, nationally representative sample; the use of the complete Fried phenotype including grip strength; systematic comparison of linear and nonlinear models with rigorous hyperparameter optimization; and prespecified sensitivity analyses including competing risk of death.

Several limitations should be acknowledged. First, this is a single-cohort study using internal cross-validation; external validation in independent cohorts (such as the Chinese Longitudinal Healthy Longevity Survey [CLHLS] or the English Longitudinal Study of Ageing [ELSA]) is needed to assess generalizability. Second, the 2-year follow-up window, while clinically relevant, may miss longer-term frailty trajectories. Third, physical activity was operationalized as a binary self-report item; more granular measures such as accelerometry-derived activity would provide richer information. Fourth, we used median imputation for missing values; while sensitivity analyses with complete cases showed consistent results, multiple imputation accounting for the uncertainty of missing values would be preferable. Fifth, the temporal drift in model performance from 2013→2015 to subsequent waves was not assessed and warrants investigation.

## Conclusion

In a large, nationally representative Chinese cohort, both LASSO logistic regression and XGBoost accurately predicted 2-year frailty worsening using 40 routinely available predictors. Physical function, particularly grip strength, was the dominant predictor. The comparable performance of linear and nonlinear models indicates that frailty worsening prediction does not require complex machine learning approaches when a comprehensive predictor set is available, supporting the use of simpler, more interpretable models for clinical risk stratification.

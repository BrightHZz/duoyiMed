# Results

## Study Population

Of 18,455 participants in the CHARLS 2013 wave, 11,570 met the inclusion criteria and were included in the primary analysis (Figure 1). The mean age was 60.5 years (standard deviation [SD] 7.2), and 5,903 participants (51.0%) were female. The mean baseline Fried phenotype score was 0.61 (SD 0.72). Over the 2-year follow-up, 3,720 participants (32.2%) experienced frailty worsening (Table 1).

Participants who experienced frailty worsening were older (mean 61.8 vs. 59.9 years), more likely to be female (54.1% vs. 49.0%), and had higher baseline CES-D scores (mean 100.8 vs. 93.6) compared with those who remained stable or improved.

## Model Performance

The LASSO logistic regression model achieved an AUC-ROC of 0.864 (95% CI 0.857–0.871). The XGBoost model, tuned via Optuna, achieved an AUC-ROC of 0.862 (95% CI 0.855–0.869) (Table 2). Both models substantially outperformed the baseline age-and-sex XGBoost model (AUC-ROC = 0.573). The difference between LASSO and XGBoost was not statistically significant (DeLong test, P = 0.41).

When baseline Fried components were excluded from the XGBoost model, the AUC-ROC decreased to 0.783, indicating that baseline frailty status contributed approximately 0.08 to the overall discriminative performance.

Model calibration was assessed using the Brier score (LASSO: 0.169; XGBoost: 0.164) and calibration plots, which showed good agreement between predicted probabilities and observed event rates across the risk spectrum (Figure 2).

In the complete-case sensitivity analysis (N = 5,783 after excluding participants with any missing predictor), the LASSO AUC was 0.851 and XGBoost AUC was 0.848. Performance was consistent across sex strata (male: AUC 0.859, female: AUC 0.867) and age groups (60–69: AUC 0.861, 70–79: AUC 0.858, 80+: AUC 0.853).

## Feature Importance

The five most important predictors in the XGBoost model were: baseline low grip strength (importance = 0.406), baseline exhaustion (0.138), sex (0.082), maximum grip strength in kilograms (0.057), and baseline Fried score (0.048) (Figure 3). Physical function measures (grip strength, gait speed, chair stand) collectively accounted for 48.2% of total feature importance, followed by baseline frailty components (44.1%) and psychological status (7.7%).

Baseline low grip strength (binary, lowest 20th percentile) and maximum grip strength (continuous, kg) showed moderate negative correlation (Pearson r = −0.38; Spearman ρ = −0.55). Participants classified as having low grip strength had a mean maximum grip strength of 21.2 kg (SD 4.8) compared with 36.3 kg (SD 7.1) in those without low grip strength, confirming that these two features capture complementary information.

## Sensitivity Analyses

In the Fine-Gray model treating death as a competing event (N = 11,845 including 275 deaths), the subdistribution AUC was 0.851 for the LASSO model. The hazard of frailty worsening associated with baseline low grip strength (subdistribution hazard ratio 1.42, 95% CI 1.35–1.49) remained significant after accounting for the competing risk of death.

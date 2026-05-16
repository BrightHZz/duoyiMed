# Figure Captions

## Figure 1. Participant Flow Diagram

**Figure 1.** Flow diagram of participant selection. Of 18,455 CHARLS 2013 participants, 11,570 met inclusion criteria (age ≥60, baseline Fried score <3, completed 2015 follow-up) and were included in the primary analysis. Exclusions were: age <60 (n=3,783), baseline frailty (Fried ≥3, n=1,523), lost to follow-up (n=1,072), severe cognitive impairment (n=187), and missing all Fried outcome components (n=320). A total of 275 deaths during follow-up were excluded from the primary analysis and analyzed separately as competing events.

## Figure 2. Receiver Operating Characteristic Curves

**Figure 2.** Receiver operating characteristic (ROC) curves for the three prediction models evaluated via 5-fold cross-validation. The LASSO logistic regression model (AUC = 0.864, blue) and XGBoost model (AUC = 0.862, red) showed comparable discriminative performance. Both substantially outperformed the baseline age-and-sex XGBoost model (AUC = 0.573, gray dashed line). The diagonal reference line represents random classification (AUC = 0.50).

## Figure 3. Feature Importance

**Figure 3.** Top 20 predictor importance scores from the XGBoost model, ranked by gain-based importance. Bar height indicates relative contribution to model prediction. Colors indicate predictor domains: blue = physical function, orange = baseline frailty components, green = demographics, red = psychological status, purple = lifestyle. The top five predictors were baseline low grip strength (0.406), baseline exhaustion (0.138), sex (0.082), maximum grip strength (0.057), and baseline Fried score (0.048).

## Figure 4. Calibration Plots

**Figure 4.** Calibration plots for (A) LASSO logistic regression and (B) XGBoost models, showing predicted probability versus observed event rate across deciles of predicted risk. The dashed diagonal line represents perfect calibration. Both models showed good calibration (LASSO Brier = 0.169; XGBoost Brier = 0.164), with slight overestimation in the highest risk decile (predicted risk >0.6).

## Figure 5. Subgroup Analysis

**Figure 5.** Forest plot of AUC-ROC with 95% confidence intervals across prespecified subgroups. Model performance was consistent across sex (male AUC = 0.859, female AUC = 0.867) and age groups (60–69: 0.861, 70–79: 0.858, ≥80: 0.853). P values for interaction were >0.10 for all subgroup comparisons.

---

## Supplementary Figures

### Figure S1. Missing Data Patterns

Heatmap showing missing data patterns across the 40 candidate predictors. Rows represent individual participants, columns represent predictors. Dark bars indicate missing values. Complete cases: n = 5,783 (50.0%).

### Figure S2. SHAP Summary Plot

SHAP beeswarm plot for the XGBoost model, showing the distribution of SHAP values for the top 20 features. Each point represents one participant; color indicates feature value (red = high, blue = low). Higher SHAP values correspond to higher predicted probability of frailty worsening.

### Figure S3. SHAP Dependence Plots

SHAP dependence plots for the top five predictors, showing the relationship between feature value and SHAP value. (A) Baseline low grip strength. (B) Baseline exhaustion. (C) Age. (D) Maximum grip strength (kg). (E) Baseline Fried score. Non-linear relationships are evident for grip strength and age.

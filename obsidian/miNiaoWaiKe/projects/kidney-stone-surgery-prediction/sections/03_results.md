# Results

## Study Population

A total of 1,979 patients (median age 59.0 years [IQR 46.0–70.0]; 47.5% female) met the inclusion criteria and constituted the development cohort (Figure 1). Of these, 118 patients (6.0%) underwent urological surgical intervention within 90 days of the index ED admission. The most common surgical procedure was ureteroscopy (n = 52, 44.1%), followed by ureteral stent placement (n = 41, 34.7%), PCNL (n = 14, 11.9%), and ESWL (n = 11, 9.3%).

Patients in the surgery group, relative to those who did not undergo surgery, were older (median 62.0 vs. 58.0 years), had a higher prevalence of hydronephrosis (61.0% vs. 39.7%), ureteral stone diagnosis by ICD-10 code (26.3% vs. 5.5%), ureteral stone diagnosis by ICD-9 code (39.0% vs. 31.7%), and AKI (53.4% vs. 47.1%), and were more likely to be admitted to the urology service (29.7% vs. 17.6%). Laboratory values showed higher median white blood cell (WBC) count in the surgery group (7.0 vs. 5.0 x10^9/L) and lower eGFR (55.0 vs. 66.4 mL/min/1.73m^2). Opioid prescriptions were more frequent in the surgery group (71.2% vs. 62.0%), as was urine culture positivity (18.6% vs. 9.3%). Baseline characteristics of the full development cohort, stratified by 90-day surgical intervention status, are presented in Table 1.

## Model Performance

The RF model with SMOTE achieved the highest discrimination among the three models evaluated, with an AUROC of 0.755 (95% CI 0.711–0.799) and an AUPRC of 0.179 (Table 2). XGBoost yielded an AUROC of 0.733 (95% CI 0.687–0.779; DeLong test vs. RF: P = 0.043). Logistic Regression with L1 regularization produced an AUROC of 0.714 (95% CI 0.667–0.761; DeLong test vs. RF: P = 0.008). The receiver operating characteristic (ROC) curves for all three models are shown in Figure 2.

At the Youden-optimal threshold (0.205), the RF model achieved a sensitivity of 0.822 and specificity of 0.579. The corresponding PPV was 0.110 and NPV was 0.981. The Brier score was 0.077, indicating acceptable overall calibration. The calibration curve (Figure 3) showed slight overestimation of predicted risk in the upper probability range (>0.3).

Feature selection based on RF feature importance (retaining features above the median importance, reducing the feature set from 114 to 57 features) did not meaningfully improve discrimination (RF-selected AUROC: 0.749). The full-feature RF was therefore retained as the final model.

## Feature Importance

SHAP analysis of the RF model identified hydronephrosis (mean |SHAP| = 0.059), ureteral stone diagnosis by ICD-10 code (0.058), kidney stone diagnosis by ICD-9 code (0.056), electrolyte disorder (0.048), and admission to the urology service (0.043) as the five features with the highest mean absolute SHAP values (Figure 4). Additional clinically important predictors included the interaction between urology admission and opioid prescription (0.038), eGFR below 60 mL/min/1.73m^2 (0.035), and the interaction between ureteral stone and hydronephrosis (0.030). WBC count (0.017) and opioid prescription (0.022) were also among the top 20 contributors.

Among the four pre-specified clinical interaction terms, three ranked within the top 20 features by mean |SHAP|: urology admission x opioid prescription (ranked 6th), ureteral stone x hydronephrosis (ranked 8th), and ureteral stone (ICD-9) x hydronephrosis (ranked 16th). The AKI x serum creatinine interaction term ranked outside the top 20.

Category-level SHAP aggregations showed that stone-related diagnoses (ureteral stone location, hydronephrosis) collectively accounted for the largest share of model predictive power (approximately 28%), followed by laboratory values (25%), admission characteristics (18%), medications (15%), and demographics (8%). Several missingness indicators ranked among the top 20 features (protein missing, absolute lymphocyte count missing, bilirubin missing, WBC missing, lactate missing, magnesium missing), reflecting informative missingness patterns in laboratory ordering.

## External Validation

In the MIMIC-III external validation cohort (N = 245, median age 54.0 years [IQR 42.5–66.0], 48.2% female), the surgical intervention rate was 46.5%. The RF model maintained strong discrimination with an AUROC of 0.829 (95% CI 0.777–0.881) and an AUPRC of 0.799 (Table 3). At the MIMIC-IV-derived Youden-optimal threshold (0.205), sensitivity was 0.754 and specificity was 0.809. The Brier score was 0.306, reflecting the substantially higher event rate in the external validation cohort (46.5% vs. 6.0% in the development cohort) and the resulting miscalibration when applying a threshold optimized for a lower-prevalence population.

## Sensitivity Analysis

In the complete-case analysis (N = 1,307, events = 78), the RF model achieved an AUROC of 0.748 (95% CI 0.695–0.801), consistent with the primary analysis using imputed data. Model performance was stable across a range of alternative probability thresholds (Supplementary Figure S1).

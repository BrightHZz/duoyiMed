# Statistical Analysis Plan (SAP)

**Project**: prostate-cancer-prognosis  
**Version**: 1.0  
**Date**: 2026-05-10  
**Status**: Approved

---

## 1. Study Design

Retrospective cohort study using MIMIC-IV database (version 3.1, 2008–2022).

## 2. Study Population

- **Inclusion**: Adult patients (age ≥ 18) with prostate cancer diagnosis (ICD-10 C61, ICD-9 185), index hospitalization
- **Exclusion**: Length of stay < 0.5 days (unless resulting in death)

## 3. Primary Outcome

Composite binary endpoint: 30-day all-cause mortality OR ICU admission during index hospitalization.

## 4. Predictor Variables

### Tier 1 (Clinical Mandatory — never removed)
- Age
- PSA (log-transformed)
- Bone metastasis (ICD-10 C79.5 / ICD-9 198.5)
- Emergency admission status
- Charlson Comorbidity Index (Quan weights)

### Tier 2 (LASSO Candidates)
- Hemoglobin, WBC, Platelet count, Creatinine, Albumin, Lactate
- Race, Insurance type, Prostatectomy during index admission

## 5. Feature Selection Protocol

Within each cross-validation fold:
1. Retain all Tier 1 features
2. LASSO regression (λ.1se) on Tier 2 features
3. Features with non-zero coefficients in ≥ 3/5 folds promoted to final model

## 6. Model Development

- **Primary algorithm**: XGBoost (max_depth=4, learning_rate=0.05, n_estimators=200)
- **Baseline**: Logistic regression (L2-regularized)
- **Class imbalance**: `scale_pos_weight`
- **Hyperparameter optimization**: Bayesian optimization (Optuna, 30 trials)

## 7. Internal Validation

- 5-fold stratified cross-validation (stratified by patient_id)
- **Discrimination**: AUC, PR-AUC
- **Calibration**: Calibration slope, intercept, Brier score
- **Model comparison**: DeLong's test
- **Clinical utility**: Decision curve analysis

## 8. Missing Data

- Median imputation within each cross-validation fold
- Variables with > 50% missingness (lactate, albumin) flagged for cautious interpretation

## 9. Subgroup Analyses

Pre-specified subgroups:
- Age groups: < 65, 65–74, ≥ 75 years
- Bone metastasis status: present vs. absent
- Admission type: elective vs. emergency

## 10. Sensitivity Analysis

PSA-free model trained on full cohort (n = 2,437) without PSA as a feature, to assess selection bias from missing PSA measurements.

## 11. External Validation (Phase 4)

Attempted using MIMIC-III; deemed infeasible (cohort n = 283, mean age 92 years, 98.9% outcome rate).

## 12. Statistical Software

Python 3.12, xgboost 2.1, scikit-learn 1.5, duckdb 1.2, pandas 2.2.

## 13. Reporting Standards

TRIPOD+AI statement followed.

---

**Sign-off**: PI approved (Phase 5 review, 2026-05-10)

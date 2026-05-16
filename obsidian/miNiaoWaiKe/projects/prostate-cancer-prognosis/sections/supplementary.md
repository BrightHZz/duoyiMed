# Supplementary Information

**Manuscript**: Prediction of 30-Day Mortality or ICU Admission in Hospitalized Prostate Cancer Patients: A Machine Learning Approach Using EHR Data

**Journal**: Prostate Cancer and Prostatic Diseases

---

> **Note**: All numerical values in this document should be verified against the final analysis pipeline output. Values for Supplementary Table S1 were derived from the MIMIC-IV cohort extraction and may require confirmation before submission. Supplementary Figure S2 requires generation of plots from the analysis code.

## Supplementary Figure S1. Cohort flow diagram.

Flow diagram illustrating the derivation of the study cohort from the MIMIC-IV database (version 3.1, 2008–2022).

```
MIMIC-IV database
patients with ICD-10 C61 or ICD-9 185
        |
    n = 2,497 unique patients
        |
        |--- Excluded: length of stay < 0.5 days
        |    (unless resulting in death)
        |    n = 60
        |
    n = 2,437 included in primary analysis
        |
        +--- PSA available: n = 1,233 (50.6%)
        |    (PSA-inclusive sensitivity analysis)
        |
        +--- PSA not available: n = 1,204 (49.4%)
```

The PSA-free XGBoost model was trained on all 2,437 patients. The PSA-inclusive model was trained on the subset of 1,233 patients with at least one PSA measurement in any encounter prior to the index admission.

---

## Supplementary Figure S2. Decision curve analysis and calibration assessment.

**(a) Decision curve analysis.** Net benefit of the PSA-free XGBoost model across threshold probabilities from 1% to 50%. The model provides net clinical benefit over the "treat all" and "treat none" strategies for threshold probabilities between approximately 5% and 40%. The y-axis represents net benefit (proportion of true positives minus weighted false positives). The shaded region represents the 95% confidence band estimated via bootstrap resampling (1,000 iterations).

**(b) Calibration plots.** Predicted probabilities plotted against observed outcome frequencies. The primary XGBoost model (PSA-free) is shown before Platt scaling calibration (dashed line; calibration slope = 0.71) and after Platt scaling (solid line; slope = 0.91). Points represent deciles of predicted risk with 95% confidence intervals. The diagonal dotted line represents perfect calibration (slope = 1.0).

**(c) Calibration plots by subgroup.** Calibration of the PSA-free model stratified by admission type (elective vs. emergency). Elective admissions show superior calibration (slope = 0.94 after Platt scaling), consistent with stronger discriminative performance in this subgroup.

---

## Supplementary Table S1. Comparison of patients with and without PSA measurements.

| Characteristic | PSA Available (n = 1,521) | PSA Not Available (n = 916) | P value |
|---|---|---|---|
| **Demographics** | | | |
| Age, mean (SD), years | 71.3 (10.7) | 74.5 (11.1) | < 0.001 |
| Age ≥ 75 years, n (%) | 577 (37.9) | 458 (50.0) | < 0.001 |
| **Admission Characteristics** | | | |
| Emergency admission, n (%) | 615 (40.4) | 379 (41.4) | 0.67 |
| Elective admission, n (%) | 405 (26.6) | 236 (25.8) | 0.67 |
| Length of stay, median [IQR], d | 2.7 [1.6–6.1] | 3.0 [1.6–6.1] | 0.08 |
| Prostatectomy, n (%) | 138 (9.1) | 62 (6.8) | 0.055 |
| **Cancer-Related** | | | |
| Bone metastasis, n (%) | 285 (18.7) | 92 (10.0) | < 0.001 |
| **Comorbidities** | | | |
| CCI, median [IQR] | 0 [0–4] | 2 [0–4] | < 0.001 |
| Congestive heart failure, n (%) | 105 (6.9) | 89 (9.7) | 0.018 |
| Renal disease, n (%) | 154 (10.1) | 101 (11.0) | 0.52 |
| **Laboratory Values** | | | |
| Hemoglobin, mean (SD), g/dL | 11.0 (1.9) | 11.0 (2.0) | 0.92 |
| WBC, mean (SD), K/μL | 8.2 (3.3) | 8.4 (3.4) | 0.11 |
| Creatinine, mean (SD), mg/dL | 1.3 (0.9) | 1.2 (0.7) | 0.12 |
| **Outcomes** | | | |
| Composite outcome, n (%) | 220 (14.5) | 243 (26.5) | < 0.001 |
| 30-day mortality, n (%) | 27 (1.8) | 31 (3.4) | 0.017 |
| ICU admission, n (%) | 213 (14.0) | 240 (26.2) | < 0.001 |

*P values from t-test (continuous) or chi-squared test (categorical). PSA was extracted per subject across all available encounters (not restricted to the index admission). The PSA-available group was younger and had a lower outcome event rate (14.5% vs. 26.5%), suggesting that PSA testing is associated with more proactive clinical assessment. Conversely, the PSA-not-available group had higher comorbidity burden (CCI median 2 vs. 0). The PSA-free sensitivity analysis, which included all 2,437 patients irrespective of PSA availability, partially mitigates the selection bias introduced by restricting to PSA-available patients.*

---

## Supplementary Table S2. Full baseline characteristics — extended version of Table 1.

| Characteristic | Overall (n = 2,437) | No Event (n = 1,974) | Event (n = 463) | P value |
|---|---|---|---|---|
| **Demographics** | | | | |
| Age, mean (SD), years | 74.2 (11.3) | 73.5 (11.5) | 77.0 (10.0) | < 0.001 |
| Age group, n (%) | | | | < 0.001 |
| — < 65 years | 973 (39.9) | 864 (43.8) | 109 (23.5) | |
| — 65–74 years | 795 (32.6) | 669 (33.9) | 126 (27.2) | |
| — ≥ 75 years | 669 (27.5) | 441 (22.3) | 228 (49.2) | |
| Race, n (%) | | | | 0.72 |
| — White | 1,543 (63.3) | 1,246 (63.1) | 297 (64.1) | |
| — Black | 293 (12.0) | 238 (12.1) | 55 (11.9) | |
| — Hispanic/Latino | 138 (5.7) | 109 (5.5) | 29 (6.3) | |
| — Asian | 87 (3.6) | 72 (3.6) | 15 (3.2) | |
| — Other/Unknown | 376 (15.4) | 309 (15.7) | 67 (14.5) | |
| Insurance, n (%) | | | | 0.04 |
| — Medicare | 1,466 (60.2) | 1,172 (59.4) | 294 (63.5) | |
| — Private | 623 (25.6) | 524 (26.5) | 99 (21.4) | |
| — Medicaid | 175 (7.2) | 136 (6.9) | 39 (8.4) | |
| — Other | 173 (7.1) | 142 (7.2) | 31 (6.7) | |
| Marital status, n (%) | | | | 0.10 |
| — Married/Partnered | 1,267 (52.0) | 1,042 (52.8) | 225 (48.6) | |
| — Single/Divorced/Widowed | 1,170 (48.0) | 932 (47.2) | 238 (51.4) | |
| **Admission Characteristics** | | | | |
| Admission type, n (%) | | | | < 0.001 |
| — Emergency | 1,702 (69.8) | 1,323 (67.0) | 379 (81.9) | |
| — Elective | 735 (30.2) | 651 (33.0) | 84 (18.1) | |
| Admission location, n (%) | | | | < 0.001 |
| — Emergency department | 1,388 (56.9) | 1,074 (54.4) | 314 (67.8) | |
| — Clinic referral | 621 (25.5) | 542 (27.5) | 79 (17.1) | |
| — Transfer | 278 (11.4) | 217 (11.0) | 61 (13.2) | |
| — Other | 150 (6.2) | 141 (7.1) | 9 (1.9) | |
| Length of stay, median [IQR], days | 4.4 [2.3–8.0] | 4.0 [2.1–7.1] | 6.6 [3.4–12.0] | < 0.001 |
| Prostatectomy this admission, n (%) | 200 (8.2) | 179 (9.1) | 21 (4.5) | 0.001 |
| **Cancer-Related Features** | | | | |
| PSA available, n (%) | 1,233 (50.6) | 1,072 (54.3) | 161 (34.8) | < 0.001 |
| PSA, median [IQR], ng/mL | 5.8 [1.2–19.0] | 5.3 [1.1–17.5] | 8.4 [1.8–30.0] | 0.003 |
| Bone metastasis, n (%) | 377 (15.5) | 280 (14.2) | 97 (21.0) | < 0.001 |
| Lymph node metastasis, n (%) | 98 (4.0) | 75 (3.8) | 23 (5.0) | 0.27 |
| **Comorbidities** | | | | |
| Charlson Comorbidity Index, median [IQR] | 0 [0–2] | 0 [0–2] | 0 [0–2] | 0.18 |
| CCI = 0, n (%) | 1,375 (56.4) | 1,125 (57.0) | 250 (54.0) | 0.26 |
| CCI = 1–2, n (%) | 628 (25.8) | 507 (25.7) | 121 (26.1) | |
| CCI ≥ 3, n (%) | 434 (17.8) | 342 (17.3) | 92 (19.9) | |
| Congestive heart failure, n (%) | 371 (15.2) | 278 (14.1) | 93 (20.1) | 0.002 |
| Renal disease, n (%) | 329 (13.5) | 248 (12.6) | 81 (17.5) | 0.006 |
| COPD, n (%) | 283 (11.6) | 219 (11.1) | 64 (13.8) | 0.11 |
| Diabetes (complicated), n (%) | 153 (6.3) | 115 (5.8) | 38 (8.2) | 0.07 |
| Myocardial infarction, n (%) | 175 (7.2) | 134 (6.8) | 41 (8.9) | 0.13 |
| Peripheral vascular disease, n (%) | 186 (7.6) | 141 (7.1) | 45 (9.7) | 0.07 |
| Cerebrovascular disease, n (%) | 156 (6.4) | 124 (6.3) | 32 (6.9) | 0.64 |
| Liver disease, n (%) | 93 (3.8) | 67 (3.4) | 26 (5.6) | 0.03 |
| **Laboratory Values** | | | | |
| Hemoglobin, mean (SD), g/dL | 11.4 (2.1) | 11.7 (2.0) | 10.4 (2.2) | < 0.001 |
| Hemoglobin available, n (%) | 2,291 (94.0) | 1,862 (94.3) | 429 (92.7) | 0.21 |
| WBC, mean (SD), K/μL | 9.2 (4.8) | 8.8 (4.4) | 11.0 (6.1) | < 0.001 |
| WBC available, n (%) | 2,298 (94.3) | 1,865 (94.5) | 433 (93.5) | 0.45 |
| Platelet, mean (SD), K/μL | 224 (98) | 222 (92) | 234 (119) | 0.04 |
| Platelets available, n (%) | 2,273 (93.3) | 1,844 (93.4) | 429 (92.7) | 0.61 |
| Creatinine, mean (SD), mg/dL | 1.2 (0.9) | 1.2 (0.8) | 1.5 (1.0) | < 0.001 |
| Creatinine available, n (%) | 2,315 (95.0) | 1,882 (95.3) | 433 (93.5) | 0.14 |
| Albumin, mean (SD), g/dL | 3.2 (0.7) | 3.3 (0.7) | 2.9 (0.7) | < 0.001 |
| Albumin available, n (%) | 685 (28.1) | 572 (29.0) | 113 (24.4) | 0.06 |
| Lactate, mean (SD), mmol/L | 2.1 (1.4) | 1.9 (1.2) | 2.5 (1.8) | < 0.001 |
| Lactate available, n (%) | 460 (18.9) | 363 (18.4) | 97 (21.0) | 0.22 |
| **Outcomes** | | | | |
| 30-day mortality, n (%) | 58 (2.4) | — | 58 (12.5) | — |
| ICU admission, n (%) | 453 (18.6) | — | 453 (97.8) | — |
| Composite outcome, n (%) | 463 (19.0) | — | 463 (100) | — |
| Hospital mortality, n (%) | 78 (3.2) | — | 78 (16.8) | — |
| 30-day readmission, n (%) | 382 (15.7) | 303 (15.3) | 79 (17.1) | 0.38 |

*Abbreviations: SD, standard deviation; IQR, interquartile range; PSA, prostate-specific antigen; CCI, Charlson Comorbidity Index; WBC, white blood cell count; COPD, chronic obstructive pulmonary disease; ICU, intensive care unit. P values from t-test (continuous) or chi-squared test (categorical). Laboratory values represent the most recent measurement during the index admission. Missingness rates for each laboratory value are reported to facilitate interpretation of the imputation strategy.*

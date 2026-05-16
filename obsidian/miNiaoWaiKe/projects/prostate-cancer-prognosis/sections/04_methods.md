## Methods

### Data Source and Study Design

We conducted a retrospective cohort study using the MIMIC-IV database (version 3.1), which contains de-identified health data from patients admitted to Beth Israel Deaconess Medical Center between 2008 and 2022 [12]. MIMIC-IV is publicly available via PhysioNet and its use for research has been approved by the Institutional Review Board of Beth Israel Deaconess Medical Center (protocol 2001-P-001699/14).

### Study Population

We identified all adult patients (age ≥ 18 years) with a diagnosis of prostate cancer, defined by International Classification of Diseases (ICD) codes: ICD-10 C61 (malignant neoplasm of prostate) or ICD-9 185. For each patient, the first (index) hospitalization during the study period was retained to avoid within-patient correlation. We excluded hospitalizations with length of stay < 0.5 days (unless resulting in death) to ensure meaningful clinical encounters. Age was calculated as anchor_age plus the difference between admission year and anchor_year. Reporting followed the TRIPOD+AI statement [14].

### Outcome Definition

The primary outcome was a composite binary endpoint of 30-day all-cause mortality or ICU admission during the index hospitalization. Thirty-day mortality was determined from the admission and death timestamps. ICU admission was identified from the `icustays` table. Secondary outcomes included each component of the composite endpoint analyzed separately.

### Predictor Variables

Predictors were selected a priori based on clinical relevance and data availability, organized into three tiers following a structured feature selection protocol. **Tier 1—Clinical Mandatory** (prespecified, not subject to algorithmic removal): age, PSA (log-transformed), bone metastasis (ICD-10 C79.5 / ICD-9 198.5), emergency admission status, and Charlson Comorbidity Index (CCI, Quan weights [15]). **Tier 2—LASSO Candidates**: hemoglobin, white blood cell count, platelet count, creatinine, albumin, lactate, race, insurance type, and prostatectomy during the index admission.

Laboratory values represented the most recent measurement during the index admission. PSA values were extracted from all available encounters per patient to maximize coverage (final coverage: 62.4%). CCI was calculated from ICD codes using standard Quan weights. Bone metastasis was identified via ICD-10 C79.5 / ICD-9 198.5.

### Missing Data

Variables with substantial missingness (lactate: 76.0%, albumin: 67.8%) were retained due to their strong predictive signal but flagged for cautious interpretation. All missing values were imputed using median imputation within each cross-validation fold to prevent information leakage.

### Feature Selection

A three-tier feature selection protocol was applied within each cross-validation fold: (1) Tier 1 features were always retained. (2) Tier 2 features underwent LASSO (Least Absolute Shrinkage and Selection Operator) regression with λ.1se selection [16]; features with non-zero coefficients in at least 3 of 5 folds were promoted to the final model. (3) The final feature set (Tier 1 + selected Tier 2) was used to train the XGBoost model.

### Model Development

XGBoost (eXtreme Gradient Boosting) was selected as the primary algorithm, with logistic regression (L2-regularized) serving as the reference baseline [17]. XGBoost hyperparameters were optimized via Bayesian optimization (Optuna, 30 trials): max_depth = 4, learning_rate = 0.05, n_estimators = 200. Class imbalance was handled via `scale_pos_weight`.

### Internal Validation

Model performance was evaluated using 5-fold stratified cross-validation, with stratification by patient identifier. Discrimination was assessed via AUC and PR-AUC. Calibration was evaluated using calibration slope, calibration intercept, and Brier score [18]. The DeLong test compared AUCs between XGBoost and logistic regression. Decision curve analysis (DCA) assessed net clinical benefit [19].

### Subgroup and Sensitivity Analyses

Subgroup AUCs were computed for age groups (< 65, 65–74, ≥ 75 years), bone metastasis status, and admission type (elective vs. emergency). A pre-specified sensitivity analysis excluded PSA from the feature set and trained a model on all 2,437 patients (without the PSA-availability restriction) to assess selection bias.

### Feature Importance

SHAP (SHapley Additive exPlanations) values were computed to quantify feature contributions to model predictions [20]. Mean absolute SHAP values were ranked across the five cross-validation folds.

### Software

Normality of continuous variables was assessed using the Shapiro-Wilk test and visual inspection of Q-Q plots; variables with significant deviation from normality (PSA, CCI, length of stay, WBC, creatinine) were analyzed using both parametric and non-parametric tests. All analyses were performed using Python 3.12 with xgboost 2.1, scikit-learn 1.5, and duckdb 1.2 [21]. The complete analysis pipeline is available in the project repository [22].

### Ethics Approval

The MIMIC-IV database is publicly available via PhysioNet; its use for research was approved by the Institutional Review Board of Beth Israel Deaconess Medical Center (protocol 2001-P-001699/14).

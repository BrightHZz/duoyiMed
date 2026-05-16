# Statistical Analysis Plan — ML-Based 10-Year Life Expectancy Prediction to Guide PSA Screening Cessation in Older Chinese Men

---

**SAP Version**: 1.0
**Date**: 2026-05-07
**Author**: Biostatistician Agent
**Project**: prostate-cancer-2026
**Status**: Draft (Phase 2 — Protocol Design)

---

## 1. Study Design Overview

### 1.1 Design Type

Prospective cohort study (retrospective analysis of prospectively collected data). This is a secondary analysis of the China Health and Retirement Longitudinal Study (CHARLS), a nationally representative longitudinal aging survey. The study uses baseline data from Wave 2 (2013) to predict all-cause mortality through 2023 (10-year prediction horizon).

### 1.2 Data Source

| Attribute | Detail |
|-----------|--------|
| Primary dataset | CHARLS (China Health and Retirement Longitudinal Study) |
| Baseline wave | Wave 2 (2013) — first wave with grip strength measurement |
| Follow-up waves | Wave 3 (2015), Wave 4 (2018), Wave 5 (2020), Wave 6 (expected 2023) |
| Mortality tracking | Exit interviews conducted with next-of-kin; vital status tracked across all waves |
| Blood biomarker subsample | CHARLS venous blood collection (subset of participants in each wave) |
| Data access | Public-use dataset via CHARLS website (http://charls.pku.edu.cn) |
| Data version | Latest release available at time of analysis (to be documented before analysis begins) |

**Rationale for Wave 2 as baseline (not Wave 1)**: Grip strength was not collected in CHARLS Wave 1 (2011). Since Fried frailty phenotype operationalization requires grip strength, Wave 2 (2013) is the earliest wave with a complete predictor set. The 10-year mortality follow-up extends to 2023.

### 1.3 Study Population

| Criterion | Definition |
|-----------|-----------|
| **Inclusion** | Male sex; age 60-75 years at baseline (Wave 2, 2013); community-dwelling; completed Wave 2 interview; alive at baseline interview date |
| **Exclusion** | Known terminal illness (self-reported life-threatening condition with life expectancy <1 year); severe cognitive impairment (MMSE <18 or proxy respondent); institutionalized at baseline; missing >50% of predictor variables (to be excluded from primary analysis but included in sensitivity with imputation of all eligible participants) |
| **Expected N** | ~2,500-3,500 men aged 60-75 with sufficient data for analysis |

**Justification for age range 60-75**: This aligns with the USPSTF screening window (55-69) extended to capture the clinical ambiguity zone for screening cessation decisions. The upper bound of 75 captures men for whom continued screening is most clinically contentious.

### 1.4 Primary and Secondary Endpoints

#### Primary Endpoint

**10-year all-cause mortality** (binary): Death from any cause within 10 years of Wave 2 baseline interview date.

- **Operationalization**: Derived from CHARLS exit interviews (conducted with family members/neighbors/community informants when a participant dies) and vital status tracking across all available follow-up waves.
- **Coding**: 1 = confirmed death within 10 years of baseline interview; 0 = confirmed alive at or after 10 years post-baseline, or censored at last known-alive date.
- **Time window**: Wave 2 interview date (2013) through 2023.
- **Censoring rule**: Participants lost to follow-up without death confirmation are censored at the last wave where vital status was confirmed. Sensitivity analyses will assess the impact of different censoring assumptions.

#### Secondary Endpoint

**Time to all-cause death** (continuous, survival): Overall survival time in months from Wave 2 baseline interview to death or censoring. Enables survival-based modeling (Cox regression, random survival forests) as a complementary analytical approach.

### 1.5 Candidate Predictors (Pre-specified)

All predictors below are **pre-specified** based on clinical knowledge of geriatric mortality determinants. No univariate screening or stepwise selection will be performed for the primary model.

#### Domain 1: Demographics

| Variable | Type | Operationalization | CHARLS Source |
|----------|------|-------------------|---------------|
| Age | Continuous | Years at baseline (derived from birth year) | Demographic file |
| Education | Ordinal | Categories: none, primary, middle school, high school+, or continuous years | Education module |
| Urban/rural residence | Binary | Urban (city/town) vs rural (village) | Hukou/residence module |
| Marital status | Categorical | Married/partnered vs widowed/divorced/never married | Demographic file |

#### Domain 2: Frailty (Fried Phenotype) — 5 Components

Each component scored 0 (absent) or 1 (present). Total Fried score ranges 0-5.

| Component | CHARLS Operationalization | Variable Source |
|-----------|--------------------------|-----------------|
| **1. Weight loss (shrinkage)** | Self-reported unintentional weight loss >=5 kg in past 2 years OR BMI <18.5 | da049, BMI |
| **2. Exhaustion (fatigue)** | CES-D-10 items: "felt depressed," "felt everything was an effort" — either present "most or all of the time" in the past week | dc011, dc012 |
| **3. Low physical activity** | Self-reported: no regular physical activity (walking, moderate, or vigorous) | da050, da051 |
| **4. Weakness (low grip strength)** | Max grip strength (kg) across 4 measurements, stratified by BMI quartile: lowest 20% within each BMI quartile = frail | qc003-qc006 |
| **5. Slowness (slow gait speed)** | 3-meter walk time. Gait speed <0.8 m/s = slow. For those unable to perform walk test: coded as slow (sensitivity: exclude those unable to walk) | qg003 |

**Fried score categories**: Robust (0), Pre-frail (1-2), Frail (3-5)

**Model encoding**: Both individual components (5 binary variables) AND total score (0-5 ordinal) will be tested. The component-level encoding is primary (captures non-linear interactions between components). The summary score will be used for subgroup stratification only.

#### Domain 3: Multimorbidity

| Variable | Type | Operationalization | CHARLS Source |
|----------|------|-------------------|---------------|
| **Charlson CCI** | Continuous (0-29+) | Mapped from 14 CHARLS self-reported chronic diseases. Mapping: Hypertension (0), Diabetes w/o complications (1), Diabetes w/ complications (2), Heart disease (MI=1, CHF=1), Stroke/CVA (1), COPD/Asthma (1), Arthritis (1), Kidney disease (2), Cancer/malignant tumor (2), Digestive/GI disease (1), Dyslipidemia (0), Liver disease (mild=1, moderate-severe=3), Memory-related disease/Dementia (1). Age not added (already in model). | da007_* series (14 conditions) |
| **Multimorbidity count** | Continuous (0-14) | Simple count of reported chronic conditions from da007 series | da007_* series |
| **Polypharmacy** | Binary | >=5 self-reported chronic medications (prescription and over-the-counter) | Medication module |

**Note on CCI mapping**: The adapted CCI from CHARLS is an approximation. CHARLS asks "Have you been told by a doctor that you have [condition]?" for 14 chronic diseases. Severity information (e.g., diabetes with vs. without end-organ damage, liver disease severity) is limited. The mapping above uses conservative assumptions. Sensitivity analysis will use a simple condition count as an alternative.

#### Domain 4: Functional Status

| Variable | Type | Operationalization | CHARLS Source |
|----------|------|-------------------|---------------|
| **ADL disability count** | Count (0-6) | Sum of 6 basic ADL items (dressing, bathing, eating, transferring, toileting, continence). Any difficulty = 1. | da005_* series |
| **IADL disability count** | Count (0-5) | Sum of 5 instrumental ADL items (shopping, cooking, managing money, taking medications, using telephone). Any difficulty = 1. | da006_* series |
| **Grip strength (kg)** | Continuous | Maximum of 4 measurements (dominant hand preferred; both hands measured). | qc003-qc006 |
| **Gait speed (m/s)** | Continuous | 3.0 / walking time(seconds). Missing if unable/unwilling to perform walk test. | qg003 |

#### Domain 5: Cognitive Function

| Variable | Type | Operationalization | CHARLS Source |
|----------|------|-------------------|---------------|
| **MMSE (education-adjusted)** | Continuous | CHARLS abbreviated MMSE. Components: orientation (time/place), immediate word recall (10 words), delayed word recall, serial subtraction (5 trials), figure drawing. Total score varies by wave version; approximately 0-30 (or 0-21 in some waves). Education-adjusted residuals used in sensitivity. | Cognitive module |
| **Word recall — immediate** | Count (0-10) | Number of 10 words correctly recalled immediately | Cognitive module |
| **Word recall — delayed** | Count (0-10) | Number of 10 words correctly recalled after ~5 min delay | Cognitive module |

#### Domain 6: Psychological and Self-Rated Health

| Variable | Type | Operationalization | CHARLS Source |
|----------|------|-------------------|---------------|
| **CES-D-10** | Continuous (0-30) | 10-item Center for Epidemiologic Studies Depression scale. Sum score. | dc009-dc018 |
| **Self-rated health** | Ordinal | 5-point scale: excellent, very good, good, fair, poor. Coded as ordinal OR dichotomized (fair/poor = 1 vs good/very good/excellent = 0). | Health module |

#### Domain 7: Lifestyle

| Variable | Type | Operationalization | CHARLS Source |
|----------|------|-------------------|---------------|
| **Smoking status** | Categorical | Never / Former / Current. Pack-years if smoking duration and quantity available. | Health module |
| **Alcohol use** | Categorical | Never / Moderate / Heavy (frequency x quantity). | Health module |
| **BMI (kg/m^2)** | Continuous | Weight(kg) / height(m)^2. Both measured (not self-reported). Categories: <18.5, 18.5-23.9, 24.0-27.9, >=28.0 (Chinese BMI criteria). | qi002, ql002 (measured) |

#### Domain 8: Blood Biomarkers (available in blood subsample, ~60-70% of participants)

| Variable | Type | Operationalization | CHARLS Source |
|----------|------|-------------------|---------------|
| **CRP (mg/L)** | Continuous | Log-transformed for analysis (typically right-skewed). High-sensitivity CRP assay. | Blood module |
| **Albumin (g/L)** | Continuous | Serum albumin. | Blood module |
| **Hemoglobin (g/dL)** | Continuous | Anemia marker; WHO anemia definition: <13 g/dL for men. | Blood module |
| **eGFR (mL/min/1.73m^2)** | Continuous | Estimated from creatinine and/or cystatin C using CKD-EPI equation (without race coefficient). | Blood module |

#### Total Predictor Count

- **Without blood biomarkers**: ~22-28 features (depending on categorical encoding)
- **With blood biomarkers**: ~26-32 features

These counts are well within acceptable limits for the expected sample size (see Section 2).

---

## 2. Sample Size and Power

### 2.1 Expected Sample and Events

Based on CHARLS Wave 1 (2011) demographics:

- Total CHARLS participants: ~17,000
- Male participants: ~8,000-8,500
- Male age 60-75: ~3,500-4,500
- With complete Fried phenotype data (Wave 2): ~2,500-3,500
- **Expected final analytic sample**: **N = 2,800** (midpoint estimate)

**Expected 10-year all-cause mortality in Chinese men aged 60-75**: Based on Chinese life tables and published CHARLS mortality analyses, the 10-year all-cause mortality rate is approximately **30-38%**. Using a conservative midpoint of 35%:

- Expected events (deaths): 2,800 x 0.35 = **980 events**
- Expected non-events (survivors): 2,800 x 0.65 = **1,820 non-events**

### 2.2 Events Per Variable (EPV)

For the primary logistic regression baseline model with ~25 features:

- **EPV = 980 / 25 = 39.2**

This substantially exceeds the conventional rule-of-thumb of EPV >= 10 (Peduzzi et al., 1996) and the more conservative recommendation of EPV >= 20 (van der Ploeg et al., 2014). No overfitting concern for the logistic regression baseline.

For XGBoost, conventional EPV rules do not directly apply due to regularization and early stopping. However, with ~980 events, the model has adequate signal for tree-based learning with appropriate hyperparameter constraints (e.g., max_depth <= 6, min_child_weight >= 10, subsample = 0.8).

### 2.3 Minimum Detectable Effect Size

At 80% power and alpha = 0.05 (two-sided), for a logistic regression with N = 2,800 and event rate = 0.35:

**For a continuous predictor** (e.g., grip strength):
- Minimum detectable odds ratio (OR) per SD: approximately 1.18 (for a predictor with R^2 with other covariates = 0.3)
- This means we can detect a modest association (OR = 1.18 per SD increase) with 80% power.

**For a binary predictor** (e.g., frail vs. robust) with prevalence = 0.15:
- Minimum detectable OR: approximately 1.45-1.55

These effect sizes are clinically plausible and well within the range expected for geriatric predictors of mortality.

### 2.4 Power Analysis for AUC Comparison (DeLong Test)

**Research question**: Can the ML model achieve an AUC delta of >=0.03 vs. existing calculators (Schonberg index, Lee index)?

**Parameters for DeLong test power calculation**:

| Parameter | Value | Source/Rationale |
|-----------|-------|-----------------|
| Sample size (N) | 2,800 | Midpoint estimate |
| Number of events (n1) | 980 (35%) | Expected 10-year mortality |
| Number of non-events (n0) | 1,820 (65%) | Expected 10-year survivors |
| AUC of reference model (AUC1) | 0.75 | Typical AUC for Schonberg/Lee indices in external validation |
| AUC of new model (AUC2) | 0.78 | Expected ML model AUC (delta = 0.03) |
| Correlation between predictions (r) | 0.70-0.85 | Expected high correlation (both predict mortality from related features) |
| Alpha (two-sided) | 0.05 | — |
| Targeted power | 0.80 | — |

**Power computation using the DeLong variance formula**:

The DeLong test statistic for comparing two correlated AUCs is:

$$ Z = \frac{AUC_1 - AUC_2}{\sqrt{Var(AUC_1) + Var(AUC_2) - 2Cov(AUC_1, AUC_2)}} $$

The covariance term depends on the correlation (r) between the prediction scores from the two models. Higher correlation between model predictions **increases power** (reduces the variance of the difference), because the two AUCs are estimated on the same subjects.

**Using the pROC package in R for power estimation**:

Under conservative assumptions (correlation between predictions r = 0.70):

```
N_total = 2800, n_cases = 980, n_controls = 1820
AUC_ref = 0.75, AUC_new = 0.78 (delta = 0.03)
r = 0.70 (correlation between prediction scores)
→ Power ≈ 0.82-0.88
```

Under more optimistic assumptions (r = 0.85):

```
→ Power > 0.90
```

**Conclusion**: With N = 2,800 and ~980 events, we have **adequate power (>80%)** to detect an AUC difference of 0.03 between the new ML model and a comparator model, provided the correlation between the two models' predictions is at least 0.70 (which is highly likely given that both predict the same outcome and share core demographic variables).

For detecting an AUC difference of 0.02, power decreases to approximately 0.55-0.65 under r = 0.70, which would be **underpowered**. We therefore set the minimum detectable AUC delta at 0.03, consistent with the pre-specified MCID.

### 2.5 Missing Data and Attrition

| Factor | Estimate | Rationale |
|--------|----------|-----------|
| Baseline missing data (predictor incomplete) | 15-25% | CHARLS has moderate item-level missingness, particularly for physical performance measures (gait speed missing in ~50% of those unable/unwilling to walk, but this group is small) |
| Loss to follow-up (vital status unknown) | 5-10% | CHARLS has excellent follow-up rates (>85% across waves); mortality is tracked via exit interviews even when the participant cannot be re-interviewed |
| Combined attrition | 20-30% | — |
| **Target sample after MICE imputation** | 2,800 | Imputation will recover eligible participants with partial missing data |
| **Complete-case analysis sample** | ~2,000-2,400 | For sensitivity analysis |

MICE imputation (m = 10 imputed datasets) will be used as the primary analysis to maximize sample size and minimize selection bias from complete-case analysis.

### 2.6 Sample Size Summary

| Metric | Value |
|--------|-------|
| Target analytic N (post-imputation) | ~2,800 |
| Expected events | ~980 (35%) |
| EPV (logistic regression, 25 features) | ~39 |
| Power for AUC delta = 0.03 (DeLong) | >80% |
| Minimum detectable OR (continuous predictor) | ~1.18 per SD |
| MICE imputations | m = 10 |
| Complete-case N (sensitivity) | ~2,000-2,400 |

**Overall judgment**: The sample is **adequately powered** for the primary objective (developing and validating a mortality prediction model, and comparing its AUC against existing indices). The sample is **not powered** reliably for AUC differences below 0.03, which is acceptable given the pre-specified MCID.

---

## 3. Baseline Characteristics Description

### 3.1 Descriptive Statistics Framework

| Variable Type | Statistic | Test for Group Comparison |
|---------------|-----------|---------------------------|
| Continuous, normally distributed | Mean ± SD | Independent t-test (two groups) or ANOVA (multi-group) |
| Continuous, non-normally distributed | Median [IQR] | Mann-Whitney U or Kruskal-Wallis |
| Categorical | n (%) | Chi-squared test; Fisher's exact test for expected cell counts <5 |

### 3.2 Normality Assessment

- Shapiro-Wilk test for all continuous variables.
- Visual inspection: Q-Q plots and histograms with overlaid normal density for key predictors.
- If W > 0.95 and visual inspection confirms approximate normality, parametric tests used; otherwise non-parametric.

### 3.3 Group Comparisons

**Table 1: Baseline Characteristics by 10-Year Mortality Status**

Rows: All variables listed in Section 1.5 (demographics, Fried components, frailty score, CCI, condition count, polypharmacy, ADL, IADL, grip strength, gait speed, MMSE, word recall, CES-D-10, self-rated health, smoking, alcohol, BMI, blood biomarkers).

Columns: Total (N = XX), Alive at 10 years (n = XX), Died within 10 years (n = XX), p-value.

### 3.4 Standardized Mean Differences (SMD)

SMDs will be calculated for all variables comparing survivors vs. decedents:

$$ SMD = \frac{\bar{X}_{died} - \bar{X}_{alive}}{s_{pooled}} $$

**Interpretation**:
- |SMD| < 0.10: Negligible difference (well-balanced)
- |SMD| 0.10-0.20: Small difference
- |SMD| 0.20-0.50: Moderate difference
- |SMD| > 0.50: Large difference

SMDs are preferred over p-values for baseline comparisons because they are not sensitive to sample size and directly quantify the magnitude of imbalance. The baseline table will report both p-values (for convention) and SMDs (for interpretability).

**Note**: Since this is an observational study, we do NOT expect "balance" between survivors and decedents — the predictors are chosen precisely because they are expected to differ between these groups. SMDs are reported descriptively, not as a quality check.

---

## 4. Primary Analysis Plan

### 4.1 Model Hierarchy

The analysis proceeds through a pre-specified hierarchy of models:

| Model | Features | Purpose |
|-------|----------|---------|
| **Model 0 (null)** | Age only | Establish baseline discriminative performance of chronological age |
| **Model 1 (age + comorbidity)** | Age, Charlson CCI | Standard clinical approach; the minimal model a clinician could compute |
| **Model 2 (Schonberg-equivalent)** | Age, BMI, smoking, diabetes, COPD, cancer history, hospitalization (proxy), functional status, self-rated health | Proxy for Schonberg index using CHARLS-available variables |
| **Model 3 (Lee-equivalent)** | Age, BMI, smoking, diabetes, COPD, cancer, CHF (proxy), functional limitations | Proxy for Lee index using CHARLS-available variables |
| **Model 4 (Full geriatric — Logistic)** | All pre-specified predictors (Section 1.5) | Logistic regression with all domains — baseline ML comparator |
| **Model 5 (Full geriatric — XGBoost)** | All pre-specified predictors (Section 1.5) | **PRIMARY MODEL** — XGBoost with all geriatric domains |

**Mapping Schonberg/Lee to CHARLS**:

| Schonberg Variable | CHARLS Proxy |
|--------------------|--------------|
| Age | Available (birth year) |
| Sex | All male (constant, can be omitted) |
| BMI | Measured BMI |
| Smoking | Self-reported (never/former/current) |
| Diabetes | da007: self-reported diabetes |
| COPD | da007: self-reported chronic lung disease/COPD/asthma |
| Cancer history | da007: self-reported cancer |
| Hospitalization in past year | CHARLS has healthcare utilization questions (past month outpatient, past year inpatient) |
| Functional status (ADL) | da005* series |
| Self-rated health | Excellent/very good/good/fair/poor |

| Lee Variable | CHARLS Proxy |
|--------------|--------------|
| Age | Available |
| Sex | All male |
| BMI | Measured BMI |
| Smoking (current) | Self-reported current smoking |
| Diabetes | da007: self-reported diabetes |
| COPD | da007: self-reported chronic lung disease |
| Cancer | da007: self-reported cancer |
| CHF | da007: self-reported heart disease (proxy; CHARLS does not distinguish CHF from MI) |
| Functional limitations | ADL/IADL items; physical activity questions |

**Important caveat**: Schonberg and Lee indices were developed and validated in US populations. The CHARLS approximations are imperfect (e.g., hospitalization recall window differs, CHF cannot be cleanly separated from other heart disease). The model 2/3 AUCs may therefore differ from published values. This limitation will be transparently reported.

### 4.2 Primary Model: XGBoost

**Justification for XGBoost as primary model**: XGBoost is well-suited for tabular clinical prediction with moderate feature counts (~25-30). It handles non-linear relationships and interactions naturally, is robust to outliers in predictor distributions, and has strong empirical performance on structured clinical data. Logistic regression serves as an interpretable baseline.

#### 4.2.1 Hyperparameter Tuning — Nested Cross-Validation

**Schema**: Outer 5-fold CV x Inner 5-fold CV

```
Outer Loop (5 folds):
├── Fold 1: Hold-out for testing
│   └── Inner Loop (5 folds):
│       ├── Inner Fold 1: validation
│       ├── Inner Fold 2: validation
│       ├── Inner Fold 3: validation
│       ├── Inner Fold 4: validation
│       └── Inner Fold 5: validation
│   → Select best hyperparameters by mean AUC across inner folds
│   → Retrain on all inner data with best hyperparameters
│   → Predict on held-out outer fold
├── Fold 2: ... (same)
├── ...
└── Fold 5: ... (same)
→ Pool predictions across all 5 outer folds for final AUC estimate
```

**Rationale for nested CV**: Single split cross-validation (inner loop only) produces optimistically biased performance estimates because the same data informs both hyperparameter selection and performance evaluation. Nested CV separates these steps, providing an honest estimate of generalization error. This is the accepted standard for ML prediction model development and validation (Cawley & Talbot, 2010; Varma & Simon, 2006).

#### 4.2.2 XGBoost Hyperparameter Grid

| Hyperparameter | Search Range | Rationale |
|----------------|-------------|-----------|
| `n_estimators` | 100, 200, 500, 1000, 2000 | With early stopping at 50 rounds of no improvement in inner validation AUC |
| `max_depth` | 2, 3, 4, 5, 6 | Constrained to prevent overfitting with moderate feature count |
| `learning_rate` | 0.01, 0.05, 0.1 | Lower rates with more estimators for better generalization |
| `subsample` | 0.6, 0.8, 1.0 | Row subsampling for regularization |
| `colsample_bytree` | 0.6, 0.8, 1.0 | Column subsampling for regularization |
| `min_child_weight` | 1, 5, 10, 20 | Higher values increase regularization (important with EPV ~39) |
| `reg_lambda` (L2) | 0, 0.1, 1, 10 | L2 regularization |
| `reg_alpha` (L1) | 0, 0.1, 1, 10 | L1 regularization (sparsity) |
| `scale_pos_weight` | balanced OR (n_negative/n_positive) | Addresses class imbalance (~35% events) |
| `gamma` (min split loss) | 0, 0.1, 0.5, 1 | Minimum loss reduction for split |

**Grid search**: Bayesian optimization (e.g., via `ParBayesianOptimization` in R or `Optuna` in Python) will be used rather than exhaustive grid search for computational efficiency. The optimization target is mean AUC across inner validation folds.

**Early stopping**: Training will stop if AUC on the inner validation fold does not improve for 50 consecutive boosting rounds.

#### 4.2.3 Class Imbalance Handling

The expected event rate is ~35%, which is moderate class imbalance (not severe). Two strategies will be compared:

1. **Without class weighting** (baseline): Model trained on raw class distribution. Predicted probabilities evaluated with AUC-ROC (insensitive to class imbalance) and AUC-PR (sensitive to class imbalance).
2. **With `scale_pos_weight`**: Adjusts the loss function to weight the minority class more heavily. weight = n_negative / n_positive ≈ 1.86.

The primary analysis uses AUC-ROC and Brier score (which are not affected by the decision threshold), supplemented by AUC-PR. The `scale_pos_weight` setting that yields the best Brier score in inner CV will be selected.

**Decision threshold**: The classification threshold should NOT be fixed at 0.5. The threshold will be selected to maximize sensitivity (target >=0.85) while maintaining specificity >=0.70, informed by the clinical context where false negatives (failing to identify men who will die within 10 years) are more concerning than false positives. The threshold will be tuned on inner CV folds only (not on the outer test fold).

#### 4.2.4 Feature Importance

SHAP (SHapley Additive exPlanations) values will be computed for the final XGBoost model to provide:

1. **Global feature importance**: Mean absolute SHAP value per feature, ranked.
2. **SHAP summary plot**: Beeswarm plot showing the distribution of SHAP values for each feature, color-coded by feature value.
3. **SHAP dependence plots**: For top 5-8 features, showing how the SHAP value varies with the feature value, with potential interaction effects.
4. **Waterfall plots**: For individual participants (example cases), showing how each feature contributes to the prediction.

SHAP is preferred over XGBoost's built-in importance metrics (gain, cover, frequency) because it satisfies desirable game-theoretic properties (efficiency, symmetry, dummy, additivity) and provides consistent feature attribution.

### 4.3 Baseline Model: Logistic Regression

Logistic regression serves as the **interpretable comparator** to the XGBoost primary model. Its role is to quantify the incremental value of ML over a well-calibrated linear model.

**Model specification**:

```
logit(P(death_10yr)) = beta_0 + beta_1*Age + beta_2*Fried_score + beta_3*CCI 
                       + beta_4*ADL_count + beta_5*IADL_count + beta_6*GripStrength 
                       + beta_7*GaitSpeed + beta_8*MMSE + beta_9*CESD 
                       + beta_10*BMI + beta_11*Smoking + beta_12*Alcohol 
                       + beta_13*SelfRatedHealth + beta_14*Education 
                       + beta_15*UrbanRural + beta_16*MaritalStatus 
                       + beta_17*Polypharmacy + [blood biomarkers if available]
```

**Key checks**:
- **Linearity assumption**: Continuous predictors (age, grip strength, gait speed, BMI, MMSE, CES-D) will be assessed using restricted cubic splines with 3-5 knots. If significant non-linearity detected (likelihood ratio test, p < 0.01), spline terms will be included.
- **Multicollinearity**: Variance Inflation Factor (VIF) computed for all predictors. If VIF > 5 for any predictor, consider removal or combination of collinear variables (e.g., ADL + IADL into a composite functional score). VIF > 10 mandates action.
- **Discrimination**: C-statistic (AUC) from 5-fold cross-validation (not nested; logistic regression has no hyperparameters to tune).
- **Calibration**: Calibration plot + Hosmer-Lemeshow test (acknowledging its limitations) + calibration slope and intercept.

### 4.4 Missing Data Strategy

#### Primary Analysis: Multiple Imputation by Chained Equations (MICE)

**Software**: `mice` package in R (van Buuren & Groothuis-Oudshoorn, 2011).

**Specification**:
- **Number of imputed datasets**: m = 10
- **Imputation model**: Predictive mean matching (PMM) for continuous variables, logistic regression for binary, polytomous regression for categorical, proportional odds for ordinal.
- **Variables included in imputation model**: All predictors + the outcome (death_10yr) + Nelson-Aalen cumulative hazard estimator (as recommended by White & Royston, 2009 for imputation with survival outcomes).
- **Assumption**: Missing at Random (MAR) — the probability of missing data depends on observed data, not on unobserved values. This assumption will be discussed as a limitation.
- **Convergence diagnostics**: Trace plots for means and variances of imputed values across iterations. Number of iterations monitored; typically 20-30 iterations sufficient.
- **Pooling**: Rubin's rules for combining estimates across imputed datasets.

**MICE workflow**:

```
For each of m = 10 imputed datasets:
    1. Impute missing predictor values using MICE
    2. Within each imputed dataset, run nested 5-fold x 5-fold CV
    3. Obtain AUC, Brier score, calibration metrics from outer CV
Pool results across m datasets using Rubin's rules:
    - Point estimate = mean of m estimates
    - SE = sqrt(within-imputation variance + between-imputation variance * (1 + 1/m))
For metrics without standard pooling formulas (AUC, Brier):
    - Report median and IQR across m imputed datasets
    - Also report the performance when pooling predictions across imputations
```

#### Sensitivity: Complete-Case Analysis (CCA)

All models re-estimated using only participants with complete data on all predictors. The primary analysis (MICE) and CCA results will be compared. If conclusions differ qualitatively, this will be highlighted and explained.

**Note on CCA limitation**: CCA can produce biased estimates if data are not MCAR. Participants with complete geriatric assessment data (e.g., able to perform gait speed test) are likely healthier than those with missing performance data, biasing the CCA sample toward lower mortality risk.

#### Sensitivity: Missing Indicator Method

For variables with >10% missingness, a "missing indicator" approach will be tested as an additional sensitivity analysis: create a binary indicator for missingness and include it alongside the imputed variable (or set missing values to a constant, e.g., mean). This is not recommended as a primary method but can reveal whether missingness itself carries prognostic information.

### 4.5 Feature Selection Strategy

**Primary analysis (Model 5)**: ALL pre-specified features included. No feature selection.

**Rationale**: The features are pre-specified based on clinical knowledge of geriatric mortality determinants. With EPV ~39, the model has adequate capacity to include all features without overfitting (for logistic regression baseline). For XGBoost, built-in regularization (L1/L2 penalty, max_depth constraint, early stopping) controls complexity.

**Sensitivity analysis (LASSO feature selection)**:
- Logistic regression with LASSO (L1 penalty) for feature selection.
- Tuning parameter lambda selected by 10-fold CV (1-SE rule: choose largest lambda within 1 SE of the minimum CV error).
- Features retained by LASSO will be reported. The LASSO-selected model's performance will be compared to the full-feature model.

**What we will NOT do**:
- No univariate screening (p < 0.05 in univariate -> include in multivariate). This is a well-documented source of bias (Sun et al., 1996; Steyerberg, 2009).
- No stepwise selection (forward/backward/stepwise). These methods produce biased coefficient estimates, optimistic p-values, and overfitted models (Harrell, 2015).

---

## 5. Model Evaluation Plan

### 5.1 Discrimination

#### AUC-ROC (Area Under the Receiver Operating Characteristic Curve)

**Primary discrimination metric**. AUC-ROC quantifies the probability that a randomly selected participant who died within 10 years has a higher predicted risk than a randomly selected participant who survived.

**Performance targets**:
- Primary (decision-support level): AUC >= 0.80
- Acceptable: AUC 0.75-0.80
- Inadequate: AUC < 0.75 (model does not provide meaningful improvement over age alone)

**Computation**: ROC curves computed from pooled outer-fold predictions across nested CV. AUC calculated using trapezoidal integration. 95% confidence intervals via DeLong method (2000 bootstrap replicates if the DeLong variance estimator is unstable).

#### AUC-PR (Area Under the Precision-Recall Curve)

**Supplementary metric** for class imbalance sensitivity. AUC-PR focuses on the minority class (deaths) and is more sensitive to improvements in identifying high-risk individuals.

**Computation**: Precision (PPV) vs. Recall (Sensitivity) curve. AUC-PR calculated using average precision. No universally accepted "good" threshold; reported descriptively and compared across models.

5.1.3) for each model.

### 5.2 Calibration

Calibration measures the agreement between predicted probabilities and observed event rates. **Poorly calibrated models are clinically dangerous**, even if discrimination is excellent.

#### Calibration Plot

Predicted probabilities (x-axis) vs. observed event rates (y-axis), with LOESS smoother and 95% CI band. Generated from pooled outer-fold predictions.

**Interpretation**: Points along the 45-degree diagonal line indicate perfect calibration. Systematic deviation above the diagonal = under-estimation of risk; below = over-estimation.

#### Calibration-in-the-Large (Calibration Intercept)

$$ \text{logit}(P(Y=1)) = \alpha + \text{offset(logit(predicted))} $$

- alpha = 0: perfect calibration-in-the-large (mean predicted risk = mean observed risk)
- alpha > 0: model systematically under-estimates risk
- alpha < 0: model systematically over-estimates risk

#### Calibration Slope

$$ \text{logit}(P(Y=1)) = \alpha + \beta \times \text{logit(predicted)} $$

- beta = 1: perfect calibration slope (predicted risk spread matches observed)
- beta < 1: predictions are too extreme (overfitting)
- beta > 1: predictions are not extreme enough (underfitting)

**Target**: Calibration slope 0.9-1.1.

#### Brier Score

$$ BS = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2 $$

where p_i = predicted probability, y_i = observed outcome (0/1).

- Brier score range: 0 (perfect) to 0.25 (non-informative model with 50% event rate, predicting 0.5 for everyone).
- **Target**: Brier score < 0.15.
- The Brier score can be decomposed into discrimination (how well predictions separate events from non-events) and calibration (how accurate the probabilities are). Both components will be reported.

**Scaled Brier score**: 
$$ BS_{scaled} = 1 - \frac{BS}{BS_{null}} $$ 
where BS_null is the Brier score of a model that predicts the marginal event rate for everyone. Scaled Brier score > 0 indicates improvement over the null model.

### 5.3 Model Comparison: Existing Life Expectancy Calculators

#### DeLong Test for Paired AUC Comparison

**Purpose**: Statistically compare AUCs between models evaluated on the same dataset.

**Models compared**:
1. XGBoost (Model 5) vs. Schonberg-equivalent (Model 2)
2. XGBoost (Model 5) vs. Lee-equivalent (Model 3)
3. XGBoost (Model 5) vs. Logistic regression full (Model 4)
4. Logistic regression full (Model 4) vs. Age only (Model 0)

**Method**: DeLong et al. (1988) non-parametric test for comparing correlated AUCs. Implemented via `pROC::roc.test()` in R with `method = "delong"`.

**Reporting**: Delta AUC with 95% CI and p-value for each comparison.

**Important caveats**:
- The CHARLS-based approximations of Schonberg and Lee indices are not the exact published models. The comparison should be interpreted as: "Does the addition of comprehensive geriatric assessment domains improve discrimination over models using only those variables available in standard clinical calculators?"
- DeLong test results will be reported, but the primary comparison metric is the **magnitude of delta AUC with 95% CI**, not the p-value. A non-significant p-value does not mean the models are equivalent; it means we cannot rule out that the observed difference is due to chance.

#### Integrated Discrimination Improvement (IDI)

$$ IDI = (IS_{new} - IS_{old}) - (IP_{new} - IP_{old}) $$

where IS = integral of sensitivity, IP = 1 - integral of specificity across all thresholds.

IDI quantifies the improvement in discrimination slope (difference in mean predicted probabilities between events and non-events). It is a continuous version of NRI that does not depend on arbitrary risk categories.

**Interpretation**: IDI > 0 indicates that the new model improves discrimination. Reported with 95% CI (bootstrap).

#### Net Reclassification Improvement (NRI) — Category-Free (cfNRI)

The category-free (continuous) NRI avoids the use of arbitrary risk categories, which is a major criticism of categorical NRI.

$$ cfNRI = P(\hat{p}_{new} > \hat{p}_{old} | event) - P(\hat{p}_{new} > \hat{p}_{old} | non-event) $$

- Event NRI: proportion of events where the new model assigns a higher predicted risk.
- Non-event NRI: proportion of non-events where the new model assigns a lower predicted risk.
- Overall cfNRI = event NRI + non-event NRI (range: -2 to +2).

**Target**: cfNRI >= 0.10 (pre-specified MCID).

**Reporting**: Event NRI, non-event NRI, and overall cfNRI with 95% CIs (bootstrap percentile method, 2000 replicates).

### 5.4 Decision Curve Analysis (DCA)

**Purpose**: Quantify the net benefit of using the model for clinical decision-making across a range of threshold probabilities, compared to default strategies ("screen all" and "screen none").

**Clinical context**: For PSA screening cessation, the threshold probability (pt) represents the predicted 10-year mortality risk above which a clinician would recommend stopping screening. A pt of 0.25 means: "if a man has a >25% chance of dying within 10 years, the harm of continued screening outweighs the benefit."

**Net benefit formula**:

$$ NB = \frac{TP}{N} - \frac{FP}{N} \times \frac{p_t}{1 - p_t} $$

**DCA interpretation**:
- Net benefit is plotted against threshold probability (pt) from 0.10 to 0.50.
- The model's net benefit is compared to:
  - "Screen all" (treat all prediction as "will survive 10+ years"): NB = event_rate - (1 - event_rate) * pt / (1-pt)
  - "Screen none" (treat all as "will die within 10 years" — do not screen anyone): NB = 0
- A model has clinical utility if its net benefit exceeds both default strategies over the clinically relevant threshold range.

**Pre-specified threshold range for clinical relevance**: pt = 0.15 to 0.40, which corresponds to the range where urologists and primary care physicians would consider stopping screening based on life expectancy.

**Implementation**: `rmda` or `dcurves` package in R (Vickers, 2006; Vickers & Elkin, 2006).

### 5.5 Summary of Model Performance Targets

| Metric | Target | Level |
|--------|--------|-------|
| AUC-ROC | >= 0.80 | Decision-support |
| AUC-PR | Better than Schonberg/Lee | Supplementary |
| Brier score | < 0.15 | Good calibration |
| Calibration slope | 0.90 - 1.10 | Acceptable calibration |
| Sensitivity (at optimal threshold) | >= 0.85 | Identify men with <10yr survival |
| Specificity (at optimal threshold) | >= 0.70 | Modest specificity acceptable |
| Delta AUC vs Schonberg/Lee | >= 0.03 (MCID) | Clinically meaningful improvement |
| cfNRI vs Schonberg/Lee | >= 0.10 (MCID) | Clinically meaningful reclassification |
| Net benefit (DCA) | Positive over pt 0.15-0.40 | Clinical utility demonstrated |

---

## 6. Subgroup Analyses and Interaction Testing

### 6.1 Pre-specified Subgroups

All subgroup analyses are **pre-specified** to avoid data-dredging. Five subgroups are defined:

| # | Subgroup | Stratification | Rationale |
|---|----------|---------------|-----------|
| 1 | **Age groups** | 60-65, 66-70, 71-75 | Determine model performance across the age spectrum; model should not degrade in older men where screening decisions are most critical |
| 2 | **Frailty status** | Robust (Fried 0), Pre-frail (1-2), Frail (3-5) | Frailty is expected to be a strong modifier; model should not underperform in frail men (where mortality risk is highest and screening cessation is most relevant) |
| 3 | **Urban vs. rural residence** | Urban (city/town) vs. Rural (village) | China has substantial urban-rural health disparities; model should generalize across both |
| 4 | **Education level** | Low (none/primary) vs. High (middle school+) | Education is a proxy for health literacy and healthcare access; may affect self-reported data quality and mortality |
| 5 | **Multimorbidity burden** | Low (<2 conditions), Medium (2-4), High (>=5) | Tests model performance across the full multimorbidity spectrum |

### 6.2 Subgroup Analysis Plan

For each subgroup:

1. **AUC-ROC** and **Brier score** within the subgroup (from model trained on the FULL dataset, tested within the subgroup). This assesses whether the model's discrimination and calibration are consistent across subgroups.
2. **Calibration plot** stratified by subgroup: predicted risk (x-axis) vs observed event rate (y-axis), with separate curves for each subgroup level. This assesses whether the model is equally well-calibrated across subgroups.
3. **Subgroup-stratified ROC curves**: ROC curves for each subgroup level, to visualize whether discrimination differs.

### 6.3 Interaction Testing

For the logistic regression baseline model (Model 4), formal interaction tests will be performed:

$$ \text{logit}(P(death)) = \text{main effects} + \text{subgroup} + \text{predictor} \times \text{subgroup} $$

where predictor = frailty score (continuous) or Charlson CCI (continuous), and subgroup = age group, education, or urban/rural.

For XGBoost, SHAP interaction values will be explored: SHAP dependence plots for key predictors (e.g., frailty score) with subgroup (e.g., age group) as the color variable to visualize potential interactions without formal hypothesis testing.

**Multiplicity**: With 5 pre-specified subgroups, no formal multiplicity correction is applied for subgroup analyses, consistent with the exploratory (hypothesis-generating) nature of subgroup analyses. Results will be explicitly labeled as exploratory.

---

## 7. Sensitivity Analyses

### 7.1 Sensitivity 1: Complete-Case Analysis vs. MICE

**Purpose**: Assess whether the MICE imputation procedure (which assumes MAR) produces results consistent with complete-case analysis.

**Method**: All primary analyses (Models 0-5) repeated on:
- Complete-case dataset (N ≈ 2,000-2,400)
- MICE-imputed dataset (primary, N ≈ 2,800)

**Comparison**: AUC, Brier score, and calibration metrics compared between CCA and MICE. If the difference in AUC >= 0.02 or if model rankings change, this suggests that the missing data mechanism may not be MAR, and the complete-case results should be reported alongside the primary MICE results.

### 7.2 Sensitivity 2: LASSO-Based Feature Selection vs. Full Model

**Purpose**: Assess whether a parsimonious LASSO-selected model achieves similar performance to the full-feature model. This has clinical relevance: a model with 8-10 features is more deployable than one with 25+ features.

**Method**:
- LASSO logistic regression with lambda selected by 10-fold CV (1-SE rule).
- Features retained by LASSO reported.
- Model performance (AUC, Brier score) of LASSO-selected features compared to full-feature model.
- If LASSO-selected model performs within delta AUC = 0.02 of the full model, the parsimonious model will be presented as a clinically practical alternative.

### 7.3 Sensitivity 3: Excluding Deaths in First 2 Years

**Purpose**: Address potential reverse causality — some participants may be approaching end of life at baseline (undiagnosed terminal illness, severe frailty leading to imminent death). Including these individuals could overestimate model performance because the model may learn to identify the actively dying rather than predict long-term mortality risk.

**Method**:
- Exclude all participants who died within 2 years of baseline.
- Re-estimate Models 0-5 on the remaining sample.
- Compare AUC and calibration to the primary analysis.

**Expected impact**: Modest reduction in AUC (perhaps 0.02-0.04) if reverse causality is present. If AUC drops substantially (>0.05), this suggests the model's discrimination was partly driven by identifying imminent death rather than long-term risk, which would diminish its clinical utility for screening cessation decisions (which require 10-year prediction).

### 7.4 Sensitivity 4: E-value for Unmeasured Confounding

**Purpose**: Quantify the robustness of the primary association (e.g., frailty as a predictor of mortality) to unmeasured confounding.

**E-value definition** (VanderWeele & Ding, 2017): The minimum strength of association that an unmeasured confounder would need to have with both the exposure (e.g., frailty) and the outcome (mortality) to fully explain away the observed association, conditional on measured covariates.

**Method**:
- For the logistic regression baseline (Model 4), compute the E-value for the frailty score coefficient (the strongest geriatric predictor).
- E-value formula: $$ E\text{-}value = OR + \sqrt{OR \times (OR - 1)} $$
  where OR is the odds ratio for frailty (adjusted for all covariates).
- Report: "An unmeasured confounder associated with both frailty and mortality by an odds ratio of at least E-value each, above and beyond the measured covariates, could explain away the frailty-mortality association. The E-value for the confidence interval limit closest to the null quantifies the confounding strength needed to shift the CI to include the null."

**Interpretation**: Large E-values (e.g., >3.0) suggest that unmeasured confounding is unlikely to fully explain the association. Small E-values (e.g., <1.5) suggest that modest unmeasured confounding could explain the result.

**Limitation**: E-value is a single-number summary and cannot capture complex confounding structures. It applies to the exposure-outcome association, not directly to model discrimination metrics.

### 7.5 Sensitivity 5: Model Excluding Blood Biomarkers

**Purpose**: Blood biomarkers are available only for a subset (~60-70%) of CHARLS participants. Assess whether including biomarkers (CRP, albumin, hemoglobin, eGFR) meaningfully improves model performance, to determine whether the added cost and complexity of blood collection is justified.

**Method**:
- Compare two XGBoost models, both trained on the complete-case biomarker subsample:
  - Model A: all predictors EXCEPT blood biomarkers
  - Model B: all predictors INCLUDING blood biomarkers
- Compare AUC, Brier score, and NRI between Model A and Model B.
- If Model B does not achieve delta AUC >= 0.02 or cfNRI >= 0.05, conclude that blood biomarkers do not add clinically meaningful predictive value in this population.

### 7.6 Sensitivity 6: Alternative Frailty Operationalization (Frailty Index)

**Purpose**: The Fried frailty phenotype (5 components) is one frailty operationalization. A deficit-accumulation Frailty Index (FI) may provide finer risk discrimination.

**Method**:
- Construct a Frailty Index from >=30 health deficit items available in CHARLS (covering chronic diseases, functional limitations, symptoms, lab abnormalities, cognitive and psychological items).
- FI = (number of deficits present) / (total number of deficits assessed).
- Replace the 5 Fried components with FI in Models 4-5.
- Compare model performance with Fried vs. FI operationalization.

**Note**: This sensitivity analysis is conditional on successful construction of a valid FI (>=30 items with adequate data quality) from CHARLS variables.

### 7.7 Sensitivity 7: Temporal Validation Using Wave 1 as Training, Wave 2 as Testing

**Purpose**: Assess temporal generalizability — does the model trained on 2011 data predict mortality in the 2013 cohort?

**Method**:
- Train models on Wave 1 (2011) baseline → 10-year follow-up (note: grip strength not available in Wave 1, so Fried phenotype will use grip strength proxy OR grip strength excluded).
- Test on Wave 2 (2013) baseline → predict 2023 mortality.
- This is a stronger test of generalizability than internal cross-validation because it evaluates performance on a temporally distinct cohort.

**Limitation**: Grip strength was not measured in Wave 1, so the predictor set will differ between training and testing. This analysis is therefore primarily useful for assessing temporal transportability rather than exact model replication.

---

## 8. Reporting Standards

### 8.1 TRIPOD Compliance

This SAP is designed to comply with the **TRIPOD (Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis or Diagnosis)** statement, specifically the TRIPOD Type 1a (development only) or Type 1b (development and validation using resampling) guidelines.

Key TRIPOD items addressed:
- Item 4a: Data source and dates (Section 1.2)
- Item 4b: Eligibility criteria (Section 1.3)
- Item 5a: Handling of predictors (Section 4.4-4.5)
- Item 5b: Handling of outcome (Section 1.4)
- Item 5c: Sample size (Section 2)
- Item 6a: Missing data (Section 4.4)
- Item 7a: Model development (Section 4.2-4.3)
- Item 7b: Model specification (Section 4.2)
- Item 8: Model performance (Section 5)
- Item 10a: Model performance measures with CIs (Section 5)
- Item 10b: Subgroup performance (Section 6)
- Item 10d: Calibration (Section 5.2)
- Item 12: Model use (Section 5.4, DCA)
- Item 15a: Overall interpretation (to be completed after analysis)
- Item 16: Limitations (to be completed after analysis)

### 8.2 Effect Size Reporting

**All results will be reported with effect sizes and 95% confidence intervals, not solely with p-values.** The following language is prohibited in all outputs:

- "The difference was statistically significant (p < 0.05)" — instead use: "XGBoost achieved a higher AUC than the Schonberg-equivalent model (delta AUC = 0.04, 95% CI: 0.02 to 0.06)"
- "p < 0.001" without effect size — always accompanied by the estimated effect and its uncertainty.

### 8.3 Figures and Tables Plan

| Table/Figure | Content |
|-------------|---------|
| **Table 1** | Baseline characteristics by 10-year mortality status |
| **Table 2** | Model discrimination and calibration metrics (all 6 models) |
| **Table 3** | Model comparison: DeLong test, IDI, cfNRI |
| **Table 4** | Subgroup-specific AUC and Brier scores |
| **Table 5** | Sensitivity analyses summary |
| **Figure 1** | Study flow diagram (CONSORT-style) |
| **Figure 2** | ROC curves: Models 0-5 on the same plot |
| **Figure 3** | Calibration plots: XGBoost (Model 5) vs. logistic regression (Model 4) |
| **Figure 4** | Decision curve analysis: XGBoost, logistic regression, Schonberg/Lee, treat-all, treat-none |
| **Figure 5** | SHAP summary plot (feature importance) |
| **Figure 6** | SHAP dependence plots (top 5 features) |
| **Figure 7** | Subgroup calibration plots |
| **Supplementary Figures** | Per-wave attrition, sensitivity analyses, imputation diagnostics |

---

## 9. Software and Packages

### 9.1 Primary Software Environment

**R version 4.3+** (or latest stable release at time of analysis).

R is preferred over Python for this project because:
1. The `mice` package for multiple imputation is the most mature implementation available.
2. The `pROC` package provides the standard DeLong test implementation.
3. TRIPOD-compliant prediction model reporting tools (e.g., `rms`, `predictABEL`) are better developed in R.
4. CHARLS data processing pipelines in the team's existing infrastructure are R-based.

Python 3.x (with `scikit-learn`, `xgboost`, `shap`, `optuna`) is an acceptable alternative if preferred by the ML Engineer, with the imputation workflow handled in R and results exchanged via CSV.

### 9.2 Key Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `xgboost` | >= 1.7 | Primary ML model |
| `mice` | >= 3.16 | Multiple imputation |
| `pROC` | >= 1.18 | ROC curves, DeLong test |
| `rms` | >= 6.7 | Logistic regression, calibration, restricted cubic splines |
| `PredictABEL` | >= 1.2 | IDI, NRI computation |
| `dcurves` or `rmda` | >= 0.4 | Decision curve analysis |
| `SHAPforxgboost` or `shapr` | >= 0.1 | SHAP values for XGBoost |
| `tableone` | >= 0.13 | Baseline characteristics table (SMD) |
| `ggplot2` | >= 3.4 | All visualizations |
| `caret` or `tidymodels` | >= 6.0 | Cross-validation framework |
| `EValue` | >= 4.1 | E-value computation |
| `glmnet` | >= 4.1 | LASSO logistic regression |
| `survival` | >= 3.5 | Survival objects for imputation |
| `doParallel` / `future` | >= 1.0 | Parallel computing for nested CV |

### 9.3 Reproducibility

- **Random seed**: Set at the beginning of the analysis script (`set.seed(20260507)`) and recorded.
- **Session info**: `sessionInfo()` output saved to a log file.
- **Package versions**: Full `renv` lockfile or `packrat` snapshot maintained.
- **Code**: All analysis code version-controlled in the project repository.
- **Data version**: CHARLS data release version and download date recorded in the analysis log.

---

## 10. Analysis Timeline and Dependencies

| Step | Task | Dependencies | Estimated Duration |
|------|------|-------------|-------------------|
| 1 | CHARLS data extraction and cleaning | Data Engineer: variable map | Week 1-2 |
| 2 | Predictor variable construction (Fried, CCI, MMSE) | Step 1 | Week 2-3 |
| 3 | Outcome variable construction (10-year mortality) | Step 1 | Week 2-3 |
| 4 | MICE imputation | Step 2-3 | Week 3-4 |
| 5 | Baseline characteristics (Table 1) | Step 2-3 | Week 4 |
| 6 | Logistic regression models (0-4) | Step 4 | Week 4-5 |
| 7 | XGBoost nested CV (Model 5) | Step 4 | Week 4-5 |
| 8 | Model evaluation (AUC, calibration, DCA) | Steps 6-7 | Week 5-6 |
| 9 | Model comparison (DeLong, IDI, NRI) | Step 8 | Week 6 |
| 10 | Subgroup analyses | Step 7 | Week 6-7 |
| 11 | Sensitivity analyses (1-7) | Step 7 | Week 7-8 |
| 12 | SHAP analysis | Step 7 | Week 7 |
| 13 | Tables and figures | Steps 8-12 | Week 8-9 |
| 14 | Statistical report | Steps 13 | Week 9-10 |

---

## 11. Protocol Amendments and Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-05-07 | Initial SAP | Biostatistician Agent |

All amendments to this SAP after analysis begins will be:
1. Documented with date, rationale, and author.
2. Reported in the final manuscript as post-hoc or protocol-deviation analyses.
3. Distinguished from pre-specified analyses in all tables and figures.

---

## References (Methodological)

1. DeLong ER, DeLong DM, Clarke-Pearson DL. Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach. *Biometrics*. 1988;44(3):837-845.
2. Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR. A simulation study of the number of events per variable in logistic regression analysis. *J Clin Epidemiol*. 1996;49(12):1373-1379.
3. van der Ploeg T, Austin PC, Steyerberg EW. Modern modelling techniques are data hungry: a simulation study for predicting dichotomous endpoints. *BMC Med Res Methodol*. 2014;14:137.
4. van Buuren S, Groothuis-Oudshoorn K. mice: Multivariate Imputation by Chained Equations in R. *J Stat Softw*. 2011;45(3):1-67.
5. White IR, Royston P. Imputing missing covariate values for the Cox model. *Stat Med*. 2009;28(15):1982-1998.
6. Cawley GC, Talbot NLC. On over-fitting in model selection and subsequent performance bias in performance evaluation. *J Mach Learn Res*. 2010;11:2079-2107.
7. Varma S, Simon R. Bias in error estimation when using cross-validation for model selection. *BMC Bioinformatics*. 2006;7:91.
8. Steyerberg EW. *Clinical Prediction Models: A Practical Approach to Development, Validation, and Updating*. Springer; 2009.
9. Harrell FE. *Regression Modeling Strategies*. 2nd ed. Springer; 2015.
10. Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. *Med Decis Making*. 2006;26(6):565-574.
11. Vickers AJ, Cronin AM, Elkin EB, Gonen M. Extensions to decision curve analysis, a novel method for evaluating diagnostic tests, prediction models and molecular markers. *BMC Med Inform Decis Mak*. 2008;8:53.
12. Pencina MJ, D'Agostino RB Sr, D'Agostino RB Jr, Vasan RS. Evaluating the added predictive ability of a new marker: from area under the ROC curve to reclassification and beyond. *Stat Med*. 2008;27(2):157-172.
13. Pencina MJ, D'Agostino RB Sr, Steyerberg EW. Extensions of net reclassification improvement calculations to measure usefulness of new biomarkers. *Stat Med*. 2011;30(1):11-21.
14. VanderWeele TJ, Ding P. Sensitivity analysis in observational research: introducing the E-value. *Ann Intern Med*. 2017;167(4):268-274.
15. Lundberg SM, Lee SI. A unified approach to interpreting model predictions. *Adv Neural Inf Process Syst*. 2017;30.
16. Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis or Diagnosis (TRIPOD): the TRIPOD statement. *Ann Intern Med*. 2015;162(1):55-63.
17. Schonberg MA, Davis RB, McCarthy EP, Marcantonio ER. Index to predict 5-year mortality of community-dwelling adults aged 65 and older using data from the National Health Interview Survey. *J Gen Intern Med*. 2009;24(10):1115-1122.
18. Lee SJ, Lindquist K, Segal MR, Covinsky KE. Development and validation of a prognostic index for 4-year mortality in older adults. *JAMA*. 2006;295(7):801-808.
19. Rubin DB. *Multiple Imputation for Nonresponse in Surveys*. Wiley; 1987.
20. Obuchowski NA, McClish DK. Sample size determination for diagnostic accuracy studies involving binormal ROC curve indices. *Stat Med*. 1997;16(13):1529-1542.
21. CHARLS Research Team. China Health and Retirement Longitudinal Study: 2013 National Baseline (Wave 2) Users' Guide. National School of Development, Peking University; 2015.

---

## Appendix: Key Statistical Formulas

### DeLong Test (Two Correlated AUCs)

$$ Z = \frac{AUC_1 - AUC_2}{\sqrt{Var(AUC_1) + Var(AUC_2) - 2Cov(AUC_1, AUC_2)}} $$

where variance and covariance are estimated using U-statistics theory as described in DeLong et al. (1988). The correlation between the two AUC estimates is a function of the correlation between the two sets of prediction scores. In practice, the correlation between predictions from two mortality models on the same data is high (>0.70), which increases the power of the DeLong test.

### Net Reclassification Improvement (Category-Free)

$$ cfNRI_{event} = \frac{\sum_{i: event} I(\hat{p}_{new,i} > \hat{p}_{old,i}) - \sum_{i: event} I(\hat{p}_{new,i} < \hat{p}_{old,i})}{N_{events}} $$

$$ cfNRI_{non-event} = \frac{\sum_{i: non-event} I(\hat{p}_{new,i} < \hat{p}_{old,i}) - \sum_{i: non-event} I(\hat{p}_{new,i} > \hat{p}_{old,i})}{N_{non-events}} $$

$$ cfNRI = cfNRI_{event} + cfNRI_{non-event} \quad (\text{range: } -2 \text{ to } +2) $$

### Integrated Discrimination Improvement

$$ IDI = (\bar{\hat{p}}_{events}^{new} - \bar{\hat{p}}_{non-events}^{new}) - (\bar{\hat{p}}_{events}^{old} - \bar{\hat{p}}_{non-events}^{old}) $$

where $\bar{\hat{p}}$ is the mean predicted probability in each group. IDI > 0 indicates that the new model improves the separation between events and non-events.

### E-value

For an observed odds ratio OR > 1:

$$ E\text{-value} = OR + \sqrt{OR \times (OR - 1)} $$

For the confidence interval limit closest to the null (OR_CI):

$$ E\text{-value}_{CI} = OR_{CI} + \sqrt{OR_{CI} \times (OR_{CI} - 1)} \quad \text{(if } OR_{CI} > 1\text{)} $$

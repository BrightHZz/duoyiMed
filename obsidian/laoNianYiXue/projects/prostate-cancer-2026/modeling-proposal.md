---
type: modeling-proposal
project: prostate-cancer-2026
topic: "ML-Based 10-Year Life Expectancy Prediction to Guide PSA Screening Cessation"
author: Computational Biologist
date: 2026-05-07
status: draft
version: 1.0
---

# Modeling Proposal: ML-Based 10-Year Life Expectancy Prediction to Guide PSA Screening Cessation in Older Chinese Men

---

## Executive Summary

**ML Task**: Supervised binary classification (primary) + survival analysis (complementary)

**Primary Model**: XGBoost with SHAP interpretability

**Expected Performance**: AUC >= 0.80, Brier score < 0.15, delta AUC >= 0.03 over Schonberg/Lee indices

**Validation**: Nested 5-fold CV (outer evaluation, inner tuning) + temporal validation

**Key Risk**: Age confounding; mitigated via incremental AUC decomposition and age-stratified subgroup analysis

---

## 1. Clinical-to-ML Mapping

### 1.1 PICO-ML Translation

```
Clinical PICO                           →  ML Formalization
─────────────────────────────────────────────────────────────────
P: Chinese men aged 60-75,              →  Training instances:
   community-dwelling                      ~2,500-3,500 CHARLS Wave 2 (2013) participants

I: Geriatric assessment across           →  Feature matrix X:
   5 domains (frailty, multimorbidity,      ~30-40 predictors from 10 domains
   function, cognition, psychology)

C: Existing life expectancy              →  Baseline comparator:
   calculators (Schonberg, Lee)             Logistic regression models using Schonberg/Lee
                                            variables only; benchmark performance

O: 10-year all-cause mortality           →  Binary label y ∈ {0,1}:
   (died 2013-2023)                         1 = died within 10 years of baseline
                                            0 = survived >= 10 years (or censored alive)
```

### 1.2 ML Task Selection: Binary Classification vs. Survival Analysis

#### Primary Task: Binary Classification (died within 10 years: yes/no)

**Rationale for primacy of binary classification**:

1. **Direct clinical alignment**: The guideline-recommended decision is inherently binary -- "life expectancy <10 years → stop screening." The USPSTF, AUA, EAU, and NCCN all use a 10-year life expectancy threshold to determine screening cessation. A binary classifier at this exact threshold directly answers the clinical question.

2. **Interpretability for clinical use**: SHAP values on a binary outcome provide a clear, threshold-level risk probability that clinicians can act on: "This patient has a predicted 65% probability of dying within 10 years → PSA screening is unlikely to provide net benefit." In contrast, survival curves require clinicians to mentally interpolate to the 10-year mark.

3. **Performance metric alignment**: AUC-ROC is well-understood in clinical ML literature and directly addresses "discrimination" -- the ability to separate men who will vs. will not die within 10 years. The target AUC >= 0.80 is a well-established threshold for clinical decision-support tools.

4. **Facilitates direct comparison with Schonberg and Lee indices**: Both existing calculators were developed and validated using binary mortality outcomes at fixed horizons (10-year for Lee, various horizons for Schonberg). Binary classification enables head-to-head comparison on the same metric.

5. **Avoids proportional hazards assumption**: The Cox PH assumption is unlikely to hold when geriatric predictors (frailty, function) are included -- these have time-varying effects. Binary classification at a fixed horizon side-steps this issue.

6. **Handles the clinical reality of "stop screening"**: The decision to stop screening is made at a single point in time (the clinical encounter), not continuously updated. A binary classifier at a fixed horizon matches the decision structure.

#### Complementary Task: Survival Analysis (time-to-death, months)

**When survival analysis adds value**:

1. **Handles censoring explicitly**: In the 2013-2023 follow-up, some men will be lost to follow-up before the 10-year mark (emigration, refusal, administrative censoring). Binary classification must either exclude them or treat them as "alive" (potential outcome misclassification). Survival analysis models the censoring mechanism and uses partial likelihood to extract information from censored observations.

2. **Produces flexible time horizons**: A survival model can predict the probability of death at any time point (5-year, 7-year, 10-year, 15-year), supporting sensitivity analyses for different screening cessation thresholds. Some guidelines use 7-year rather than 10-year thresholds for certain populations.

3. **Enables dynamic risk assessment**: A patient's survival curve shows how risk accumulates over time, which can inform discussions about "when" (not just "whether") to stop screening.

4. **Provides complementary performance metrics**: C-index (Harrell's concordance) for survival models is analogous to AUC-ROC and provides a second, independent measure of discrimination.

**Recommended approach**: Develop both binary classification and survival analysis models in parallel. The binary classifier is the primary model for direct clinical decision support. The survival model serves as (a) a sensitivity analysis to assess the impact of censoring on binary classification results, (b) a source of complementary evidence for model discrimination, and (c) a tool for analyses at alternative time horizons.

#### When Each Approach is Most Appropriate

| Scenario | Recommended Approach | Reason |
|----------|---------------------|--------|
| Point-of-care screening cessation decision | Binary classification | Directly answers "stop or continue?" |
| Censoring rate > 15% | Survival analysis (primary) | Binary outcomes may be biased if censoring is non-ignorable |
| Need for dynamic risk prediction at multiple horizons | Survival analysis | Single model produces predictions at any time t |
| External validation against Schonberg/Lee | Binary classification | Aligns with how these indices were developed and validated |
| Model interpretability (SHAP) | Binary classification | SHAP values on binary probability are more intuitive for clinicians than SHAP on hazard |
| Sensitivity to time-varying covariate effects | Survival analysis (RSF/DeepSurv) | Flexible modeling of non-proportional hazards |

**Final recommendation**: **Binary classification is the primary analysis.** Survival analysis is a pre-specified complementary analysis that serves as a robustness check. The binary classifier is what gets deployed in the clinical decision support tool.

---

## 2. Data Overview

### 2.1 Data Source

| Attribute | Detail |
|-----------|--------|
| Cohort | China Health and Retirement Longitudinal Study (CHARLS) |
| Baseline | Wave 2 (2013) -- first wave with grip strength measurement |
| Population | Male participants, age 60-75 at baseline |
| Follow-up | Wave 3 (2015), Wave 4 (2018), Wave 5 (2020), plus exit interviews through 2023 |
| Mortality ascertainment | Exit interviews with family members/neighbors; vital status tracking across all waves |
| Expected N | ~2,500-3,500 with complete data on core predictors |
| Expected events | ~750-1,400 (30-40% 10-year mortality) |
| Blood subsample | ~60-70% of participants have CRP, albumin |

### 2.2 Predictor Domains and Variable Count

| Domain | Number of Features | Variables |
|--------|-------------------|-----------|
| Demographics | 4 | Age, education (years/categorical), urban/rural (binary), marital status (binary) |
| Fried Frailty | 6 | 5 individual components (binary: yes/no for each) + composite score (0-5) |
| Multimorbidity | 2-3 | Charlson CCI score (continuous) + individual disease flags (if exploratory) |
| Functional Status | 4 | ADL score (0-6), IADL score (continuous), grip strength (kg), gait speed (m/s) |
| Cognitive | 3 | MMSE (education-adjusted), immediate word recall, delayed word recall |
| Psychological | 1 | CES-D-10 score (0-30) |
| Anthropometric | 3 | BMI (kg/m^2), height (cm), weight (kg) -- note: BMI is derived, may be collinear |
| Medication | 1 | Polypharmacy (>=5 meds: binary) |
| Lifestyle | 2 | Smoking status (never/former/current), alcohol use (never/moderate/heavy) |
| Self-rated Health | 1 | Self-rated health (5-level ordinal) |
| Blood Biomarkers | 2 | CRP (mg/L, log-transformed), albumin (g/dL) |
| **Total** | **~29-31** | (excluding blood biomarkers: ~27-29) |

### 2.3 Features-to-Events Ratio Assessment

```
Primary analysis (without blood biomarkers):
  ~27-29 features / ~750-1,400 events → 26-52 events per feature

Sensitivity analysis (with blood biomarkers):
  ~29-31 features / ~750-1,400 events → 24-48 events per feature
```

**Verdict**: Well above the conventional threshold of 10-20 events per variable (EPV) for logistic regression. For XGBoost with regularization, this EPV is comfortable. The risk of overfitting from insufficient events is low.

**Caveats for XGBoost**: EPV is a concept developed for logistic regression. For tree-based models, the relevant concern is not EPV but the minimum samples per leaf relative to event count. With ~1,000 events and a typical `min_child_weight` of 1-3, we maintain >= 300-1,000 events per terminal node, which is acceptable.

---

## 3. Method Design

### 3.1 Baseline Models (Performance Anchors)

All baseline models serve as performance floors. The primary model must demonstrate clinically meaningful improvement over the best baseline.

#### Model 0: Age-Only Logistic Regression

```
y ~ age
```

**Purpose**: Quantify how much discrimination comes from chronological age alone. This is the absolute minimum a model must beat. If geriatric predictors do not meaningfully improve over age alone, the model has no clinical value.

#### Model 1: Age + Charlson CCI -- Logistic Regression

```
y ~ age + charlson_cci
```

**Purpose**: Represent the "standard primary care" level of prediction. Most clinicians estimate life expectancy based on age and comorbidity count alone. This is the current standard of care against which geriatric-enhanced prediction must demonstrate value.

#### Model 2: Schonberg Index Variables -- Logistic Regression

**Predictors** (Schonberg et al., J Gen Intern Med 2011):
- Age
- Sex (all male in our cohort)
- BMI
- Smoking status
- Current cancer (excluded from our population)
- Diabetes mellitus
- COPD
- Heart disease
- Functional impairment (ADL)
- Self-rated health
- Hospitalization in past year
- Surrogate for hospitalization: available in CHARLS (da007 health service utilization)

**Implementation**: Replicate Schonberg index in CHARLS cohort using logistic regression with the same predictor set. This provides a direct calibration benchmark against the current clinical standard.

**Caveat**: The Schonberg index was developed in US adults aged 65+. Its calibration in Chinese community-dwelling adults aged 60-75 is unknown. We will assess both discrimination (AUC) and calibration (Brier score, calibration plots) of the Schonberg index in our CHARLS cohort.

#### Model 3: Lee Index Variables -- Logistic Regression

**Predictors** (Lee et al., JAMA 2006):
- Age
- Sex (all male)
- BMI
- Smoking status
- Diabetes mellitus
- COPD/cancer/heart failure/renal disease (any)
- Functional impairment (ADL and mobility)
- Self-rated health

**Implementation**: Replicate Lee index in CHARLS cohort. Same caveats as Schonberg regarding population transportability.

#### Baseline Survival Models: Cox Proportional Hazards

For the complementary survival analysis, implement Cox PH versions of Models 0-3 using the same predictor sets. This provides survival-based baselines for comparison with RSF and other advanced survival models.

### 3.2 Primary Model: XGBoost Binary Classification

#### Justification for XGBoost

XGBoost is the recommended primary model for this specific scenario (tabular data, moderate N, ~30 features, binary outcome with ~1,000 events). The justifications span four dimensions:

**1. Methodological Fit**

| Characteristic | XGBoost | Logistic Regression | Random Forest | DeepSurv/DeepHit |
|---------------|---------|---------------------|---------------|------------------|
| Handles non-linear relationships | Yes (inherent) | Requires manual specification (splines, polynomials) | Yes | Yes |
| Automatic interaction discovery | Yes | No | Yes (implicit) | Yes (implicit) |
| Handles mixed data types (continuous, binary, ordinal) | Yes | Yes | Yes | Yes (with embedding) |
| Robust to irrelevant features | Yes (feature importance-based splitting) | No (all features in model) | Moderate (random subspace) | Requires regularization |
| Handles moderate N (~3,000) | Excellent | Excellent | Good (less efficient) | Moderate (data-hungry) |
| Handles ~30 features | Excellent (this is XGBoost's sweet spot) | Adequate | Good | Moderate (may overfit) |
| Interpretability tooling | SHAP (mature, well-validated) | Odds ratios / marginal effects | SHAP / permutation importance | SHAP (less mature for DL survival) |
| Computational cost | Low (minutes on CPU) | Very low (seconds) | Low-moderate | High (GPU recommended) |

**2. Empirical Performance**

In clinical prediction benchmarks with tabular data and N < 10,000:
- XGBoost typically outperforms logistic regression by delta AUC 0.02-0.06 when non-linear relationships or interactions are present
- XGBoost and Random Forest perform similarly, but XGBoost tends to have better calibration (due to its boosting objective function being a proper scoring rule)
- Deep learning (DeepSurv, DeepHit) rarely outperforms XGBoost at N < 5,000 and fewer than 100 features

**3. Interpretability for Clinical Deployment**

SHAP (SHapley Additive exPlanations) provides:
- **Global feature importance**: Which geriatric domains matter most for predicting 10-year mortality?
- **Individual-level explanations**: For THIS patient, why is the predicted mortality risk 65%? Which predictors drive the risk up (frailty components, low MMSE) and which drive it down (good grip strength, never smoked)?
- **Interaction effects**: Does frailty amplify the mortality risk of multimorbidity? SHAP interaction values quantify and visualize these synergies.

SHAP on XGBoost is more mature and well-validated than SHAP on deep learning models for tabular data.

**4. Reproducibility and Deployment**

- XGBoost is deterministic given a fixed seed (unlike some deep learning approaches with stochastic optimization)
- XGBoost models are lightweight (a few MB), easily serialized (pickle/JSON), and deployable in EHR systems
- XGBoost does not require GPU for inference, making it suitable for resource-constrained clinical settings in China

**Alternative considered but not selected**:

- **Random Forest**: Would be acceptable. The key disadvantage vs. XGBoost is that RF averages trees rather than iteratively correcting errors. For mortality prediction where some predictors (age, frailty) have very strong signals and others (lifestyle, self-rated health) have weaker signals, boosting's ability to focus on hard cases is advantageous. RF remains a pre-specified sensitivity analysis.

- **Elastic Net Logistic Regression**: Would be acceptable. The key disadvantage is that it cannot automatically capture non-linearities or interactions. If we pre-specify splines for age and frailty-by-age interactions, Elastic Net becomes competitive but loses the "automatic" advantage. Elastic Net remains a pre-specified sensitivity analysis for linear model comparison.

#### Hyperparameter Tuning Strategy

**Bayesian optimization with Tree-structured Parzen Estimator (TPE)** using Optuna (preferred) or `hyperopt`:

| Parameter | Search Range | Rationale |
|-----------|-------------|-----------|
| `n_estimators` | 100-1,000 | Ensemble size; more trees needed if learning rate is low |
| `learning_rate` | 0.01-0.30 (log-uniform) | Lower learning rate with more trees generally improves calibration |
| `max_depth` | 2-8 | Restrict to prevent overfitting; with ~30 features, trees deeper than 8 may model noise |
| `min_child_weight` | 1-20 | Higher values regularize; important with ~1,000 events to avoid leaves with too few samples |
| `subsample` | 0.6-1.0 | Row subsampling for regularization |
| `colsample_bytree` | 0.6-1.0 | Column subsampling for regularization |
| `reg_alpha` | 1e-8 to 10 (log-uniform) | L1 regularization on leaf weights |
| `reg_lambda` | 1e-8 to 10 (log-uniform) | L2 regularization on leaf weights |
| `scale_pos_weight` | Calculated as (negatives / positives) | Handles class imbalance if event rate is not ~50% |

**Tuning objective**: Maximize AUC-ROC on inner validation folds (see Section 6 for nested CV design).

**Calibration-specific tuning**: After selecting the best model by AUC, optionally re-tune with Brier score as the objective to ensure calibration quality. This is a sensitivity analysis; the primary approach is to tune for discrimination and then assess calibration of the selected model.

**Fixed parameters**:
- `objective = 'binary:logistic'` (produces probability estimates)
- `eval_metric = 'auc'` (matches primary evaluation metric)
- `tree_method = 'hist'` (fast histogram-based algorithm)
- `random_state = 42` (reproducibility)
- `early_stopping_rounds = 50` (prevents overfitting; evaluated on inner validation fold)

### 3.3 Advanced Models (for Comparison)

#### Random Survival Forest (RSF)

**Purpose**: Primary complementary model for the survival analysis. RSF does not assume proportional hazards, which is a concern when geriatric predictors (frailty, function) are included.

**Implementation**: `scikit-survival` or `randomForestSRC` (R). Tune: `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf`.

**When RSF may outperform Cox**: If frailty has a strong early effect (< 5 years) that attenuates over time (because the frail die early), the hazard ratio is time-varying and Cox PH is misspecified. RSF is not constrained by the PH assumption.

#### DeepSurv (Optional)

**Purpose**: Neural network extension of Cox PH for comparison. Allows non-linear and interactive effects while maintaining the proportional hazards structure.

**Implementation**: `pycox` or custom PyTorch. Architecture: 2-3 hidden layers (64, 32, 16) with ReLU, dropout (0.2-0.3), batch normalization.

**Precondition for use**: Requires N >= 3,000 with sufficient events for stable training. If the final analytic sample is at the lower end of the expected range (~2,500), DeepSurv will be deprioritized or run as exploratory only.

**Risk**: Deep learning with moderate N risks overfitting. Mitigation: early stopping, dropout, weight decay, and comparison of training vs. validation loss curves.

#### Stacking Ensemble (Optional)

**Purpose**: Combine predictions from multiple model classes (logistic regression, XGBoost, Random Forest) via a meta-learner.

**Architecture**:
- Level 0 (base learners): XGBoost, Random Forest, Elastic Net
- Level 1 (meta-learner): Logistic regression (simple, calibrated)

**When to use**: If individual models have comparable discrimination but different calibration profiles, stacking may produce a model with both high discrimination and good calibration. However, stacking sacrifices the clean SHAP interpretability of XGBoost alone. For this reason, stacking is reserved as an exploratory analysis.

### 3.4 Feature Selection

**Pre-specified full-inclusion approach** (primary):

All ~30 predictors are included in the model. This is the recommended approach per TRIPOD guidelines for prediction model development when the number of predictors is modest relative to the number of events. Variable selection driven by p-values or stepwise procedures is explicitly **not** recommended because it:
1. Produces biased regression coefficients (selection bias)
2. Produces over-optimistic performance estimates
3. Is unstable across samples (small changes in data produce different selected feature sets)

**LASSO sensitivity analysis**:

As a sensitivity analysis, apply LASSO logistic regression to identify the subset of features selected by L1 regularization. Compare:
- The feature set selected by LASSO vs. the full model's SHAP importance ranking
- The discrimination (AUC) of the LASSO-selected model vs. the full feature model
- Whether LASSO "drops" any clinically important geriatric domains

This sensitivity analysis addresses the concern: "Are all these geriatric variables actually needed, or can we simplify?"

### 3.5 SHAP Interpretability Analysis

This is **not optional** -- it is a core deliverable. The model must be interpretable to be clinically actionable.

#### Global Feature Importance

- **Mean |SHAP| bar plot**: Rank all 30 features by their average impact on mortality prediction.
- **Hypothesis**: Frailty components, multimorbidity, and functional status will be among the top predictors, after age. If age dominates and geriatric features have near-zero SHAP, the model is not adding clinical value.

#### SHAP Dependence Plots

For each of the top 10 features:
- Plot SHAP value vs. feature value
- Color-code by age (to visualize age interactions)
- **Key plots to produce**:
  - SHAP vs. grip strength, colored by age: Does low grip strength have the same mortality implication at 65 vs. 75?
  - SHAP vs. Charlson CCI, colored by frailty status: Does multimorbidity matter more in the frail?
  - SHAP vs. gait speed: Is there a threshold effect (e.g., gait speed < 0.6 m/s is particularly ominous)?

#### SHAP Interaction Values

- **Pre-specified interaction**: Frailty (composite or components) x Age
  - Hypothesis: Frailty amplifies age-related mortality risk. A 65-year-old with frailty may have the mortality risk of a 75-year-old without frailty.
- **Pre-specified interaction**: Multimorbidity x Frailty
  - Hypothesis: Multimorbidity in the context of frailty ("frail multimorbidity") is more lethal than multimorbidity alone.
- **SHAP-discovered interactions**: Identify the top 3-5 interactions by mean |SHAP interaction value|. These are data-driven interaction discoveries that may generate new hypotheses.

#### Individual-Level Explanations

- **Waterfall plots** for 10 representative patients:
  - A high-risk patient (predicted probability > 70%)
  - A low-risk patient (predicted probability < 20%)
  - A borderline patient (predicted probability 45-55%)
  - For each, show which features push the prediction up vs. down
- **Clinical utility**: These plots are what the urologist sees at the point of care: "For THIS patient, the 10-year mortality risk is elevated because of X, Y, Z."

---

## 4. Feature Engineering Strategy

### 4.1 Fried Frailty: Individual Components vs. Composite Score

**Recommendation**: Include **both**.

| Encoding | Variables | Rationale |
|----------|-----------|-----------|
| **Individual components** | 5 binary features: weight_loss, exhaustion, low_grip, slow_gait, low_activity | Allows the model to learn component-specific effects. Exhaustion may have different mortality implications than low grip strength. XGBoost can also learn interactions between components (e.g., weight loss + low grip = sarcopenic obesity pattern, which is particularly high-risk). |
| **Composite score** | 1 ordinal/integer feature: fried_score (0-5) | Provides the summary frailty signal. Useful for clinical communication ("frailty score of 4/5"). SHAP dependence on this feature is more interpretable for clinicians than separate SHAP values for 5 binary flags. |
| **Categorical encoding** | 1 categorical: robust (0) / pre-frail (1-2) / frail (3-5) | Optional: include as an alternative to the continuous score. This encodes the clinical frailty staging concept. |

**Decision**: The model includes all 5 individual binary components AND the continuous composite score (0-5). The 5 individual components have 4 degrees of freedom (they sum to the composite score), so including both introduces collinearity. However, XGBoost handles collinearity through its greedy splitting mechanism (it picks one of the correlated features and the others contribute less). For logistic regression baselines, we include only the composite score to avoid collinearity, and run a sensitivity analysis with individual components.

**For baseline logistic regression models**: Include only the composite score (0-5) or the categorical encoding (robust/pre-frail/frail) as the frailty representation.

### 4.2 Age Non-linearity

**Recommendation**: Include multiple representations and let the model choose.

| Representation | Implementation | Rationale |
|----------------|---------------|-----------|
| **Linear age** | `age` (continuous, years) | Simplest; included in all models |
| **Restricted cubic splines** | `rcs(age, df=3)` with knots at 65, 70, 75 | Captures non-linear age effects. Mortality risk may accelerate after 70. For logistic regression baselines. |
| **Polynomial age** | `age`, `age^2` | Alternative to splines; simpler, fewer parameters |
| **Age categories** | 60-64 / 65-69 / 70-75 | Crude but interpretable; useful for subgroup reporting |

**For XGBoost**: Include only linear `age` as a feature. XGBoost can learn non-linearities through tree splits. Adding polynomial or spline features to XGBoost does not add information that the tree structure cannot already capture and may harm interpretability.

**For logistic regression baselines**: Include `rcs(age, df=3)` to allow non-linear age effects. Linear age alone would systematically underestimate mortality risk at older ages and overestimate at younger ages.

### 4.3 Interaction Features

**Pre-specified interactions (included in all models)**:

| Interaction | Encoding | Clinical Rationale |
|-------------|----------|-------------------|
| `frailty x age` | `fried_score * age` | Frailty amplifies age-related mortality. A frail 65-year-old may have the mortality risk of a robust 75-year-old. |
| `multimorbidity x age` | `charlson_cci * age` | Comorbidity burden has greater mortality impact at older ages. |
| `frailty x multimorbidity` | `fried_score * charlson_cci` | "Frail multimorbidity" -- the combination of frailty and multimorbidity may be synergistically lethal. |

**For XGBoost**: These interaction terms are included as features in addition to the main effects. XGBoost can theoretically learn interactions from main effects alone, but providing explicit interaction terms as features improves the model's ability to detect them, especially with moderate N. SHAP interaction analysis will verify whether these interactions are actually used.

**For logistic regression baselines**: These interaction terms are included in the fully specified model (not in the Schonberg/Lee baseline which do not include frailty). A likelihood ratio test compares models with and without interactions.

**SHAP-discovered interactions**: After fitting XGBoost, compute SHAP interaction values for all feature pairs. The top 3-5 data-driven interactions will be visualized using SHAP dependence plots. These are hypothesis-generating and will be reported separately from pre-specified interactions.

### 4.4 Blood Biomarker Strategy

**Primary analysis**: Blood biomarkers are **excluded**. The blood subsample covers only ~60-70% of participants, and exclusion of non-blood-subsample participants would reduce N by ~30-40%, substantially reducing power. The primary model must be deployable without requiring blood draws (aligning with point-of-care use in primary care / urology clinic settings where CRP and albumin are not routinely ordered for life expectancy estimation).

**Sensitivity analysis 1**: Complete-case analysis on the blood subsample only. Fit the same XGBoost model with CRP (log-transformed) and albumin added as predictors. Compare:
- AUC vs. primary model (tested on the same subsample for fair comparison)
- SHAP importance of CRP and albumin relative to non-blood predictors
- Does adding blood biomarkers meaningfully improve discrimination?

**Sensitivity analysis 2**: Multiple imputation of blood biomarkers for the full cohort. Use MICE (Multiple Imputation by Chained Equations) with 10 imputations, incorporating all other predictors and the outcome (mortality) in the imputation model. Fit the model on each imputed dataset and pool results using Rubin's rules.

**Hypothesis**: CRP and albumin will have moderate SHAP importance (top 10-15 features) but will not substantially improve AUC beyond the non-blood features. If they do substantially improve AUC, this would be an important finding suggesting that inflammatory/nutritional biomarkers capture risk not captured by clinical geriatric assessment.

### 4.5 Additional Feature Engineering

| Transformation | Rationale |
|----------------|-----------|
| **Grip strength**: `max_grip` (maximum of 4 measurements) AND `max_grip / BMI` (sarcopenic index) | Normalizing grip by body size may improve mortality prediction |
| **Gait speed**: Include `gait_speed` AND indicator for `gait_missing` | Gait speed is missing for participants unable to complete the walk test. The missingness is informative (worse health). A missing indicator prevents listwise deletion and captures this signal. |
| **Chair stand time**: Include AND indicator for `chair_stand_missing` | Same rationale as gait speed missingness. |
| **Polypharmacy**: `med_count >= 5` (binary) AND `med_count` (continuous) | Binary for clinical threshold; continuous for dose-response. Check collinearity with Charlson CCI (multimorbidity predicts polypharmacy). |
| **Self-rated health**: Ordinal encoding (1-5) as continuous, OR one-hot encoding, OR both | One-hot encoding allows non-monotonic effects. Ordinal encoding is simpler. XGBoost handles ordinal naturally; use ordinal. |
| **Education**: Years of education (continuous) | SES gradient in mortality. Continuous encoding preferred for efficiency. |

---

## 5. Validation Strategy

### 5.1 Nested Cross-Validation

**Purpose**: Unbiased estimation of generalization performance while also tuning hyperparameters without data leakage.

**Design**:

```
Outer loop (5-fold): Performance estimation
  ├── Fold 1: Train (80%) → Test (20%)
  ├── Fold 2: Train → Test
  ├── ...
  └── Fold 5: Train → Test

  For each outer fold's training set:
    Inner loop (5-fold): Hyperparameter tuning
      ├── Inner Fold 1: Train → Validation
      ├── ...
      └── Inner Fold 5: Train → Validation
      → Select hyperparameters that maximize mean AUC across inner folds
    → Retrain with best hyperparameters on entire outer training set
    → Evaluate on outer test fold
```

**Key implementation details**:

- **Stratification**: Outer fold splits are stratified on the binary outcome (died within 10 years: yes/no) to ensure each fold has approximately equal event rates.
- **Seed**: Fixed random seed (42) for reproducibility of fold assignments.
- **Fold preservation**: Fold assignments are saved as CSV files for reproducibility and for use by other team members (e.g., Biostatistician).
- **Nestedness**: The inner tuning loop operates ONLY on the outer training set. The outer test set is never seen during tuning.

**Performance reporting**:

| Metric | Calculation |
|--------|-------------|
| Mean AUC | Mean of AUC across 5 outer test folds |
| 95% CI for AUC | Based on standard deviation across folds (conservative) or DeLong's variance estimate |
| Mean Brier score | Mean across 5 outer test folds |
| Calibration slope | Mean across 5 outer test folds; computed by regressing observed outcome on predicted log-odds for each test fold |

**Alternative stratification**: For Cox PH models in the survival analysis, stratification on outcome is not applicable. Use random 5-fold CV. Ensure fold assignments are identical across binary classification and survival models (same outer fold membership for each participant).

### 5.2 Temporal Validation

**Purpose**: Assess model transportability to a different time period. This is a stronger test of generalization than random cross-validation because it assesses whether the relationship between predictors and outcome is stable over time.

**Design**:

| Training | Testing | Rationale |
|----------|---------|-----------|
| Wave 2 (2013 baseline) | Wave 1 (2011 baseline) | Train on 2013, test on 2011. Caveat: Wave 1 does not have grip strength. Use a reduced feature set (drop grip strength, gait speed -- or use Wave 1 chair stand as proxy). This validates whether the model, stripped of physical performance measures, still works in an earlier cohort. |
| Wave 2 (2013 baseline) | Wave 3 (2015 baseline) | Train on 2013, test on 2015. All features available. Predict 10-year mortality from 2015 to 2025 -- requires Wave 5+ data. If 10-year follow-up is incomplete for Wave 3, use 8-year mortality (2015-2023) as a proxy and adjust the prediction threshold. |

**Performance metric**: AUC on the temporal test set. A drop in AUC of >= 0.05 from cross-validation to temporal validation suggests distribution shift (cohort effects, secular trends in mortality, changing predictor-outcome relationships).

**Caveat**: If the time gap is large (e.g., 2013 vs. 2023), secular trends in healthcare, smoking, and mortality rates may shift the relationship. Report temporal validation AUC alongside 2013 cross-validation AUC. If temporal drop is substantial, discuss implications for model updating (recalibration or refitting is recommended before deploying to contemporary populations).

### 5.3 External Benchmark Comparison

**Schonberg Index and Lee Index on CHARLS**:

For every outer test fold:
1. Compute Schonberg index predicted probability of 10-year mortality for each test participant (using the published Schonberg model coefficients applied to CHARLS variables).
2. Compute Lee index predicted probability (using the published Lee coefficients).
3. Compare AUC, Brier score, calibration slope between:
   - Our XGBoost model (trained on outer training set, tested on outer test set)
   - Schonberg index (externally applied, no CHARLS-specific training)
   - Lee index (externally applied, no CHARLS-specific training)

**This is the key head-to-head comparison.** The XGBoost model must demonstrate clinically meaningful improvement (delta AUC >= 0.03) over Schonberg and Lee.

**Note on recalibrated Schonberg/Lee**: In addition to the externally applied (original coefficients) comparison, we will also report the performance of Schonberg/Lee when their coefficients ARE recalibrated on CHARLS training data (i.e., refit the logistic regression with Schonberg/Lee variables on CHARLS). This distinguishes:
- Poor discrimination because the variables themselves are insufficient (fundamental limitation of Schonberg/Lee) from
- Poor calibration because the published coefficients don't transport to Chinese population (recalibration solves this)

---

## 6. Evaluation Plan

### 6.1 Primary Metric: AUC-ROC

**Target**: AUC >= 0.80 (decision-support level)

**Rationale**: AUC measures the model's ability to discriminate between men who will vs. will not die within 10 years. This is the most commonly reported metric in clinical prediction literature, enabling direct comparison with published models.

**Calculation**: AUC computed on each outer test fold; mean and 95% CI reported.

**Sensitivity analysis**: Compute AUC by age group (60-64, 65-69, 70-75) to assess whether discrimination varies by age. If AUC is substantially lower in the 60-64 age group (where mortality is rarer and harder to predict), this is clinically important -- the model may be less useful for screening cessation decisions in younger men.

### 6.2 Secondary Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| **AUC-PR (Precision-Recall)** | Report; no specific target | More informative than AUC-ROC when event rate is not 50%. With 30-40% event rate, AUC-ROC and AUC-PR should be consistent. If they diverge, AUC-PR takes priority. |
| **Brier Score** | < 0.15 | Measures both discrimination and calibration. A Brier score of 0.15 means the mean squared error of predictions is 0.15 (on a 0-1 scale). For reference: a naive model predicting the base rate (e.g., always predicting 0.35 if 35% event rate) has Brier score = 0.35 * (1-0.35) = 0.2275. Our model should meaningfully improve over this. |
| **Calibration Slope** | 0.9-1.1 | Slope of the regression of observed outcome on predicted log-odds. Slope = 1 means perfect calibration on average. Slope < 1 means overfitting (predicted probabilities are too extreme). Slope > 1 means underfitting. |
| **Calibration Intercept** | -0.1 to 0.1 | Intercept of the calibration regression. Intercept = 0 means no systematic over- or under-prediction. Intercept > 0 means systematic under-prediction (model predicts too low). |
| **Expected Calibration Error (ECE)** | < 0.05 | Mean absolute difference between predicted and observed probabilities across deciles. This is a more interpretable calibration metric than Brier score for clinical audiences. |

### 6.3 Model Comparison Metrics

#### DeLong Test for Correlated AUCs

**Purpose**: Formal statistical test comparing AUC of our XGBoost model vs. Schonberg index on the same test set.

**Implementation**: `pROC::roc.test()` (R) or `delong_roc_test` (Python `mlxtend`). Test applied to the pooled predictions across all outer test folds.

**Null hypothesis**: AUC_XGBoost = AUC_Schonberg (or AUC_Lee)

**Interpretation**: A significant DeLong test (p < 0.05) provides statistical evidence that XGBoost has superior discrimination. However, statistical significance does not guarantee clinical significance. The delta AUC >= 0.03 threshold is the clinical significance criterion.

#### Integrated Discrimination Improvement (IDI)

**Purpose**: Quantifies how much the new model improves discrimination across ALL risk thresholds (not just a single threshold like sensitivity/specificity).

**Interpretation**: IDI = (improvement in sensitivity) - (improvement in 1 - specificity), integrated over the predicted risk distribution. IDI > 0 means the new model is, on average, better at discriminating cases and controls.

**Reporting**: IDI with 95% CI. An IDI of 0.02 means the new model improves the average sensitivity by 2 percentage points without worsening specificity (or vice versa).

#### Category-Free Net Reclassification Improvement (NRI)

**Purpose**: Measures improvement in risk classification. For binary outcomes, category-free (continuous) NRI is preferred over category-based NRI (which requires predefined risk categories that are arbitrary for life expectancy prediction).

**Reporting**: NRI > 0 with 95% CI. NRI of 0.15 means that 15% of individuals are correctly reclassified by the new model (net of incorrect reclassifications).

### 6.4 Clinical Utility: Decision Curve Analysis (DCA)

**Purpose**: Evaluate whether using the model to decide screening cessation provides net benefit over default strategies ("screen all men 60-75" or "screen none").

**Method**: Plot net benefit (y-axis) vs. threshold probability (x-axis), where:
- **Threshold probability**: The predicted mortality risk above which we recommend stopping screening.
  - Low threshold (e.g., 0.10): We are willing to stop screening even at modest predicted mortality risk (aggressive screening cessation). Few false positives, many true positives.
  - High threshold (e.g., 0.40): We only stop screening at high predicted mortality risk (conservative screening cessation). Fewer true positives, fewer false positives.
- **Net benefit**: `(True Positives / N) - (False Positives / N) * (threshold / (1 - threshold))`
  - Intuitively: the benefit of correctly stopping screening minus the harm of incorrectly stopping screening, weighted by how much we care about false positives at that threshold.

**Reference lines**:
- "Screen all": Continue screening all men 60-75 regardless of predicted mortality. Net benefit = 0 at thresholds where the event rate matches the threshold.
- "Screen none": Stop screening all men 60-75. Net benefit = 0 at any threshold (no one is screened, so no one benefits or is harmed by screening cessation).

**Interpretation**: The model provides net benefit if its DCA curve lies above both "screen all" and "screen none" reference lines over the clinically relevant threshold range (0.10-0.40). If the model's net benefit overlaps with "screen all," the model does not add clinical value.

**Threshold range of interest**: 0.10-0.40. Below 0.10, we would stop screening almost everyone (too aggressive). Above 0.40, we would only stop screening at very high predicted mortality (too conservative -- we might as well screen everyone). The clinically relevant range is where urologists would realistically consider stopping screening (approximately 20-40% predicted 10-year mortality risk).

### 6.5 Calibration Assessment: Focus on High-Risk Deciles

**Purpose**: For clinical use, calibration in high-risk deciles (predicted probability > 50%) matters more than calibration in low-risk deciles. If the model predicts 70% 10-year mortality for a patient, the observed mortality in patients with similar predictions must be close to 70%. If it is actually 50%, the model is miscalibrated in exactly the range where clinical decisions are made.

**Method**:
1. Bin predicted probabilities into deciles (10 equal-sized groups by predicted risk).
2. Plot observed vs. predicted mortality for each decile.
3. Report the calibration slope and intercept WITHIN the top 3 deciles (high-risk patients where screening cessation would be recommended).
4. Report the Hosmer-Lemeshow test (with the caveat that it is sensitive to sample size and should not be the sole calibration metric).

**Calibration plot**: x-axis = predicted probability (decile mean), y-axis = observed mortality rate. Points above the diagonal = model under-predicts (predictions too low); points below = model over-predicts. Confidence intervals via bootstrapping.

### 6.6 Sensitivity and Specificity at Clinically Relevant Thresholds

The clinical decision is binary: stop screening if predicted 10-year mortality risk exceeds a threshold T. The choice of T involves a trade-off:

| Threshold (T) | Sensitivity (catch men who will die) | Specificity (avoid stopping screening for men who will survive) | Clinical Implication |
|---------------|--------------------------------------|----------------------------------------------------------------|---------------------|
| Low (e.g., 0.30) | High (few false negatives; we rarely miss men who will die) | Low (many false positives; we stop screening for many men who would survive) | Aggressive screening cessation; prioritizes minimizing overscreening |
| High (e.g., 0.50) | Moderate | Moderate-High | Balanced approach |
| Very high (e.g., 0.70) | Low | Very High | Conservative; only stops screening for very high-risk men |

**Recommended primary target**: Sensitivity >= 0.85, Specificity >= 0.70

**Rationale**: Per the USPSTF Grade D recommendation for men 70+, the harm of PSA screening (overdiagnosis, overtreatment cascades) outweighs the benefit. Therefore, we prioritize sensitivity (catching men who will die) over specificity (avoiding false positives). A sensitivity of 0.85 means we correctly identify 85% of men who will die within 10 years and spare them unnecessary screening. A specificity of 0.70 means 30% of men who would survive 10+ years are erroneously told to stop screening -- the harm of this is modest per USPSTF.

**Reporting**: Report the ROC curve with the operating point at the threshold achieving sensitivity >= 0.85. Report sensitivity, specificity, PPV, and NPV at this threshold.

---

## 7. Risk Assessment and Mitigation

### 7.1 Overfitting Risk: Features-to-Events Ratio

**Assessment**: **Low risk**. With ~27-29 features and ~750-1,400 events, we have 26-52 events per variable (EPV). This is well above the conventional EPV >= 10-20 threshold. XGBoost's built-in regularization (subsample, column subsampling, L1/L2 on leaf weights, `min_child_weight`) provides additional overfitting protection.

**Mitigation**:
1. Nested cross-validation ensures that hyperparameters are tuned on inner folds and performance is estimated on unseen outer folds.
2. Early stopping (`early_stopping_rounds = 50`) halts training when validation AUC stops improving.
3. Restricted tree depth (`max_depth` 2-8 in tuning search space) prevents overly complex trees.
4. Calibration slope on test folds is the overfitting litmus test: slope < 0.9 suggests overfitting. If observed, increase regularization and re-tune.

### 7.2 Age Confounding

**Risk**: Age is the single strongest predictor of mortality. The model may learn to predict mortality largely from age, with geriatric variables contributing little. If so, the model is effectively an age calculator, not a geriatric risk stratifier.

**Assessment approach**:
1. **Incremental AUC decomposition**:
   - AUC(age only) -- baseline
   - AUC(age + Charlson) -- comorbidity contribution
   - AUC(age + Charlson + Fried) -- frailty contribution
   - AUC(age + Charlson + Fried + Functional) -- functional contribution
   - ...
   - AUC(full model) -- total

   Report the delta AUC contributed by each domain. If the geriatric domains (frailty, function, cognition) collectively contribute delta AUC < 0.02 over age + comorbidity, the added value of geriatric assessment is questionable.

2. **SHAP dependence on age**: Plot SHAP(age) vs. age. The relationship should be smooth and monotonic (higher age → higher mortality risk). A wavy or non-monotonic pattern suggests age is interacting with other features in unexpected ways (which may be genuine or artefactual).

3. **Age-stratified analysis**:
   - Subgroup 1: Age 60-69 (younger old)
   - Subgroup 2: Age 70-75 (older old)
   - Report AUC for each subgroup separately.
   - **Key question**: Does the model discriminate well within the younger subgroup, where age variability is less informative and geriatric heterogeneity is the main source of mortality risk differentiation? If AUC drops substantially in the 60-69 subgroup, the model may be less clinically useful for screening cessation decisions in younger men (ages 60-64, where USPSTF screening is controversial anyway).

4. **Age-adjusted analysis**: Fit a model using all features EXCEPT age. This model directly tests whether geriatric assessment alone can predict mortality. If AUC(geriatric only) >= 0.75, geriatric assessment has strong independent predictive value. If AUC(geriatric only) < 0.70, age is doing most of the work.

### 7.3 Missing Data

**Patterns of missingness**:

| Variable | Missingness Mechanism | Expected Missing Rate | Mitigation |
|----------|----------------------|----------------------|------------|
| Grip strength | MNAR (missing in frailest, unable to perform test) | ~15-20% | Missing indicator method + sensitivity: multiple imputation |
| Gait speed | MNAR (missing in those unable to walk 3m) | ~30-40% | Missing indicator method + sensitivity: multiple imputation |
| Chair stand time | MNAR (missing in those unable to rise from chair) | ~20-30% | Missing indicator method |
| Blood biomarkers (CRP, albumin) | MCAR/MAR (random blood subsample) | ~30-40% | Excluded from primary analysis. Multiple imputation in sensitivity analysis. |
| CES-D items | MAR (skip pattern or refusal) | ~5-10% | Multiple imputation if >5% missing |
| Self-rated health | MAR (refusal) | <5% | Multiple imputation |

**Primary analysis**: Missing indicator method for performance-based measures (grip, gait, chair stand). This preserves sample size and explicitly models that missingness is informative (those who cannot complete the test are at higher mortality risk). Listwise deletion is NOT used because it would systematically exclude the frailest participants and bias the model toward healthier survivors.

**Sensitivity analysis**: Multiple imputation by chained equations (MICE) with 10 imputed datasets. The imputation model includes all predictors + the outcome variable (mortality). For the blood biomarker sensitivity analysis, MI is the primary approach to retain the full sample.

**Caveat**: For participants with >50% missing data across all domains, exclusion is acceptable. These participants are likely severe health outliers (proxy respondents, dementia) who are already excluded per clinical criteria.

### 7.4 Distribution Shift

**Risk**: A model trained on CHARLS 2013 data may not generalize to:
1. **Contemporary Chinese older adults (2026+)**: Secular trends in smoking, obesity, healthcare access, and mortality rates may shift the predictor-outcome relationship.
2. **Urban vs. rural populations**: CHARLS is nationally representative, but the urban/rural mortality gradient is changing as China urbanizes.
3. **Different regions of China**: Mortality rates vary by province (higher in western China, lower in eastern coastal provinces).

**Mitigation**:
1. Temporal validation (Section 5.2) directly tests transportability across time.
2. Report model performance stratified by urban/rural residence. If AUC differs substantially, a region-specific model or an urban/rural interaction term may be warranted.
3. Acknowledge that any model deployed in clinical practice should undergo local recalibration/validation before use. This is standard for clinical prediction models (per TRIPOD Type 4 -- model development with external validation recommendation).

### 7.5 Censoring and Outcome Misclassification

**Risk 1: Censoring before 10-year mark**: Men lost to follow-up at Wave 3 (2015) or Wave 4 (2018). Their vital status at 10 years is unknown. If we classify them as "alive" (did not die within 10 years), we misclassify any who actually died after loss to follow-up. This biases the model toward under-prediction of mortality.

**Mitigation 1**: Report the censoring rate by baseline characteristics. If highly frail men are more likely to be lost to follow-up (because they died without exit interview), the outcome misclassification is differential and biases model performance estimates.

**Sensitivity analysis 1**: Two extreme-case analyses:
- "Worst-case": Assume all censored men died within 10 years. Re-classify outcome and re-fit model.
- "Best-case": Assume all censored men survived >= 10 years (this is the default).
- If AUC changes by < 0.03 between best-case and worst-case, censoring is unlikely to substantively affect conclusions.

**Risk 2: Misclassification of death timing**: In CHARLS, death is ascertained at the wave when an exit interview is conducted. If a participant dies in year 3 but the exit interview occurs in year 4 (at the next wave), death is recorded at year 4. This is a minor issue for 10-year binary classification (it does not change the binary outcome), but affects time-to-event analysis.

**Mitigation 2**: For survival analysis, use interval-censored methods if exact death date is not available. If the death year is known, use mid-year imputation (assume death at month 6 of the recorded year).

### 7.6 Competing Risks (for Q2 only)

For the primary Q1 analysis (all-cause mortality), competing risks are not relevant -- death is death, regardless of cause. For secondary Q2 analysis (cancer incidence prediction), death before cancer is a competing event. This is addressed in the Q2-specific modeling proposal.

---

## 8. Reproducibility Plan

### 8.1 Seed Setting

All random processes must be seeded for reproducibility:

```python
RANDOM_SEED = 42

import random
random.seed(RANDOM_SEED)
import numpy as np
np.random.seed(RANDOM_SEED)
import xgboost as xgb
# Pass random_state=RANDOM_SEED to all XGBoost functions
```

**Multi-seed sensitivity**: After the primary analysis is complete and the final model is selected, re-run the entire pipeline with 3 different random seeds (42, 123, 999) to assess the stability of:
- Cross-validation AUC (should vary by < 0.01 across seeds if N is adequate)
- Feature importance rankings (top 5 features should be identical across seeds)
- Selected hyperparameters (similar, but minor variation is expected with Bayesian optimization)

### 8.2 Cross-Validation Fold Definitions

Fold assignments are saved to ensure all team members use the same splits:

```
project/
  outputs/
    cv_folds/
      outer_folds.csv        # participant_id, outer_fold (1-5)
      inner_folds.csv        # participant_id, outer_fold, inner_fold (1-5)
      temporal_split.csv     # participant_id, split (train/test), wave
```

**Format**: CSV with columns: `participant_id`, `outer_fold`, `inner_fold` (for the relevant outer training set).

### 8.3 Environment Specification

**Python environment** (primary):

```yaml
# conda environment or pip requirements.txt
python: 3.11.x
xgboost: 2.0.x
scikit-learn: 1.5.x
shap: 0.45.x
optuna: 3.6.x
scikit-survival: 0.22.x  # for RSF, Cox PH
pandas: 2.2.x
numpy: 1.26.x
matplotlib: 3.9.x
seaborn: 0.13.x
jupyter: 1.0.x
```

**R environment** (for Schonberg/Lee implementation and DeLong test):

```r
# renv.lock
R: 4.3.x
rms: 6.8.x    # restricted cubic splines, calibration
pROC: 1.18.x  # DeLong test
survival: 3.5.x
randomForestSRC: 3.2.x
mice: 3.16.x  # multiple imputation
Hmisc: 5.1.x
```

**Containerization** (recommended): Docker image with pinned package versions, or a `renv.lock` (R) + `requirements.txt` (Python) committed to the repository.

### 8.4 Code Repository Structure

```
prostate-cancer-2026/
├── modeling-proposal.md          # This document
├── code/
│   ├── 00_data_preprocessing.py  # Variable derivation, missing data handling
│   ├── 01_feature_engineering.py # Frailty score, splines, interactions
│   ├── 02_baseline_models.py     # Models 0-3 (LR) + Cox PH baselines
│   ├── 03_xgboost_model.py       # XGBoost with nested CV + Optuna tuning
│   ├── 04_advanced_models.py     # RSF, DeepSurv (optional), stacking
│   ├── 05_evaluation.py          # AUC, Brier, calibration, DCA, DeLong, IDI, NRI
│   ├── 06_shap_analysis.py       # SHAP global, dependence plots, interactions
│   ├── 07_sensitivity_analyses.py # Blood biomarkers, missing data, seeds
│   ├── 08_figures.py             # Publication-quality figures
│   └── 09_tables.py              # Table generation
├── outputs/
│   ├── models/                   # Trained model objects (.pkl, .json)
│   ├── cv_folds/                 # Fold assignments
│   ├── results/                  # Performance metrics (CSV, JSON)
│   ├── figures/                  # Figures (PNG, PDF)
│   └── shap/                     # SHAP values and plots
├── renv.lock                     # R environment lockfile
├── requirements.txt              # Python dependencies
└── README.md                     # Project overview + reproduction instructions
```

### 8.5 Documentation Standards

- Every script begins with a docstring describing its purpose, inputs, outputs, and dependencies.
- Random seed is explicitly set and logged at the top of each script.
- All file paths are relative to the project root (uses `pathlib.Path`).
- Intermediate results (processed data, fold assignments, model objects) are saved to `outputs/` and loaded by downstream scripts so the pipeline can be restarted from any stage.

---

## 9. Time Estimation

### 9.1 Development Timeline

| Phase | Task | Estimated Time | Dependencies |
|-------|------|---------------|--------------|
| **1. Data Prep** | Variable derivation, missing data analysis, feature engineering, descriptive statistics table | 1-2 weeks | CHARLS data access confirmed; variable map finalized by Clinical Researcher |
| **2. Baseline Models** | Implement Models 0-3 (LR + Cox), compute performance metrics, calibration assessment | 1 week | Phase 1 complete |
| **3. Primary Model** | Set up nested CV pipeline, Optuna hyperparameter tuning, XGBoost training, evaluation on outer folds | 1-2 weeks | Phases 1-2 complete |
| **4. Advanced Models** | Implement RSF, prepare DeepSurv if N is sufficient, stacking ensemble (optional) | 1 week | Phase 3 complete |
| **5. SHAP Analysis** | Global importance, dependence plots, interaction plots, individual waterfall plots | 1 week | Phase 3 complete (XGBoost model trained) |
| **6. Sensitivity Analyses** | Blood biomarkers, temporal validation, multiple imputation, multi-seed stability | 1-2 weeks | Phases 3-5 complete |
| **7. Figure & Table Generation** | Publication-quality figures for manuscript, formatted tables | 1 week | Phases 1-6 complete |
| **8. Model Documentation** | Model card, deployment considerations, clinical decision support prototype specification | 0.5 week | Phase 7 complete |
| **Total** | | **7-10 weeks** | |

### 9.2 Critical Path

```
Data Prep → Baseline Models → Primary Model (XGBoost) → Evaluation → SHAP → Sensitivity → Manuscript
                            ↘ Advanced Models (parallel) ↗
```

Baseline models and primary model are on the critical path. Advanced models and sensitivity analyses can proceed in parallel once XGBoost is trained.

### 9.3 Bottlenecks

1. **CHARLS variable derivation**: Mapping the specified clinical constructs (Fried frailty, Charlson CCI, 10-year mortality) to CHARLS variable names and handling wave-specific skip patterns is the most labor-intensive step. Close collaboration with the Data Engineer and Clinical Researcher is required.
2. **Missing data diagnosis**: Understanding the patterns and mechanisms of missingness for gait speed, chair stand, and grip strength requires exploratory analysis that may reveal unexpected patterns.
3. **DeepSurv feasibility**: If the analytic N is at the lower bound of the expected range (~2,500), DeepSurv may be infeasible and should be deprioritized early to avoid wasted effort.

---

## 10. Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary ML task | Binary classification | Direct alignment with clinical decision (10-year threshold) |
| Complementary task | Survival analysis | Handles censoring; flexible time horizons |
| Primary model | XGBoost | Best fit for tabular data + moderate N + interpretability via SHAP |
| Frailty encoding | Both individual components + composite score | Individual for model learning; composite for clinical interpretability |
| Age encoding | Linear for XGBoost; RCS for logistic regression baselines | XGBoost learns non-linearity internally |
| Pre-specified interactions | frailty x age, multimorbidity x age, frailty x multimorbidity | Clinical rationale; included as explicit features |
| Blood biomarkers | Excluded from primary; sensitivity analysis with MI | Preserves sample size; aligns with point-of-care deployment scenario |
| Validation | Nested 5-fold CV (stratified) + temporal validation | Unbiased performance estimation; tests generalizability across time |
| Primary metric | AUC-ROC >= 0.80 | Clinical decision-support standard |
| Calibration target | Brier < 0.15; calibration slope 0.9-1.1 | Essential for clinical risk communication |
| Model comparison | DeLong test + IDI + NRI vs. Schonberg, Lee | Head-to-head comparison with existing calculators |
| Clinical utility | Decision Curve Analysis (0.10-0.40 threshold range) | Demonstrates net benefit for screening cessation decisions |
| Interpretability | SHAP (global + dependence + interaction + individual) | Required for clinical deployment and trust |
| Reproducibility | Fixed seed (42); saved CV folds; containerized environment | Enables independent verification and team collaboration |

---

## Appendix: Performance Targets Summary

| Metric | Target | Level |
|--------|--------|-------|
| AUC-ROC | >= 0.80 | Primary |
| AUC-PR | Report (no fixed target) | Secondary |
| Brier Score | < 0.15 | Primary (calibration) |
| Calibration Slope | 0.9-1.1 | Primary (calibration) |
| Calibration Intercept | -0.1 to 0.1 | Secondary |
| ECE | < 0.05 | Secondary |
| Sensitivity (at clinical threshold) | >= 0.85 | Clinical utility |
| Specificity (at clinical threshold) | >= 0.70 | Clinical utility |
| Delta AUC vs. Schonberg | >= 0.03 | Clinical (MCID) |
| Delta AUC vs. Lee | >= 0.03 | Clinical (MCID) |
| Net benefit on DCA (0.10-0.40) | Positive vs. "screen all" and "screen none" | Clinical utility |
| DeLong test p-value | < 0.05 | Statistical |
| NRI (category-free) | > 0.10 | Clinical |

---

*This modeling proposal was prepared by the Computational Biologist role. All methodological decisions are based on established best practices in clinical prediction modeling (TRIPOD guidelines, Steyerberg's Clinical Prediction Models) and machine learning for tabular data. Feature engineering decisions reference the clinical computability assessment prepared by the Clinical Researcher. Validation and evaluation strategies incorporate feedback from the Biostatistician and PI roles.*

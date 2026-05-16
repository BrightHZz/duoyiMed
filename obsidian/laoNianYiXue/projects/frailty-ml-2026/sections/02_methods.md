# Methods

## Study Design and Setting

We conducted a prospective cohort study using data from the China Health and Retirement Longitudinal Study (CHARLS), a nationally representative survey of Chinese adults aged 45 years and older. CHARLS employs multistage stratified probability-proportional-to-size sampling covering 28 provinces, 150 counties, and 450 villages/urban communities. We used the 2013 wave (Wave 2) as baseline and the 2015 wave (Wave 3) for outcome ascertainment. This study is reported in accordance with the Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis or Diagnosis — Artificial Intelligence (TRIPOD+AI) statement.

## Study Population

We included CHARLS participants who met all of the following criteria: (1) aged 60 years or older at baseline (2013); (2) non-frail at baseline, defined as Fried phenotype score less than 3; (3) completed the 2015 follow-up assessment with evaluable Fried phenotype components. We excluded participants with severe cognitive impairment at baseline (Mini-Mental State Examination [MMSE] score below 18, or proxy respondents). Deaths occurring between 2013 and 2015 were excluded from the primary analysis and treated as a competing event in sensitivity analyses.

## Outcome

The primary outcome was frailty worsening over the 2-year follow-up, defined as an increase of one or more points in the Fried phenotype score (range 0–5) between 2013 and 2015. The Fried phenotype was operationalized using five components measured at both waves:

1. **Weight loss**: Self-reported unintentional weight loss (CHARLS variable `da049`, coded as present if the participant reported weight decrease).
2. **Exhaustion**: Two items from the Center for Epidemiologic Studies Depression scale (CES-D) — "I felt everything I did was an effort" (`dc011`) and "I could not get going" (`dc012`). Either item reported as occurring 3 or more days per week was coded as exhaustion present.
3. **Low grip strength**: Maximum grip strength across four measurements (`qc003`–`qc006`), stratified by sex into the lowest 20th percentile, coded as present if below the sex-specific cutoff.
4. **Slow gait speed**: Walking speed over a 3-meter course (`qg003`), calculated as 3.0 divided by time in seconds. Stratified by sex into the lowest 20th percentile.
5. **Low physical activity**: Self-reported physical activity (`da050`), coded as present if the participant reported no regular physical activity.

## Predictors

We included 40 candidate predictors measured at baseline (2013), organized into eight domains:

- **Demographics** (4): age, sex, education years, urban/rural residence.
- **Physical function** (8): maximum grip strength (kg), mean grip strength, grip strength standard deviation across trials, gait speed (m/s), chair stand time (s), activities of daily living (ADL) sum score, instrumental ADL sum score, and three balance test items.
- **Anthropometrics** (4): body mass index, height, weight, waist circumference.
- **Hemodynamics** (3): systolic blood pressure, diastolic blood pressure, pulse rate.
- **Chronic conditions** (6): total number of chronic conditions, plus binary indicators for hypertension, diabetes, heart disease, stroke, chronic lung disease, and arthritis.
- **Psychological status** (5): CES-D total score and four individual CES-D items.
- **Lifestyle** (3): smoking status, alcohol consumption, physical inactivity.
- **Baseline frailty components** (5): each of the five Fried phenotype components at baseline and the total baseline Fried score.

CHARLS missing value codes (values 900 or above) were replaced with missing values (NaN) before imputation.

## Model Development

We developed and compared three models:

1. **Baseline model**: XGBoost classifier using only age and sex as predictors, serving as a performance anchor.
2. **LASSO logistic regression**: L1-penalized logistic regression with regularization strength C = 0.1, performing embedded feature selection.
3. **XGBoost**: Gradient-boosted tree ensemble with hyperparameters tuned via Optuna (Tree-structured Parzen Estimator, 20 trials). The search space included number of estimators (100–500), maximum depth (3–8), learning rate (0.01–0.2, log-uniform), subsample ratio (0.6–1.0), column subsample ratio (0.6–1.0), minimum child weight (1–10), gamma (0–1.0), and L1/L2 regularization terms (0–10). Scale-positive weight was set to the inverse class ratio to address class imbalance. The optimal configuration was: n_estimators = 438, max_depth = 6, learning_rate = 0.0102.

All continuous predictors were standardized to zero mean and unit variance. Missing values were imputed using median imputation. All preprocessing steps were performed within the cross-validation loop to prevent information leakage.

## Model Evaluation

Model performance was evaluated using 5-fold stratified cross-validation, repeated with five different random seeds. The primary metric was the area under the receiver operating characteristic curve (AUC-ROC). Secondary metrics included area under the precision-recall curve (AUC-PR) and Brier score. We report mean performance across the five cross-validation folds with 95% confidence intervals estimated via bootstrap (1,000 resamples).

Feature importance was assessed using XGBoost's built-in gain-based importance. We additionally report the correlation between the top-ranked baseline frailty component (low grip strength) and its continuous counterpart (maximum grip strength) to assess potential collinearity.

## Sensitivity Analyses

We conducted the following prespecified sensitivity analyses: (1) complete-case analysis excluding participants with any missing predictor values; (2) XGBoost model excluding all baseline Fried components to assess the predictive contribution of frailty status; (3) analysis stratified by sex and age group (60–69, 70–79, 80+); (4) treating death as a competing event using Fine-Gray subdistribution hazard models.

## Software

All analyses were performed using Python 3.12 with scikit-learn (v1.3), XGBoost (v2.0), Optuna (v3.0), and pandas (v2.0). CHARLS original data were in Stata format (.dta) and were converted to CSV for analysis.

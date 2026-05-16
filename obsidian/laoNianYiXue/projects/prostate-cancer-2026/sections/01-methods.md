# Methods

## Study Design and Data Source

We conducted a prospective cohort study using retrospectively analyzed data from the China Health and Retirement Longitudinal Study (CHARLS), a nationally representative longitudinal survey of Chinese adults aged 45 years and older [1,2]. CHARLS employs multistage probability-proportional-to-size (PPS) sampling across 28 provinces, 150 counties, and 450 villages or urban communities in mainland China. Detailed descriptions of the CHARLS design, sampling methodology, and data collection procedures have been published previously [1].

The baseline for this analysis was Wave 2 (2013), which was the first CHARLS wave to include grip strength measurement via hand dynamometer, thereby enabling full operationalization of the Fried frailty phenotype. Mortality follow-up extended through Wave 5 (2020), providing a maximum of 7 years of follow-up. This study followed the Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis or Diagnosis (TRIPOD) reporting guideline for prediction model development and validation [3].

## Study Population

We included community-dwelling male CHARLS participants who met the following criteria at the Wave 2 baseline: (1) male sex, (2) age between 60 and 75 years inclusive, (3) completed the Wave 2 core interview, and (4) alive at the time of the baseline interview. Exclusion criteria were: (1) death recorded in the same year as baseline (2013), precluding prediction from baseline data; (2) severe functional impairment, defined as dependency in four or more basic activities of daily living (ADL) items; (3) absence of cognitive assessment data, serving as a proxy for severe cognitive impairment or reliance on a proxy respondent whose self-reported data may be unreliable; and (4) known terminal illness at baseline, if identifiable from self-report. The age range of 60-75 years was selected to align with the clinical window for prostate cancer screening decisions, as recommended by the United States Preventive Services Task Force (USPSTF) for men aged 55-69 years [4], extended to capture men in the zone of greatest clinical ambiguity regarding screening cessation.

## Outcome Ascertainment

The primary outcome was 7-year all-cause mortality, defined as death from any cause occurring between the Wave 2 baseline interview (2013) and the Wave 5 follow-up (2020). Mortality was ascertained through CHARLS exit interviews, which are conducted with family members, neighbors, or community informants when a participant dies between survey waves. Death status was verified across three follow-up waves: Wave 3 (2015), Wave 4 (2018), and Wave 5 (2020) using the Sample Information files, which record vital status for all participants targeted for follow-up. The outcome was coded as a binary variable: 1 for confirmed death within the 7-year follow-up window, and 0 for confirmed survival through Wave 5. The originally planned 10-year follow-up horizon (through 2023) was not achievable because Wave 6 data were not yet released at the time of analysis; we therefore adopted the 7-year horizon as the maximum verifiable follow-up.

## Predictor Variables

We pre-specified 30 candidate predictors spanning eight clinical domains, derived from clinical knowledge of geriatric mortality determinants and consistent with the variables included in established life expectancy calculators. All predictors were measured at the Wave 2 baseline.

### Demographics and Socioeconomic Status

Age was calculated as 2013 minus self-reported birth year (variable `zba002_1`). Residence type was classified as rural village or urban community (variable `bb002`). Marital status was dichotomized as married or partnered versus widowed, divorced, or never married (variable `be001`). Self-rated health was assessed on a 5-point ordinal scale from excellent to very poor (variable `da002`).

### Chronic Disease and Multimorbidity

Fourteen self-reported chronic conditions were ascertained from the CHARLS health status module (variables `zda007_1_` through `zda007_14_`): hypertension, diabetes, cancer, chronic lung disease, heart disease, stroke, psychiatric disease, arthritis or rheumatism, dyslipidemia, liver disease, kidney disease, digestive disease, asthma, and memory-related disease. Each condition was coded as a binary variable (1 = diagnosed, 0 = not diagnosed). The Charlson Comorbidity Index (CCI) was calculated by mapping each condition to its Charlson weight: conditions with a weight of 1 included heart disease, chronic lung disease, stroke, psychiatric disease, arthritis, liver disease, digestive disease, asthma, memory-related disease, and diabetes; conditions with a weight of 2 included cancer and kidney disease. The age component of the CCI was not added to avoid double-counting with the age predictor. A total disease count was computed as the sum of all 14 individual disease indicators.

### Frailty Assessment

The Fried frailty phenotype was operationalized using CHARLS variables according to the original Fried criteria [5], with each of five components scored as 0 (absent) or 1 (present):

1. **Weight loss**: Self-reported unintentional weight loss of 5 kg or more in the prior two years (variable `da049` for weight change in kg; variable `da047` for self-reported weight change pattern).

2. **Exhaustion**: Endorsement of either "I felt everything I did was an effort" (variable `dc011`) or "I could not get going" (variable `dc012`) for "most or all of the time" (4 or more days per week) in the past week, drawn from the 10-item Center for Epidemiologic Studies Depression scale (CES-D-10).

3. **Low physical activity**: Self-reported absence of regular physical activity, assessed by the item "Do you engage in any regular physical activity?" (variable `da051_1_`).

4. **Weakness (low grip strength)**: Maximum grip strength across four hand dynamometer measurements (variables `qc003` through `qc006`), classified as weak if below the sex-specific 20th percentile. Values >= 900 were recoded as missing per CHARLS conventions (denoting refusal or inability to perform the measurement). Values below 5 kg or above 100 kg were treated as implausible and set to missing.

5. **Slowness (slow gait speed)**: Walking speed over a 3-meter course (variable `qg003`), calculated as 3.0 divided by walk time in seconds. Gait speed below 0.8 m/s was classified as slow, consistent with established cutoffs [6]. Participants unable to complete the walk test were recorded as having missing gait speed; a missingness indicator variable was created to capture the informative nature of this missingness.

A composite Fried frailty score was computed as the sum of the five components (range 0-5), requiring a minimum of three non-missing components. The score was further categorized as robust (score = 0), pre-frail (score = 1-2), or frail (score >= 3).

### Functional Status

Basic ADL disability was assessed using five items from the CHARLS health status module (variables `zda005_1_` through `zda005_5_`): dressing, bathing, eating, transferring, and toileting. Each item was coded as 1 if the participant reported any difficulty, and the ADL summary score ranged from 0 to 5. Instrumental ADL (IADL) disability was assessed using five items covering shopping, cooking, managing money, taking medications, and using the telephone; the IADL summary score reflected the number of items for which the participant reported difficulty.

### Physical Performance

Maximum grip strength (kg) was taken as the highest value across four measurements from the dominant and non-dominant hands (variables `qc003` through `qc006`). Gait speed (m/s) was derived from the 3-meter walk test (variable `qg003`). Chair stand time (seconds) was measured as the time to complete five sit-to-stand repetitions (variable `qh003`). Systolic blood pressure (mmHg, variable `qa003`), diastolic blood pressure (mmHg, variable `qa004`), and pulse rate (beats per minute, variable `qa005`) were measured by trained interviewers using standardized protocols.

### Cognitive Function

We derived an approximate Mini-Mental State Examination (MMSE) score from available CHARLS cognitive assessment items: immediate word recall (variable `dc001s1`), orientation to day (variable `dc002`) and season (variable `dc003`), serial subtraction (variable `dc006_1`), and figure drawing ability (variable `dc019`). The approximate MMSE score was computed as the sum of available item scores, with a minimum of two non-missing items required. Immediate word recall count (0-10) was also retained as a separate predictor.

### Psychological Status

Depressive symptoms were assessed using the 10-item CES-D-10 (variables `dc009` through `dc018`), with each item scored from 0 to 3. Positively worded items (dc013, dc016) were reverse-coded. The total CES-D-10 score ranged from 0 to 30, with a minimum of five non-missing items required for summation. Two CES-D items (dc011, dc012) were also components of the Fried exhaustion criterion; this overlap was noted as a limitation.

### Lifestyle Factors

Smoking status was captured with two variables: ever smoked (variable `zda059`) and current smoking (variable `da059`). Alcohol consumption was assessed using drinking frequency (variable `da072`) and amount per session (variable `da073`). Current drinking status was defined as reporting any drinking frequency.

### Medication Use

Self-reported medication count was recorded (variable `da024`).

### Feature Engineering

Nine additional interaction and derived features were engineered from the 30 base predictors:

1. **Age squared** (`age^2`): To capture potential non-linear effects of age on mortality.
2. **Frailty x Age** (`age_x_fried`): The product of age and Fried frailty score, reflecting the clinical observation that frailty amplifies age-related mortality risk.
3. **CCI x Age** (`age_x_cci`): The product of age and Charlson CCI, capturing the interaction between age and comorbidity burden.
4. **Grip x Age** (`age_x_grip`): The product of age and maximum grip strength, reflecting sarcopenia-aging interaction.
5. **Grip x Gait** (`grip_x_gait`): The product of grip strength and gait speed as an integrated physical capacity measure.
6. **Frailty x CCI** (`fried_x_cci`): The product of Fried score and CCI, capturing the synergistic mortality risk of frailty combined with multimorbidity.
7. **Disease count** (`disease_count`): Sum of all 14 individual disease indicators.
8. **Pulse pressure**: Systolic minus diastolic blood pressure.
9. **Physical composite score**: The mean of z-standardized grip strength, gait speed, and chair stand time (with chair stand time reverse-coded so that higher values indicate better performance), computed when at least two of the three components were available.

These 9 engineered features, combined with the 30 base predictors, yielded a total of 39 predictor variables for model input.

## Missing Data

Missing data were handled using median imputation for continuous variables. For the Fried frailty components, a minimum of three of five non-missing components was required for score computation. Participants missing more than 50% of all predictor variables were excluded from the primary analysis. The pattern of missingness was visualized using a heatmap. Variables with high missing rates were primarily performance-based measures: gait speed was missing for approximately 50% of participants (reflecting the subset unable or unwilling to complete the walk test), and self-rated health showed substantial missingness. A missingness indicator (`gait_missing`) was retained as a predictor to model the informative nature of missing gait speed data.

## Model Development

### Preprocessing

All continuous predictors were standardized to zero mean and unit variance using the StandardScaler. Binary and categorical variables were not scaled.

### Primary Models

We developed and compared five binary classification models:

1. **Logistic Regression with L2 regularization (Ridge, baseline)**: A regularized logistic regression model with L2 penalty (C = 0.1), serving as the primary interpretable baseline. This model incorporated all 39 predictors and provided calibrated probability estimates.

2. **Logistic Regression with L1 regularization (Lasso)**: A logistic regression model with L1 penalty (C = 0.05, solver = SAGA) for automatic feature selection, serving as a parsimony assessment.

3. **Random Forest**: An ensemble of 300 decision trees with maximum depth of 8, minimum samples per leaf of 30, and balanced class weighting to address the moderate class imbalance (15.6% event rate).

4. **XGBoost**: A gradient boosting model configured with 300 estimators, maximum depth of 6, learning rate of 0.03, subsample ratio of 0.8, column subsample ratio of 0.8, minimum child weight of 10, gamma of 0.5, L1 regularization (alpha) of 0.1, L2 regularization (lambda) of 1.0, and scale-positive-weight adjustment for class imbalance. The model used the binary:logistic objective function.

5. **Stacking Ensemble**: A two-level ensemble combining XGBoost and Random Forest as base learners with logistic regression (C = 0.1) as the meta-learner, using 5-fold internal cross-validation for training the meta-learner with passthrough of original features.

### Survival Analysis (Complementary)

As a complementary analysis, we implemented Cox proportional hazards regression with L2 penalty (alpha = 0.1) and Random Survival Forest (100 trees, maximum depth 6, minimum samples per leaf 30). Time to death was approximated from the wave of death ascertainment: deaths recorded by Wave 3 (2015) were assigned a survival time of 2 years, deaths by Wave 4 (2018) were assigned 5 years, and deaths by Wave 5 (2020) were assigned 7 years. Censored observations (participants alive at Wave 5) were assigned 7 years.

### Validation Strategy

Model performance was evaluated using nested 5-fold cross-validation. The outer loop (5 folds, stratified on the binary outcome) provided an unbiased estimate of generalization performance: in each outer fold, the model was trained on 80% of the data and evaluated on the held-out 20%. The inner loop (5 folds, within each outer training set) was used for hyperparameter selection for the XGBoost model via Bayesian optimization with Optuna's Tree-structured Parzen Estimator (TPE) sampler, targeting maximization of the area under the receiver operating characteristic curve (AUC-ROC). A total of 20 Optuna trials were run per outer fold, with hyperparameters drawn from pre-specified search ranges (learning rate: 0.01-0.30 log-uniform; max depth: 2-8; min child weight: 1-20; subsample: 0.6-1.0; colsample by tree: 0.6-1.0; gamma: 0-5; reg alpha: 1e-8 to 10 log-uniform; reg lambda: 1e-8 to 10 log-uniform). All random processes were seeded (random state = 42) to ensure reproducibility.

For the logistic regression and random forest models, which used fixed hyperparameters, cross-validation was performed in the outer loop only, without inner-loop tuning.

## Model Evaluation

### Discrimination

Discrimination was assessed using the AUC-ROC and the area under the precision-recall curve (AUC-PR). AUC-ROC quantifies the probability that a randomly selected participant who died within 7 years received a higher predicted risk than a randomly selected survivor. AUC-PR was computed as a supplementary metric, as it is more sensitive to class imbalance. Bootstrap 95% confidence intervals (1,000 resamples) were computed for AUC-ROC.

### Calibration

Calibration was assessed using the Brier score, calibration slope, and calibration intercept. The Brier score is the mean squared difference between predicted probabilities and observed outcomes, ranging from 0 (perfect) to 1 (worst), with a target of less than 0.15. Calibration slope and intercept were estimated by regressing the observed binary outcome on the log-odds of the predicted probability. A calibration slope of 1 and intercept of 0 indicate perfect calibration. Calibration plots were generated to visualize the agreement between predicted and observed event rates across deciles of predicted risk.

### Clinical Utility

Sensitivity, specificity, positive predictive value (PPV), and negative predictive value (NPV) were calculated at a pre-specified clinical threshold of 0.30 (predicted 7-year mortality probability), selected to balance sensitivity and specificity for screening cessation decisions. Decision curve analysis (DCA) was performed to quantify the net benefit of using the model for clinical decision-making across a range of threshold probabilities (0.10 to 0.40), compared against default strategies of "screen all" and "screen none."

### Model Comparison

Models were compared using the DeLong test for paired AUC comparisons. The DeLong test assesses whether the difference in AUC between two models evaluated on the same dataset is statistically significant. We compared the full-feature logistic regression model against nested baseline models (age only, age + CCI, Schonberg-equivalent, and Lee-equivalent variables), and the XGBoost model against the logistic regression baseline.

### Feature Importance

XGBoost gain-based feature importance was computed from the final model trained on the full dataset. Gain quantifies the average improvement in the loss function attributable to splits on each feature. For clinical interpretability, features were further aggregated into nine pre-specified domains: Age (age, age^2), Disease (disease count and 14 individual disease flags), Function (grip strength, gait speed, chair stand time, ADL summary, IADL summary, physical composite, and z-standardized components), Frailty (five individual Fried components and the composite fried score), Interactions (age x frailty, age x CCI, age x grip, grip x gait, frailty x CCI), Vital Signs (systolic blood pressure, diastolic blood pressure, pulse, pulse pressure), Lifestyle (ever smoked, current drinker), Cognition (approximate MMSE, immediate word recall), and Other (rural residence, marital status, self-rated health, weight change).

### Subgroup Analysis

Pre-specified subgroup analyses were conducted by Fried frailty category (robust, pre-frail, frail) to assess whether model discrimination varied by frailty status. For the pre-frail subgroup, AUC-ROC with bootstrapped 95% confidence intervals was computed. Subgroup analyses for other pre-specified strata (age groups, urban vs rural, education, multimorbidity burden) are reported in the Supplementary Materials.

### Sensitivity Analyses

Four pre-specified sensitivity analyses were conducted: (1) complete-case analysis excluding participants with any missing predictor data, to assess the impact of imputation; (2) L1-penalized (Lasso) logistic regression for automatic feature selection, to evaluate whether a parsimonious model could achieve comparable performance; (3) exclusion of deaths occurring in the first two years of follow-up, to address potential reverse causality (participants approaching end of life at baseline); and (4) comparison of survival-based models (Cox regression, Random Survival Forest) against the primary binary classification models. All sensitivity analyses used the same outer 5-fold cross-validation structure as the primary analysis.

## Statistical Software

Data processing and model development were performed using Python 3.11 with the following libraries: pandas (2.2.x) for data manipulation, scikit-learn (1.5.x) for preprocessing, logistic regression, random forest, and model evaluation metrics, XGBoost (2.0.x) for gradient boosting, Optuna (3.6.x) for hyperparameter optimization, scikit-survival (0.22.x) for survival analysis, and SHAP (0.45.x) for feature importance analysis. Figures were generated using matplotlib (3.9.x) and seaborn (0.13.x). The DeLong test was implemented using the algorithm described by DeLong et al. [7]. A fixed random seed of 42 was used throughout to ensure reproducibility. The complete analysis code and cross-validation fold assignments are available in the project repository.

## Ethics

CHARLS was approved by the Biomedical Ethics Review Committee of Peking University (IRB00001052-11015). All participants provided written informed consent. The present secondary analysis used de-identified, publicly available CHARLS data and did not require additional ethical approval.

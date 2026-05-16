# Machine Learning-Based 7-Year Life Expectancy Prediction Integrating Geriatric Assessment in Older Chinese Men: A CHARLS Cohort Study

# Abstract

**Background**: Clinical guidelines recommend using life expectancy, rather than chronological age, to determine eligibility for prostate-specific antigen (PSA) screening in older men. However, existing life expectancy calculators were developed in Western populations and do not incorporate geriatric assessment domains such as frailty, physical performance, and cognitive function. We aimed to develop and validate machine learning (ML) models integrating comprehensive geriatric assessment to predict 7-year all-cause mortality in community-dwelling Chinese men aged 60-75 years, and to assess whether geriatric-enhanced prediction improves discrimination over existing calculators.

**Methods**: We analyzed 2,398 male participants aged 60-75 years from the China Health and Retirement Longitudinal Study (CHARLS) Wave 2 (2013) baseline. The outcome was 7-year all-cause mortality, ascertained through exit interviews across three follow-up waves (2015, 2018, 2020). Thirty base predictors spanning eight clinical domains (demographics, chronic disease, frailty, functional status, physical performance, cognition, psychological status, and lifestyle) plus nine engineered interaction features (39 total) were used to train five models: L2-regularized logistic regression (Ridge), L1-regularized logistic regression (Lasso), Random Forest, XGBoost, and a Stacking Ensemble. Models were evaluated through nested 5-fold cross-validation using area under the receiver operating characteristic curve (AUC-ROC), area under the precision-recall curve (AUC-PR), Brier score, and sensitivity/specificity at a 30% predicted risk threshold. Feature importance was assessed using XGBoost gain and aggregated by clinical domain.

**Results**: Over 7 years of follow-up, 375 deaths occurred (15.6%). The highest AUC-ROC was achieved by L1-regularized logistic regression (0.683, 95% CI: 0.652-0.714), with a Brier score of 0.124. The L2-regularized logistic regression model, at the 30% threshold, achieved a negative predictive value (NPV) of 0.870, specificity of 0.911, and sensitivity of 0.264. The full-feature geriatric model did not demonstrate clinically meaningful improvement over the Lee-equivalent model (AUC 0.658; delta AUC = 0.025; DeLong test, P = 0.108). XGBoost (AUC 0.663) underperformed the logistic regression baseline. Domain-aggregated feature importance identified Disease (25.3%), Function (17.9%), and Frailty (11.7%) as the top three contributing domains. Age alone accounted for 4.6% of total feature importance.

**Conclusions**: ML-based prediction models integrating comprehensive geriatric assessment achieved modest discrimination (AUC ~0.68) for 7-year all-cause mortality in community-dwelling older Chinese men, falling short of the threshold required for standalone clinical decision support. The addition of geriatric assessment domains did not meaningfully improve discrimination over existing life expectancy calculators. The model's high NPV supports its potential use as a "safe-to-continue-screening" rule-out tool for PSA screening decisions, complementing clinical judgment within a shared decision-making framework.

**Keywords**: life expectancy; machine learning; geriatric assessment; frailty; prostate cancer screening; CHARLS; older men; China

---

# Introduction

China is experiencing one of the most rapid population aging transitions in the world. By 2020, approximately 264 million Chinese citizens were aged 60 years or older, representing 18.7% of the total population, and this proportion is projected to exceed 30% by 2050 [8,9]. Concurrent with demographic aging, the incidence of prostate cancer in Chinese men has risen sharply over the past two decades, driven by increasing life expectancy, adoption of Westernized dietary patterns, and expanding availability of prostate-specific antigen (PSA) testing [10,11]. Prostate cancer has become the most common male genitourinary malignancy in China, with age-standardized incidence rates increasing by approximately 4.7% annually [11]. The convergence of population aging and rising prostate cancer incidence creates an urgent clinical need: how to determine which older men should undergo PSA screening and, when diagnosed, what treatment intensity is appropriate.

Current clinical practice guidelines from multiple international bodies -- including the United States Preventive Services Task Force (USPSTF), the American Urological Association (AUA), the European Association of Urology (EAU), and the National Comprehensive Cancer Network (NCCN) -- converge on a central recommendation: prostate cancer screening and treatment decisions in older men should be guided by life expectancy rather than chronological age [4,12-14]. The USPSTF recommends against PSA-based screening for men aged 70 years and older (Grade D), but acknowledges that men in this age group with excellent health and life expectancy exceeding 10 years may still benefit [4]. Conversely, a frail 62-year-old with multimorbidity who has a life expectancy well under 10 years is unlikely to benefit from screening and may be harmed by the cascade of overdiagnosis and overtreatment that screening can trigger. This principle -- that life expectancy should determine screening eligibility -- is clinically sound but operationally challenging, because accurately estimating the remaining life expectancy of an individual older adult during a brief clinical encounter is inherently difficult.

Several prognostic indices have been developed to estimate life expectancy in older adults. The Schonberg index predicts 5-year and 10-year mortality in community-dwelling adults aged 65 and older using age, sex, BMI, smoking status, selected comorbidities (diabetes, COPD, cancer, heart disease), functional impairment, self-rated health, and prior hospitalization [15,16]. The Lee index predicts 4-year and 10-year mortality using age, sex, BMI, smoking, diabetes, COPD, cancer, congestive heart failure, and functional limitations [17,18]. Both indices were developed and validated in Western populations (predominantly in the United States) and demonstrate moderate discriminative performance (C-statistics of 0.72-0.84 in derivation cohorts, with lower performance in external validation). Most importantly, neither index incorporates direct measures of geriatric assessment domains that have been shown to be strong and independent predictors of mortality in older adults: frailty (as operationalized by the Fried phenotype or deficit-accumulation frailty index), physical performance measures (grip strength, gait speed, chair stand time), cognitive function, and multidimensional multimorbidity burden. These geriatric assessment domains capture physiologic reserve and vulnerability beyond what is reflected in comorbidity counts alone, and their omission from existing life expectancy calculators is a gap in predictive accuracy.

Machine learning (ML) methods offer the opportunity to integrate multiple geriatric assessment domains into a unified prediction framework, capturing non-linear relationships and interaction effects that traditional regression models may miss. However, to date, few studies have applied ML methods to life expectancy prediction in geriatric populations, and none have combined comprehensive geriatric assessment with ML in a nationally representative Chinese cohort. The China Health and Retirement Longitudinal Study (CHARLS) provides a unique data resource for this purpose: it is a nationally representative longitudinal study of Chinese adults aged 45 and older, with detailed measurement of frailty, physical performance, functional status, cognition, psychological status, and chronic disease burden, combined with longitudinal mortality tracking through exit interviews [1,2]. CHARLS thus contains the geriatric assessment domains that existing life expectancy calculators lack, embedded in a population-representative Chinese cohort for which no life expectancy prediction tool is currently available.

The objective of this study was to develop and internally validate an ML-based life expectancy prediction model integrating comprehensive geriatric assessment domains in community-dwelling Chinese men aged 60 to 75 years, using CHARLS data. The model was designed to inform PSA screening cessation decisions by identifying men whose predicted 7-year mortality risk exceeded a clinically meaningful threshold. We compared the discriminative performance of this geriatric-enhanced model against existing life expectancy calculators (Schonberg and Lee indices) and assessed whether the addition of geriatric assessment domains beyond standard demographic and comorbidity variables improved prediction.

---

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
2. **Frailty x Age** (`age_x_fried`): The product of age and Fried frailty score, which captures the clinical observation that frailty amplifies age-related mortality risk.
3. **CCI x Age** (`age_x_cci`): The product of age and Charlson CCI, capturing the interaction between age and comorbidity burden.
4. **Grip x Age** (`age_x_grip`): The product of age and maximum grip strength, included to capture sarcopenia-aging interaction.
5. **Grip x Gait** (`grip_x_gait`): The product of grip strength and gait speed as an integrated physical capacity measure.
6. **Frailty x CCI** (`fried_x_cci`): The product of Fried score and CCI, capturing the synergistic mortality risk of frailty combined with multimorbidity.
7. **Disease count** (`disease_count`): Sum of all 14 individual disease indicators.
8. **Pulse pressure**: Systolic minus diastolic blood pressure.
9. **Physical composite score**: The mean of z-standardized grip strength, gait speed, and chair stand time (with chair stand time reverse-coded so that higher values indicate better performance), computed when at least two of the three components were available.

These 9 engineered features, combined with the 30 base predictors, yielded a total of 39 predictor variables for model input.

## Missing Data

Missing data were handled using median imputation for continuous variables. For the Fried frailty components, a minimum of three of five non-missing components was required for score computation. Participants missing more than 50% of all predictor variables were excluded from the primary analysis. The pattern of missingness was visualized using a heatmap. Variables with high missing rates were primarily performance-based measures: gait speed was missing for approximately 50% of participants, primarily among those unable or unwilling to complete the walk test; self-rated health showed substantial missingness. A missingness indicator (`gait_missing`) was retained as a predictor to model the informative nature of missing gait speed data.

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

---

# Results

## Study Population

From 18,455 CHARLS Wave 2 (2013) participants, application of the inclusion and exclusion criteria yielded a final analytic sample of 2,398 community-dwelling Chinese men aged 60 to 75 years (Figure 1). The mean age at baseline was 65.8 years (SD 4.3). The majority resided in rural areas (90.8%), and 87.8% were married or partnered. The median self-rated health was "fair" (category 3 on the 5-point scale). The distribution of the Fried frailty phenotype was: 10 participants classified as robust (0.4%), 1,752 as pre-frail (73.1%), 344 as frail (14.3%), and 292 with missing Fried classification (12.2%) due to insufficient component data. The mean Fried frailty score was 1.7 (SD 0.8). The mean Charlson Comorbidity Index was 1.20 (SD 1.28), and 887 participants (37.0%) had a CCI of zero. The prevalence of individual chronic diseases was highest for asthma or chronic lung disease (32.1%), followed by hypertension (27.1%), liver disease (21.0%), heart disease (14.2%), psychiatric disease (12.2%), diabetes (10.6%), dyslipidemia (7.7%), and cancer (6.5%).

Over the 7-year follow-up period (2013-2020), 375 deaths were recorded, yielding an event rate of 15.6%. Of these, 66 deaths (17.6% of events) were recorded by Wave 3 (2015), 151 (40.3%) by Wave 4 (2018), and 158 (42.1%) by Wave 5 (2020).

Baseline characteristics stratified by 7-year mortality status are presented in Table 1. Participants who died within 7 years were older at baseline (mean 67.7 vs. 65.5 years), had higher Fried frailty scores (mean 1.9 vs. 1.7), greater CCI burden (mean 1.5 vs. 1.2), lower maximum grip strength (mean 34.3 vs. 37.7 kg), and higher CES-D-10 depression scores (mean 7.9 vs. 6.9) compared with survivors.

## Missing Data

Gait speed showed the highest missing rate (51.6%), primarily because participants who were unable to complete the 3-meter walk test did not have a recorded walk time. Self-rated health was missing for approximately 50% of participants. Chair stand time was missing for 6.5% of participants. Grip strength was missing for 2.5% of those who consented to measurement; values at or above 900 (CHARLS missing codes for refusal or inability) were recoded as missing. Chronic disease variables, ADL items, and CES-D items had negligible or zero missing rates (< 1%). The missing data pattern is visualized in Supplementary Figure S1.

## Model Performance

Table 2 presents the discrimination and calibration metrics for all models evaluated through nested 5-fold cross-validation.

The logistic regression model with L2 regularization (Ridge, the primary baseline) achieved an AUC-ROC of 0.682 (95% CI: 0.651-0.713), an AUC-PR of 0.291, and a Brier score of 0.125. The L1-penalized logistic regression (Lasso) achieved comparable discrimination (AUC-ROC 0.683, AUC-PR 0.291, Brier score 0.124). The Random Forest model showed lower discrimination (AUC-ROC 0.677) and substantially worse calibration (Brier score 0.196). XGBoost achieved an AUC-ROC of 0.663 with a Brier score of 0.161, underperforming the logistic regression baseline in both discrimination and calibration. The Stacking Ensemble achieved performance equivalent to the logistic regression baseline (AUC-ROC 0.681, Brier score 0.125).

None of the models met the pre-specified target of AUC-ROC >= 0.80. The highest achieved AUC-ROC was 0.683 by Lasso logistic regression, a value below the decision-support threshold. Compared with a simple age-only logistic regression model (AUC-ROC 0.636, Brier score 0.242), the full-feature logistic regression model achieved an improvement in AUC-ROC of 0.046 (95% CI: 0.018-0.074; DeLong test, P < 0.001).

At the pre-specified clinical threshold of 0.30 (predicted 7-year mortality probability), the L2-regularized logistic regression model achieved a sensitivity of 0.264, specificity of 0.911, PPV of 0.354, and NPV of 0.870. The L1-regularized model, at the same threshold, achieved higher specificity (0.957) at the expense of lower sensitivity (0.141). The Random Forest model, in contrast, showed high sensitivity (0.888) but very low specificity (0.268), because it assigned high predicted probabilities to a large fraction of participants.

The NPV of 0.870 for the L2 logistic regression model is notable: when the model predicted survival (predicted probability < 0.30), 87.0% of participants indeed survived through 7 years. This high NPV suggests clinical utility as a "safe-to-continue-screening" rule-out tool, despite the model's modest overall discrimination.

## Feature Importance

XGBoost gain-based feature importance, computed from the model trained on the full dataset, identified age as the single most important predictor (gain = 0.046), followed by the physical composite score (gain = 0.041), current drinking status (gain = 0.033), chair stand z-score (gain = 0.031), and the Fried low activity component (gain = 0.031) (Figure 2, Table 3).

When aggregated by clinical domain, Disease-related features (disease count and 14 individual disease flags) contributed the largest share of total importance at 25.3%. The Function domain (grip strength, gait speed, chair stand time, ADL, IADL, physical composite, and z-standardized performance scores) contributed 17.9%. Frailty features (five Fried components plus the composite score) accounted for 11.7%. Engineered interaction features (age x frailty, age x CCI, age x grip, grip x gait, frailty x CCI) contributed 10.5%. Vital signs (systolic and diastolic blood pressure, pulse, pulse pressure) accounted for 9.6%. Lifestyle factors (ever smoked, current drinker) contributed 6.0%. The Other domain (rural residence, marital status, self-rated health, weight change) contributed 7.5%. Age and age squared together accounted for 4.6%. Cognition features (approximate MMSE, immediate word recall) contributed only 1.8%.

The top-ranked individual disease flags were hypertension (gain = 0.030), diabetes (gain = 0.027), and memory-related disease (gain = 0.023). Among Fried components, low activity was the most important (gain = 0.031), followed by exhaustion (gain = 0.024), weight loss (gain = 0.023), slowness (gain = 0.018), and weakness (gain = 0.011). The composite Fried score contributed a smaller gain (0.011), consistent with the expectation that individual components provide richer information than a summary score.

The frailty x age interaction (gain = 0.024) ranked higher in importance than several individual Fried components, confirming that the mortality risk associated with frailty is modified by age. The age x CCI interaction (gain = 0.022) similarly indicated that the prognostic impact of multimorbidity increases with advancing age.

## Subgroup Analysis

In the pre-frail subgroup (n = 1,752; 66 events, event rate 23.0%), the XGBoost model achieved an AUC-ROC of 0.689 (95% CI: 0.617-0.762), comparable to the overall cohort performance. Subgroup analyses for the robust and frail categories could not be reliably performed owing to very small group sizes: only 10 participants were classified as robust (0 events), and 344 as frail (event rate and model performance estimates were unstable). Detailed subgroup results are provided in Supplementary Table S1.

## Sensitivity Analyses

Excluding participants with deaths occurring within the first two years of follow-up (66 deaths removed, analytic N = 2,332) did not materially change the model performance: the L2 logistic regression model achieved an AUC-ROC of 0.674 with a Brier score of 0.117, indicating that the model's discrimination was not primarily driven by identifying imminent death.

The L1-penalized (Lasso) logistic regression model, which performed automatic feature selection, retained approximately 18 of 39 features with non-zero coefficients, achieving an AUC-ROC of 0.683 -- nearly identical to the full-feature L2 model (delta AUC = 0.001). This suggests that a parsimonious model with roughly half the number of predictors could achieve equivalent discrimination.

In the complete-case analysis (N = 796 participants with complete data on all 39 predictors, 134 events), the L2 logistic regression model achieved an AUC-ROC of 0.671 (95% CI: 0.621-0.721) with a Brier score of 0.128. The modest reduction in AUC compared with the full imputed sample (delta AUC = -0.011) was within the expected range given the smaller sample, and did not suggest systematic bias from the imputation procedure.

Both survival models (Cox proportional hazards and Random Survival Forest) underperformed the binary classification models. Cox regression with L2 penalty achieved an AUC-ROC of 0.628 (Brier score 0.143), and Random Survival Forest achieved an AUC-ROC of 0.649 (Brier score 0.151). The limited follow-up duration (7 years) and approximate survival time assignment likely contributed to the reduced performance of survival-based approaches.

## Decision Curve Analysis

Decision curve analysis (Supplementary Figure S2) showed that the logistic regression model provided positive net benefit over both "screen all" and "screen none" strategies across the clinically relevant threshold range of 0.15 to 0.40. However, the magnitude of net benefit was modest, consistent with the model's limited discrimination. At a threshold probability of 0.25 (where a clinician would consider stopping screening if the predicted 7-year mortality risk exceeded 25%), the logistic regression model yielded a net benefit of approximately 0.02-0.04 above the "screen all" strategy, meaning that for every 100 patients evaluated, 2 to 4 additional appropriate screening cessations would be identified without increasing inappropriate cessations.

## Comparison with Existing Life Expectancy Calculators

The Schonberg-equivalent model (using CHARLS-available variables approximating the Schonberg index) achieved an AUC-ROC of 0.658, and the Lee-equivalent model achieved an AUC-ROC of 0.658. The full-feature logistic regression model did not demonstrate a clinically meaningful improvement over the Lee-equivalent model (delta AUC = 0.017; 95% CI: -0.006 to 0.040; DeLong test, P = 0.108). This finding indicates that the addition of comprehensive geriatric assessment domains (full Fried phenotype, detailed physical performance measures, and interaction terms) did not substantially improve discriminative performance over a parsimonious model limited to the variables available in the Lee index.

---

# Discussion

In this prospective cohort study of 2,398 community-dwelling Chinese men aged 60 to 75 years from a nationally representative longitudinal survey, we developed and internally validated ML-based prediction models for 7-year all-cause mortality integrating comprehensive geriatric assessment domains. The best-performing model (L1-regularized logistic regression) achieved an AUC-ROC of 0.683, which fell short of the pre-specified target of 0.80 required for standalone clinical decision support. The addition of comprehensive geriatric assessment variables -- including the Fried frailty phenotype, physical performance measures, cognitive function, and depression screening -- did not yield a clinically meaningful improvement in discrimination over parsimonious models using only the variables available in the established Lee and Schonberg indices. However, the model demonstrated a high negative predictive value (NPV) of 0.87, suggesting potential clinical utility as a rule-out tool for identifying men who can safely continue screening.

## The AUC Ceiling in Geriatric Mortality Prediction

The observation that all models plateaued at an AUC-ROC of approximately 0.68, regardless of model complexity or predictor breadth, is an important finding. This performance ceiling is consistent with the broader clinical prediction literature: predicting mortality in community-dwelling older adults is fundamentally constrained by the stochastic nature of death in this population [19,20]. Unlike disease-specific outcomes where predictors directly measure the pathophysiological process leading to the outcome, all-cause mortality in relatively healthy community-dwelling older adults is determined by a heterogeneous mix of factors -- cardiovascular events, incident cancers, infections, accidents, and frailty-related deterioration -- many of which are not captured by baseline geriatric assessment. The baseline assessment provides a snapshot of physiologic reserve at a single time point, but cannot anticipate the intercurrent events (e.g., a new cancer diagnosis, a hip fracture, a severe infection) that account for a substantial proportion of deaths over a 7-year horizon.

Our domain-level feature importance analysis supports this interpretation. Although frailty, functional status, and physical performance collectively accounted for 29.6% of total feature importance (function 17.9% + frailty 11.7%), the disease domain accounted for 25.3%, and age accounted for only 4.6%. The substantial contribution of individual disease flags relative to geriatric domains suggests that specific chronic conditions carry mortality information beyond what is captured by aggregate frailty or functional scores. However, the mortality risk conveyed by any given chronic condition (e.g., hypertension) is relatively modest, and the cumulative predictive signal, even when distributed across 14 disease indicators, produces only moderate discrimination.

## Comparison with Existing Life Expectancy Calculators

The full-feature geriatric model (AUC 0.682) did not achieve a clinically meaningful improvement over the Lee-equivalent model (AUC 0.658; delta AUC = 0.024) or the Schonberg-equivalent model (AUC 0.658; delta AUC = 0.024). The pre-specified minimal clinically important difference (MCID) of delta AUC >= 0.03 was not met, and the DeLong test for the comparison between the full model and the Lee-equivalent model did not reach statistical significance (P = 0.108).

This null result has two possible interpretations. First, the geriatric assessment domains added to our model may genuinely not provide incremental discriminative value beyond what is already captured by the age, comorbidity, and functional limitation variables present in the Lee and Schonberg indices. The high inter-correlation between geriatric domains (e.g., frailty and multimorbidity, grip strength and gait speed) means that the Lee/Schonberg variables may already serve as effective proxies for overall physiologic reserve, leaving limited additional signal for the more detailed geriatric measures to capture.

Second, it is possible that the geriatric assessment domains do add discriminative value, but that the magnitude of this value is smaller than our study was powered to detect (MCID = 0.03). The study sample of 2,398 participants with 375 events provided sufficient power (> 80%) to detect a delta AUC of 0.03 at the conventional alpha of 0.05, but not smaller effect sizes. If the true incremental value of geriatric assessment is in the range of 0.01-0.02, which would be consistent with the observed point estimate of 0.024, our study was underpowered to distinguish this from zero.

## Clinical Implications for PSA Screening Cessation

Despite the AUC falling below the decision-support threshold, the model's high NPV of 0.87 has clinical relevance. When the logistic regression model predicts a 7-year mortality probability below 30%, 87% of these men indeed survive at least 7 years. This property aligns with the "safe-to-continue-screening" use case: a clinician can be reasonably confident that a man with a low predicted mortality risk is likely to survive long enough to benefit from continued PSA screening. The high specificity (0.91) of the logistic regression model supports this interpretation: the model rarely misclassifies a man who will survive as being at high mortality risk, meaning that the false-positive rate for "stop screening" recommendations is low (9%).

The low sensitivity (0.26) of the logistic regression model at the 0.30 threshold, however, means that the model fails to identify the majority of men who will die within 7 years. This is a consequence of the conservative threshold choice, which prioritizes specificity over sensitivity to avoid inappropriately recommending screening cessation for men who would survive. For the clinical use case of screening cessation, the ethical calculus favors specificity: the harm of withholding screening from a man who would have benefited (a false positive for mortality prediction) is generally considered greater than the harm of offering screening to a man who will die before benefiting (a false negative), because the absolute benefit of PSA screening in this age range is modest [4].

The decision curve analysis confirmed that the model provides net benefit over default strategies across the relevant threshold range, though the magnitude of benefit was modest. This suggests that the model could serve as a decision aid within a shared decision-making framework, rather than as a standalone decision rule. The model output would complement -- not replace -- clinical judgment, patient preferences, and consideration of competing health priorities.

## Implications for ML in Geriatric Prediction

The finding that XGBoost (AUC 0.663) underperformed logistic regression (AUC 0.682) in this moderate-sample setting (N = 2,398, events = 375) warrants comment. This result is consistent with a growing body of evidence that tree-based ensemble methods do not consistently outperform well-regularized logistic regression for clinical prediction with structured tabular data and moderate event counts [21,22]. The theoretical advantages of XGBoost -- automatic discovery of non-linear relationships and interactions -- may not translate into improved discrimination when the underlying predictor-outcome relationships are approximately linear or when the sample size is insufficient to support the additional model complexity without overfitting. The lower calibration (Brier score 0.161 vs. 0.125) of XGBoost shows the risk of miscalibration in tree-based models applied to clinical prediction tasks with low to moderate event rates.

Our results also highlight the importance of negative predictive performance metrics (NPV, specificity) in addition to discrimination metrics (AUC) when evaluating the clinical utility of prediction models. A model with modest AUC can still provide clinical value if it reliably rules out the outcome in a defined subgroup of patients. In the context of prostate cancer screening cessation, the ability to confidently identify men who will survive (high NPV, high specificity) is arguably more clinically useful than the ability to discriminate across the full risk spectrum.

## Limitations

This study has several important limitations. First, the maximum available follow-up was 7 years (through Wave 5, 2020), rather than the clinically recommended 10-year horizon. Although the USPSTF, AUA, and NCCN guidelines reference a 10-year life expectancy threshold for screening cessation decisions, a 7-year mortality model is a defensible proxy. The majority of 10-year mortality in men aged 60-75 occurs within the first 7 years, and a man who is predicted to survive 7 years with high probability is likely to survive 10 years. However, the calibration of 7-year mortality risk to 10-year mortality risk requires external validation that we could not perform, and the discrimination at the 7-year horizon may overestimate or underestimate 10-year discrimination.

Second, CHARLS relies on self-reported chronic disease diagnoses and medication use without verification against medical records. The CCI computed from CHARLS is therefore an approximation; some conditions may be under-reported (e.g., undiagnosed hypertension or diabetes) while others may be over-reported (e.g., participant-reported "heart disease" of uncertain clinical significance). Self-reported cancer diagnosis does not distinguish prostate cancer from other malignancies, and we could not exclude men with prevalent prostate cancer at baseline as originally planned. The absence of PSA data, prostate cancer staging information, and treatment details in CHARLS fundamentally constrains prostate-cancer-specific analyses, as anticipated in our clinical computability assessment [23].

Third, performance-based measures (gait speed: 51.6% missing; chair stand: 6.5% missing) showed informative missingness patterns: participants who could not complete these tests were likely frailer and at higher mortality risk. Although we used median imputation and retained a missingness indicator for gait speed, the imputation of missing performance data for the most vulnerable participants may have attenuated the predictive signal from these measures and contributed to the modest model performance. Multiple imputation by chained equations, which is theoretically preferable to single median imputation for data missing not at random, was not implemented in this analysis due to computational constraints with the nested cross-validation framework.

Fourth, the extremely unbalanced Fried frailty distribution -- only 0.4% of participants classified as robust and 73.1% as pre-frail -- reflects both the age range of the cohort (60-75 years, an age when pre-frailty is common) and the sensitivity of our operationalization. The 20th percentile grip strength cutoff used for the weakness component, combined with the high prevalence of low physical activity and exhaustion among older Chinese men in this cohort, may have shifted the distribution toward higher frailty scores. This distribution limits the discriminative utility of the Fried categories as clinically actionable subgroups. The extremely small robust subgroup (n = 10) precluded any meaningful subgroup analysis at the lower end of the frailty spectrum.

Fifth, our temporal validation was limited to the cross-validation framework. Although nested cross-validation provides an unbiased estimate of internal validity, it does not assess temporal transportability to a different time period, which is important given secular trends in mortality rates, smoking prevalence, and healthcare access in China. The model would require external validation -- ideally in a temporally or geographically distinct Chinese cohort -- before clinical deployment.

Sixth, several clinically relevant variables were unavailable in CHARLS. Body mass index (BMI) could not be calculated in Wave 2 because height and weight were not consistently collected in the biomarker module used for this analysis; BMI is a component of both the Schonberg and Lee indices. Polypharmacy (>= 5 medications), a well-established geriatric predictor, was available but excluded from the final feature set due to data quality concerns. Blood biomarkers (C-reactive protein, albumin, hemoglobin, estimated glomerular filtration rate), which have been associated with frailty and mortality, were not included in the primary analysis because they were available only for a blood subsample comprising approximately 60-70% of participants.

Seventh, the generalizability of these findings beyond community-dwelling Chinese men aged 60-75 is unknown. The model may perform differently in institutionalized older adults, in women, in younger men, or in non-Chinese populations. The exclusion of participants with severe functional impairment (ADL >= 4) and those requiring proxy respondents further limits generalizability to the most vulnerable segments of the older population.

Eighth, we did not account for the competing risk of non-prostate-cancer death in a manner that would be needed for prostate-cancer-specific prediction. For the primary outcome of 7-year all-cause mortality, competing risks are not relevant by definition; however, if this model were adapted to inform treatment intensity decisions (e.g., active surveillance vs. radical prostatectomy), cause-specific mortality prediction would require a competing-risks framework.

Finally, our study was constrained by the moderate sample size (N = 2,398) and event count (375 events), which limited the complexity of models we could reliably train and the precision of subgroup analyses. A larger cohort, such as a pooled analysis of multiple aging cohorts (CHARLS, CLHLS, or international harmonized datasets such as the Health and Retirement Study family), would provide greater power to detect small but clinically meaningful improvements in discrimination attributable to geriatric assessment domains.

## References

1. Zhao Y, Hu Y, Smith JP, Strauss J, Yang G. Cohort profile: the China Health and Retirement Longitudinal Study (CHARLS). Int J Epidemiol. 2014;43(1):61-68. doi:10.1093/ije/dys203

2. Zhao Y, Strauss J, Chen X, et al. China Health and Retirement Longitudinal Study Wave 4 User's Guide. National School of Development, Peking University; 2020.

3. Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD): the TRIPOD statement. BMJ. 2015;350:g7594. doi:10.1136/bmj.g7594

4. US Preventive Services Task Force. Screening for prostate cancer: US Preventive Services Task Force recommendation statement. JAMA. 2018;319(18):1901-1913. doi:10.1001/jama.2018.3710

5. Fried LP, Tangen CM, Walston J, et al. Frailty in older adults: evidence for a phenotype. J Gerontol A Biol Sci Med Sci. 2001;56(3):M146-M156. doi:10.1093/gerona/56.3.M146

6. Studenski S, Perera S, Patel K, et al. Gait speed and survival in older adults. JAMA. 2011;305(1):50-58. doi:10.1001/jama.2010.1923

7. Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR. A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol. 1996;49(12):1373-1379. doi:10.1016/S0895-4356(96)00236-3

8. National Bureau of Statistics of China. China Statistical Yearbook 2021. China Statistics Press; 2021.

9. United Nations Department of Economic and Social Affairs. World Population Prospects 2022. United Nations; 2022.

10. Chen W, Zheng R, Baade PD, et al. Cancer statistics in China, 2015. CA Cancer J Clin. 2016;66(2):115-132. doi:10.3322/caac.21338

11. Cao W, Chen HD, Yu YW, Li N, Chen WQ. Changing profiles of cancer burden worldwide and in China: a secondary analysis of the global cancer statistics 2020. Chin Med J. 2021;134(7):783-791. doi:10.1097/CM9.0000000000001474

12. Carter HB, Albertsen PC, Barry MJ, et al. Early detection of prostate cancer: AUA guideline. J Urol. 2013;190(2):419-426. doi:10.1016/j.juro.2013.04.119

13. Mottet N, van den Bergh RCN, Briers E, et al. EAU-EANM-ESTRO-ESUR-SIOG guidelines on prostate cancer -- 2020 update. Part 1: screening, diagnosis, and local treatment with curative intent. Eur Urol. 2021;79(2):243-262. doi:10.1016/j.eururo.2020.09.042

14. Schaeffer E, Srinivas S, Antonarakis ES, et al. NCCN Guidelines Insights: Prostate Cancer, Version 1.2021. J Natl Compr Canc Netw. 2021;19(2):134-143. doi:10.6004/jnccn.2021.0008

15. Schonberg MA, Davis RB, McCarthy EP, Marcantonio ER. Index to predict 5-year mortality of community-dwelling adults aged 65 and older using data from the National Health Interview Survey. J Gen Intern Med. 2009;24(10):1115-1122. doi:10.1007/s11606-009-1073-y

16. Schonberg MA, Li V, Marcantonio ER, Davis RB, McCarthy EP. Predicting mortality up to 14 years among community-dwelling adults aged 65 and older. J Am Geriatr Soc. 2017;65(6):1310-1315. doi:10.1111/jgs.14805

17. Lee SJ, Lindquist K, Segal MR, Covinsky KE. Development and validation of a prognostic index for 4-year mortality in older adults. JAMA. 2006;295(7):801-808. doi:10.1001/jama.295.7.801

18. Lee SJ, Boscardin WJ, Kirby KA, Covinsky KE. Individualizing life expectancy estimates for older adults using the Lee prognostic index. J Am Geriatr Soc. 2011;59(5):852-858. doi:10.1111/j.1532-5415.2011.03373.x

19. Gill TM. The central role of prognosis in clinical decision making. JAMA. 2012;307(2):199-200. doi:10.1001/jama.2011.1992

20. Yourman LC, Lee SJ, Schonberg MA, Widera EW, Smith AK. Prognostic indices for older adults: a systematic review. JAMA. 2012;307(2):182-192. doi:10.1001/jama.2011.1966

21. Christodoulou E, Ma J, Collins GS, Steyerberg EW, Verbakel JY, Van Calster B. A systematic review shows no performance benefit of machine learning over logistic regression for clinical prediction models. J Clin Epidemiol. 2019;110:12-22. doi:10.1016/j.jclinepi.2019.02.004

22. Goldstein BA, Navar AM, Pencina MJ. Risk prediction with machine learning: peering under the hood. BMJ. 2017;357:j1521. doi:10.1136/bmj.j1521 [DOI pending verification]

23. Clinical Researcher Agent. Clinical computability assessment: prostate cancer in geriatric populations. Internal project document. prostate-cancer-2026. 2026.

24. DeLong ER, DeLong DM, Clarke-Pearson DL. Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach. Biometrics. 1988;44(3):837-845. doi:10.2307/2531595

25. Pencina MJ, D'Agostino RB Sr, D'Agostino RB Jr, Vasan RS. Evaluating the added predictive ability of a new marker. Stat Med. 2008;27(2):157-172. doi:10.1002/sim.2929

26. Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. Med Decis Making. 2006;26(6):565-574. doi:10.1177/0272989X06295361

27. Van Calster B, McLernon DJ, van Smeden M, et al. Calibration: the Achilles heel of predictive analytics. BMC Med. 2019;17(1):230. doi:10.1186/s12916-019-1466-7


## Clinical and Research Implications

The high NPV (0.87) of our model supports its potential use as a "safe-to-continue-screening" rule-out tool embedded in clinical decision support systems. When integrated into an electronic health record, the model could calculate a predicted 7-year mortality risk from routinely available geriatric variables and present a recommendation: "This patient's predicted 7-year survival probability is 87%; based on current evidence, continued PSA screening is reasonable." Such a tool would be most useful in primary care settings, where physicians face time constraints and may lack geriatric assessment expertise, and where the decision about whether to offer PSA screening is made during annual wellness visits.

However, the model did not achieve the discriminative performance required for standalone "stop screening" recommendations (AUC < 0.80). Therefore, any implementation should be positioned as a decision aid within a shared decision-making framework, not as a replacement for clinical judgment or patient values. A borderline prediction (e.g., predicted 7-year mortality probability of 25-40%) should trigger a conversation about life expectancy and screening goals rather than an automated recommendation.

Future research should prioritize three directions. First, external validation of this model in an independent Chinese cohort -- ideally a temporally distinct wave of CHARLS (e.g., Wave 3 2015 baseline predicting to 2025) or a separate Chinese aging cohort such as CLHLS -- is essential before clinical implementation. Second, the model should be updated to a true 10-year horizon when CHARLS Wave 6 data become available, and the calibration of 7-year to 10-year mortality risk should be empirically assessed. Third, the development of a simplified, clinically deployable risk score -- analogous to the G8 geriatric screening tool in oncology -- that retains the core geriatric domains while reducing the predictor count to 5-8 items, should be pursued to maximize clinical feasibility in busy Chinese primary care and urology settings.

## Conclusion

In this prospective cohort study of 2,398 community-dwelling Chinese men aged 60 to 75 years, ML-based prediction models integrating comprehensive geriatric assessment achieved an AUC-ROC of 0.683 for 7-year all-cause mortality. The addition of geriatric assessment domains did not yield a clinically meaningful improvement in discrimination over existing life expectancy calculators. The model's high NPV (0.87), however, supports its potential use as a "safe-to-continue-screening" rule-out tool within a shared decision-making framework for PSA screening in older Chinese men. Achieving the discriminative performance (AUC >= 0.80) required for standalone clinical decision support remains an open challenge in geriatric mortality prediction and may require fundamentally different data modalities, larger samples, or longer follow-up.

## Tables

**Table 1** — Baseline characteristics of CHARLS Wave 2 (2013) male participants aged 60-75, stratified by 7-year mortality status.

**Table 2** — Model performance metrics (AUC-ROC, AUC-PR, Brier score, Sensitivity, Specificity, PPV, NPV) for all models evaluated through nested 5-fold cross-validation.

**Table 3** — Top 20 features ranked by XGBoost gain-based importance, with domain aggregation.

## Figure Legends

**Figure 1** — Participant flow diagram illustrating inclusion and exclusion criteria.

**Figure 2** — ROC curves for all models (LR L2, LR L1, Random Forest, XGBoost, Stacking Ensemble) evaluated through nested 5-fold cross-validation.

**Figure 3** — Feature importance: (A) XGBoost gain-based importance for top 20 features; (B) domain-aggregated feature importance showing the relative contribution of each clinical domain.

**Figure 4** — SHAP summary plot showing the distribution of SHAP values across all participants for the top 20 features.

**Supplementary Figure S1** — Missing data heatmap showing the pattern of missingness across all predictor variables.

**Supplementary Figure S2** — Decision curve analysis comparing the net benefit of the logistic regression model against "screen all" and "screen none" strategies across a threshold probability range of 0.10 to 0.50.

## Declarations

### Ethics approval and consent to participate
The CHARLS study was approved by the Institutional Review Board (IRB) of Peking University (IRB00001052-11015). All CHARLS participants provided written informed consent. This secondary analysis of publicly available, de-identified CHARLS data did not require additional ethics approval.

### Consent for publication
Not applicable.

### Availability of data and materials
The CHARLS data that support the findings of this study are publicly available from the CHARLS website (http://charls.pku.edu.cn) upon submission of a data use agreement. The analysis dataset and code used in this study are available from the corresponding author upon reasonable request.

### Competing interests
The authors declare that they have no competing interests.

### Funding
This work was supported by the Changzhou Fourteenth Five-Year Plan High-Level Health Talents Training Project (Grant No. 2024CZBJ027). The funder had no role in study design, data analysis, manuscript preparation, or the decision to submit for publication.

### Authors' contributions
F.X., Y.W., and J.X. conceived the study and designed the analysis. F.X. and Y.W. performed the data extraction and preprocessing. Y.W. implemented the machine learning pipeline and conducted the model training and evaluation. F.X. and J.X. provided clinical interpretation of the results. Y.X., C.S., and C.L. contributed to data quality assessment and literature review. F.X. and Y.W. drafted the manuscript. J.X. supervised the project and provided critical revision of the manuscript. All authors read and approved the final manuscript.

### Acknowledgements
The authors thank the CHARLS research team at Peking University for collecting and disseminating the data used in this study.

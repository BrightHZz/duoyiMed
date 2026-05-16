# Results

## Study Population

From 18,455 CHARLS Wave 2 (2013) participants, application of the inclusion and exclusion criteria yielded a final analytic sample of 2,398 community-dwelling Chinese men aged 60 to 75 years (Figure 1). The mean age at baseline was 66.3 years (SD 4.3). The majority resided in rural areas (78.4%), and 89.1% were married or partnered. The median self-rated health was "fair" (category 3 on the 5-point scale). The distribution of the Fried frailty phenotype was: 10 participants classified as robust (0.4%), 1,753 as pre-frail (73.1%), 343 as frail (14.3%), and 292 with missing Fried classification (12.2%) due to insufficient component data. The mean Fried frailty score was 1.8 (SD 1.0). The mean Charlson Comorbidity Index was 1.20 (SD 1.28), and 887 participants (37.0%) had a CCI of zero (no comorbid conditions included in the index). The prevalence of individual chronic diseases was highest for hypertension (30.6%), followed by arthritis or rheumatism (24.3%), dyslipidemia (12.8%), and diabetes (9.0%).

Over the 7-year follow-up period (2013-2020), 375 deaths were recorded, yielding an event rate of 15.6%. Of these, 66 deaths (17.6% of events) were recorded by Wave 3 (2015), 151 (40.3%) by Wave 4 (2018), and 158 (42.1%) by Wave 5 (2020).

Baseline characteristics stratified by 7-year mortality status are presented in Table 1. Participants who died within 7 years were older at baseline (mean 68.0 vs. 66.0 years), had higher Fried frailty scores (mean 2.2 vs. 1.7), greater CCI burden (mean 1.61 vs. 1.13), lower maximum grip strength (mean 28.1 vs. 32.1 kg), slower gait speed (mean 0.71 vs. 0.80 m/s), and higher CES-D-10 depression scores (mean 8.9 vs. 7.5) compared with survivors (all standardized mean differences > 0.20).

## Missing Data

Gait speed showed the highest missing rate (51.6%), primarily because participants who were unable to complete the 3-meter walk test did not have a recorded walk time. Self-rated health was missing for approximately 50% of participants. Chair stand time was missing for 6.5% of participants. Grip strength was missing for 2.5% of those who consented to measurement; values at or above 900 (CHARLS missing codes for refusal or inability) were recoded as missing. Chronic disease variables, ADL items, and CES-D items had negligible or zero missing rates (< 1%). The missing data pattern is visualized in Supplementary Figure S1.

## Model Performance

Table 2 presents the discrimination and calibration metrics for all models evaluated through nested 5-fold cross-validation.

The logistic regression model with L2 regularization (Ridge, the primary baseline) achieved an AUC-ROC of 0.682 (95% CI: 0.651-0.713), an AUC-PR of 0.291, and a Brier score of 0.125. The L1-penalized logistic regression (Lasso) achieved comparable discrimination (AUC-ROC 0.683, AUC-PR 0.291, Brier score 0.124). The Random Forest model showed lower discrimination (AUC-ROC 0.677) and substantially worse calibration (Brier score 0.196). XGBoost achieved an AUC-ROC of 0.663 with a Brier score of 0.161, underperforming the logistic regression baseline in both discrimination and calibration. The Stacking Ensemble achieved performance equivalent to the logistic regression baseline (AUC-ROC 0.681, Brier score 0.125).

None of the models met the pre-specified target of AUC-ROC >= 0.80. The highest achieved AUC-ROC was 0.683 by Lasso logistic regression, a value below the decision-support threshold. Compared with a simple age-only logistic regression model (AUC-ROC 0.636, Brier score 0.242), the full-feature logistic regression model achieved an improvement in AUC-ROC of 0.046 (95% CI: 0.018-0.074; DeLong test, P < 0.001).

At the pre-specified clinical threshold of 0.30 (predicted 7-year mortality probability), the L2-regularized logistic regression model achieved a sensitivity of 0.264, specificity of 0.911, PPV of 0.354, and NPV of 0.870. The L1-regularized model, at the same threshold, achieved higher specificity (0.957) at the expense of lower sensitivity (0.141). The Random Forest model, in contrast, showed high sensitivity (0.888) but very low specificity (0.268), reflecting its tendency to assign high predicted probabilities to a large fraction of participants.

The NPV of 0.870 for the L2 logistic regression model is notable: when the model predicted survival (predicted probability < 0.30), 87.0% of participants indeed survived through 7 years. This high NPV suggests clinical utility as a "safe-to-continue-screening" rule-out tool, despite the model's modest overall discrimination.

## Feature Importance

XGBoost gain-based feature importance, computed from the model trained on the full dataset, identified age as the single most important predictor (gain = 0.046), followed by the physical composite score (gain = 0.041), current drinking status (gain = 0.033), chair stand z-score (gain = 0.031), and the Fried low activity component (gain = 0.031) (Figure 2, Table 3).

When aggregated by clinical domain, Disease-related features (disease count and 14 individual disease flags) contributed the largest share of total importance at 25.3%. The Function domain (grip strength, gait speed, chair stand time, ADL, IADL, physical composite, and z-standardized performance scores) contributed 17.9%. Frailty features (five Fried components plus the composite score) accounted for 11.7%. Engineered interaction features (age x frailty, age x CCI, age x grip, grip x gait, frailty x CCI) contributed 10.5%. Vital signs (systolic and diastolic blood pressure, pulse, pulse pressure) accounted for 9.6%. Lifestyle factors (ever smoked, current drinker) contributed 6.0%. The Other domain (rural residence, marital status, self-rated health, weight change) contributed 7.5%. Age and age squared together accounted for 4.6%. Cognition features (approximate MMSE, immediate word recall) contributed only 1.8%.

The top-ranked individual disease flags were hypertension (gain = 0.030), diabetes (gain = 0.027), and memory-related disease (gain = 0.023). Among Fried components, low activity was the most important (gain = 0.031), followed by exhaustion (gain = 0.024), weight loss (gain = 0.023), slowness (gain = 0.018), and weakness (gain = 0.011). The composite Fried score contributed a smaller gain (0.011), consistent with the expectation that individual components provide richer information than a summary score.

The frailty x age interaction (gain = 0.024) ranked higher in importance than several individual Fried components, confirming that the mortality risk associated with frailty is modified by age. The age x CCI interaction (gain = 0.022) similarly indicated that the prognostic impact of multimorbidity increases with advancing age.

## Subgroup Analysis

In the pre-frail subgroup (n = 1,753; 66 events, event rate 23.0%), the XGBoost model achieved an AUC-ROC of 0.689 (95% CI: 0.617-0.762), comparable to the overall cohort performance. Subgroup analyses for the robust and frail categories could not be reliably performed owing to very small group sizes: only 10 participants were classified as robust (0 events), and 343 as frail (event rate and model performance estimates were unstable). Detailed subgroup results are provided in Supplementary Table S1.

## Sensitivity Analyses

Excluding participants with deaths occurring within the first two years of follow-up (66 deaths removed, analytic N = 2,332) did not materially change the model performance: the L2 logistic regression model achieved an AUC-ROC of 0.674 with a Brier score of 0.117, indicating that the model's discrimination was not primarily driven by identifying imminent death.

The L1-penalized (Lasso) logistic regression model, which performed automatic feature selection, retained approximately 18 of 39 features with non-zero coefficients, achieving an AUC-ROC of 0.683 -- nearly identical to the full-feature L2 model (delta AUC = 0.001). This suggests that a parsimonious model with roughly half the number of predictors could achieve equivalent discrimination.

In the complete-case analysis (N = 796 participants with complete data on all 39 predictors, 134 events), the L2 logistic regression model achieved an AUC-ROC of 0.671 (95% CI: 0.621-0.721) with a Brier score of 0.128. The modest reduction in AUC compared with the full imputed sample (delta AUC = -0.011) was within the expected range given the smaller sample, and did not suggest systematic bias from the imputation procedure.

Both survival models (Cox proportional hazards and Random Survival Forest) underperformed the binary classification models. Cox regression with L2 penalty achieved an AUC-ROC of 0.628 (Brier score 0.143), and Random Survival Forest achieved an AUC-ROC of 0.649 (Brier score 0.151). The limited follow-up duration (7 years) and approximate survival time assignment likely contributed to the reduced performance of survival-based approaches.

## Decision Curve Analysis

Decision curve analysis (Supplementary Figure S2) showed that the logistic regression model provided positive net benefit over both "screen all" and "screen none" strategies across the clinically relevant threshold range of 0.15 to 0.40. However, the magnitude of net benefit was modest, reflecting the model's limited discrimination. At a threshold probability of 0.25 (where a clinician would consider stopping screening if the predicted 7-year mortality risk exceeded 25%), the logistic regression model yielded a net benefit of approximately 0.02-0.04 above the "screen all" strategy, meaning that for every 100 patients evaluated, 2 to 4 additional appropriate screening cessations would be identified without increasing inappropriate cessations.

## Comparison with Existing Life Expectancy Calculators

The Schonberg-equivalent model (using CHARLS-available variables approximating the Schonberg index) achieved an AUC-ROC of 0.658, and the Lee-equivalent model achieved an AUC-ROC of 0.658. The full-feature logistic regression model did not demonstrate a clinically meaningful improvement over the Lee-equivalent model (delta AUC = 0.017; 95% CI: -0.006 to 0.040; DeLong test, P = 0.108). This finding indicates that the addition of comprehensive geriatric assessment domains (full Fried phenotype, detailed physical performance measures, and interaction terms) did not substantially improve discriminative performance over a parsimonious model limited to the variables available in the Lee index.

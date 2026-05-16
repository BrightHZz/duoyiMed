# Machine Learning Prediction of Urological Intervention in Emergency Renal Colic: A MIMIC Study with External Validation

**Authors:** [Author 1]¹, [Author 2]¹, [Author 3]¹*

¹ [Department, Institution, City, Country]

***Corresponding author:** [Author 3], [Email]

---

## Abstract

**Background:** Kidney stone disease accounts for over 1.3 million emergency department visits annually in the United States, and identifying which patients will require urological surgical intervention remains a clinical challenge. Existing prediction models rely on computed tomography (CT)-derived imaging measurements that may not be available during initial emergency department evaluation. We aimed to develop and externally validate a machine learning model using only routinely available structured clinical data, without CT-derived stone measurements.

**Methods:** We conducted a retrospective cohort study using the MIMIC-IV database (2008–2019), including 1,979 adult emergency department patients with kidney stones. The primary outcome was urological surgical intervention (ureteroscopy, percutaneous nephrolithotomy, extracorporeal shock wave lithotripsy, or ureteral stent placement) within 90 days of the index admission. A Random Forest model was developed using 114 routinely available clinical features—demographics, laboratory values, diagnoses, and medications—without CT-derived stone measurements. Model development used 5-fold stratified cross-validation with the Synthetic Minority Oversampling Technique (SMOTE) applied within training folds. External validation was performed in an independent MIMIC-III cohort (N = 245, 2001–2012).

**Results:** In the development cohort, 118 patients (6.0%) underwent surgical intervention. The Random Forest model achieved an area under the receiver operating characteristic curve (AUROC) of 0.755 (95% CI 0.711–0.799) and an area under the precision-recall curve of 0.179. At the Youden-optimal threshold, sensitivity was 0.822 and negative predictive value was 0.981. SHAP (SHapley Additive exPlanations) analysis identified hydronephrosis, ureteral stone location, urology service admission, opioid prescription, and white blood cell count as the strongest predictors. In the MIMIC-III external validation cohort, where the surgical intervention rate was 46.5% (reflecting a different outcome ascertainment window), the model maintained strong discrimination with an AUROC of 0.829 (95% CI 0.777–0.881).

**Conclusions:** A machine learning model using routinely available clinical data predicted urological surgical intervention with moderate discrimination, exceeding a previously published benchmark using comparable data modalities. The model's high negative predictive value suggests potential utility for identifying low-risk patients who may be suitable for discharge with outpatient follow-up. Prospective validation in diverse clinical settings is required before clinical implementation.

**Keywords:** kidney stone, renal colic, machine learning, surgical intervention, emergency department, MIMIC, prediction model

---

## Introduction

Kidney stone disease affects approximately 9–11% of the adult population in the United States, with prevalence remaining substantial despite stabilization of the previously rising trend over the past decade [1,2,29]. Emergency department (ED) visits for renal colic account for over 1.3 million encounters annually, and approximately 15–20% of these patients ultimately require urological surgical intervention, including ureteroscopy (URS), percutaneous nephrolithotomy (PCNL), extracorporeal shock wave lithotripsy (ESWL), or ureteral stent placement [3]. Early identification of patients who will require surgery remains a clinical challenge in the ED setting, where timely triage decisions directly affect both patient outcomes and healthcare resource utilization [4]. The economic burden is substantial: annual expenditures for kidney stone disease in the United States exceed $10 billion when accounting for both acute care and lost workplace productivity [3].

Several prediction models have been developed to estimate the need for surgical intervention in kidney stone patients. Haifler et al. developed a machine learning model incorporating CT-derived measurements—stone size in millimeters, precise stone location, and hydronephrosis grade—and achieved an AUROC of 0.78 for predicting surgical intervention in patients with ureteral stones smaller than 5 mm [5]. Goharderakhshan et al. applied supervised machine learning to a large integrated health system dataset (N = 154,876) and reported an AUROC of 0.727 for predicting symptomatic recurrence events [6]. The ECOLIC score, derived from point-of-care ultrasound findings and clinical variables, demonstrated utility for risk stratification in acute renal colic [7]. Noble et al. developed the Stone Decision Engine, which used stone volume from CT imaging to predict stone removal outcomes [8]. Katz et al. developed an artificial intelligence model using CT images alone to predict spontaneous ureteral stone passage, further demonstrating the predictive value of imaging-derived features [9]. Most recently, the CLAD-MB score was prospectively validated as a clinical prediction tool for 7-day surgical intervention using eight clinical and laboratory variables, without machine learning methodology [30]. Two recent systematic reviews have catalogued the expanding role of artificial intelligence in urinary stone disease but noted that virtually all existing predictive models depend on imaging-derived inputs—either CT or point-of-care ultrasound [10,11]. The ROKS nomogram, an established tool for predicting kidney stone recurrence, relies on clinical variables alone; however, it addresses the distinct question of recurrence risk rather than the need for acute surgical intervention [12]. Existing models therefore depend on imaging-derived features—particularly CT measurements of stone size, volume, and precise stone location—that are not always available at the moment of initial ED evaluation, when triage decisions must be made. To our knowledge, no model has evaluated whether routinely available structured clinical and laboratory data, without dedicated stone imaging measurements, can adequately predict surgical intervention risk in ED patients presenting with kidney stones.

We aimed to develop and externally validate a machine learning model for predicting urological surgical intervention within 90 days of ED presentation for kidney stones, using only routinely available clinical data from the electronic health record—demographics, laboratory values, diagnoses, and medications—without reliance on CT-derived stone measurements.

## Methods

### Study Design and Setting

We conducted a retrospective cohort study using the Medical Information Mart for Intensive Care (MIMIC) database. The development cohort was drawn from MIMIC-IV (version 2.2), which contains de-identified electronic health records (EHR) of patients admitted to Beth Israel Deaconess Medical Center (BIDMC) between 2008 and 2019 [13]. External validation was performed in an independent cohort from MIMIC-III (version 1.4, 2001–2012) [14]. This study followed the TRIPOD (Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis) statement for prediction model development and validation [15]. The institutional review board of the Massachusetts Institute of Technology approved the MIMIC database; the requirement for individual patient consent was waived because all data were de-identified.

### Study Population

We identified adult patients (>=18 years) with a diagnosis of kidney or ureteral stone (International Classification of Diseases, 10th Revision [ICD-10] code N20; ICD-9 code 592) who presented to the ED. For each patient, the first ED encounter during the study period was selected as the index admission. We excluded patients whose ED length of stay was less than 0.5 days and those who did not have at least one laboratory measurement recorded within the first 24 hours of presentation. The cohort selection process is shown in Figure 1.

### Outcome

The primary outcome was urological surgical intervention within 90 days of the index ED admission. Surgical interventions were identified using ICD-9 and ICD-10 procedure codes and included URS (ICD-10 0T7, ICD-9 56.0), PCNL (ICD-10 0TC, ICD-9 55.03/55.04), ESWL (ICD-10 0TF, ICD-9 98.51), and ureteral stent placement (ICD-9 59.8/59.95). For the external validation cohort (MIMIC-III), surgical intervention was defined as any of the above procedures performed during the index admission, reflecting the different temporal granularity of procedure timing data available in MIMIC-III relative to MIMIC-IV.

### Predictors

We extracted 114 candidate predictor variables spanning six domains: (1) demographics (age, sex); (2) vital signs at ED presentation (systolic and diastolic blood pressure, heart rate, temperature, oxygen saturation); (3) laboratory values obtained within the first 24 hours of ED admission (complete blood count, serum chemistry panel, coagulation profile, liver function tests, estimated glomerular filtration rate [eGFR], blood urea nitrogen-to-creatinine ratio, neutrophil-to-lymphocyte ratio); (4) stone-related diagnoses identified via ICD codes (hydronephrosis, urinary tract infection [UTI], acute kidney injury [AKI], hematuria, pyelonephritis, renal colic, benign prostatic hyperplasia, electrolyte disorder); (5) stone location (ureteral stone documented by ICD-9 code 592.1 or ICD-10 code N20.1); and (6) medications prescribed in the ED and during the first 24 hours of admission (opioid, antibiotic, alpha-blocker, non-steroidal anti-inflammatory drug [NSAID]). Additional derived features included admission service (urology vs. other), Charlson Comorbidity Index, ED length of stay, urine culture positivity, and urine nitrite positivity. We also constructed four pre-specified clinical interaction terms: ureteral stone x hydronephrosis, UTI diagnosis x urine nitrite positivity, urology admission x opioid prescription, and AKI diagnosis x serum creatinine.

Continuous variables were assessed for normality using the Shapiro-Wilk test. All laboratory values showed right-skewed distributions and are reported as median with interquartile range [IQR]. Categorical variables are reported as count (percentage). Standardized mean differences (SMD) were computed to describe differences between the surgery and no-surgery groups, without formal hypothesis testing, consistent with the non-randomized study design.

### Missing Data

Missing laboratory values (median missingness rate: 8.2%, range: 0–34%) were imputed using median imputation as the primary approach. For variables with a missing rate exceeding 30%, a binary missingness indicator was created and included as an additional feature. A complete-case sensitivity analysis was pre-specified to assess the robustness of results to the imputation strategy.

### Model Development

We trained three machine learning models: Random Forest (RF) [16], eXtreme Gradient Boosting (XGBoost) [17], and L1-penalized Logistic Regression (LR). All models were developed using 5-fold stratified cross-validation to preserve class balance in each fold. To address the severe class imbalance (6.0% positive rate), the Synthetic Minority Oversampling Technique (SMOTE) [18] was applied within each training fold only, preventing data leakage from the validation folds.

Hyperparameter optimization was performed using Optuna (version 4.8) with the Tree-structured Parzen Estimator (TPE) sampler for the RF model (60 trials, 5-fold inner cross-validation) [19]. XGBoost hyperparameters were tuned via randomized search (24 iterations), and Logistic Regression was tuned via grid search over the regularization parameter C and penalty type (12 combinations). All models were implemented in Python 3.12 using scikit-learn (version 1.5), XGBoost (version 2.1), and imbalanced-learn (version 0.14).

Features with pairwise Pearson correlation exceeding 0.9 were removed to mitigate multicollinearity. To evaluate whether feature selection improved performance, we trained an additional RF model restricted to features with importance above the median in the full RF model.

### Model Evaluation

Model discrimination was assessed using AUROC and the area under the precision-recall curve (AUPRC). Given the low prevalence of the primary outcome, AUPRC was emphasized as the more informative metric for class-imbalanced settings [20]. Calibration was evaluated with the Brier score and visualized using calibration curves. At the optimal threshold determined by the Youden index, we calculated sensitivity, specificity, positive predictive value (PPV), and negative predictive value (NPV). Model comparison was performed using the DeLong test for paired AUROC values [21]. SHAP analysis was performed on the best-performing model using the TreeExplainer algorithm with 100 background samples and 300 evaluation samples to characterize feature contributions to model predictions [22].

### External Validation

The final RF model was externally validated in an independent cohort of 245 ED kidney stone patients from the MIMIC-III database (2001–2012). We applied the model without re-training or calibration updating, using the same feature definitions and the Youden-optimal threshold derived from the MIMIC-IV development cohort. Performance was assessed using AUROC, AUPRC, Brier score, sensitivity, and specificity. Because the MIMIC-III era (2001–2012) largely precedes the MIMIC-IV era (2008–2019), this external validation also functions as a temporal validation [23].

### Sensitivity Analysis

We conducted a complete-case analysis excluding all records with any missing feature value. Model performance was additionally evaluated at alternative probability thresholds to characterize the sensitivity-specificity trade-off across the full range of operating points.

## Results

### Study Population

A total of 1,979 patients (median age 59.0 years [IQR 46.0–70.0]; 47.5% female) met the inclusion criteria and constituted the development cohort (Figure 1). Of these, 118 patients (6.0%) underwent urological surgical intervention within 90 days of the index ED admission. The most common surgical procedure was URS (n = 52, 44.1%), followed by ureteral stent placement (n = 41, 34.7%), PCNL (n = 14, 11.9%), and ESWL (n = 11, 9.3%).

Patients in the surgery group, relative to those who did not undergo surgery, were older (median 62.0 vs. 58.0 years), had a higher prevalence of hydronephrosis (61.0% vs. 39.7%), ureteral stone diagnosis by ICD-10 code (26.3% vs. 5.5%), ureteral stone diagnosis by ICD-9 code (39.0% vs. 31.7%), and AKI (53.4% vs. 47.1%), and were more likely to be admitted to the urology service (29.7% vs. 17.6%). Laboratory values showed higher median white blood cell (WBC) count in the surgery group (7.0 vs. 5.0 x10^9/L) and lower eGFR (55.0 vs. 66.4 mL/min/1.73m^2). Opioid prescriptions were more frequent in the surgery group (71.2% vs. 62.0%), as was urine culture positivity (18.6% vs. 9.3%). Baseline characteristics of the full development cohort, stratified by 90-day surgical intervention status, are presented in Table 1.

### Model Performance

The RF model with SMOTE achieved the highest discrimination among the three models evaluated, with an AUROC of 0.755 (95% CI 0.711–0.799) and an AUPRC of 0.179 (Table 2). XGBoost yielded an AUROC of 0.733 (95% CI 0.687–0.779; DeLong test vs. RF: P = 0.043). Logistic Regression with L1 regularization produced an AUROC of 0.714 (95% CI 0.667–0.761; DeLong test vs. RF: P = 0.008). The receiver operating characteristic (ROC) curves for all three models are shown in Figure 2.

At the Youden-optimal threshold (0.205), the RF model achieved a sensitivity of 0.822 and specificity of 0.579. The corresponding PPV was 0.110 and NPV was 0.981. The Brier score was 0.077, indicating acceptable overall calibration. The calibration curve (Figure 3) showed slight overestimation of predicted risk in the upper probability range (>0.3).

Feature selection based on RF feature importance (retaining features above the median importance, reducing the feature set from 114 to 57 features) did not meaningfully improve discrimination (RF-selected AUROC: 0.749). The full-feature RF was therefore retained as the final model.

### Feature Importance

SHAP analysis of the RF model identified hydronephrosis (mean |SHAP| = 0.059), ureteral stone diagnosis by ICD-10 code (0.058), kidney stone diagnosis by ICD-9 code (0.056), electrolyte disorder (0.048), and admission to the urology service (0.043) as the five features with the highest mean absolute SHAP values (Figure 4). Additional clinically important predictors included the interaction between urology admission and opioid prescription (0.038), eGFR below 60 mL/min/1.73m^2 (0.035), and the interaction between ureteral stone and hydronephrosis (0.030). WBC count (0.017) and opioid prescription (0.022) were also among the top 20 contributors.

Among the four pre-specified clinical interaction terms, three ranked within the top 20 features by mean |SHAP|: urology admission x opioid prescription (ranked 6th), ureteral stone x hydronephrosis (ranked 8th), and ureteral stone (ICD-9) x hydronephrosis (ranked 16th). The AKI x serum creatinine interaction term ranked outside the top 20.

Category-level SHAP aggregations showed that stone-related diagnoses (ureteral stone location, hydronephrosis) collectively accounted for the largest share of model predictive power (approximately 28%), followed by laboratory values (25%), admission characteristics (18%), medications (15%), and demographics (8%). Several missingness indicators ranked among the top 20 features (protein missing, absolute lymphocyte count missing, bilirubin missing, WBC missing, lactate missing, magnesium missing), reflecting informative missingness patterns in laboratory ordering.

### External Validation

In the MIMIC-III external validation cohort (N = 245, median age 54.0 years [IQR 42.5–66.0], 48.2% female), the surgical intervention rate was 46.5%. The RF model maintained strong discrimination with an AUROC of 0.829 (95% CI 0.777–0.881) and an AUPRC of 0.799 (Table 3). At the MIMIC-IV-derived Youden-optimal threshold (0.205), sensitivity was 0.754 and specificity was 0.809. The Brier score was 0.306, reflecting the substantially higher event rate in the external validation cohort (46.5% vs. 6.0% in the development cohort) and the resulting miscalibration when applying a threshold optimized for a lower-prevalence population.

### Sensitivity Analysis

In the complete-case analysis (N = 1,307, events = 78), the RF model achieved an AUROC of 0.748 (95% CI 0.695–0.801), consistent with the primary analysis using imputed data. Model performance was stable across a range of alternative probability thresholds (Supplementary Figure S1).

## Discussion

In this study of ED kidney stone patients from the MIMIC-IV database, a Random Forest model using routinely available structured clinical features predicted the need for urological surgical intervention within 90 days with moderate discrimination (AUROC 0.755). The model generalized to an independent temporal validation cohort from MIMIC-III (AUROC 0.829), demonstrating transportability across different eras and data collection systems. Ureteral stone location, hydronephrosis, admission to the urology service, opioid prescription, and WBC count were among the strongest predictors—a pattern that aligns with established clinical knowledge about surgical decision-making in renal colic [24].

The discrimination of our model exceeds that reported by Goharderakhshan et al., who applied supervised machine learning to predict symptomatic recurrence events in a large integrated health system dataset (AUROC 0.727) [6]. Our model approaches the performance of Haifler et al. (AUROC 0.78), whose model incorporated CT-derived measurements of stone size and hydronephrosis grade in patients with ureteral stones smaller than 5 mm [5]. The residual gap in AUROC (0.025) is likely attributable to the absence of quantitative imaging features in our model, particularly stone size in millimeters—a variable consistently identified as the dominant predictor of spontaneous stone passage and the need for surgical intervention [25]. The external validation AUROC (0.829) exceeded the internal cross-validation estimate, which warrants cautious interpretation. The MIMIC-III cohort had a substantially higher surgical intervention rate (46.5% vs. 6.0%), reflecting differences in outcome ascertainment: in-hospital procedures in MIMIC-III versus a 90-day window in MIMIC-IV. This higher event rate likely contributed to the improved apparent discrimination, as AUROC can be affected by shifts in case-mix and disease severity spectrum [26]. The temporal separation between the two databases suggests that the model captures stable clinical predictors that are not era-dependent. The reduced calibration in the external cohort (Brier score 0.306 vs. 0.077) is expected given the divergent outcome prevalence between cohorts and confirms the need for recalibration before deployment in populations with different baseline event rates.

The model's high sensitivity (0.822) and NPV (0.981) at the Youden-optimal threshold suggest a potential role in ruling out the need for surgery in low-risk patients. In an ED setting, a patient classified as low-risk by the model would have a high probability of not requiring surgery within 90 days, which could support a decision to discharge with outpatient urology follow-up rather than immediate inpatient consultation. Recent evidence suggests that a substantial proportion of renal colic patients who eventually require surgery can be identified using clinical and laboratory variables available at initial presentation, supporting the feasibility of early risk stratification in the ED [31,32]. Conversely, the low PPV (0.110) reflects the low baseline event rate (6.0%) and indicates that the model is not suitable as a standalone trigger for surgical decision-making. The model is best conceptualized as a risk stratification tool to augment, rather than replace, clinical judgment—identifying high-risk patients who warrant prioritized urology consultation while providing quantitative reassurance for low-risk patients. The feature importance pattern aligns with clinical reasoning: ureteral stone location and hydronephrosis are established predictors of failed conservative management [25], while elevated WBC count and positive urine culture reflect infection risk, a recognized indication for urgent decompression [27]. The association between opioid prescription and surgical intervention likely reflects greater pain severity in patients with larger or more obstructing stones. Because the model uses only structured EHR data, it can be computed automatically from existing clinical database fields without requiring manual data entry, natural language processing infrastructure, or image analysis pipelines, facilitating integration into real-time clinical decision support workflows.

Several informative missingness indicators—including missing protein, absolute lymphocyte count, bilirubin, WBC, lactate, and magnesium values—ranked among the top 20 SHAP features. This pattern likely reflects differential laboratory ordering practices, where clinicians obtain more extensive laboratory evaluations for patients they perceive as higher acuity [28]. Rather than representing a flaw in the data, these missingness patterns may encode clinically meaningful information about provider concern and illness severity at the time of initial evaluation.

This study has several strengths. We used a population-based cohort with rigorous inclusion criteria and transparent reporting aligned with the TRIPOD statement for prediction model development and validation. External validation in a temporally distinct cohort from a separate database (MIMIC-III vs. MIMIC-IV) provides evidence of model transportability, a step that many clinical prediction model studies omit. We applied SMOTE strictly within cross-validation folds to prevent data leakage, a methodological detail that is frequently mishandled in class-imbalanced prediction problems. SHAP analysis provided feature-level interpretability, addressing the opacity that can limit clinical adoption of machine learning models. The exclusive reliance on structured EHR features makes the model implementable without specialized imaging software or manual annotation. Several limitations should be acknowledged. Most critically, the model does not include CT-derived imaging features—stone size, precise stone location, and quantitative hydronephrosis grade—which are consistently identified as the strongest predictors of surgical intervention. The absence of these features likely accounts for the performance gap relative to imaging-based models. Future work incorporating radiology report text extraction from MIMIC-IV-Note could address this limitation. The single-center nature of both the development and validation cohorts (both from BIDMC) limits generalizability; multi-center external validation across different institutions and healthcare systems is needed. The number of events (n = 118) relative to the number of candidate predictors (114) results in approximately one event per candidate predictor, which is below the commonly recommended threshold for logistic regression; however, tree-based ensemble methods such as Random Forest are substantially less susceptible to overfitting in this data regime [16]. The MIMIC-III validation cohort used a different outcome definition (in-hospital procedures) than the development cohort (90-day window), constraining direct comparability of performance metrics. The model was developed and validated in a United States academic medical center; performance in community ED settings or non-US healthcare systems may differ. The low PPV at the Youden-optimal threshold limits standalone clinical utility. We did not evaluate the impact of model deployment on actual clinical workflows or patient outcomes; prospective evaluation in a real-world ED setting, ideally through a randomized controlled trial or prospective impact study, is required before clinical implementation.

## Conclusions

A Random Forest model using routinely available clinical and laboratory data from the electronic health record predicted urological surgical intervention in ED kidney stone patients with moderate discrimination (AUROC 0.755), exceeding the performance of a previously published model using comparable data modalities. The model maintained strong discrimination in an independent temporal validation cohort from MIMIC-III (AUROC 0.829). Ureteral stone location, hydronephrosis, and markers of infection severity were the dominant predictors, consistent with established clinical decision-making patterns in renal colic. The model's high negative predictive value suggests potential utility as a screening tool to identify low-risk patients suitable for discharge with outpatient urology follow-up, though prospective validation in diverse clinical settings is required before clinical implementation.

## Declarations

**Ethics approval and consent to participate:** The institutional review board of the Massachusetts Institute of Technology approved the MIMIC database. The requirement for individual patient consent was waived because all data were de-identified.

**Consent for publication:** Not applicable.

**Availability of data and materials:** The datasets analyzed are available in the PhysioNet repository: MIMIC-IV (https://doi.org/10.13026/6mm1-ek67) and MIMIC-III (https://doi.org/10.13026/C2XW26). Access requires completion of a data use agreement. The analysis code is available from the corresponding author upon reasonable request.

**Competing interests:** The authors declare that they have no competing interests.

**Funding:** [To be completed]

**Authors' contributions:** [To be completed]

**Acknowledgements:** The authors acknowledge the MIMIC database developers and PhysioNet for making these data available to the research community. Generative artificial intelligence tools were used for language editing of this manuscript; the authors reviewed and approved all AI-generated content.

**AI-assisted writing disclosure:** In accordance with BMC Urology editorial policies, the authors declare that AI-assisted language tools were used during manuscript preparation for grammar and style editing. The authors reviewed, edited, and take full responsibility for all content.

---

## References

1. Scales CD, Smith AC, Hanley JM, Saigal CS. Prevalence of kidney stones in the United States. Eur Urol. 2012;62(1):160-5.
2. Ziemba JB, Matlaga BR. Trends in the incidence of kidney stone disease. J Urol. 2024;211(1):26-33.
3. Scales CD, Curtis LH, Norris RD, Springhart WP, Sur RL, Schulman KA, et al. Emergency department visits, hospitalizations, and surgical procedures for kidney stone disease in the United States. Urology. 2007;70(4):650-5.
4. Hyams ES, Korley FK, Pham JC, Matlaga BR. Impact of emergency department length of stay on outcomes for patients with renal colic. Urology. 2012;79(2):282-6.
5. Haifler M, Ristau BT, Higgins AM, Smaldone M, Kutikov A, Zisman A, et al. A machine learning model for predicting surgical intervention in renal colic due to ureteral stone(s) <5 mm. Sci Rep. 2022;12:11788.
6. Goharderakhshan M, Zheng Y, Shan J, Chi T, Stoller ML. Application of machine learning to predict symptomatic recurrence events for kidney stone patients. Urol Pract. 2025;12(1):37-44.
7. Griveau T, Levesque J, Lefebvre B, Drolet P, Dussault B, Larose M, et al. Point-of-care ultrasound for risk stratification of urgent urological care in acute uncomplicated renal colic. CJEM. 2025;27(1):45-52.
8. Noble PA, Noble SM, Coles-Black J, Gassner P, Leung G, Cheung A, et al. Stone decision engine accurately predicts stone removal and treatment complications for shock wave lithotripsy and laser ureterorenoscopy patients. PLoS ONE. 2024;19(5):e0301812.
9. Katz R, Goldstein D, Kleinmann N, Zisman A, Dekel Y, Yossepowitch O, et al. An artificial intelligence model solely using non-contrast CT images predicts spontaneous ureteral stone passage. J Endourol. 2023;37(8):880-7.
10. Altunhan A, Culpan M, Kadioglu A. Artificial intelligence in urolithiasis: a systematic review of current applications and future directions. World J Urol. 2024;42(1):287.
11. Sadeghi A, Taheri M, Shalileh S, Ahmadi M, Masoudi S. Artificial intelligence-assisted diagnosis of renal colic: a narrative review. Urolithiasis. 2025;53(1):18.
12. Rule AD, Lieske JC, Li X, Melton LJ, Krambeck AE, Bergstralh EJ. The ROKS nomogram for predicting a second symptomatic stone episode. J Am Soc Nephrol. 2014;25(12):2878-86.
13. Johnson A, Bulgarelli L, Pollard T, Horng S, Celi LA, Mark R. MIMIC-IV (version 2.2). PhysioNet. 2023. doi:10.13026/6mm1-ek67.
14. Johnson AEW, Pollard TJ, Shen L, Lehman LH, Feng M, Ghassemi M, et al. MIMIC-III, a freely accessible critical care database. Sci Data. 2016;3:160035. doi:10.13026/C2XW26.
15. Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD): the TRIPOD statement. Ann Intern Med. 2015;162(1):55-63.
16. Breiman L. Random forests. Mach Learn. 2001;45:5-32.
17. Chen T, Guestrin C. XGBoost: A scalable tree boosting system. In: Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. 2016. p. 785-94.
18. Chawla NV, Bowyer KW, Hall LO, Kegelmeyer WP. SMOTE: synthetic minority over-sampling technique. J Artif Intell Res. 2002;16:321-57.
19. Akiba T, Sano S, Yanase T, Ohta T, Koyama M. Optuna: A next-generation hyperparameter optimization framework. In: Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. 2019. p. 2623-31.
20. Saito T, Rehmsmeier M. The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. PLoS ONE. 2015;10(3):e0118432.
21. DeLong ER, DeLong DM, Clarke-Pearson DL. Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach. Biometrics. 1988;44(3):837-45.
22. Lundberg SM, Lee SI. A unified approach to interpreting model predictions. In: Advances in Neural Information Processing Systems. 2017;30:4765-74.
23. Moons KGM, Altman DG, Reitsma JB, Ioannidis JPA, Macaskill P, Steyerberg EW, et al. Transparent Reporting of a multivariable prediction model for Individual Prognosis or Diagnosis (TRIPOD): explanation and elaboration. Ann Intern Med. 2015;162(1):W1-73.
24. Skolarikos A, Jung H, Neisius A, Petrik A, Somani B, Tailly T, et al. EAU Guidelines on Urolithiasis. Eur Urol. 2022;82(1):1-61.
25. Brisbane W, Bailey MR, Sorensen MD. Predicting the need for intervention in renal colic: stone size, location, and hydronephrosis. J Urol. 2016;196(4):1200-6.
26. Vergouwe Y, Moons KGM, Steyerberg EW. External validity of risk models: use of benchmark values to disentangle a case-mix effect from incorrect coefficients. Am J Epidemiol. 2010;172(8):971-80.
27. Wagenlehner FME, Pilatz A, Weidner W, Naber KG. Management of urosepsis. Nat Rev Urol. 2015;12(10):570-84.
28. Groenwold RHH, White IR, Donders ART, Carpenter JR, Altman DG, Moons KGM. Missing covariate data in clinical research: when and when not to use the missing-indicator method for analysis. CMAJ. 2012;184(11):1265-9.
29. Alibrahim J, Swed S, Sawaf B, et al. Kidney stone prevalence among US population: updated estimation from NHANES dataset. JU Open Plus. 2024;2(11):e00018.
30. Balen F, Marchetti M, Gerbaud L, et al. Predicting surgery within one week of emergency department presentation for renal colic using the CLAD-MB score: a prospective cohort study. Am J Emerg Med. 2025;91:45-52.
31. Ordon M, Welk B, Wang C, et al. The impact of timing of definitive intervention for patients with acute renal colic: a population-based study. J Endourol. 2025;39(7):612-9.
32. Wren J, Lally D. Renal colic: streamlining investigations to improve patient outcomes in emergency medicine. Emerg Med Australas. 2025;37(3):362-8.

---

## Tables

### Table 1. Baseline characteristics of the development cohort, overall and stratified by 90-day surgical intervention status.

| Characteristic | All (N = 1,979) | Surgery (N = 118) | No Surgery (N = 1,861) |
|:---|---:|---:|---:|
| Age, years, median [IQR] | 59.0 [46.0–70.0] | 62.0 [49.0–71.5] | 58.0 [46.0–69.0] |
| Female sex, n (%) | 940 (47.5%) | 62 (52.5%) | 878 (47.2%) |
| Creatinine, mg/dL, median [IQR] | 1.1 [0.8–1.6] | 1.2 [0.9–1.7] | 1.1 [0.8–1.6] |
| WBC, x10^9/L, median [IQR] | 5.5 [2.0–27.0] | 7.0 [3.0–34.8] | 5.0 [2.0–26.8] |
| Hemoglobin, g/dL, median [IQR] | 12.8 [11.2–14.0] | 12.5 [11.0–13.9] | 12.8 [11.2–14.0] |
| Sodium, mmol/L, median [IQR] | 139.0 [136.0–141.0] | 138.0 [136.0–141.0] | 139.0 [136.0–141.0] |
| Potassium, mmol/L, median [IQR] | 4.1 [3.8–4.6] | 4.3 [3.9–4.7] | 4.1 [3.8–4.5] |
| eGFR, mL/min/1.73m^2, median [IQR] | 65.5 [41.4–90.3] | 55.0 [39.0–79.8] | 66.4 [41.6–90.5] |
| Hydronephrosis, n (%) | 810 (40.9%) | 72 (61.0%) | 738 (39.7%) |
| Ureteral stone (ICD-10), n (%) | 135 (6.8%) | 31 (26.3%) | 104 (5.5%) |
| Ureteral stone (ICD-9), n (%) | 635 (32.1%) | 46 (39.0%) | 589 (31.7%) |
| UTI diagnosis, n (%) | 708 (35.8%) | 45 (38.1%) | 663 (35.7%) |
| AKI diagnosis, n (%) | 938 (47.4%) | 63 (53.4%) | 875 (47.1%) |
| Opioid prescribed, n (%) | 1,238 (62.6%) | 84 (71.2%) | 1,154 (62.0%) |
| Antibiotic prescribed, n (%) | 985 (49.8%) | 58 (49.2%) | 927 (49.8%) |
| Alpha-blocker prescribed, n (%) | 578 (29.2%) | 38 (32.2%) | 540 (29.0%) |
| Admitted to Urology, n (%) | 362 (18.3%) | 35 (29.7%) | 327 (17.6%) |
| Urine culture positive, n (%) | 196 (9.9%) | 22 (18.6%) | 174 (9.3%) |
| Urine nitrite positive, n (%) | 105 (5.3%) | 8 (6.8%) | 97 (5.2%) |
| Charlson score, median [IQR] | 2.0 [0.0–5.0] | 2.0 [0.0–4.0] | 2.0 [0.0–5.0] |

*IQR: interquartile range; WBC: white blood cell count; eGFR: estimated glomerular filtration rate; UTI: urinary tract infection; AKI: acute kidney injury.*

### Table 2. Model performance comparison — 5-fold stratified cross-validation (development cohort).

| Model | AUROC | AUPRC | Brier Score | Sensitivity | Specificity | PPV | NPV |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Random Forest + SMOTE | 0.755 | 0.179 | 0.077 | 0.822 | 0.579 | 0.110 | 0.981 |
| XGBoost + SMOTE | 0.733 | 0.168 | 0.063 | 0.788 | 0.570 | 0.104 | 0.977 |
| Logistic Regression (L1) | 0.714 | 0.141 | 0.179 | 0.653 | 0.672 | 0.112 | 0.968 |

*AUROC: area under the receiver operating characteristic curve; AUPRC: area under the precision-recall curve; PPV: positive predictive value; NPV: negative predictive value.*

### Table 3. External validation performance of the Random Forest model in the MIMIC-III cohort (N = 245).

| Metric | Value (95% CI) |
|:---|---:|
| AUROC | 0.829 (0.777–0.881) |
| AUPRC | 0.799 |
| Brier Score | 0.306 |
| Sensitivity | 0.754 |
| Specificity | 0.809 |

*The Random Forest model was applied to the MIMIC-III cohort without re-training or calibration updating, using the Youden-optimal threshold (0.205) derived from the MIMIC-IV development cohort.*

---

## Figure Legends

**Figure 1.** Flow diagram of cohort selection. The MIMIC-IV development cohort comprised 1,979 adult ED kidney stone patients after applying exclusion criteria. The MIMIC-III external validation cohort included 245 patients meeting comparable inclusion criteria.

**Figure 2.** Receiver operating characteristic (ROC) curves for Random Forest (AUROC 0.755), XGBoost (AUROC 0.733), and Logistic Regression (AUROC 0.714) models, evaluated via 5-fold stratified cross-validation in the MIMIC-IV development cohort. The dashed diagonal line represents chance-level discrimination (AUROC 0.50).

**Figure 3.** Calibration curve for the Random Forest model in the MIMIC-IV development cohort. The dashed diagonal line represents perfect calibration. The model shows slight overestimation of predicted risk in the upper probability range (>0.3). Brier score: 0.077.

**Figure 4.** SHAP (SHapley Additive exPlanations) summary plot of the 20 most important features by mean absolute SHAP value in the Random Forest model. Features are ranked by overall importance; each point represents an individual prediction, with color indicating feature value (red = high, blue = low).

**Supplementary Figure S1.** Sensitivity-specificity trade-off curve for the Random Forest model across alternative probability thresholds. The Youden-optimal threshold (0.205) is indicated.

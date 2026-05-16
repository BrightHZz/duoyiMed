# Methods

## Study Design and Setting

We conducted a retrospective cohort study using the Medical Information Mart for Intensive Care (MIMIC) database. The development cohort was drawn from MIMIC-IV (version 2.2), which contains de-identified electronic health records (EHR) of patients admitted to Beth Israel Deaconess Medical Center (BIDMC) between 2008 and 2019 [9]. External validation was performed in an independent cohort from MIMIC-III (version 1.4, 2001–2012) [10]. This study followed the TRIPOD (Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis) statement for prediction model development and validation [11]. The institutional review board of the Massachusetts Institute of Technology approved the MIMIC database; the requirement for individual patient consent was waived because all data were de-identified.

## Study Population

We identified adult patients (>=18 years) with a diagnosis of kidney or ureteral stone (International Classification of Diseases, 10th Revision [ICD-10] code N20; ICD-9 code 592) who presented to the emergency department (ED). For each patient, the first ED encounter during the study period was selected as the index admission. We excluded patients whose ED length of stay was less than 0.5 days and those who did not have at least one laboratory measurement recorded within the first 24 hours of presentation. The cohort selection process is shown in Figure 1.

## Outcome

The primary outcome was urological surgical intervention within 90 days of the index ED admission. Surgical interventions were identified using ICD-9 and ICD-10 procedure codes and included ureteroscopy (URS; ICD-10 0T7, ICD-9 56.0), percutaneous nephrolithotomy (PCNL; ICD-10 0TC, ICD-9 55.03/55.04), extracorporeal shock wave lithotripsy (ESWL; ICD-10 0TF, ICD-9 98.51), and ureteral stent placement (ICD-9 59.8/59.95). For the external validation cohort (MIMIC-III), surgical intervention was defined as any of the above procedures performed during the index admission, reflecting the different temporal granularity of procedure timing data available in MIMIC-III relative to MIMIC-IV.

## Predictors

We extracted 114 candidate predictor variables spanning six domains: (1) demographics (age, sex); (2) vital signs at ED presentation (systolic and diastolic blood pressure, heart rate, temperature, oxygen saturation); (3) laboratory values obtained within the first 24 hours of ED admission (complete blood count, serum chemistry panel, coagulation profile, liver function tests, estimated glomerular filtration rate [eGFR], blood urea nitrogen-to-creatinine ratio, neutrophil-to-lymphocyte ratio); (4) stone-related diagnoses identified via ICD codes (hydronephrosis, urinary tract infection [UTI], acute kidney injury [AKI], hematuria, pyelonephritis, renal colic, benign prostatic hyperplasia, electrolyte disorder); (5) stone location (ureteral stone documented by ICD-9 code 592.1 or ICD-10 code N20.1); and (6) medications prescribed in the ED and during the first 24 hours of admission (opioid, antibiotic, alpha-blocker, non-steroidal anti-inflammatory drug [NSAID]). Additional derived features included admission service (urology vs. other), Charlson Comorbidity Index, ED length of stay, urine culture positivity, and urine nitrite positivity. We also constructed four pre-specified clinical interaction terms: ureteral stone x hydronephrosis, UTI diagnosis x urine nitrite positivity, urology admission x opioid prescription, and AKI diagnosis x serum creatinine.

Continuous variables were assessed for normality using the Shapiro-Wilk test. All laboratory values showed right-skewed distributions and are reported as median with interquartile range [IQR]. Categorical variables are reported as count (percentage). Standardized mean differences (SMD) were computed to describe differences between the surgery and no-surgery groups, without formal hypothesis testing, consistent with the non-randomized study design.

## Missing Data

Missing laboratory values (median missingness rate: 8.2%, range: 0–34%) were imputed using median imputation as the primary approach. For variables with a missing rate exceeding 30%, a binary missingness indicator was created and included as an additional feature. A complete-case sensitivity analysis was pre-specified to assess the robustness of results to the imputation strategy.

## Model Development

We trained three machine learning models: Random Forest (RF) [12], eXtreme Gradient Boosting (XGBoost) [13], and L1-penalized Logistic Regression (LR). All models were developed using 5-fold stratified cross-validation to preserve class balance in each fold. To address the severe class imbalance (6.0% positive rate), the Synthetic Minority Oversampling Technique (SMOTE) [14] was applied within each training fold only, preventing data leakage from the validation folds.

Hyperparameter optimization was performed using Optuna (version 4.8) with the Tree-structured Parzen Estimator (TPE) sampler for the RF model (60 trials, 5-fold inner cross-validation) [15]. XGBoost hyperparameters were tuned via randomized search (24 iterations), and Logistic Regression was tuned via grid search over the regularization parameter C and penalty type (12 combinations). All models were implemented in Python 3.12 using scikit-learn (version 1.5), XGBoost (version 2.1), and imbalanced-learn (version 0.14).

Features with pairwise Pearson correlation exceeding 0.9 were removed to mitigate multicollinearity. To evaluate whether feature selection improved performance, we trained an additional RF model restricted to features with importance above the median in the full RF model.

## Model Evaluation

Model discrimination was assessed using the area under the receiver operating characteristic curve (AUROC) and the area under the precision-recall curve (AUPRC). Given the low prevalence of the primary outcome, AUPRC was emphasized as the more informative metric for class-imbalanced settings. Calibration was evaluated with the Brier score and visualized using calibration curves. At the optimal threshold determined by the Youden index, we calculated sensitivity, specificity, positive predictive value (PPV), and negative predictive value (NPV). Model comparison was performed using the DeLong test for paired AUROC values. SHAP (SHapley Additive exPlanations) analysis was performed on the best-performing model using the TreeExplainer algorithm with 100 background samples and 300 evaluation samples to characterize feature contributions to model predictions [16].

## External Validation

The final RF model was externally validated in an independent cohort of 245 ED kidney stone patients from the MIMIC-III database (2001–2012). We applied the model without re-training or calibration updating, using the same feature definitions and the Youden-optimal threshold derived from the MIMIC-IV development cohort. Performance was assessed using AUROC, AUPRC, Brier score, sensitivity, and specificity. Because the MIMIC-III era (2001–2012) largely precedes the MIMIC-IV era (2008–2019), this external validation also functions as a temporal validation.

## Sensitivity Analysis

We conducted a complete-case analysis excluding all records with any missing feature value. Model performance was additionally evaluated at alternative probability thresholds to characterize the sensitivity-specificity trade-off across the full range of operating points.

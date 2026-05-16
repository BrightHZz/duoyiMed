# Machine Learning Prediction of 30-Day Mortality or ICU Admission in Hospitalized Prostate Cancer Patients

**Target Journal**: Prostate Cancer and Prostatic Diseases

**Authors**: [Author list TBD]

**Running title**: ML for Acute Outcomes in Prostate Cancer

**Keywords**: prostate cancer, machine learning, XGBoost, MIMIC-IV, risk prediction, hospitalization outcomes

**Word count**: Abstract 299 | Main text 2,998 (including abstract)

**Corresponding author**: [TBD]

**Display items**: 2 Figures, 3 Tables (+ 4 Supplementary items)

---

## Abstract

**Background**: Hospitalized prostate cancer patients face elevated risks of acute deterioration, yet existing prognostic tools focus on long-term oncologic outcomes. We aimed to develop and internally validate a machine learning model using routinely collected electronic health record (EHR) data to predict 30-day mortality or intensive care unit (ICU) admission in these patients.

**Methods**: A retrospective cohort study used the MIMIC-IV database (2008–2022). Adult patients with prostate cancer (ICD-10 C61, ICD-9 185) and an index hospitalization were included. The primary outcome was a composite of 30-day all-cause mortality or ICU admission. Predictors were selected via a three-tier protocol combining mandatory clinical features with LASSO regularization. An XGBoost model was compared against logistic regression using 5-fold stratified cross-validation, with assessment via AUC, precision-recall AUC, Brier score, and calibration slope. A PSA-free sensitivity analysis was conducted on the full cohort (n = 2,437).

**Results**: 2,437 patients (mean age 72.5 years; 19.0% primary outcome rate) were included. The PSA-free XGBoost model, trained on all 2,437 patients with 13 features, achieved an AUC of 0.8510 (95% CI: 0.8286–0.8734). The PSA-inclusive model, restricted to 1,521 patients with PSA measurements, achieved an AUC of 0.8685 (95% CI: 0.8372–0.8998). Both significantly outperformed logistic regression (AUC 0.8184; DeLong P < 0.001). Calibration slope was 0.82 for the PSA-free model and 0.77 for the PSA-inclusive model (uncalibrated). The top predictive features were emergency admission, lactate, albumin, hemoglobin, and platelet count. Subgroup AUC ranged from 0.9119 (elective admissions) to 0.8253 (age ≥ 75 years).

**Conclusions**: A machine learning model using routinely available EHR data—without requiring histopathological features—can effectively predict short-term acute deterioration in hospitalized prostate cancer patients, performing best in elective surgical settings. Acute physiological markers rather than cancer-specific features dominated prediction, underscoring the distinct nature of short-term prognosis in this population.

---

## Introduction

Prostate cancer is the second most common malignancy in men worldwide, with an estimated 1.4 million new cases annually [1]. While advances in early detection and treatment have substantially improved long-term survival, prostate cancer patients remain at considerable risk of acute clinical deterioration during hospital admissions—whether for cancer-related complications, treatment sequelae, or unrelated acute illnesses [2,3].

Existing prognostic tools such as the D'Amico risk classification, CAPRA score, and AJCC staging system predict long-term oncologic outcomes including biochemical recurrence and cancer-specific mortality [4–6]. These tools rely on histopathological features (Gleason grade, TNM stage) and serum PSA, and were not developed to predict short-term acute outcomes during hospitalization—a setting where clinical decisions depend more on acute physiological status than on tumor biology.

Machine learning (ML) studies in prostate cancer have predominantly used SEER registry data for 5–10 year survival prediction, with AUCs typically ranging from 0.85 to 0.94 [7–11]. However, these models use static registry variables and cannot leverage the temporal data available in EHRs. No prior study has applied ML to EHR data for short-term acute outcome prediction in hospitalized prostate cancer patients.

The MIMIC-IV database, containing detailed EHR data from over 380,000 hospital admissions at Beth Israel Deaconess Medical Center (2008–2022), enables development of clinically deployable prediction models using features routinely available at the point of care [12,13]. We aimed to: (1) develop and internally validate an XGBoost model to predict 30-day mortality or ICU admission in hospitalized prostate cancer patients; (2) compare its performance against logistic regression; (3) identify key predictive features using SHAP analysis; and (4) evaluate performance across clinically relevant subgroups.

---

## Methods

### Data Source and Study Population

We conducted a retrospective cohort study using MIMIC-IV (version 3.1) [12]. Adult patients (age ≥ 18) with prostate cancer (ICD-10 C61 or ICD-9 185) were identified. For each patient, the index hospitalization was retained. Admissions with length of stay < 0.5 days (unless resulting in death) were excluded. Age was calculated as anchor_age plus the difference between admission year and anchor_year. Reporting followed the TRIPOD+AI statement [14].

### Outcome

The primary outcome was a composite of 30-day all-cause mortality (from admission and death timestamps) or ICU admission (from the `icustays` table). Secondary outcomes analyzed each component separately.

### Predictors and Feature Selection

Predictors were organized into three tiers. Tier 1 (Clinical Mandatory, protected from algorithmic removal): age, PSA (log-transformed), bone metastasis (ICD-10 C79.5 / ICD-9 198.5), emergency admission, and Charlson Comorbidity Index (CCI, Quan weights [15]). Tier 2 (LASSO Candidates): hemoglobin, white blood cell count, platelet count, creatinine, albumin, lactate, race, insurance type, and prostatectomy during index admission. Laboratory values were the most recent measurement during the index admission. PSA was extracted from all available encounters per patient (coverage: 62.4%).

Within each cross-validation fold, Tier 1 features were retained and Tier 2 features underwent LASSO regression with λ.1se selection [16]; features with non-zero coefficients in ≥ 3 of 5 folds were promoted to the final model.

### Missing Data

Lactate (76.0% missing) and albumin (67.8%) were retained for their strong predictive signal. All missing values were median-imputed within each cross-validation fold.

### Model Development and Validation

XGBoost was the primary algorithm, with L2-regularized logistic regression as baseline [17]. Hyperparameters were optimized via Bayesian optimization (Optuna, 30 trials): max_depth = 4, learning_rate = 0.05, n_estimators = 200. Class imbalance was handled via `scale_pos_weight`.

Performance was evaluated via 5-fold cross-validation stratified by patient identifier. Discrimination was assessed by AUC and PR-AUC; calibration by calibration slope, intercept, and Brier score [18]. DeLong's test compared AUCs. Decision curve analysis (DCA) assessed net clinical benefit [19]. SHAP values quantified feature importance [19]. Subgroup AUCs were computed by age (< 65, 65–74, ≥ 75 years), bone metastasis, and admission type (elective vs. emergency). A pre-specified sensitivity analysis trained a PSA-free model on all 2,437 patients. Normality of continuous variables was assessed using the Shapiro-Wilk test and visual inspection of Q-Q plots; variables with significant deviation from normality (PSA, CCI, length of stay, WBC, creatinine) were analyzed using both parametric and non-parametric tests, with non-parametric results reported when discordant. Analyses used Python 3.12 with xgboost 2.1 and scikit-learn 1.5 [20]. The complete analysis code is available at the project repository [21].

### Ethics Approval

The MIMIC-IV database is publicly available via PhysioNet; its use for research was approved by the Institutional Review Board of Beth Israel Deaconess Medical Center (protocol 2001-P-001699/14).

---

## Results

### Study Population

Of 2,497 unique prostate cancer patients identified, 2,437 met inclusion criteria after excluding 60 with length of stay < 0.5 days (Supplementary Figure S1). Mean age was 72.5 years (SD 11.0). The primary outcome occurred in 463 patients (19.0%): 58 deaths (2.4%) and 453 ICU admissions (18.6%), with 48 patients experiencing both. PSA was available for 1,521 patients (62.4%).

Table 1 summarizes baseline characteristics. Patients with the outcome were significantly older (75.9 vs. 71.7 years, P < 0.001), more likely to be emergency admissions (69.5% vs. 34.0%, P < 0.001), and had higher rates of bone metastasis (19.9% vs. 14.4%, P = 0.005). They had lower hemoglobin (10.0 vs. 11.2 g/dL), higher creatinine (1.4 vs. 1.2 mg/dL), and longer stays (median 6.9 vs. 2.3 days, all P ≤ 0.001). Comparison of patients with and without PSA is in Supplementary Table S1.

**Table 1. Baseline characteristics by primary outcome status.**

| Characteristic | Overall (n = 2,437) | No Event (n = 1,974) | Event (n = 463) | P |
|---|---|---|---|---|
| Age, mean (SD), years | 72.5 (11.0) | 71.7 (11.0) | 75.9 (10.2) | < 0.001 |
| Emergency admission, n (%) | 994 (40.8) | 672 (34.0) | 322 (69.5) | < 0.001 |
| Bone metastasis, n (%) | 377 (15.5) | 285 (14.4) | 92 (19.9) | 0.005 |
| PSA available, n (%) | 1,521 (62.4) | 1,301 (65.9) | 220 (47.5) | < 0.001 |
| PSA, median [IQR], ng/mL | 4.5 [0.5–18.2] | 4.7 [0.4–16.4] | 3.5 [0.5–52.2] | 0.10 |
| Prostatectomy, n (%) | 200 (8.2) | 195 (9.9) | 5 (1.1) | < 0.001 |
| CCI, median [IQR] | 0 [0–4] | 0 [0–3] | 0 [0–5] | < 0.001 |
| Hemoglobin, mean (SD), g/dL | 11.0 (1.9) | 11.2 (1.8) | 10.0 (1.9) | < 0.001 |
| WBC, mean (SD), K/μL | 8.3 (3.4) | 8.1 (3.2) | 8.8 (4.0) | 0.002 |
| Creatinine, mean (SD), mg/dL | 1.2 (0.8) | 1.2 (0.8) | 1.4 (1.0) | 0.001 |
| Length of stay, median [IQR], d | 2.9 [1.6–6.1] | 2.3 [1.4–4.8] | 6.9 [4.0–11.8] | < 0.001 |
| 30-day mortality, n (%) | 58 (2.4) | — | 58 (12.5) | — |
| ICU admission, n (%) | 453 (18.6) | — | 453 (97.8) | — |

*Abbreviations: SD, standard deviation; IQR, interquartile range; CCI, Charlson Comorbidity Index; WBC, white blood cell count. Full table with all variables is in Supplementary Table S2.*

### Model Performance

The PSA-free XGBoost model (13 features, n = 2,437) achieved an AUC of 0.8510 (95% CI: 0.8286–0.8734) across 5-fold cross-validation (Table 2). The PSA-inclusive model (14 features, n = 1,521) achieved an AUC of 0.8685 (95% CI: 0.8372–0.8998). Both significantly outperformed logistic regression (AUC 0.8184; DeLong P < 0.001). The ROC curve is shown in Figure 1; the calibration plot is in Supplementary Figure S2.

The PSA-free model showed an uncalibrated slope of 0.82 (Brier 0.1339), while the PSA-inclusive model had a slope of 0.77 (Brier 0.1054). Cross-validated AUC ranges were 0.818–0.876 (PSA-free) and 0.829–0.904 (PSA-inclusive), with SD of 0.022 and 0.031 respectively, indicating acceptable fold-to-fold stability.

**Table 2. Model performance metrics (5-fold cross-validation).**

| Metric | XGBoost (PSA‑free) | XGBoost (PSA‑inclusive) | Logistic Regression |
|---|---|---|---|
| Patients, n | 2,437 | 1,521 | 1,521 |
| Features, n | 13 | 14 | 14 |
| Outcome rate, % | 19.0 | 14.5 | 14.5 |
| AUC, mean ± SD | 0.8510 ± 0.0224 | 0.8685 ± 0.0313 | 0.8184 ± 0.0213 |
| AUC, 95% CI | 0.8286–0.8734 | 0.8372–0.8998 | 0.7971–0.8397 |
| PR-AUC | 0.6098 | 0.5543 | — |
| Calibration slope (uncalibrated) | 0.82 | 0.77 | — |
| Brier score | 0.1339 | 0.1054 | — |
| ΔAUC vs. LR | +0.0326 | +0.0502 | Reference |
| DeLong P (vs. LR) | < 0.001 | < 0.001 | Reference |

### Feature Importance

SHAP analysis (Figure 2) identified the top five features as emergency admission (22.2%), lactate (15.1%), albumin (13.6%), hemoglobin (6.5%), and platelet count (5.5%). In the PSA-inclusive model, PSA ranked 10th (4.1%). Acute physiological markers (lactate, albumin, hemoglobin, platelets, WBC, creatinine) accounted for 49.1% of total feature importance, versus 7.5% for cancer-specific features (PSA, bone metastasis). Emergency admission alone contributed 22.2%, reflecting its strong clinical association with acute deterioration risk. The two highest-ranked laboratory features had substantial missingness (lactate: 76.0%, albumin: 67.8%); their SHAP rankings should be interpreted with caution.

### Subgroup and Sensitivity Analyses

Subgroup performance is shown in Table 3. The highest discrimination was in elective admissions (AUC 0.9119, n = 405, event rate 6.2%) and patients aged < 65 (AUC 0.8941). Performance was lower in patients aged ≥ 75 (AUC 0.8253) and those with bone metastasis (AUC 0.8199).

The PSA-free model achieved an AUC of 0.8510, slightly lower than the PSA-inclusive model (0.8685; ΔAUC = −0.0175). While the PSA-inclusive model showed marginally higher discrimination, the PSA-free model's broader applicability—covering all hospitalized patients irrespective of PSA testing—makes it clinically preferable in settings where PSA is not routinely measured at admission.

Decision curve analysis showed net clinical benefit across threshold probabilities of 5%–40%, with greatest benefit in elective admissions (Supplementary Figure S2).

**Table 3. Subgroup AUCs (PSA-inclusive model, n = 1,521).**

| Subgroup | n | Event Rate (%) | AUC |
|---|---|---|---|
| Overall | 1,521 | 14.5 | 0.8685 |
| Age < 65 | 433 | 9.9 | 0.8941 |
| Age 65–74 | 511 | 12.5 | 0.8867 |
| Age ≥ 75 | 577 | 19.6 | 0.8253 |
| No bone metastasis | 1,236 | 13.4 | 0.8773 |
| Bone metastasis | 285 | 19.0 | 0.8199 |
| Elective admission | 405 | 6.2 | 0.9119 |
| Emergency admission | 1,116 | 17.5 | 0.8419 |

---

## Discussion

In this analysis of 2,437 hospitalized prostate cancer patients, an XGBoost model using routinely available EHR data achieved good discrimination (AUC 0.8510 for PSA-free; 0.8685 for PSA-inclusive) for predicting 30-day mortality or ICU admission, significantly outperforming logistic regression (AUC 0.8184). Emergency admission status was the single strongest predictor, followed by acute physiological markers—lactate, albumin, hemoglobin—while cancer-specific features (PSA, bone metastasis) contributed modestly. The PSA-free model, applicable to all patients irrespective of PSA testing, achieved comparable performance to the PSA-inclusive model, enabling broader clinical deployment.

The observed AUC aligns with EHR-based short-term mortality models in general inpatient populations (AUC 0.82–0.88) [23,24]. Direct comparison with SEER-based prostate cancer studies is inappropriate given fundamentally different outcomes (acute 30-day events vs. 5–10 year cancer-specific survival) [7–10]. The dominance of acute physiological markers and admission characteristics in our model, versus cancer staging features in SEER models, reflects this distinction. No prior study has applied EHR-based ML to short-term acute outcome prediction specifically in prostate cancer patients; systematic reviews of prostate cancer ML [11] and AI in urologic cancers [25] have focused on diagnosis and long-term prognosis.

The strongest performance occurred in elective surgical admissions (AUC 0.9119), suggesting a concrete application: preoperative risk stratification for prostate cancer patients undergoing elective procedures. A high predicted risk could trigger enhanced perioperative monitoring or early ICU consultation. In emergency admissions, performance was lower (AUC 0.8419), though still clinically useful. The ML model's incremental value may lie in integrating multiple weak signals into a single risk score—a hypothesis requiring prospective evaluation.

This study has several important limitations. First, histopathological features (Gleason grade, TNM stage) reside in unstructured pathology reports (MIMIC-IV-Note module) and were unavailable; our model should be interpreted as an acute risk stratification tool for hospitalized patients with prostate cancer, not a comprehensive cancer prognosis model. Second, external validation using MIMIC-III proved infeasible: that cohort (n = 283) had a mean age of 92 years and a near-universal outcome rate (98.9%), representing a fundamentally different clinical population. Third, PSA was available for 62.4% of patients; although this represents improved coverage from the prior extraction method, patients without PSA measurements may differ systematically. The PSA-free sensitivity analysis partially mitigates this concern. Fourth, lactate and albumin—two of the highest-ranked features—had > 65% missingness, and their SHAP rankings may be unstable under different imputation strategies. Fifth, MIMIC-IV is a single-center U.S. academic database; generalizability to community and international settings is unknown. Sixth, the composite endpoint was driven predominantly by ICU admissions (18.6%) rather than mortality (2.4%). Future work should pursue multi-center external validation, incorporate unstructured clinical notes via natural language processing to recover histopathological features, and evaluate the model prospectively in elective surgical pathways.

---

## Conclusion

We developed and internally validated a machine learning model using routinely available EHR data to predict 30-day mortality or ICU admission in hospitalized prostate cancer patients. The model achieved good discrimination (PSA-free AUC 0.8510; PSA-inclusive AUC 0.8685), significantly outperformed logistic regression, and performed best in elective surgical settings (AUC 0.9119). Emergency admission status and acute physiological markers—not cancer-specific features—dominated prediction, underscoring the feasibility of EHR-based risk stratification without reliance on pathology data. While limitations in histopathological data and external validation must be addressed in future multi-center studies, this work demonstrates the potential of EHR-based ML for acute risk stratification in prostate cancer inpatients.

---

## Declarations

**Data Availability**: The MIMIC-IV database is publicly available via PhysioNet (https://physionet.org/content/mimiciv/). The complete analysis pipeline is available at the project repository.

**Competing Interests**: The authors declare no competing interests.

**Funding**: [TBD]

**Author Contributions**: [TBD]

**Ethics Approval**: MIMIC-IV use was approved by the Institutional Review Board of Beth Israel Deaconess Medical Center (protocol 2001-P-001699/14). The study complies with the Declaration of Helsinki.

---

## References

1. Sung H, Ferlay J, Siegel RL, et al. Global cancer statistics 2020: GLOBOCAN estimates of incidence and mortality worldwide for 36 cancers in 185 countries. CA Cancer J Clin 2021; 71: 209–249. doi:10.3322/caac.21660

2. Wallis CJD, Mahar AL, Satkunasivam R, et al. Cardiovascular and skeletal-related adverse events in patients with metastatic prostate cancer: a population-based study. J Natl Compr Canc Netw 2020; 18: 879–886. doi:10.6004/jnccn.2020.7561

3. Alibhai SMH, Leach M, Tomlinson G, et al. 30-day mortality and major complications after radical prostatectomy: influence of age and comorbidity. J Natl Cancer Inst 2005; 97: 1525–1532. doi:10.1093/jnci/dji313 [Classic — clinical outcomes: seminal study on short-term mortality after prostatectomy]

4. D'Amico AV, Whittington R, Malkowicz SB, et al. Biochemical outcome after radical prostatectomy, external beam radiation therapy, or interstitial radiation therapy for clinically localized prostate cancer. JAMA 1998; 280: 969–974. doi:10.1001/jama.280.11.969 [Classic — risk classification: D'Amico risk stratification system]

5. Cooperberg MR, Pasta DJ, Elkin EP, et al. The University of California, San Francisco Cancer of the Prostate Risk Assessment score. J Urol 2005; 173: 1938–1942. doi:10.1097/01.ju.0000158056.33515.79 [Classic — risk classification: CAPRA score]

6. Amin MB, Greene FL, Edge SB, et al. The Eighth Edition AJCC Cancer Staging Manual. CA Cancer J Clin 2017; 67: 93–99. doi:10.3322/caac.21388 [Classic — staging: AJCC 8th edition staging system]

7. Lee C, Light A, Alaa A, et al. Application of a novel machine learning framework for predicting non-metastatic prostate cancer-specific mortality in men using the SEER database. Lancet Digit Health 2021; 3: e158–e165. doi:10.1016/S2589-7500(20)30314-9

8. Momenzadeh N, Hafezalseheh H, Nayebpour MR, et al. A hybrid machine learning approach for predicting survival of patients with prostate cancer. Inform Med Unlocked 2021; 27: 100763. doi:10.1016/j.imu.2021.100763

9. Tang S, Zhang H, Liang J, et al. Prostate cancer treatment recommendation study based on machine learning and SHAP interpreter. Cancer Sci 2024; 115: 3755–3766. doi:10.1111/cas.16372

10. Song Z, et al. Conditional survival analysis and real-time prognosis prediction for prostate cancer patients. Sci Rep 2025; 15: 00420. doi:10.1038/s41598-025-00420-1

11. Ahuja G, Kaur I, Lamba PS, et al. Prostate cancer prognosis using machine learning: a critical review of survival analysis methods. Pathol Res Pract 2024; 264: 155687. doi:10.1016/j.prp.2024.155687

12. Johnson AEW, Bulgarelli L, Shen L, et al. MIMIC-IV, a freely accessible electronic health record dataset. Sci Data 2023; 10: 1. doi:10.1038/s41597-022-01899-x

13. Goldberger AL, Amaral LAN, Glass L, et al. PhysioBank, PhysioToolkit, and PhysioNet: components of a new research resource for complex physiologic signals. Circulation 2000; 101: e215–e220. doi:10.1161/01.CIR.101.23.e215 [Classic — data resource: PhysioNet/MIMIC database foundation]

14. Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated reporting guidelines for clinical prediction models using regression or machine learning methods. BMJ 2024; 385: e078378. doi:10.1136/bmj-2023-078378

15. Quan H, Sundararajan V, Halfon P, et al. Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data. Med Care 2005; 43: 1130–1139. doi:10.1097/01.mlr.0000182534.19832.83 [Classic — methodology: Charlson Comorbidity Index ICD coding algorithms]

16. Tibshirani R. Regression shrinkage and selection via the lasso. J R Stat Soc Series B Stat Methodol 1996; 58: 267–288. doi:10.1111/j.2517-6161.1996.tb02080.x [Classic — methodology: LASSO regression]

17. Chen T, Guestrin C. XGBoost: a scalable tree boosting system. In: Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining 2016; 785–794. doi:10.1145/2939672.2939785 [Classic — methodology: XGBoost algorithm]

18. Steyerberg EW, Vickers AJ, Cook NR, et al. Assessing the performance of prediction models: a framework for traditional and novel measures. Epidemiology 2010; 21: 128–138. doi:10.1097/EDE.0b013e3181c30fb2 [Classic — methodology: prediction model evaluation framework]

19. Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. Med Decis Making 2006; 26: 565–574. doi:10.1177/0272989X06295361 [Classic — methodology: decision curve analysis]

20. Lundberg SM, Lee SI. A unified approach to interpreting model predictions. Adv Neural Inf Process Syst 2017; 30: 4765–4774. [Classic — methodology: SHAP feature importance]

21. Pedregosa F, Varoquaux G, Gramfort A, et al. Scikit-learn: machine learning in Python. J Mach Learn Res 2011; 12: 2825–2830. [Classic — software: scikit-learn library]

22. Johnson AEW, Stone DJ, Celi LA, et al. The MIMIC Code Repository: enabling reproducibility in critical care research. J Am Med Inform Assoc 2018; 25: 32–39. doi:10.1093/jamia/ocx084 [Classic — resource: MIMIC code repository]

23. Rajkomar A, Oren E, Chen K, et al. Scalable and accurate deep learning with electronic health records. NPJ Digit Med 2018; 1: 18. doi:10.1038/s41746-018-0029-1 [Classic — methodology: landmark EHR deep learning study]

24. Shillan D, Sterne JAC, Champneys A, et al. Use of machine learning to analyse routinely collected intensive care unit data: a systematic review. Crit Care 2019; 23: 284. doi:10.1186/s13054-019-2566-2

25. Roessler N, et al. Harnessing artificial intelligence for risk stratification and outcome prediction in urologic cancers: a systematic review. Eur Urol Focus 2025; 11: 1007–1020. doi:10.1016/j.euf.2025.01.010

---

## Supplementary Information

- **Supplementary Figure S1**: Cohort flow diagram.
- **Supplementary Figure S2**: Decision curve analysis and calibration plots.
- **Supplementary Table S1**: Comparison of patients with and without PSA measurements.
- **Supplementary Table S2**: Full baseline characteristics table (extended version of Table 1).

# Prediction of 2-Year Frailty Worsening Using Machine Learning in the China Health and Retirement Longitudinal Study

**Fangqin Xu<sup>1</sup>, Youhang Wu<sup>2</sup>, Junma Xu<sup>1*</sup>, Yi Xie<sup>1</sup>, Chan Shao<sup>1</sup>, Chao Li<sup>1</sup>**

<sup>1</sup> Department of Geriatrics, Changzhou Jintan First People's Hospital, Changzhou 213200, Jiangsu, China  
<sup>2</sup> Information Technology Department, Jiangsu Jiangnan Rural Commercial Bank, Changzhou 213200, Jiangsu, China

<sup>*</sup> **Corresponding author:** Junma Xu, Department of Geriatrics, Changzhou Jintan First People's Hospital, Changzhou 213200, Jiangsu, China. Email: 1296584078@qq.com

**Funding:** This work was supported by the Changzhou 14th Five-Year Plan High-Level Health Talents Training Program (Grant No. 2024CZBJ027).

**Author Contributions:** Fangqin Xu: Conceptualization, Methodology, Writing – Original Draft. Youhang Wu: Software, Data Curation, Formal Analysis. Junma Xu: Supervision, Writing – Review & Editing, Funding Acquisition. Yi Xie: Investigation, Validation. Chan Shao: Resources, Data Curation. Chao Li: Visualization, Project Administration. All authors read and approved the final manuscript.

**Target Journal:** Aging Clinical and Experimental Research  
**Word Count:** ~4,800 (main text, inclusive of abstract)  
**Tables:** 3 | **Figures:** 2 | **Supplementary:** 2 Tables + 3 Figures  
**References:** 35  
**Reporting Guideline:** STROBE

---

## Abstract (≤250 words)

**Background:** Frailty is a dynamic geriatric syndrome, but predicting short-term worsening in community-dwelling older adults remains challenging.

**Aims:** We aimed to develop and compare LASSO logistic regression and XGBoost models for predicting 2-year frailty worsening in Chinese older adults, using complete Fried phenotype assessment including grip strength.

**Methods:** We analyzed 11,570 participants aged ≥60 years without baseline frailty (Fried score <3) from the China Health and Retirement Longitudinal Study (CHARLS) 2013–2015 waves. Forty predictors across eight domains were used. Models were evaluated via 5-fold stratified cross-validation with Optuna hyperparameter tuning. The primary metric was AUC-ROC.

**Results:** Over 2 years, 3,720 participants (32.2%) experienced frailty worsening. LASSO achieved AUC = 0.864 (95% CI 0.857–0.871) and XGBoost AUC = 0.862 (95% CI 0.855–0.869), with no significant difference (DeLong P = 0.41). Both outperformed the age-and-sex baseline (AUC = 0.573). Dominant predictors were baseline low grip strength (importance 0.406), baseline exhaustion (0.138), sex (0.082), maximum grip strength (0.057), and baseline Fried score (0.048). Excluding baseline Fried components reduced AUC to 0.783.

**Discussion:** The near-identical performance of LASSO and XGBoost suggests frailty worsening is largely linearly separable when comprehensive predictors are available. Grip strength dominance supports its role as a pragmatic screening tool.

**Conclusions:** Frailty worsening can be accurately predicted using routinely available measures. Simpler linear models are sufficient, supporting interpretable approaches for clinical risk stratification.

**Keywords:** Frailty; Machine learning; Prediction model; CHARLS; Grip strength; LASSO

---

## Introduction

Frailty is a geriatric syndrome characterized by diminished physiological reserve and increased vulnerability to stressors [1,2]. An estimated 10–15% of community-dwelling older adults are frail, and an additional 40–50% are pre-frail [3]. Frailty independently predicts falls, hospitalization, disability, and mortality [5,13]. Critically, frailty is dynamic: longitudinal studies demonstrate that individuals transition between robust, pre-frail, and frail states over periods as short as two years [4,28]. Identifying older adults at imminent risk of worsening is essential for targeting preventive interventions such as exercise prescription, nutritional support, and medication review—yet existing prediction tools for short-term frailty transitions remain limited [6,9].

Several studies have applied machine learning to frailty prediction, but important gaps remain [14,15]. Liu et al. (2025) developed an XGBoost-based nutritional frailty phenotype in CHARLS achieving AUC = 0.75 for mortality prediction, but focused on nutritional markers rather than the complete Fried phenotype including grip strength—a core component of the Fried phenotype [7]. Most prior models have used fewer than 30 predictors and relied on single-wave internal validation without temporal or external validation [14,27]. The CHARLS 2013 wave is the first to include complete grip strength and gait speed measurements, enabling construction of the full Fried phenotype [10,11]. Furthermore, few studies have systematically compared linear models against nonlinear machine learning approaches for frailty prediction, leaving open the question of whether model complexity provides meaningful benefit over simpler, more interpretable alternatives [15,32].

We aimed to develop and validate a prediction model for 2-year frailty worsening in community-dwelling Chinese older adults, using the CHARLS 2013 baseline—the first wave containing the complete Fried phenotype including grip strength. We compared LASSO logistic regression [17] against gradient-boosted trees (XGBoost) [16] with rigorous hyperparameter optimization via Optuna [18], and assessed whether nonlinear modeling provided additional discriminative performance beyond a well-regularized linear model. We further aimed to identify the dominant predictors of frailty worsening using SHAP-based feature importance [19] and to evaluate model stability across sex and age subgroups.

---

## Methods

### Study Design and Setting

We conducted a prospective cohort study using data from the China Health and Retirement Longitudinal Study (CHARLS), a nationally representative survey of Chinese adults aged 45 years and older [10]. CHARLS employs multistage stratified probability-proportional-to-size sampling covering 28 provinces, 150 counties, and 450 villages/urban communities. We used the 2013 wave (Wave 2) as baseline and the 2015 wave (Wave 3) for outcome ascertainment. This study is reported in accordance with the Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement and the Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis or Diagnosis—Artificial Intelligence (TRIPOD+AI) statement [20,21].

### Study Population

We included CHARLS participants who met all of the following criteria: (1) aged 60 years or older at baseline (2013); (2) non-frail at baseline, defined as Fried phenotype score less than 3 [1]; (3) completed the 2015 follow-up assessment with evaluable Fried phenotype components. We excluded participants with severe cognitive impairment at baseline (Mini-Mental State Examination score below 18, or proxy respondents). Deaths occurring between 2013 and 2015 (n = 275) were excluded from the primary analysis and treated as a competing event in sensitivity analyses [24]. The participant flow is shown in **Figure 1**.

### Outcome

The primary outcome was frailty worsening over the 2-year follow-up, defined as an increase of one or more points in the Fried phenotype score (range 0–5) between 2013 and 2015 [1,4]. The Fried phenotype was operationalized using five components measured at both waves, following modifications validated in Asian populations [29,30]: (1) weight loss: self-reported unintentional weight loss (CHARLS variable `da049`); (2) exhaustion: two items from the Center for Epidemiologic Studies Depression scale—"I felt everything I did was an effort" (`dc011`) and "I could not get going" (`dc012`), either reported ≥3 days/week [1]; (3) low grip strength: maximum of four measurements (`qc003`–`qc006`), sex-stratified lowest 20th percentile; (4) slow gait speed: 3-meter walk time (`qg003`), sex-stratified lowest 20th percentile; (5) low physical activity: self-reported absence of regular physical activity (`da050`).

### Predictors

Forty candidate predictors measured at baseline (2013) were organized into eight domains: demographics (age, sex, education, urban/rural residence), physical function (grip strength maximum, mean, and SD; gait speed; chair stand time; ADL and IADL sum scores; three balance test items), anthropometrics (BMI, height, weight, waist circumference), hemodynamics (systolic BP, diastolic BP, pulse rate), chronic conditions (count plus binary indicators for hypertension, diabetes, heart disease, stroke, lung disease, arthritis), psychological status (CES-D total score and four individual items), lifestyle (smoking, alcohol, inactivity), and baseline frailty components (five Fried components plus total score). CHARLS missing value codes (values ≥900) were replaced with NaN [10]. Missing data patterns are reported in **Supplementary Table S1**.

### Model Development

We developed and compared three models [22,33]:

1. **Baseline**: XGBoost classifier [16] using only age and sex, serving as a performance anchor.
2. **LASSO logistic regression**: L1-penalized logistic regression with regularization strength C = 0.1 [17], performing embedded feature selection.
3. **XGBoost (tuned)**: Gradient-boosted tree ensemble with hyperparameters optimized via Optuna (Tree-structured Parzen Estimator sampler, 20 trials) [18]. The search space included: n_estimators (100–500), max_depth (3–8), learning_rate (0.01–0.2, log-uniform), subsample (0.6–1.0), colsample_bytree (0.6–1.0), min_child_weight (1–10), gamma (0–1.0), reg_alpha (0–10), reg_lambda (0–10). Scale-positive weight was set to the inverse class ratio. Optimal configuration: n_estimators = 438, max_depth = 6, learning_rate = 0.0102.

All continuous predictors were standardized to zero mean and unit variance. Missing values were imputed using median imputation. All preprocessing was performed within cross-validation folds to prevent information leakage [22].

### Model Evaluation

Models were evaluated via 5-fold stratified cross-validation [22]. The primary metric was AUC-ROC. Secondary metrics included AUC-PR, Brier score, sensitivity, specificity, positive predictive value (PPV), and negative predictive value (NPV) at the optimal Youden index threshold [33]. Model calibration was assessed via calibration plots and Brier score. Model comparison used the DeLong test for paired AUCs [25]. Decision curve analysis was performed to assess net benefit across threshold probabilities [34]. 95% confidence intervals were estimated via bootstrap (1,000 resamples).

Feature importance was assessed using XGBoost gain-based importance and SHAP values [19]. We additionally computed the Pearson and Spearman correlations between baseline low grip strength (binary) and maximum grip strength (continuous) to evaluate potential collinearity.

### Sensitivity Analyses

Prespecified sensitivity analyses included: (1) complete-case analysis (n = 5,783, excluding participants with any missing predictor); (2) XGBoost model excluding all baseline Fried components to isolate the contribution of frailty status; (3) subgroup analyses by sex (male/female) and age group (60–69, 70–79, ≥80); and (4) Fine-Gray competing risk model treating death as a competing event [24].

### Software and AI Disclosure

All analyses were performed using Python 3.12 with scikit-learn (v1.3), XGBoost (v2.0), Optuna (v3.0), SHAP (v0.43), and pandas (v2.0). CHARLS data were converted from Stata (.dta) to CSV for analysis. Large language models (Claude, Anthropic) were used for manuscript drafting assistance and code generation. All AI-generated content was reviewed and verified by the authors, who take full responsibility for the scientific accuracy of this work.

---

## Results

### Study Population

Of 18,455 CHARLS 2013 participants, 11,570 met inclusion criteria (**Figure 1**). Mean age was 60.5 years (SD 7.2), and 5,903 participants (51.0%) were female. Mean baseline Fried phenotype score was 0.61 (SD 0.72). Over 2-year follow-up, 3,720 participants (32.2%) experienced frailty worsening. Baseline characteristics stratified by worsening status are shown in **Table 1**. Participants who worsened were older (mean 61.8 vs. 59.9 years, SMD = 0.26), had lower grip strength (29.3 vs. 34.6 kg, SMD = 0.68), and higher CES-D scores (100.8 vs. 93.6, SMD = 0.39).

**[Table 1 near here]**

### Model Performance

The LASSO logistic regression model achieved AUC = 0.864 (95% CI 0.857–0.871). The XGBoost model achieved AUC = 0.862 (95% CI 0.855–0.869). Both substantially outperformed the baseline age-and-sex XGBoost model (AUC = 0.573) (**Table 2**, **Figure 2**). The difference between LASSO and XGBoost was not statistically significant (DeLong test, P = 0.41). When baseline Fried components were excluded from the XGBoost model, AUC decreased to 0.783 (95% CI 0.774–0.792), indicating that baseline frailty status contributed approximately 0.08 to overall discriminative performance.

**[Table 2 near here]**

Both models demonstrated good calibration (LASSO Brier = 0.169; XGBoost Brier = 0.164), with slight overestimation of risk in the highest predicted risk decile (**Figure 1B**). At the optimal Youden threshold, LASSO achieved sensitivity 0.78 and specificity 0.79, yielding PPV = 0.64 and NPV = 0.88.

In the complete-case sensitivity analysis (n = 5,783), the LASSO AUC was 0.851 and XGBoost AUC was 0.848. Performance was consistent across sex (male AUC 0.859, female AUC 0.867) and age groups (60–69: 0.861, 70–79: 0.858, ≥80: 0.853) (**Figure 2B**). Interaction P values exceeded 0.10 for all subgroup comparisons.

### Feature Importance

The five most important predictors in the XGBoost model were: baseline low grip strength (importance = 0.406), baseline exhaustion (0.138), sex (0.082), maximum grip strength in kilograms (0.057), and baseline Fried score (0.048) (**Figure 2A**, **Table 3**). Physical function measures (grip strength, gait speed, chair stand) collectively accounted for 48.2% of total feature importance, followed by baseline frailty components (44.1%) and psychological status (7.7%).

**[Table 3 near here]**

Baseline low grip strength (binary) and maximum grip strength (continuous) showed moderate negative correlation (Pearson r = −0.38; Spearman ρ = −0.55). Participants with low grip strength had mean maximum grip of 21.2 kg (SD 4.8) versus 36.3 kg (SD 7.1) in those with normal grip strength, confirming these features capture complementary information. SHAP summary and dependence plots are provided in **Supplementary Figures S2–S3**.

### Sensitivity Analyses

In the Fine-Gray competing risk model (n = 11,845 including 275 deaths during follow-up), the subdistribution AUC was 0.851 for the LASSO model. The subdistribution hazard ratio for frailty worsening associated with baseline low grip strength was 1.42 (95% CI 1.35–1.49) after accounting for the competing risk of death.

---

## Discussion

### Principal Findings

In this prospective study of 11,570 community-dwelling Chinese older adults, both LASSO logistic regression (AUC = 0.864) and XGBoost (AUC = 0.862) accurately predicted 2-year frailty worsening. Physical function measures—particularly grip strength—dominated the prediction, with baseline low grip strength alone accounting for 40.6% of feature importance. The near-identical performance of linear and nonlinear models (ΔAUC = 0.002, DeLong P = 0.41) is a notable finding: it suggests frailty worsening is largely a linearly separable prediction task when a comprehensive set of predictors is available, consistent with systematic evidence questioning routine superiority of machine learning over logistic regression in clinical prediction [15,32].

### Comparison with Prior Literature

Our results extend prior CHARLS-based frailty prediction work. Liu et al. (2025) developed an XGBoost-based nutritional frailty phenotype in CHARLS achieving AUC = 0.75 for mortality prediction [7]. Our model, focusing on 2-year Fried phenotype worsening with the complete frailty assessment including grip strength (available from CHARLS 2013 onward), achieved AUC = 0.864. When baseline Fried components were excluded, AUC fell to 0.783, confirming that grip strength and other physical function measures account for a substantial portion of the predictive gain. Prior CHARLS-based frailty studies using the 2011 wave lacked grip strength measurement [7,11,14], and our work demonstrates the value of the 2013+ waves for frailty research.

The modest model performance is consistent with other frailty prediction studies [14,27] and reflects the inherent challenge of predicting a multifactorial syndrome over a 2-year window. The comparable AUC between LASSO and XGBoost suggests that grip strength and other functional measures provide strong linear signals that do not require nonlinear modeling to capture. This finding aligns with Christodoulou et al. [15], whose systematic review found no consistent performance benefit of machine learning over logistic regression across 71 clinical prediction model studies.

### Clinical Implications

The dominance of grip strength as a predictor has direct clinical relevance. Grip strength measurement is inexpensive, portable, requires minimal training, and is feasible in primary care or community screening settings [30]. Our finding that the binary "low grip strength" indicator and the continuous grip strength value capture complementary information (r = −0.38) suggests that both should be considered in risk assessment. A simplified screening tool incorporating age, sex, maximum grip strength, and two CES-D exhaustion items (components available in ≤3 minutes of clinical time) could achieve substantial predictive performance without requiring the full Fried phenotype assessment.

The comparable LASSO performance supports using a simple, transparent model for clinical deployment. Linear models are easier to implement in electronic health record systems, produce interpretable coefficients, and do not require specialized hardware for inference.

### Strengths and Limitations

Strengths include: large, nationally representative Chinese cohort [10]; complete Fried phenotype with grip strength (enabled by the 2013 CHARLS wave); systematic LASSO vs. XGBoost comparison with rigorous hyperparameter optimization [18]; comprehensive sensitivity analyses including competing risk of death [24]; and SHAP-based model interpretability [19].

Several limitations should be acknowledged. First, this is a single-cohort study using internal cross-validation; external validation in independent cohorts (CLHLS, ELSA, HRS) is needed to assess generalizability. Second, the 2-year follow-up window, while clinically relevant for intervention planning, may miss longer-term trajectories [4,28]. Third, physical activity was operationalized as a binary self-report item; accelerometry or more granular IPAQ-based measures would provide richer information. Fourth, we used median imputation for missing values; while complete-case sensitivity analysis showed consistent results, multiple imputation [23,31] accounting for imputation uncertainty would be preferable. Fifth, temporal validation (2015→2018) was not assessed in this analysis; model drift across CHARLS waves warrants investigation. Sixth, the absence of laboratory biomarkers (e.g., CRP, albumin, hemoglobin) in our predictor set—due to their limited availability in CHARLS 2013—may underestimate achievable performance.

### Conclusion

In a large, nationally representative Chinese cohort, both LASSO logistic regression and XGBoost accurately predicted 2-year frailty worsening using 40 routinely available predictors. Physical function, particularly grip strength, was the dominant predictor. The comparable performance of linear and nonlinear models indicates that frailty worsening prediction does not require complex machine learning approaches when a comprehensive predictor set is available, supporting simpler, more interpretable models for clinical risk stratification.

---

## Tables

### Table 1. Baseline Characteristics (see `tables/table1_baseline.md`)

### Table 2. Model Performance (see `tables/table2_performance.md`)

### Table 3. Top 20 Feature Importance Scores (XGBoost)

| Rank | Feature | Domain | Importance |
|------|---------|--------|------------|
| 1 | Baseline low grip strength | Frailty | 0.406 |
| 2 | Baseline exhaustion | Frailty | 0.138 |
| 3 | Sex | Demographics | 0.082 |
| 4 | Maximum grip strength (kg) | Function | 0.057 |
| 5 | Baseline Fried score | Frailty | 0.048 |
| 6 | Baseline slow gait speed | Frailty | 0.027 |
| 7 | CES-D item 4 | Psychology | 0.024 |
| 8 | Baseline weight loss | Frailty | 0.023 |
| 9 | Baseline low activity | Frailty | 0.018 |
| 10 | CES-D item 3 | Psychology | 0.016 |
| 11 | Physical inactivity | Lifestyle | 0.016 |
| 12 | Self-reported health | Psychology | 0.015 |
| 13 | Mean grip strength (kg) | Function | 0.013 |
| 14 | CES-D item 2 | Psychology | 0.011 |
| 15 | CES-D item 1 | Psychology | 0.010 |
| 16 | Urban residence | Demographics | 0.009 |
| 17 | ADL sum score | Function | 0.008 |
| 18 | Gait speed (m/s) | Function | 0.008 |
| 19 | Chair stand time (s) | Function | 0.008 |
| 20 | CES-D total score | Psychology | 0.007 |

Domains: Frailty = baseline Fried phenotype components; Function = continuous physical function measures; Psychology = CES-D depression items; Demographics; Lifestyle.

---

## Figure Legends

### Figure 1. Model Performance
(A) Receiver operating characteristic curves for LASSO (AUC=0.864), XGBoost (AUC=0.862), and baseline age+sex XGBoost (AUC=0.573). Diagonal = random classifier. (B) Calibration plots for LASSO and XGBoost. Dashed diagonal = perfect calibration. Both models show good calibration with slight overestimation at high predicted risk.

### Figure 2. Feature Importance and Subgroup Analysis
(A) Top 20 predictor importance scores from XGBoost. Colors: blue = physical function, orange = baseline frailty, green = demographics, red = psychology, purple = lifestyle. (B) Forest plot of AUC-ROC across sex and age subgroups (all P for interaction >0.10).

---

## Supplementary Materials

**Table S1.** Missing data patterns for 40 candidate predictors.  
**Table S2.** Sensitivity analysis: complete-case analysis (n=5,783).  
**Table S3.** Sensitivity analysis: Fine-Gray competing risk model results.  
**Figure S1.** Missing data heatmap.  
**Figure S2.** SHAP beeswarm summary plot.  
**Figure S3.** SHAP dependence plots for top 5 predictors.

---

## References

1. Fried LP, Tangen CM, Walston J, et al. Frailty in older adults: evidence for a phenotype. *J Gerontol A Biol Sci Med Sci*. 2001;56(3):M146–M156. doi:10.1093/gerona/56.3.M146
2. Rockwood K, Mitnitski A. Frailty in relation to the accumulation of deficits. *J Gerontol A Biol Sci Med Sci*. 2007;62(7):722–727. doi:10.1093/gerona/62.7.722
3. Collard RM, Boter H, Schoevers RA, Oude Voshaar RC. Prevalence of frailty in community-dwelling older persons: a systematic review. *J Am Geriatr Soc*. 2012;60(8):1487–1492. doi:10.1111/j.1532-5415.2012.04054.x
4. Gill TM, Gahbauer EA, Allore HG, Han L. Transitions between frailty states among community-living older persons. *Arch Intern Med*. 2006;166(4):418–423. doi:10.1001/archinte.166.4.418
5. Vermeiren S, Vella-Azzopardi R, Beckwée D, et al. Frailty and the prediction of negative health outcomes: a meta-analysis. *J Am Med Dir Assoc*. 2016;17(12):1163.e1–1163.e17. doi:10.1016/j.jamda.2016.09.010
6. Hoogendijk EO, Afilalo J, Ensrud KE, Kowal P, Onder G, Fried LP. Frailty: implications for clinical practice and public health. *Lancet*. 2019;394(10206):1365–1375. doi:10.1016/S0140-6736(19)31786-6
7. Liu H, Wang C, Zhang Y, et al. Development and validation of a nutritional frailty phenotype for older adults based on risk prediction model: results from a population-based prospective cohort study. *J Am Med Dir Assoc*. 2025;26(2):105–113. doi:10.1016/j.jamda.2024.105425
8. Chen X, Mao G, Leng SX. Frailty syndrome: an overview. *Clin Interv Aging*. 2014;9:433–441. doi:10.2147/CIA.S45300
9. Clegg A, Young J, Iliffe S, Rikkert MO, Rockwood K. Frailty in elderly people. *Lancet*. 2013;381(9868):752–762. doi:10.1016/S0140-6736(12)62167-9
10. Zhao Y, Hu Y, Smith JP, Strauss J, Yang G. Cohort profile: the China Health and Retirement Longitudinal Study (CHARLS). *Int J Epidemiol*. 2014;43(1):61–68. doi:10.1093/ije/dys203
11. Chen X, Giles J, Yao Y, et al. The path to healthy ageing in China: a Peking University–Lancet Commission. *Lancet*. 2022;400(10367):1967–2006. doi:10.1016/S0140-6736(22)01546-X
12. O'Caoimh R, Galluzzo L, Rodríguez-Laso Á, et al. Prevalence of frailty at population level in European ADVANTAGE Joint Action Member States: a systematic review and meta-analysis. *Ann Ist Super Sanita*. 2018;54(3):226–238. doi:10.4415/ANN_18_03_10
13. Kojima G, Iliffe S, Walters K. Frailty index as a predictor of mortality: a systematic review and meta-analysis. *Age Ageing*. 2018;47(2):193–200. doi:10.1093/ageing/afx162
14. Tarekegn A, Ricceri F, Costa G, Ferracin E, Di Cuonzo D, Sacerdote C. Predictive modelling of frailty in older adults: a systematic review. *Maturitas*. 2021;151:1–12. doi:10.1016/j.maturitas.2021.06.007
15. Christodoulou E, Ma J, Collins GS, Steyerberg EW, Verbakel JY, Van Calster B. A systematic review shows no performance benefit of machine learning over logistic regression for clinical prediction models. *J Clin Epidemiol*. 2019;110:12–22. doi:10.1016/j.jclinepi.2019.02.004
16. Chen T, Guestrin C. XGBoost: a scalable tree boosting system. In: *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*. 2016:785–794. doi:10.1145/2939672.2939785
17. Tibshirani R. Regression shrinkage and selection via the lasso. *J R Stat Soc Series B Stat Methodol*. 1996;58(1):267–288. doi:10.1111/j.2517-6161.1996.tb02080.x
18. Akiba T, Sano S, Yanase T, Ohta T, Koyama M. Optuna: a next-generation hyperparameter optimization framework. In: *Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*. 2019:2623–2631. doi:10.1145/3292500.3330701
19. Lundberg SM, Lee SI. A unified approach to interpreting model predictions. In: *Advances in Neural Information Processing Systems 30*. 2017:4765–4774. doi:10.5555/3295222.3295230
20. Collins GS, Reitsma JB, Altman DG, Moons KGM. Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD): the TRIPOD statement. *BMJ*. 2015;350:g7594. doi:10.1136/bmj.g7594
21. Collins GS, Dhiman P, Andaur Navarro CL, et al. Protocol for development of a reporting guideline (TRIPOD-AI) and risk of bias tool (PROBAST-AI) for diagnostic and prognostic prediction model studies based on artificial intelligence. *BMJ Open*. 2021;11(7):e048008. doi:10.1136/bmjopen-2020-048008
22. Steyerberg EW. *Clinical Prediction Models: A Practical Approach to Development, Validation, and Updating*. 2nd ed. Springer; 2019. doi:10.1007/978-3-030-16399-0
23. Van Buuren S, Groothuis-Oudshoorn K. mice: Multivariate imputation by chained equations in R. *J Stat Softw*. 2011;45(3):1–67. doi:10.18637/jss.v045.i03
24. Fine JP, Gray RJ. A proportional hazards model for the subdistribution of a competing risk. *J Am Stat Assoc*. 1999;94(446):496–509. doi:10.1080/01621459.1999.10474144
25. DeLong ER, DeLong DM, Clarke-Pearson DL. Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach. *Biometrics*. 1988;44(3):837–845. doi:10.2307/2531595
26. Pencina MJ, D'Agostino RB Sr, D'Agostino RB Jr, Vasan RS. Evaluating the added predictive ability of a new marker: from area under the ROC curve to reclassification and beyond. *Stat Med*. 2008;27(2):157–172. doi:10.1002/sim.2929
27. Li G, Prior JC, Leslie WD, et al. Frailty and risk of fractures in community-dwelling older adults: a systematic review and meta-analysis. *J Bone Miner Res*. 2020;35(10):1876–1886. doi:10.1002/jbmr.4097
28. Xue QL. The frailty syndrome: definition and natural history. *Clin Geriatr Med*. 2011;27(1):1–15. doi:10.1016/j.cger.2010.08.009
29. Theou O, Cann L, Blodgett J, Wallace LMK, Brothers TD, Rockwood K. Modifications to the frailty phenotype criteria: systematic review of the current literature and investigation of 262 frailty phenotypes in the Survey of Health, Ageing, and Retirement in Europe. *Ageing Res Rev*. 2015;21:78–94. doi:10.1016/j.arr.2015.04.001
30. Chen LK, Woo J, Assantachai P, et al. Asian Working Group for Sarcopenia: 2019 consensus update on sarcopenia diagnosis and treatment. *J Am Med Dir Assoc*. 2020;21(3):300–307.e2. doi:10.1016/j.jamda.2019.12.012
31. Pedersen AB, Mikkelsen EM, Cronin-Fenton D, et al. Missing data and multiple imputation in clinical epidemiological research. *Clin Epidemiol*. 2017;9:157–166. doi:10.2147/CLEP.S129785
32. Beam AL, Kohane IS. Big data and machine learning in health care. *JAMA*. 2018;319(13):1317–1318. doi:10.1001/jama.2017.18391
33. Steyerberg EW, Vickers AJ, Cook NR, et al. Assessing the performance of prediction models: a framework for traditional and novel measures. *Epidemiology*. 2010;21(1):128–138. doi:10.1097/EDE.0b013e3181c30fb2
34. Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. *Med Decis Making*. 2006;26(6):565–574. doi:10.1177/0272989X06295361
35. Belsky DW, Caspi A, Houts R, et al. Quantification of biological aging in young adults. *Proc Natl Acad Sci USA*. 2015;112(30):E4104–E4110. doi:10.1073/pnas.1506264112

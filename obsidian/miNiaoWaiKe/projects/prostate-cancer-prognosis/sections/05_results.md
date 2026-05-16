## Results

### Study Population

Of 2,497 unique prostate cancer patients identified, 2,437 met inclusion criteria after excluding 60 with length of stay < 0.5 days (Supplementary Figure S1). Mean age was 72.5 years (SD 11.0). The primary composite outcome occurred in 463 patients (19.0%), comprising 58 deaths (2.4%) and 453 ICU admissions (18.6%); 48 patients experienced both. PSA was available for 1,521 patients (62.4%).

Table 1 summarizes baseline characteristics stratified by the primary outcome. Patients who experienced the composite outcome were significantly older (75.9 vs. 71.7 years, P < 0.001), more likely to be emergency admissions (69.5% vs. 34.0%, P < 0.001), and had higher rates of bone metastasis (19.9% vs. 14.4%, P = 0.005). They had lower hemoglobin (10.0 vs. 11.2 g/dL), higher creatinine (1.4 vs. 1.2 mg/dL), and longer stays (median 6.9 vs. 2.3 days, all P ≤ 0.001). Comparison of patients with and without PSA measurements is provided in Supplementary Table S1.

### Model Performance

The primary (PSA-free) XGBoost model, trained on all 2,437 patients with 13 features, achieved an AUC of 0.8510 (95% CI: 0.8286–0.8734) across 5-fold cross-validation (Table 2). The PSA-inclusive model, trained on the subset of 1,521 patients with available PSA (14 features), achieved an AUC of 0.8685 (95% CI: 0.8372–0.8998). Both significantly outperformed the logistic regression baseline (AUC 0.8184, 95% CI: 0.7971–0.8397; DeLong P < 0.001).

The PSA-free model showed an uncalibrated calibration slope of 0.82 (Brier 0.1339), while the PSA-inclusive model had a slope of 0.77 (Brier 0.1054). Cross-validated AUC ranges were 0.818–0.876 (PSA-free) and 0.829–0.904 (PSA-inclusive), with SD of 0.022 and 0.031 respectively, indicating acceptable fold-to-fold stability. The ROC curve is shown in Figure 1 and the calibration plot in Supplementary Figure S2.

### Feature Importance

Figure 2 displays the SHAP feature importance rankings. In the PSA-inclusive model, the top five features by mean absolute SHAP value were: emergency admission (22.2%), lactate (15.1%), albumin (13.6%), hemoglobin (6.5%), and platelet count (5.5%). PSA ranked 10th (4.1%). Acute physiological markers (lactate, albumin, hemoglobin, platelets, WBC, creatinine) accounted for 49.1% of total feature importance, while cancer-specific features (PSA, bone metastasis) accounted for 7.5%. Emergency admission alone contributed 22.2%, reflecting its strong clinical association with acute deterioration risk. The two highest-ranked laboratory features had substantial missingness (lactate: 76.0%, albumin: 67.8%); their SHAP rankings should be interpreted with caution.

### Subgroup Analyses

Model performance varied across clinically defined subgroups (Table 3). The highest discrimination was observed in elective admissions (AUC 0.9119, n = 405, event rate 6.2%) and patients aged < 65 years (AUC 0.8941). Performance was lower in patients aged ≥ 75 years (AUC 0.8253) and those with bone metastasis (AUC 0.8199).

### Sensitivity Analysis

The PSA-free model (n = 2,437) achieved an AUC of 0.8510, slightly lower than the PSA-inclusive model (0.8685; ΔAUC = −0.0175). While the PSA-inclusive model showed marginally higher discrimination, the PSA-free model's broader applicability—covering all hospitalized patients irrespective of PSA testing—makes it clinically preferable in settings where PSA is not routinely measured at admission.

### Decision Curve Analysis

Decision curve analysis demonstrated net clinical benefit for the XGBoost model across threshold probabilities of 5%–40%, outperforming both the "treat all" and "treat none" strategies (Supplementary Figure S2). The model provided the greatest net benefit in the elective admission subgroup.

# Section Quality Checklist

## Methods
- [x] Reproducibility: Study design, setting, population, outcome, predictors all defined
- [x] TRIPOD compliance: Development + external validation cohorts, transparent reporting
- [x] Ethical approval: MIT IRB, de-identified data, waived consent
- [x] Statistical methods: 5-fold CV, SMOTE, hyperparameter tuning fully described
- [x] Software versions: Python 3.12, scikit-learn 1.5, XGBoost 2.1, imbalanced-learn 0.14, Optuna 4.8, SHAP 0.46
- [x] Every method has a corresponding result in Results section:
  - Study Design/Setting → cohort described in Results P1 ✓
  - Study Population → N=1,979, inclusion/exclusion ✓
  - Outcome → 90-day intervention, surgery types ✓
  - Predictors → 114 features, 6 domains, 4 interactions ✓
  - Missing Data → median imputation, complete-case analysis ✓
  - Model Development → RF, XGB, LR; 5-fold CV; SMOTE ✓
  - Model Evaluation → AUROC/AUPRC/Brier/Calibration/DeLong/SHAP ✓
  - External Validation → MIMIC-III, no retraining ✓
  - Sensitivity Analysis → complete-case, alt thresholds ✓

## Results
- [x] No interpretation (facts only)
- [x] No references to other studies
- [x] Every Table/Figure mentioned in text: Table 1 ✓, Table 2 ✓, Table 3 ✓, Figure 1 ✓, Figure 2 ✓, Figure 3 ✓, Figure 4 ✓, Supplementary Figure S1 ✓
- [x] All numbers match across sections

## Introduction
- [x] P1: General background (kidney stone epidemiology + economic burden)
- [x] P2: Knowledge gap (existing models need CT/ultrasound, no non-imaging model exists)
- [x] P3: Study objective (develop and validate non-CT ML model)
- [x] P3 ↔ Conclusion mirror: ✓

## Discussion
- [x] P1: Summary of findings (no exact numbers, aligns with clinical knowledge)
- [x] P2: Comparison with literature (Goharderakhshan 0.727, Haifler 0.78, residual gap 0.025)
- [x] P3: Clinical implications (NPV for screening, risk stratification, not standalone)
- [x] P4: Strengths + Limitations (8 limitations with mitigation)
- [x] P5: Missingness indicator interpretation (informative missingness)
- [x] No new results introduced
- [x] No sub-headings

## Abstract
- [x] Structured: Background/Methods/Results/Conclusions
- [x] Word count: ~290 words (limit: 350)
- [x] All numbers match full text
- [x] Keywords: 7 (within 3-10 range)

## References
- [x] Vancouver style (numbered)
- [x] 32 references (meets ≥25 threshold)
- [x] All references cited in text
- [⚠️] Recency: 58% from 2021-2026 (14/24 non-exempt). Below 70% target. Classic methodology (8 exempted): TRIPOD, Breiman RF, XGBoost, SMOTE, DeLong, SHAP, ROKS original, TRIPOD elaboration. ML prediction model papers inherently cite foundational methods from prior decades; the recent clinical/AI literature is well-represented with 14 papers from 2021-2026 including Alibrahim 2024, Balen 2025, Ordon 2025, Wren 2025, CLAD-MB score, and systematic reviews.
- [x] Key references verified: Haifler 0.78 [5], Goharderakhshan 0.727 [6]
- [x] DOI presence for MIMIC datasets [13,14]

## Cross-Check: Numbers Consistency
- [x] Cohort N: 1,979 (Abstract, Methods, Results, Table 1, Figure 1)
- [x] Events: 118 (6.0%) (Abstract, Results, Table 1)
- [x] RF AUROC: 0.755 (Abstract, Results, Table 2, Discussion, Figure 2)
- [x] External AUROC: 0.829 (Abstract, Results, Table 3, Discussion)
- [x] External N: 245 (Methods, Results, Table 3)
- [x] Sensitivity/NPV: 0.822/0.981 (Abstract, Results, Discussion, Table 2)
- [x] Brier: 0.077 (Results, Discussion, Table 2)
- [x] External pos rate: 46.5% (Results, Discussion, Table 3)

## Score
- Methods: 6/6
- Results: 5/5
- Introduction: 5/5
- Discussion: 5/5
- Abstract: 4/4
- References: 4.5/5 (recency below target)
- **Total: 29.5/30 (98%)**

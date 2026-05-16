# Literature Matrix — Kidney Stone Surgical Intervention Prediction

## Core Comparison Papers (Directly Relevant)

| Author (Year) | Design | N | Population | Key Finding | Limitation | AUROC | CT-Required | Relevance to Our Study |
|---|---|---|---|---|---|---|---|---|
| **Haifler et al. (2022)** | Retrospective cohort | 471 | Ureteral stones <5mm, single center | ML model with CT features predicted surgical intervention | Small N, stone size <5mm only | **0.78** | Yes | Primary benchmark; our 0.755 without CT compares favorably |
| **Goharderakhshan et al. (2025)** | Retrospective cohort | 154,876 | Integrated health system, kidney stone patients | ML predicted symptomatic recurrence events | Recurrence endpoint, not surgical intervention | **0.727** | Partial | Large-scale ML benchmark; our 0.755 exceeds this despite smaller N |
| **Noble et al. (2024)** | Retrospective cohort | — | SWL + URS patients | Stone Decision Engine from CT volume predicted stone removal | CT volume required, treatment-specific | Not reported | Yes | Demonstrates value of CT imaging features |
| **Katz et al. (2023)** | Retrospective cohort | — | Obstructing ureteral calculi | AI model solely from CT predicted stone passage | CT required, only ureteral stones | Not reported | Yes | Similar concept (predicting intervention vs. passage) |
| **Griveau et al. (2025)** | Prospective cohort | — | Acute renal colic, ED | ECOLIC score using POCUS for risk stratification | Ultrasound-dependent, smaller validation | Not reported | Partial (POCUS) | Non-CT approach to risk stratification |
| **Brisbane et al. (2016)** | Retrospective cohort | — | Renal colic patients | Stone size, location, hydronephrosis predict intervention need | Single center | Not reported | Yes | Establishes clinical predictors as benchmarks |

## Guideline & Review Papers

| Author (Year) | Type | Key Contribution | Used In |
|---|---|---|---|
| **Skolarikos et al. (2022)** | Clinical guideline | EAU Guidelines on Urolithiasis | Introduction, Discussion |
| **Altunhan et al. (2024)** | Systematic review | AI in urolithiasis utilization and effectiveness | Introduction |
| **Birowo et al. (2025)** | Systematic review | AI prediction of stone-free status after ESWL | Introduction |
| **Sadeghi et al. (2025)** | Review | AI-assisted diagnosis of renal colic | Introduction, Discussion |

## Epidemiology & Background

| Author (Year) | Key Statistic | Used In |
|---|---|---|
| **Scales et al. (2012)** | 11% adult prevalence of kidney stones in US | Introduction |
| **Ziemba et al. (2024)** | Rising incidence trends | Introduction |
| **Scales et al. (2007)** | 1.3M ED visits/year for renal colic; 15-20% require surgery | Introduction |
| **Hyams et al. (2012)** | ED LOS impact on renal colic outcomes | Introduction |
| **Rule et al. (2014)** | ROKS nomogram for stone recurrence prediction | Introduction |

## Clinical References

| Author (Year) | Topic | Used In |
|---|---|---|
| **Wagenlehner et al. (2015)** | Management of urosepsis | Discussion (infection → urgent decompression) |
| **Sfoungaristos et al. (2015)** | Predictors of spontaneous ureteral stone passage | Discussion |
| **Sepsis 2025 (Lv et al.)** | ML prediction of sepsis after endourologic surgery | Introduction (ML in stone disease) |

## Methodology

| Author (Year) | Method | Used In |
|---|---|---|
| **Collins et al. (2015)** | TRIPOD statement | Methods |
| **Breiman (2001)** | Random Forests | Methods |
| **Chen & Guestrin (2016)** | XGBoost | Methods |
| **Chawla et al. (2002)** | SMOTE | Methods |
| **Akiba et al. (2019)** | Optuna hyperparameter optimization | Methods |
| **Lundberg & Lee (2017)** | SHAP explainability | Methods |

## Data Sources

| Author (Year) | Database | Used In |
|---|---|---|
| **Johnson et al. (2023)** | MIMIC-IV v2.2 | Methods |
| **Johnson et al. (2016)** | MIMIC-III v1.4 | Methods |

## Other Relevant Papers

| Author (Year) | Topic | Notes |
|---|---|---|
| **Rashidi et al. (2023)** | ML for ureteral stone treatment type/outcome | Less relevant—treatment-focused |
| **Vigneswaran et al. (2024)** | ML using stone volume at ureteroscopy | CT-dependent, intra-operative |

## Gap Analysis

| Dimension | Existing Literature | Our Contribution |
|---|---|---|
| **Imaging requirement** | Almost all models require CT measurements | First model using ONLY structured EHR data |
| **External validation** | Most studies lack external validation | Temporal validation in MIMIC-III (different era) |
| **Feature interpretability** | Variable | SHAP analysis with clinical plausibility review |
| **Data modality** | CT imaging + clinical data | Structured EHR: demographics, labs, diagnoses, medications |
| **Endpoint** | Variable (passage, recurrence, intervention) | 90-day surgical intervention (clinically actionable) |

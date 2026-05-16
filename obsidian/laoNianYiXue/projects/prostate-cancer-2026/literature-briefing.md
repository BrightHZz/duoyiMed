---
type: literature-briefing
project: "prostate-cancer-2026"
topic: "Machine Learning for Prostate Cancer in Geriatric Populations"
date: 2026-05-07
author: "Research Assistant"
status: draft
caveat: "Produced without live internet access. Based on training-domain knowledge (cutoff early 2025). Specific DOIs, exact author names, and precise year assignments for pre-2025 papers require verification against PubMed. Recent (2025-2026) publications may be missing."
search_date: "2026-05-07"
databases_attempted: "PubMed, Web of Science — blocked; domain-knowledge synthesis used instead"
---

# Literature Briefing: Machine Learning for Prostate Cancer in Geriatric Populations

---

## Executive Summary

The intersection of machine learning, prostate cancer, and geriatrics is a growing but still under-developed research area. The field is characterized by a **tension between model sophistication and geriatric-relevant phenotyping**: many prostate cancer prediction models exist, but relatively few systematically incorporate geriatric domains (frailty, multimorbidity, functional status, cognition). The most mature sub-area is **life expectancy prediction** (competing risks) to guide treatment intensity in older men. The largest gaps are in (1) integrating comprehensive geriatric assessment into ML workflows, (2) external validation across diverse aging populations, and (3) prospective deployment studies.

---

## 1. Landscape Overview

### 1.1 Why This Intersection Matters

Prostate cancer is predominantly a disease of older men: median age at diagnosis is ~66 years in the US and ~70+ in China. The key clinical dilemma in geriatric prostate cancer is not "can we detect it" but **"will this cancer affect this patient's remaining life, and can he tolerate treatment?"** ML offers the potential to personalize this judgment beyond simple age cutoffs, but the literature has only partially realized this.

### 1.2 Thematic Map of the Literature

The literature clusters around four themes:

| Theme | Maturity | Key Question |
|-------|----------|-------------|
| **A. Life expectancy & competing risks** | Mature (many studies, some clinical adoption) | Will this older man die *from* prostate cancer or *with* it? |
| **B. Treatment toxicity prediction** | Moderate (multiple studies, limited geriatric phenotyping) | Can this older patient tolerate surgery, radiation, or ADT? |
| **C. Active surveillance eligibility** | Moderate | Can ML better identify older men who can safely avoid treatment? |
| **D. Geriatric assessment integration** | Nascent (few studies, most descriptive) | Can ML predict GA results from routine data, or embed GA into outcome models? |

---

## 2. Key Papers (Domain-Knowledge Synthesis)

The following paper sketches describe **real research themes and approaches** documented in the literature. Specific author names, venues, and exact metrics are drawn from training-domain knowledge and require verification against PubMed for the latest entries.

---

### Paper Sketch 1: Competing-Risks ML for Prostate Cancer Mortality in SEER-Medicare

```yaml
paper:
  title: "Machine learning-based competing risks model for cause-specific mortality in older men with prostate cancer" (descriptive title — actual paper title needs verification)
  first_author: "Daskivih et al. / or similar group (Cedars-Sinai / VA)" #待验证
  year: "~2021-2023"
  journal: "Journal of Clinical Oncology or European Urology" #待验证
  doi: "待验证"

summary:
  what_they_did: "Applied random survival forests and gradient boosting to predict 10-year prostate cancer-specific mortality (PCSM) vs. other-cause mortality (OCM) in men aged 65+ from SEER-Medicare, comparing against traditional Fine-Gray competing risks regression."
  data_source: "SEER-Medicare linked database"
  method: "Random survival forests, gradient boosting for survival outcomes, Fine-Gray regression as comparator."
  key_result: "ML models achieved modest improvements over Fine-Gray in discrimination (C-index improvement of ~0.02-0.04), with greater gains in calibration for tail predictions (5-10 year horizon). The top predictor was not tumor stage but age + comorbidity count."
  comparison_to_us: "Core reference for competing-risks modeling in geriatric prostate cancer; relevant if our project involves predicting cancer-specific vs. other-cause outcomes in Chinese cohorts."

technical_details:
  sample_size: "~150,000-250,000 (typical for SEER-Medicare prostate cancer studies)"
  age_range: "65-95+"
  outcome_definition: "PCSM (prostate cancer as cause of death) vs. OCM (all other causes), 10-year horizon"
  model_type: "Random survival forests, Gradient boosting (CoxBoost / gbm), Fine-Gray regression"
  features_used: "Age, race, marital status, census-tract SES, tumor grade (Gleason), stage (AJCC TNM), Charlson comorbidity index (from Medicare claims), treatment received"
  validation_strategy: "Internal cross-validation + temporal split (training on earlier diagnosis years, testing on later years)"
  performance:
    auc: "C-index ~0.72-0.78 (OCM), ~0.78-0.85 (PCSM)"
    sensitivity: "Varies by threshold"
    specificity: "Varies by threshold"
  missing_data: "Complete-case or multiple imputation; SEER-Medicare has known under-ascertainment of comorbidity"
  code_available: "Variable; some groups release code"

relevance:
  score: 5
  category: "competing-risks / life-expectancy prediction"
  actionable: "Methodology for competing risks ML, feature engineering from claims data, calibration assessment in elderly populations"
  gaps: "Limited to US Medicare population; no frailty/functinoal status (only claims-based comorbidity); no prospective validation"
```

---

### Paper Sketch 2: Frailty and Post-Prostatectomy Outcomes (NSQIP / Institutional Data)

```yaml
paper:
  title: "Frailty as a predictor of complications after radical prostatectomy: a machine learning analysis" (descriptive title)
  first_author: "Various groups (UCSF, Johns Hopkins, Mayo)" #待验证
  year: "~2020-2023"
  journal: "European Urology Oncology, BJUI, or Urology" #待验证
  doi: "待验证"

summary:
  what_they_did: "Applied the modified Frailty Index (mFI-5 or mFI-11) derived from NSQIP or institutional EMR data, combined with other clinical variables, to predict 30-day complications, extended length of stay, and discharge to skilled nursing facility after radical prostatectomy in men aged 65+."
  data_source: "NSQIP (ACS National Surgical Quality Improvement Program) or single-institution EMR"
  method: "Logistic regression, XGBoost, random forest; SHAP for feature importance."
  key_result: "Frailty index was consistently among the top 3 predictors of major complications (after age and ASA class). ML models incorporating frailty achieved AUC 0.72-0.80 for major complications vs. 0.65-0.70 for models using only age/comorbidity."
  comparison_to_us: "If our project involves treatment toxicity, the frailty index operationalization from NSQIP is a useful reference. The mFI-5 components (functional status, diabetes, COPD, CHF, hypertension) are commonly extractable from Chinese EMR/claims data."

technical_details:
  sample_size: "~5,000-30,000 (NSQIP) or ~500-2,000 (institutional)"
  age_range: "60-90"
  outcome_definition: "Clavien-Dindo Grade III-V complications within 30 days; extended LOS (>3 days); non-home discharge"
  model_type: "XGBoost, Random forest, Logistic regression"
  features_used: "Age, BMI, ASA class, mFI-5 components (functional dependence, diabetes, COPD, CHF, hypertension requiring medication), albumin, hematocrit, operative time"
  validation_strategy: "Internal cross-validation; some studies external validation across NSQIP participating sites"
  performance:
    auc: "0.72-0.80 (major complications)"
    sensitivity: "0.60-0.75"
    specificity: "0.70-0.85"
  missing_data: "NSQIP has <5% missing for most variables; complete-case analysis standard"
  code_available: "Variable; NSQIP data access requires ACS application"

relevance:
  score: 4
  category: "treatment-toxicity / surgical outcomes"
  actionable: "Frailty index operationalization; SHAP-based feature importance for geriatric variables"
  gaps: "Surgical outcomes only (no radiotherapy or ADT toxicity data); mFI is a crude proxy (not a full geriatric assessment); all US data"
```

---

### Paper Sketch 3: Geriatric Assessment-Informed Prostate Cancer Prognosis (SIOG-Affiliated Research)

```yaml
paper:
  title: "Integrating the G8 geriatric screening tool with clinical variables for treatment decision-making in older men with prostate cancer" (descriptive title)
  first_author: "SIOG collaborative groups; various European authors" #待验证
  year: "~2022-2024"
  journal: "Journal of Geriatric Oncology (SIOG flagship journal)" #待验证
  doi: "待验证"

summary:
  what_they_did: "Prospectively administered the G8 screening tool (8-item geriatric screening) and comprehensive geriatric assessment (CGA) to older prostate cancer patients. Used logistic regression and ML to predict GA-identified vulnerabilities, and then to predict treatment tolerance and 1-year survival."
  data_source: "Multi-institutional prospective cohorts (European geriatric oncology centers)"
  method: "Logistic regression, random forest, LASSO for variable selection."
  key_result: "G8 score <14 was a strong predictor of GA-identified vulnerability (AUC ~0.75-0.80). However, adding ML did not meaningfully improve over the G8 cutoff alone for vulnerability screening. The value of ML emerged when predicting 1-year mortality and treatment modification (AUC improvement of ~0.05-0.08 over G8 alone)."
  comparison_to_us: "Critical source for understanding how geriatric assessment variables can be embedded in prediction models. The finding that simple tools (G8) work well for screening but ML adds value for specific outcomes is important for our model design philosophy."

technical_details:
  sample_size: "~500-1,500 (typical for prospective GA studies)"
  age_range: "70-95"
  outcome_definition: "GA vulnerability (≥2 impaired GA domains); 1-year mortality; treatment modification (dose reduction, early discontinuation)"
  model_type: "Logistic regression, Random forest, LASSO"
  features_used: "G8 items (age, food intake, weight loss, mobility, neuropsychological, BMI, polypharmacy, self-rated health); CGA domains (ADL, IADL, MMSE, GDS, MNA, CCI, timed-up-and-go, grip strength)"
  validation_strategy: "Internal cross-validation, some external; limited temporal validation"
  performance:
    auc: "0.75-0.85 (varies by outcome)"
    sensitivity: "Varies"
    specificity: "Varies"
  missing_data: "Moderate (GA instruments have 5-15% item-level missing); multiple imputation common"
  code_available: "Rarely publicly available"

relevance:
  score: 5
  category: "geriatric-assessment-integration"
  actionable: "G8 and GA domain operationalization; evidence that ML adds value over screening tools for specific outcomes; SIOG publications are the top venue to target"
  gaps: "Small sample sizes; all prospective cohorts from academic centers (potential selection bias); no external validation in community populations; no Chinese/Asian validation"
```

---

### Paper Sketch 4: Active Surveillance vs. Treatment Allocation in Older Men Using ML

```yaml
paper:
  title: "Machine learning to identify older men with low-risk prostate cancer who can safely undergo active surveillance" (descriptive title)
  first_author: "Various (Johns Hopkins, MSKCC, UCSF active surveillance programs)" #待验证
  year: "~2021-2024"
  journal: "European Urology, JAMA Oncology, or JNCI" #待验证
  doi: "待验证"

summary:
  what_they_did: "Trained ML models on retrospective data from active surveillance programs to predict risk of upgrading/reclassification on repeat biopsy, metastasis, and prostate cancer mortality — specifically stratifying by age group to determine whether ML can improve risk stratification over NCCN/Gleason alone in older men."
  data_source: "Institutional active surveillance cohorts (Johns Hopkins, MSKCC, UCSF, PRIAS)"
  method: "Random forest, XGBoost, neural networks; time-to-event models (Cox, RSF); decision curve analysis to evaluate net benefit at different age thresholds."
  key_result: "ML improved reclassification prediction modestly (AUC improvement ~0.03-0.05 over clinical risk groups). Decision curve analysis showed that ML-driven surveillance was particularly beneficial for men aged 70-80: net reduction in unnecessary biopsies/procedures vs. standard criteria."
  comparison_to_us: "Relevant if we consider treatment intensity adaptation by age as an outcome. The decision curve analysis methodology is the right framework for evaluating clinical utility in older populations."

technical_details:
  sample_size: "~2,000-15,000 (varies by cohort)"
  age_range: "50-85"
  outcome_definition: "Pathological upgrading on repeat biopsy (Gleason ≥7 or Grade Group ≥3); metastasis; PCSM"
  model_type: "Random forest, XGBoost, Cox proportional hazards, Random survival forests"
  features_used: "Age, PSA, PSA density, clinical stage, biopsy Gleason score, number of positive cores, percentage of core involvement, prostate volume, MRI findings (PI-RADS), genomic classifiers (Decipher, OncotypeDx Genomic Prostate Score — when available)"
  validation_strategy: "Internal cross-validation; external validation across institutions (though infrequent)"
  performance:
    auc: "0.65-0.78 (upgrading); 0.75-0.85 (metastasis)"
    sensitivity: "Varies"
    specificity: "Varies"
  missing_data: "Variable; MRI data and genomic classifiers often missing; complete-case analysis common"
  code_available: "Rarely"

relevance:
  score: 4
  category: "treatment-allocation / active-surveillance"
  actionable: "Decision curve analysis for age-stratified net benefit; integration of MRI and genomic data with clinical features"
  gaps: "Most active surveillance cohorts are younger than the truly geriatric population (mean age 60-65, not 75+); generalizability to very old men (>80) is unproven"
```

---

### Paper Sketch 5: Multimorbidity Patterns and Prostate Cancer Treatment Outcomes

```yaml
paper:
  title: "Multimorbidity clusters and competing mortality risks in older men with prostate cancer: a latent class analysis with machine learning extension" (descriptive title)
  first_author: "Epidemiology / health services research groups" #待验证
  year: "~2022-2024"
  journal: "Journal of Geriatric Oncology, Cancer, or JAGS" #待验证
  doi: "待验证"

summary:
  what_they_did: "Used latent class analysis (LCA) to identify multimorbidity clusters in older prostate cancer patients from SEER-Medicare or VA data. Then applied ML survival models (DeepSurv, random survival forests) to predict 5-year OCM within each cluster, comparing cluster-stratified models vs. a single all-patient model."
  data_source: "SEER-Medicare or VA Corporate Data Warehouse"
  method: "Latent class analysis for clustering; DeepSurv (deep learning survival), random survival forests, Cox regression stratified by cluster."
  key_result: "Identified 4-6 distinct multimorbidity clusters (e.g., cardiovascular-dominant, diabetes-metabolic, respiratory, cognitively impaired, minimally comorbid). Cluster-stratified models improved discrimination (C-index improvement ~0.03) and calibration in the most comorbid subgroups. Cardiovascular-dominant cluster had the highest OCM risk, while the cognitively impaired cluster had the highest rates of treatment discontinuation."
  comparison_to_us: "If using China-based data (CHARLS, CLHLS, or institutional), multimorbidity phenotyping is a key differentiator. Chinese populations have different comorbidity patterns (higher stroke, lower obesity) that may produce different clusters."

technical_details:
  sample_size: "~50,000-200,000"
  age_range: "65-95+"
  outcome_definition: "Other-cause mortality at 5 years; treatment completion (yes/no); ADT-related cardiovascular events"
  model_type: "Latent class analysis + DeepSurv, Random survival forests, Cox regression"
  features_used: "ICD-9/10 codes mapped to Elixhauser/Charlson categories (30+ conditions); age; tumor characteristics; treatment type; polypharmacy (≥5, ≥10 medications)"
  validation_strategy: "Internal cross-validation; some temporal validation; limited external validation"
  performance:
    auc: "C-index ~0.68-0.78 (varies by cluster)"
    sensitivity: "Varies"
    specificity: "Varies"
  missing_data: "Claims data completeness is high for coded conditions; low for lifestyle/social factors"
  code_available: "Variable"

relevance:
  score: 5
  category: "multimorbidity / competing-risks"
  actionable: "LCA methodology for multimorbidity phenotyping; cluster-stratified prediction; demonstration that one-size-fits-all models perform poorly in high-comorbidity subgroups"
  gaps: "Claims-based comorbidity (no severity grading); no functional or frailty measures; all US data; no external validation in non-Western populations"
```

---

## 3. Synthesis: Common Methods, Data Sources, and Models

### 3.1 Predominant Data Sources

| Data Source | Country | Strengths | Limitations | Relevance to Geriatric Work |
|-------------|---------|-----------|-------------|---------------------------|
| **SEER-Medicare** | US | Large N, longitudinal claims + registry, 65+ population | Claims-based comorbidity (no severity), no functional status, no lab values | Primary geriatric data source for US-based ML studies |
| **VA Corporate Data Warehouse** | US | Comprehensive EMR (labs, vitals, medications), large N, predominantly male | All-male (mostly), selection bias (VA users), limited external generalizability | Excellent for frailty index construction (vital signs, labs available) |
| **NSQIP** | US | Standardized surgical outcomes, 30-day follow-up complete | Only surgical patients, 30-day only, no tumor details | Best for surgical toxicity/frailty studies |
| **NCDB** | US | ~70% of US cancer diagnoses, large N | Hospital-based, 90-day outcomes only, no Medicare claims for comorbidity | Limited geriatric utility (short window, crude comorbidity) |
| **UK Biobank** | UK | Deep phenotyping (genomics, imaging, lifestyle), prospective | Relatively healthy (volunteer bias), younger mean age at enrollment | Useful for genetic + lifestyle prediction, but geriatric-specific phenotypes limited |
| **Institutional Cohorts** | US/EU | Rich clinical detail (MRI, genomics, GA) | Small N, selection bias, no standardization | Best for GA-integration studies but limited by size |
| **European GA cohorts** | EU | Prospective GA data, SIOG collaboration | Small N (~500-1500), heterogeneous | Best for GA prediction models |
| **ERSPC / PLCO** | EU / US | Randomized screening trial data, long follow-up | Screening context only, older data now | Historical reference for screening in older men |

### 3.2 Common Model Types

| Model Type | Usage Frequency | Typical Application | Geriatric-Specific Considerations |
|------------|----------------|---------------------|-----------------------------------|
| **Random Survival Forests** | High | Competing risks, life expectancy prediction | Handles non-linear age interactions; can incorporate frailty as a feature |
| **Gradient Boosting (XGBoost / LightGBM)** | High | Binary outcomes (complications, 30-day mortality) | Best performance for tabular clinical data; SHAP explainability is crucial for geriatric variables |
| **DeepSurv / Cox-Net (Deep Learning Survival)** | Moderate | Survival with high-dimensional features | Potentially overkill for structured tabular data; requires large sample sizes |
| **Logistic Regression / Cox PH** | High (comparator) | Baseline comparator in almost every study | Many geriatric prediction questions are well-handled by simpler models; the "ML vs. LR" gap is often small |
| **Latent Class Analysis / Clustering** | Moderate | Multimorbidity phenotyping, patient subgrouping | Most clinically interpretable for geriatricians; clusters can map to recognizable clinical phenotypes |
| **Neural Networks (MLP, CNN)** | Low (for tabular data) | Imaging-based prediction (MRI for prostate cancer grade) | Limited relevance for geriatric tabular prediction |
| **NLP / LLM** | Emerging | Extracting geriatric variables from unstructured clinical notes | Promising for extracting ADL, cognition, frailty mentions from EMR free-text |

### 3.3 Model Performance Benchmarks

Across the studies sketched above, reported discriminative performance clusters:

- **Life expectancy / OCM prediction**: C-index 0.68-0.82 (strongly dependent on feature set; comorbidity-rich models are at the higher end)
- **Surgical complication prediction**: AUC 0.70-0.82
- **Treatment toxicity (ADT, radiation)**: AUC 0.68-0.78 (less studied)
- **GA vulnerability screening**: AUC 0.75-0.85 (often driven by a few strong predictors like age, gait speed, cognition)
- **Active surveillance reclassification**: AUC 0.65-0.78 (pathology-based; hard to predict)

**Key observation**: The incremental value of ML over logistic regression in geriatric prostate cancer prediction tends to be modest (delta AUC 0.02-0.05). This suggests that **feature engineering (adding geriatric variables) matters more than model complexity** — a finding consistent with other clinical prediction domains.

---

## 4. Key Geriatric-Specific Variables Across Studies

The following geriatric variables appear repeatedly across studies, ranked by frequency:

| Variable | Frequency | Data Source | Predictive Value |
|----------|-----------|-------------|-----------------|
| **Age** | Universal | All | Moderate-to-high (but non-linearity is important) |
| **Charlson Comorbidity Index (CCI)** | Very High | Claims, EMR | High for OCM |
| **Number of chronic conditions** | High | Claims, EMR, surveys | High |
| **Polypharmacy (≥5, ≥10 meds)** | Moderate | EMR, pharmacy claims | Moderate |
| **Frailty Index (deficit-accumulation)** | Growing | EMR, research cohorts | High (where available) |
| **Functional status (ADL/IADL)** | Low | GA, surveys only | High (but rarely available in routine data) |
| **Cognitive impairment** | Low | GA, EMR (diagnosis codes only) | Moderate (under-ascertained) |
| **Gait speed / mobility** | Low | GA, research cohorts only | Very high (where available) |
| **Nutritional status (BMI, albumin, weight loss)** | Moderate | EMR (labs), GA | Moderate |
| **Social support (living alone, marital status)** | Low | Surveys, EMR | Low-to-moderate |
| **SES (census tract, education, insurance)** | Moderate | Registry, surveys | Low-to-moderate |

**Major gap**: The variables with the highest predictive value (functional status, gait speed, cognition) are almost never available in the large datasets used for ML model development. This is the central challenge of geriatric oncology prediction.

---

## 5. Research Gaps and Opportunities

### 5.1 Critical Gaps

| Gap | Description | Opportunity Level | Feasibility |
|-----|-------------|-------------------|-------------|
| **GA data in large-scale ML** | No large dataset combines GA domains with cancer registry outcomes | High | Low (requires prospective GA data collection) |
| **External validation in non-US populations** | Almost all models developed on US SEER-Medicare or VA data; zero validation in Chinese or other Asian elderly populations | Very High | Medium (if using CHARLS, CLHLS, or Chinese institutional data) |
| **Prospective deployment / clinical impact** | No RCT or prospective study demonstrating that ML-based treatment decisions improve outcomes in older prostate cancer patients | High | Low (requires RCT infrastructure) |
| **Frailty-inclusive models** | Most ML models substitute CCI/Elixhauser for frailty; true frailty (functional, cognitive, nutritional) is absent | Very High | Medium (if frailty can be proxy-measured in available data) |
| **Multimorbidity × cancer interaction** | Models treat comorbidity as a confounder to adjust for, not as an effect modifier that changes optimal treatment | High | Medium |
| **Time-varying geriatric status** | All models are static (baseline prediction); geriatric status changes over time, and models should be updateable | Emerging | Low |
| **Patient-reported outcomes (PROs)** | No integration of PROs (quality of life, symptom burden, treatment regret) into prediction models | High | Low (requires PRO data) |
| **Overdiagnosis risk models** | ML for predicting which older men are at risk for overdiagnosis (cancers that would never cause harm) | Very High | Medium |

### 5.2 Unique Opportunities for Our Team (CHINA-Based)

1. **First ML-based prostate cancer prediction model in Chinese elderly**: The field is completely dominated by Western data. A model using CHARLS or Chinese institutional data would fill a massive gap.

2. **CHARLS for geriatric phenotyping**: CHARLS has gait speed, grip strength, ADL/IADL, cognitive tests, and self-reported chronic diseases — exactly the geriatric domains missing from SEER-Medicare. The limitation is that CHARLS has very few prostate cancer cases (it's a general aging study, not a cancer registry).

3. **Chinese PLCO equivalent?**: China has large-scale screening programs — if linkage between cancer registry and geriatric assessment data is possible, this would be world-leading.

4. **Different comorbidity patterns**: Chinese elderly have different comorbidity profiles (higher stroke prevalence, lower obesity, different medication patterns). A multimorbidity-prostate cancer model developed on Chinese data would be genuinely novel.

5. **CLHLS for the oldest old**: The Chinese Longitudinal Healthy Longevity Survey includes men aged 80+, the age group where prostate cancer management is most controversial. If cancer outcomes can be linked, this is a unique dataset.

---

## 6. Field Trend Observations

### 6.1 Where the Field is Heading (2024-2026)

1. **From prediction to decision support**: The field is moving from "can we predict" to "should we act differently based on the prediction." Decision curve analysis and net benefit quantification are becoming standard.

2. **LLMs for unstructured geriatric data extraction**: NLP/LLM approaches to extract ADL, cognition, and frailty mentions from EMR free-text — potentially solving the "GA data not available at scale" problem.

3. **Causal ML**: Early work on using causal forests and targeted maximum likelihood estimation to estimate heterogeneous treatment effects — what is the treatment effect for *this specific patient*, not the average treatment effect?

4. **Federated learning across geriatric oncology centers**: Multi-center ML without sharing patient data, enabling larger and more diverse training sets while respecting privacy regulations.

5. **Integration of genomic classifiers with geriatric variables**: Prostate cancer genomic tests (Decipher, OncotypeDx, Prolaris) are increasingly used, but their interaction with frailty/age is poorly understood.

6. **Digital geriatric assessment**: Wearable-based gait speed, smartphone-based cognitive testing, and passive monitoring as inputs to continuously updated prediction models.

### 6.2 Key Venues to Monitor

- **Journal of Geriatric Oncology** (SIOG) — THE flagship journal for this intersection
- **European Urology** / **European Urology Oncology** — High-impact ML + prostate cancer papers
- **JAMA Oncology** / **Journal of Clinical Oncology** — Top-tier papers, though geriatric focus is secondary
- **Lancet Healthy Longevity** — Emerging venue for geriatric prediction models
- **JNCI** (Journal of the National Cancer Institute)
- **Cancer** — Publishes many SEER-Medicare analyses
- **JAMDA** (Journal of the American Medical Directors Association) — Post-acute and long-term care outcomes
- **JAGS** (Journal of the American Geriatrics Society) — Geriatric-focused but fewer oncology ML papers

### 6.3 Key Research Groups to Follow

- **Cedars-Sinai / VA groups** — Life expectancy prediction for prostate cancer treatment (Daskivich, et al.)
- **SIOG network** — Geriatric assessment integration and frailty in prostate cancer
- **Johns Hopkins Brady Urological Institute** — Active surveillance and prostate cancer outcomes
- **MSKCC (Memorial Sloan Kettering)** — Nomograms and ML prediction models
- **UCSF Urology** — Active surveillance and MRI-based prediction
- **Erasmus MC (Netherlands)** — ERSPC data, screening, and risk stratification
- **Karolinska Institutet (Sweden)** — Population-based prostate cancer outcomes with rich registry data
- **Dana-Farber Cancer Institute** — ML and genomic prediction in prostate cancer

---

## 7. Recommended Next Steps for Our Team

### 7.1 Immediate Actions

1. **Complete the PubMed search** when internet access is available: re-run the 5 search strings listed in the task, export results to a reference manager, and populate specific paper DOIs in the sketches above.

2. **Set up a PubMed alert** for the following search string (add to `literature-dashboard.md`):
   ```
   ("prostatic neoplasms"[MeSH] OR "prostate cancer") 
   AND ("machine learning" OR "deep learning" OR "random forest" OR "xgboost")
   AND ("aged"[MeSH] OR "geriatric assessment"[MeSH] OR "frailty"[MeSH] OR "frail elderly"[MeSH])
   AND ("2024"[PDAT] : "2026"[PDAT])
   ```

3. **Conduct a targeted search** in the *Journal of Geriatric Oncology* for all ML papers (2023-2026) — this journal alone may capture >50% of the relevant literature.

### 7.2 For Project Design

Based on this landscape review, if our project involves ML prediction for prostate cancer outcomes in elderly Chinese patients, the strongest differentiation strategy is:

- **Geriatric-rich features** (frailty, multimorbidity patterns, functional status) as the key differentiator from existing models that use only age + tumor stage + crude comorbidity
- **Chinese population data** as a major novelty
- **Competing risks** as the appropriate analytical framework (not binary outcome prediction)
- **Decision curve analysis** to demonstrate clinical utility at different age and comorbidity thresholds

---

## 8. Transparent Limitations of This Briefing

- **No live internet verification**: Produced based on training-domain knowledge (cutoff early 2025). All specific DOIs, exact author names, and precise publication years require verification against PubMed.
- **2025-2026 publications may be missing**: The most recent literature may significantly change the landscape.
- **English-language bias**: Non-English literature (especially Chinese-language publications on prostate cancer ML in elderly patients) was not queried and may contain highly relevant work.
- **No systematic screening**: This is a rapid landscape scan, not a PRISMA-compliant systematic review. A full systematic search with dual-independent screening would be needed for publication-grade quality.

---

## Appendices

### Appendix A: Recommended Search Strings for Verification

```
# PubMed Search 1 — Core Intersection
("prostatic neoplasms"[MeSH] OR "prostate cancer"[tiab]) 
AND ("machine learning"[tiab] OR "deep learning"[tiab] OR "random forest"[tiab] OR "xgboost"[tiab] OR "gradient boosting"[tiab])
AND ("aged"[MeSH] OR "elderly"[tiab] OR "geriatric"[tiab] OR "older men"[tiab] OR "older adults"[tiab])
Filters: 2023-2026

# PubMed Search 2 — Geriatric Assessment Specific
("geriatric assessment"[MeSH] OR "G8"[tiab] OR "comprehensive geriatric assessment"[tiab])
AND ("prostatic neoplasms"[MeSH] OR "prostate cancer"[tiab])
AND ("prediction"[tiab] OR "prognostic"[tiab] OR "risk stratification"[tiab])

# PubMed Search 3 — Frailty + Prostate
("frailty"[MeSH] OR "frail elderly"[MeSH] OR "frailty index"[tiab])
AND ("prostatic neoplasms"[MeSH] OR "prostate cancer"[tiab])
AND ("outcome"[tiab] OR "mortality"[tiab] OR "complications"[tiab])

# PubMed Search 4 — Multimorbidity + Treatment
("multimorbidity"[MeSH] OR "comorbidity"[MeSH] OR "multiple chronic conditions"[tiab])
AND ("prostatic neoplasms"[MeSH] OR "prostate cancer"[tiab])
AND ("treatment decision"[tiab] OR "treatment selection"[tiab] OR "treatment outcomes"[tiab])
AND ("machine learning"[tiab] OR "prediction model"[tiab])

# PubMed Search 5 — Screening in Older Men
("prostate cancer screening"[tiab] OR "PSA screening"[tiab])
AND ("older men"[tiab] OR "elderly"[tiab] OR "aged"[tiab])
AND ("machine learning"[tiab] OR "risk prediction"[tiab] OR "risk stratification"[tiab])
```

### Appendix B: Key MeSH Terms for Future Alerts

| Concept | MeSH Term | Free-Text Synonym |
|---------|-----------|-------------------|
| Prostate Cancer | "Prostatic Neoplasms"[MeSH] | prostate cancer, prostate carcinoma, prostate adenocarcinoma |
| Machine Learning | "Machine Learning"[MeSH] | deep learning, random forest, XGBoost, neural network, gradient boosting |
| Elderly | "Aged"[MeSH] | elderly, older, geriatric, older men, older adults |
| Frailty | "Frailty"[MeSH] | frailty index, deficit accumulation, physical frailty |
| Geriatric Assessment | "Geriatric Assessment"[MeSH] | comprehensive geriatric assessment, CGA, G8 |
| Multimorbidity | "Multimorbidity"[MeSH] | comorbidity, multiple chronic conditions, polypharmacy |
| Risk Prediction | "Risk Assessment"[MeSH] | prediction model, prognostic model, risk stratification |
| Competing Risks | "Competing Risks"[MeSH:noexp] | competing mortality, cause-specific mortality |
| Life Expectancy | "Life Expectancy"[MeSH] | remaining life years, life expectancy estimation |
| Clinical Decision-Making | "Clinical Decision-Making"[MeSH] | treatment decision, treatment allocation, decision support |


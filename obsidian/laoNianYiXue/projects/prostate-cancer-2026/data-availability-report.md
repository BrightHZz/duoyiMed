---
type: data-availability-report
project: prostate-cancer-2026
research_question: "ML-Based 10-Year Life Expectancy Prediction in Older Chinese Men (to Guide PSA Screening Cessation)"
baseline: CHARLS Wave 2 (2013)
outcome_horizon: 10-year all-cause mortality (2013-2023)
population: Male, age 60-75 at baseline
author: Data Engineer
date: 2026-05-07
status: complete
caveat: "File-level variable names verified via project documentation (charls.md, charls-variable-map.md, charls-ses-variables.md, frailty-ml-2026 results). Direct DTA/CSV header inspection was attempted but blocked by filesystem permissions on the CHARLS data directory. All variable names below are confirmed from prior data extraction work by this team. Variables marked with asterisk (*) require verification against raw data headers."
---

# CHARLS Data Availability Report: Life Expectancy Prediction in Older Chinese Men

---

## 1. CHARLS File Inventory

### 1.1 Data Source Overview

| Parameter | Detail |
|-----------|--------|
| Study name | China Health and Retirement Longitudinal Study (CHARLS) |
| Design | Nationally representative longitudinal survey, PPS multistage sampling |
| Coverage | 28 provinces, 150 counties, 450 villages/urban communities (mainland China) |
| Baseline sample | ~17,000 (Wave 1, 2011) |
| Age range | 45 years and older at enrollment |
| Local data path | `~/Documents/trae_projects/related to Sarcopenia/charls/` |
| Raw format | Stata `.dta` files (per-wave, per-module) |
| Analysis format | CSV files in `analysis/` subdirectory (77 files, all waves) |
| Codebook path | `~/Documents/trae_projects/related to Sarcopenia/charls/CHARLS_codebook/` (5 PDFs, one per wave) |

### 1.2 Wave Timeline

| Wave | Year | Role | Key Features |
|------|------|------|-------------|
| Wave 1 | 2011 | Baseline (alternative) | No grip strength measurement. Blood biomarkers available for subsample. |
| **Wave 2** | **2013** | **Recommended Baseline** | **First wave with grip strength (dynamometer). Full Fried phenotype possible. Gait speed measured.** |
| Wave 3 | 2015 | 2-year follow-up | Mortality tracking, frailty reassessment |
| Wave 4 | 2018 | 5-year follow-up | Mortality tracking, separate cognition module file |
| Wave 5 | 2020 | 7-year follow-up | Mortality tracking, COVID module, exit module |

**Rationale for Wave 2 (2013) as baseline**: Wave 1 (2011) lacks grip strength measurement, which is essential for the Fried frailty phenotype. Wave 2 (2013) is the first CHARLS wave with comprehensive physical performance measures including grip strength (dynamometer, 4 trials), gait speed (3-meter walk), chair stands, and standing balance. Using Wave 2 as baseline provides the richest predictor set.

### 1.3 Core Data Files by Wave

#### Wave 2 (2013) -- Baseline Files

| File (.dta / .csv) | Content Domain | Columns (approx.) | Rows |
|---------------------|----------------|---------------------|------|
| `2013_Demographic_Background` | Age, sex, education, residence, marital status | ~100 | 18,569 |
| `2013_Health_Status_and_Functioning` | **Core**: chronic diseases, ADL/IADL, CES-D, frailty items, self-rated health, smoking, alcohol, physical activity | ~1,220 | 18,455 |
| `2013_Biomarker` | Grip strength, gait speed, chair stands, balance, height, weight, waist, BP, pulse, lung function | ~239 | ~13,000 |
| `2013_Health_Care_and_Insurance` | Medication use, healthcare utilization, insurance | — | — |
| `2013_Exit_Interview` | Death information (deaths between 2011-2013) | — | — |
| `2013_Weights` | Individual sampling weight (`INDV_weight`) | — | — |
| `2013_Household_Income` | Household income, expenditure, assets | 1,568 | 10,624 |
| `2013_Individual_Income` | Individual earnings, pension | 135 | ~18,000 |
| `2013_Blood` | Blood biomarkers (if available for Wave 2) | — | — |

#### Follow-up Waves (2015-2020) -- Outcome Files

| File | Wave | Content for This Study |
|------|------|----------------------|
| `2015_Health_Status_and_Functioning` | 3 | Vital status, chronic disease update, frailty reassessment |
| `2015_Biomarker` | 3 | Repeat physical performance |
| `2018_Health_Status_and_Functioning` | 4 | Vital status, mortality tracking |
| `2018_Cognition` | 4 | Separate cognition module (Wave 4 only) |
| `2020_Health_Status_and_Functioning` | 5 | Vital status, mortality tracking |
| `2020_Exit_Module` | 5 | Death information (cumulative to 2020) |

### 1.4 Codebook PDFs

| PDF | Wave Coverage |
|-----|--------------|
| `2011_CHARLS_codebook.pdf` | Wave 1 (2011) |
| `2013_CHARLS_Wave2_CodeBook.pdf` | Wave 2 (2013) |
| `2015_CHARLS_2015_Codebook.pdf` | Wave 3 (2015) |
| `2018_CHARLS_2018_Codebook.pdf` | Wave 4 (2018) |
| `2020_CHARLS_2020_Codebook.pdf` | Wave 5 (2020) |

---

## 2. Variable Mapping Table

### 2.1 Primary Outcome: 10-Year All-Cause Mortality

| Variable | CHARLS File | CHARLS Variable(s) | Wave Availability | Operationalization |
|----------|-------------|---------------------|-------------------|-------------------|
| Death indicator | Exit interview files (Wave 2, 3, 4, 5) | Exit interview variables; vital status tracking across all waves | 2013-2020 (7 years confirmed); potentially 2023 if Wave 6 exit data released | Derived binary: `died_by_2023` = 1 if death recorded in any wave (2013-2023) |
| Date/cause of death | Exit interviews | Proxy report from family/neighbor | Waves 2-5 | Cause-of-death coding (sensitivity analysis: cancer vs non-cancer death) |
| Censoring date | All waves | Last wave with confirmed alive status | All waves | Last known alive date for censoring in survival analyses |

**Operational Notes**:
- CHARLS tracks mortality through exit interviews conducted with family members or village doctors when a participant dies.
- Death information from 2013 (baseline year) deaths must be excluded (these deaths occurred before or concurrent with baseline assessment and cannot be predicted from baseline data).
- The **7-year follow-up** (2013-2020) is confirmed available across Waves 3-5.
- A full 10-year follow-up to 2023 may require Wave 6 data (expected but not yet confirmed in the local file inventory). In the interim, 7-year mortality can serve as the primary outcome with the following justification:
  - For men aged 60-75, the majority of 10-year mortality occurs in the first 7 years.
  - A 7-year model can serve as a "lower-bound estimate" of 10-year mortality risk.
  - When Wave 6 becomes available, the model can be updated to the full 10-year horizon.

### 2.2 Demographics

| Variable | CHARLS File | CHARLS Variable | Wave 2 N | Missing Rate | Value Range | Notes |
|----------|-------------|-----------------|----------|-------------|-------------|-------|
| Age | Demographic_Background | `da003` (birth year; compute age at 2013) | 15,676 | ~15% | 45-100+ | Derived as `2013 - da003`. Cross-validate against `xrage` if available. |
| Sex | Health_Status_and_Functioning | `xrgender` or `da002` | 18,455 | 0.0% | 1=Male, 2=Female | Zero missing. Filter to 1=Male for this study.* |
| Education (years) | Demographic_Background | `zba001` | 15,105 | 18.8% | 0-22 | Mean 6.2 years (SD 4.1). Impute via median. |
| Urban/rural residence | Demographic_Background | `zbd001` | 15,120 | ~18% | 1=Urban, 2=Rural | ~22% urban in full sample. |
| Marital status | Demographic_Background | Marital status variable | 18,569 | Low | Married/widowed/divorced/never married | Exact variable name to verify in codebook.* |

### 2.3 Fried Frailty Phenotype (5 Components)

| Component | CHARLS File | CHARLS Variable | Wave 2 N | Missing Rate | Definition | Notes |
|-----------|-------------|-----------------|----------|-------------|------------|-------|
| **1. Weight loss** | Health_Status | `da049` | ~16,000 | ~10% | 1=Gain, 2=Loss, 3=Same | Coded as present if `da049 == 2` (self-reported weight decrease) |
| **2. Exhaustion** | Health_Status | `dc011`, `dc012` | ~16,000 | ~11% | 1=Rarely (<1 day), 2=Some (1-2 days), 3=Occasional (3-4 days), 4=Most (5-7 days) | Either `dc011 >= 3` OR `dc012 >= 3` = exhaustion present. CES-D items: "I felt everything I did was an effort" / "I could not get going" |
| **3. Low grip strength** | **Biomarker** | `qc003`, `qc004`, `qc005`, `qc006` | ~12,800 | ~2.5% (among measured) | Continuous (kg); ≥900 = missing code | **Max of 4 measurements**. Low grip = lowest 20th percentile, sex-stratified. Available only from Wave 2 onward. |
| **4. Slow gait speed** | **Biomarker** | `qg003` | ~6,380 | **51.6%** (among all) | Seconds for 3m walk | **CRITICAL MISSING RATE.** Gait speed (m/s) = 3.0 / `qg003`. Low gait = lowest 20th percentile, sex-stratified. Only participants able and consenting to walk test have data. |
| **5. Low physical activity** | Health_Status | `da050` | 16,693 | 9.5% | 1=Yes (active), 2=No (inactive) | Coded as low activity if `da050 == 2`. Alternative: `da051_1_`, `da051_2_`, `da051_3_` (detailed activity frequency), but 67% skip-pattern missing. |

**Fried Score Construction**:
```
Fried = sum([weight_loss, exhaustion, low_grip, slow_gait, low_activity])
Robust = 0, Pre-frail = 1-2, Frail = 3-5
```

**Key Issue**: Gait speed (`qg003`) has a **51.6% missing rate**, which is the dominant bottleneck for complete-case Fried phenotype construction. Strategies:
1. **Multiple imputation (MICE)**: Impute gait speed from age, sex, grip strength, BMI, ADL, self-rated health. Recommended primary approach.
2. **Modified Fried (4-component)**: Exclude gait speed from the phenotype. Reduced sensitivity for mobility-related frailty.
3. **SPPB proxy**: Use full SPPB composite (balance + gait + chair stand) if available, which may increase completeness.

### 2.4 Multimorbidity (14 Chronic Disease Indicators)

| Condition | CHARLS File | CHARLS Variable | Code | Notes |
|-----------|-------------|-----------------|------|-------|
| Hypertension | Health_Status | `da007_1` | 1/0 | |
| Diabetes | Health_Status | `da007_2` | 1/0 | |
| Heart disease | Health_Status | `da007_3` | 1/0 | CAD, MI, CHF |
| Stroke | Health_Status | `da007_4` | 1/0 | |
| Chronic lung disease | Health_Status | `da007_5` | 1/0 | COPD |
| Arthritis | Health_Status | `da007_6` | 1/0 | |
| Kidney disease | Health_Status | `da007_7` | 1/0 | |
| Cancer | Health_Status | `da007_8` | 1/0 | Self-reported; **all cancers combined**; no prostate-specific identifier |
| Digestive disease | Health_Status | `da007_9` | 1/0 | |
| Asthma | Health_Status | `da007_10` | 1/0 | |
| Dyslipidemia | Health_Status | `da007_11` | 1/0 | |
| Liver disease | Health_Status | `da007_12` | 1/0 | |
| Memory-related | Health_Status | `da007_13` | 1/0 | Dementia/Alzheimer's (self-report) |
| Other chronic | Health_Status | `da007_14` | 1/0 | |

**Charlson CCI Mapping**:
The 14 CHARLS chronic diseases map well to Charlson Comorbidity Index components:
- MI/CHF: `da007_3` (heart disease, with sub-question differentiation if available)
- Stroke: `da007_4`
- Diabetes: `da007_2` (requires end-organ damage coding; may default to uncomplicated)
- COPD: `da007_5`
- Cancer: `da007_8`
- Kidney disease: `da007_7` (moderate/severe; may overestimate)
- Liver disease: `da007_12` (mild, unless cirrhosis queried)
- Dementia: `da007_13`

**Data Quality**: All `da007_*` variables have 0.0% missing in the extracted dataset (N=8,737 in frailty project). Mean chronic condition count: 1.8 (SD 1.5).

### 2.5 Functional Status (ADL/IADL)

| Variable | CHARLS File | CHARLS Variable(s) | Items | Missing Rate | Notes |
|----------|-------------|---------------------|-------|-------------|-------|
| ADL (Basic) | Health_Status | `da005_*` series | 6 items: dressing, bathing, eating, transferring, toileting, continence | 0.0% | Sum score 0-6. Score >0 indicates disability. |
| IADL | Health_Status | `da006_*` series | 5-8 items: shopping, cooking, managing money, medications, telephone, housework, laundry, transportation | Very low | Sum score. Exact number of items varies slightly by wave. |
| Chair stand (5-rep) | Biomarker | `qh003` | Seconds | 6.5% | Sit-to-stand time. >15 sec = poor lower-extremity strength. |
| Balance tests (3 levels) | Health_Status / Biomarker | `da013s1`, `da013s2`, `da013s3` | Side-by-side, semi-tandem, tandem | Low | Part of SPPB. |
| SPPB composite | Constructible from Biomarker | Balance + gait + chair stand | 0-12 scale | Depends on gait (51.6% missing) | Composite of above three components. |

### 2.6 Cognitive Function

| Variable | CHARLS File | CHARLS Variable(s) | Wave Availability | Missing Rate | Notes |
|----------|-------------|---------------------|-------------------|-------------|-------|
| MMSE (abbreviated) | Health_Status (Waves 1-3,5); Cognition (Wave 4) | Cognitive module items | All waves | ~11% | Modified MMSE, score varies by wave version (0-21 or 0-30). Components: orientation, immediate/delayed word recall, serial subtraction, drawing. |
| Immediate word recall | Health_Status / Cognition | Word recall, 10-word list | All waves | Moderate | Score 0-10. |
| Delayed word recall | Health_Status / Cognition | Word recall after delay (~5 min) | All waves | Moderate | Score 0-10. |
| Cognitive impairment | Derived | MMSE + education-adjusted threshold | All waves | — | **Critical: proxy respondents should NOT be mixed with self-respondents for cognitive scores.** Exclude or flag proxy respondents in cognitive analyses. |

**Note**: In Wave 4 (2018), cognitive assessment is in a separate file (`2018_Cognition.dta`) rather than embedded in Health_Status.

### 2.7 Psychological: CES-D-10

| Variable | CHARLS File | CHARLS Variable(s) | Items | Missing Rate | Notes |
|----------|-------------|---------------------|-------|-------------|-------|
| CES-D Total | Health_Status | `dc009` through `dc018` | 10 items | ~0% (after processing) | Each item 1-4. Total range 10-40. High in published study due to transformation (96.5 mean in Table 1, suggesting sum × scaling factor was used). |
| Depressive symptoms | Derived from CES-D | CES-D ≥ 10 (clinical cutoff) or CES-D ≥ 12 | Binary | 0% | Based on standardized 10-item CES-D. |
| Item: "Bothered by things" | Health_Status | `dc009` | Single | ~0% | |
| Item: "Trouble concentrating" | Health_Status | `dc010` | Single | ~0% | |
| Item: "Felt depressed" | Health_Status | `dc011` | Single | ~0% | Also used for exhaustion (Fried #2). |
| Item: "Everything was an effort" | Health_Status | `dc012` | Single | ~0% | Also used for exhaustion (Fried #2). |
| Item: "Felt hopeful" | Health_Status | `dc013` | Single | ~0% | Reverse-coded. |
| Item: "Felt fearful" | Health_Status | `dc014` | Single | ~0% | |
| Item: "Restless sleep" | Health_Status | `dc015` | Single | ~0% | |
| Item: "Felt happy" | Health_Status | `dc016` | Single | ~0% | Reverse-coded. |
| Item: "Felt lonely" | Health_Status | `dc017` | Single | ~0% | |
| Item: "Could not get going" | Health_Status | `dc018` | Single | ~0% | Also used for exhaustion (Fried #2). |

**Important**: Items `dc011` and `dc012` are shared between CES-D total and the Fried exhaustion component. To avoid double-use as independent predictors, either:
1. Use the remaining 8 CES-D items for the depression score, OR
2. Keep the full 10-item CES-D but note the partial overlap in limitations.

### 2.8 Physical Performance (Biomarker File)

| Variable | CHARLS File | CHARLS Variable | Wave 2 N | Missing Rate | Value Range | Notes |
|----------|-------------|-----------------|----------|-------------|-------------|-------|
| **Grip strength (4 trials)** | Biomarker | `qc003`, `qc004`, `qc005`, `qc006` | ~12,800 | ~2.5% | 0-80 kg (≥900 = missing code) | Maximum of 4 trials. Available Wave 2+. |
| **Gait speed (3m walk)** | Biomarker | `qg003` | ~6,380 | **51.6%** | Seconds for 3 meters | Gait speed (m/s) = 3.0 / `qg003`. Low gait <0.8 m/s. |
| **Height** | Biomarker | `qi002` | 13,021 | 1.1% | cm | |
| **Weight** | Biomarker | `ql002` | 13,009 | 1.2% | kg | |
| **Waist circumference** | Biomarker | `qm002` | ~12,800 | ~0.7% | cm | |
| **BMI** | Derived | `ql002` / (`qi002`/100)^2 | 12,913 | ~1.1% | kg/m^2 | Mean 24.0 (SD 3.8) |
| **Systolic BP** | Biomarker | `qa003` | 12,984 | 1.4% | mmHg | Mean 132.7 (SD 20.8) |
| **Diastolic BP** | Biomarker | `qa004` | 12,984 | 1.4% | mmHg | Mean 77.8 (SD 11.5) |
| **Pulse** | Biomarker | Pulse variable | ~12,800 | 1.3% | bpm | |

### 2.9 Polypharmacy

| Variable | CHARLS File | CHARLS Variable(s) | Availability | Notes |
|----------|-------------|---------------------|-------------|-------|
| Medication count | Health_Care_and_Insurance | Self-reported medication list | All waves | **Polypharmacy = >=5 long-term medications. Accuracy constrained by self-report.** CHARLS collects medication names (Western and Chinese medicines), which should allow counting unique medications. The exact variable name mapping requires codebook inspection.* |

### 2.10 Smoking and Alcohol

| Variable | CHARLS File | Availability | Notes |
|----------|-------------|-------------|-------|
| Smoking status | Health_Status | Available (extracted in frailty project: ~30% current smokers) | Variable name to verify against codebook.* Successfully extracted for frailty-ml-2026 (Table 1). |
| Alcohol consumption | Health_Status | Available (extracted in frailty project: ~33% consumers) | Variable name to verify against codebook.* Successfully extracted for frailty-ml-2026 (Table 1). |

### 2.11 Self-Rated Health

| Variable | CHARLS File | CHARLS Variable | Wave 2 N | Missing Rate | Notes |
|----------|-------------|-----------------|----------|-------------|-------|
| Self-rated health | Health_Status | `da001` or similar | ~9,000 | **50.4%** | 5-point ordinal: 1=Excellent, 5=Poor. High missing rate documented in frailty project (50.1% in N=8,737 cohort). Use with caution or as optional predictor. |

### 2.12 Blood Biomarkers (Subsample Only)

| Biomarker | CHARLS File | Availability | Expected N (subsample) | Notes |
|-----------|-------------|-------------|----------------------|-------|
| C-reactive protein (CRP) | Blood module | Wave 2 (2013)*, Wave 3 (2015) | ~8,000 (full sample); ~2,500 (male 60-75) | Available for blood subsample (~60-70% of participants). Key inflammatory marker. *Verify Wave 2 blood file availability: the file is `2011_Blood_20140429.dta` for Wave 1; Wave 2 blood availability needs confirmation. Wave 3 has `2015_Blood.dta`. |
| Hemoglobin | Blood module | Same as above | ~8,000 | Anemia marker |
| HbA1c | Blood module | Same as above | ~8,000 | Glycemic control |
| Total cholesterol | Blood module | Same as above | ~8,000 | |
| HDL cholesterol | Blood module | Same as above | ~8,000 | |
| LDL cholesterol | Blood module | Same as above | ~8,000 | |
| Triglycerides | Blood module | Same as above | ~8,000 | |
| Creatinine | Blood module | Same as above | ~8,000 | Can calculate eGFR |
| Cystatin C | Blood module | Same as above | ~8,000 | Alternative renal function marker |
| Albumin | Blood module | Same as above | ~8,000 | Nutritional and inflammatory marker; strongly associated with frailty and mortality |

**Blood Data Caveat**: The blood subsample is not a random subset -- it requires participant consent and venous blood collection ability. The subsample may be biased toward healthier participants able to provide blood. Analysis should include comparison of demographics between those with and without blood data.

### 2.13 Sampling Weights

| Variable | CHARLS File | Notes |
|----------|-------------|-------|
| Individual weight | `{wave}_Weights.csv` | `INDV_weight` -- must be applied for population-representative prevalence estimates and descriptive statistics. For ML prediction (within-sample discrimination), weights are generally not applied but should be evaluated in sensitivity analysis. |

---

## 3. Data Quality Assessment (DQ-CARE Framework)

### 3.1 Completeness

| Variable Category | Key Variable | N Total | Missing % | DQ Rating |
|-------------------|-------------|---------|-----------|-----------|
| Sex | `xrgender` | 18,455 | 0.0% | Green -- Perfect |
| ADL sum | `da005_*` | 18,455 | 0.0% | Green -- Perfect |
| Chronic disease count | `da007_*` (14 items) | 18,455 | 0.0% | Green -- Perfect |
| CES-D total | `dc009`-`dc018` | 18,455 | 0.0% | Green -- Perfect |
| Urban/Rural | `zbd001` | ~15,120 | ~18% | Green -- Acceptable |
| Physical inactivity | `da050` | 16,693 | 9.5% | Green -- Acceptable |
| Grip strength (max) | `qc003`-`qc006` | ~12,800 | ~2.5%* | Green -- Good (*low among those who consented to measurement) |
| BMI | Derived from `qi002`/`ql002` | 12,913 | 1.1%* | Green -- Good |
| Weight | `ql002` | 13,009 | 1.2%* | Green -- Good |
| Height | `qi002` | 13,021 | 1.1%* | Green -- Good |
| Waist circumference | `qm002` | ~12,800 | 0.7%* | Green -- Good |
| Systolic BP | `qa003` | 12,984 | 1.4%* | Green -- Good |
| Chair stand | `qh003` | 12,310 | 6.5%* | Green -- Acceptable |
| Education (years) | `zba001` | 15,105 | 18.8% | Yellow -- Warning |
| Age | `da003` (birth year) | ~15,676 | ~15% | Yellow -- Warning |
| Self-rated health | `da001` or equivalent | ~9,000 | 50.4% | Red -- Critical |
| **Gait speed** | `qg003` | ~6,380 | **51.6%** | **Red -- Critical** |

*Missing rate for biomarker variables is the rate among all participants, not just those measured. The missingness is primarily driven by non-consent or inability to complete the physical measurement, not data recording errors. This is informative missingness (not MCAR) and must be handled via multiple imputation, not complete-case analysis.

### 3.2 Accuracy

| Variable | Expected Range | Observed Range | Accuracy Check |
|----------|---------------|----------------|----------------|
| Age | 45-110 | 45-105 (expected) | Derived from birth year; check for implausible values (>110) |
| Grip strength | 0-80 kg (adults) | From frailty project: mean 32.9 (SD 8.2) kg, overall | ≥900 = CHARLS missing code -- must be recoded to NaN before analysis |
| Height | 120-200 cm | Expected ~140-190 cm | Check for <130 or >195 cm |
| Weight | 30-150 kg | Expected ~35-140 kg | Check for <30 or >150 kg |
| BMI | 15-50 kg/m^2 | Mean 24.0 (SD 3.8) | Check for <14 or >55 |
| Systolic BP | 70-250 mmHg | Mean 132.7 (SD 20.8) | Check for <70 or >250 |
| Gait speed (3m time) | 1-60 seconds | — | Values >30 sec suggest inability; >60 sec may be errors |
| CES-D items | 1-4 per item | — | 1=Rarely, 4=Most of time; check for values outside 1-4 |
| ADL items | Binary (0/1) or ordinal | Sum score mean 9.5 (SD 1.8) in frailty project | Note: frailty project used ADL scoring different from standard 0-6; verify coding scheme* |

**Known Accuracy Issues**:
1. **Grip strength missing codes**: Values ≥900 in grip variables are CHARLS missing codes (refusal, unable, etc.), not actual kg measurements. Must be filtered before analysis.
2. **Self-reported chronic diseases**: No verification against medical records. Recall bias possible, especially for conditions like dyslipidemia (which requires lab testing for diagnosis).
3. **Age derivation**: Age should be computed as `2013 - da003` (birth year). Check consistency with self-reported age (`xrage`) if available.

### 3.3 Reliability (Repeated Measures)

| Measure | Repeated? | Reliability Evidence |
|---------|-----------|---------------------|
| Grip strength (4 trials) | Yes, 4 consecutive measurements | Use maximum or mean. From frailty project: mean grip SD across trials = usable feature. Correlation between max and mean grip: very high. |
| Blood pressure (3 measurements) | Yes, typically 3 measurements | Use mean of available measurements. |
| Fried phenotype (2 waves) | Yes, 2013 and 2015 | 32.2% frailty worsening rate over 2 years (frailty project). Shows responsiveness to change. |
| CES-D (2 waves) | Yes, repeated at each wave | Test-retest reliability over 2 years expected moderate (depressive symptoms fluctuate). |

### 3.4 Explicability (Metadata Completeness)

| Metadata Item | Status | Notes |
|---------------|--------|-------|
| Codebook (PDF) | Available for all 5 waves | Located in `CHARLS_codebook/` directory |
| Variable naming convention | Consistent across waves | CHARLS uses `da`, `dc`, `qc` etc. prefixes consistently |
| Missing value coding | Documented | Codes ≥900 typically represent missing/refused/unable. CSV conversion may produce empty cells. |
| Skip patterns | Partially documented | Activity `da051_*` has ~67% skip-pattern missing; gait speed and other biomarker variables have conditional missing |
| Sampling weights | Available per wave | `INDV_weight` variable |
| Proxy respondent flag | Available | Must be applied to filter cognitive assessments |

---

## 4. Sample Size Feasibility

### 4.1 Enrollment Cascade (Estimated)

```
CHARLS Wave 2 (2013) total participants:             18,455
  ├── Male participants (~48%):                      ~8,600
  │   └── Male, age 60-75:                          ~4,000
  │       ├── With demographic data (age, sex):      ~3,400  (15% missing age)
  │       ├── With complete CES-D:                   ~4,000  (0% missing)
  │       ├── With complete chronic disease data:    ~4,000  (0% missing)
  │       ├── With complete ADL data:                ~4,000  (0% missing)
  │       ├── With complete grip strength:           ~2,800  (70% consent/able)
  │       ├── With complete gait speed:              ~1,960  (49% consent/able)
  │       ├── With complete Fried phenotype (all 5): ~1,960  (gait is bottleneck)
  │       ├── With complete cognitive assessment:    ~3,560  (~11% missing)
  │       ├── With self-reported medications:         TBD    (need codebook verification)
  |       └── With blood biomarkers:                 ~1,200-1,400 (60-70% of Fried-complete)
```

### 4.2 Estimated Final N Under Different Strategies

| Strategy | Description | Estimated N | Pros | Cons |
|----------|-------------|-------------|------|------|
| **Complete-case** | No missing data on any predictor | ~800-1,000 | No imputation assumptions | Severe selection bias (healthier, mobile men); underpowered |
| **MICE (primary)** | Multiple imputation for all predictors | ~3,500-4,000 | Preserves sample size; valid under MAR | Requires careful imputation model; gait speed MAR assumption arguable |
| **Excluding gait speed** | Drop gait speed from predictor set; use Modified Fried (4-component) | ~2,800-3,200 | Avoids the worst missingness variable | Loses important predictor; Fried definition altered |
| **MICE + blood sensitivity** | MICE-imputed main analysis + complete-case blood biomarker sensitivity | Main: ~3,500; Blood: ~1,200 | Comprehensive approach | More complex analysis pipeline |

### 4.3 Power Considerations for Binary Outcome

For 10-year mortality prediction:
- Expected 10-year mortality in Chinese men aged 60-75: approximately 25-35% (based on Chinese life tables and CHARLS data)
- If using 7-year mortality as proxy: approximately 15-25%
- Binary outcome: events/total

| Sample Size | Expected Events (7 yr, 20% rate) | Expected Events (10 yr, 30% rate) | Adequate for ML? |
|-------------|----------------------------------|-----------------------------------|-----------------|
| N=800 (CCA) | 160 | 240 | No -- severely underpowered |
| N=1,960 (gait complete) | 392 | 588 | Marginal for XGBoost with 20-30 features |
| N=2,800 (no-gait) | 560 | 840 | Adequate |
| N=3,500 (MICE) | 700 | 1,050 | Adequate |

**Power Benchmark**: A common rule of thumb for binary ML prediction is >=10-20 events per candidate predictor. With ~20-30 predictors and ~700-1,050 events, the events-per-variable (EPV) is ~23-53, which is adequate for tree-based models but on the lower end for logistic regression with many features. LASSO regularization mitigates EPV concerns.

---

## 5. Mortality Follow-Up Verification

### 5.1 Mortality Tracking Mechanism

CHARLS tracks participant deaths through:
1. **Exit interviews**: When a participant dies, CHARLS field staff conduct an exit interview with a family member, neighbor, or village doctor. These interviews collect date of death, cause of death (proxy-reported), and circumstances.
2. **Vital status tracking**: At each follow-up wave, interviewers attempt to locate all participants. If a participant has died, an exit interview is conducted.
3. **Proxy informants**: For participants who cannot respond (including deceased), information is collected from knowledgeable proxies.

### 5.2 Available Mortality Follow-up from Wave 2 (2013) Baseline

| Data Source | Follow-up Years from 2013 | Deaths Recorded | Notes |
|-------------|--------------------------|-----------------|-------|
| Wave 3 (2015) -- Health Status + Exit | 2 years | Included in frailty project: 275 deaths among 11,845 (60+, non-frail) | 2-year mortality ~2.3% in non-frail cohort |
| Wave 4 (2018) -- Health Status + Exit | 5 years | Available | Cumulative mortality tracking |
| Wave 5 (2020) -- Health Status + Exit Module | 7 years | Available in `2020_Exit_Module.dta` | Most complete exit data available |
| **Total confirmed follow-up** | **7 years** (2013-2020) | **Cumulative across Waves 3-5** | |

### 5.3 Expected 10-Year Mortality Rate

For Chinese men aged 60-75 (community-dwelling, from CHARLS data and Chinese life tables):
- 2-year mortality: ~2-4%
- 5-year mortality: ~10-15%
- 7-year mortality: ~15-25%
- 10-year mortality: ~25-35%

These estimates are for community-dwelling men, which may be healthier than the general population (healthy volunteer/survivor bias). The exact rate should be verified against:
- CHARLS internal mortality rates (calculate from exit interviews)
- WHO China life tables for males
- Published CHARLS mortality analyses

### 5.4 Follow-up Limitations

1. **Maximum follow-up is 7 years (to 2020), not 10 years (to 2023)**: Wave 6 (expected ~2022-2023) data is not confirmed in the local file inventory. The project plan noted "total follow-up: Wave 2 through Wave 5 (2013-2020)".
2. **Mitigation**: The primary analysis can use **7-year mortality** as the outcome, with "life expectancy <10 years" implied by high 7-year mortality risk. A threshold-based approach: predicted 7-year mortality risk > X% maps to predicted 10-year mortality > Y%, where X and Y are calibrated against available mortality data.
3. **When Wave 6 becomes available**: The model can be directly updated to a true 10-year horizon.

---

## 6. Gap Analysis

### 6.1 Variables Completely Unavailable in CHARLS

| Missing Variable | Importance | Impact | Possible Mitigation |
|-----------------|------------|--------|---------------------|
| PSA (prostate-specific antigen) | Critical for prostate cancer screening | Cannot model screening benefit or cancer risk | Shift to life expectancy prediction (Q1 strategy); PSA is not needed for screening cessation guidance |
| Prostate cancer staging (Gleason, TNM) | Critical for cancer-specific models | Cannot model prostate cancer prognosis | N/A for life expectancy prediction |
| Cancer treatment data (surgery, radiation, ADT) | Critical for treatment outcome models | Cannot model treatment complications | N/A for life expectancy prediction |
| Family history of prostate cancer | Important predictor for screening eligibility | Missing key screening risk factor | Acknowledge as limitation; not essential for life expectancy prediction |
| Urinary symptoms (IPSS, AUA score) | Important clinical context | Cannot assess clinical presentation | Acknowledge as limitation |
| Detailed medication names (for Beers Criteria) | Moderate for geriatric assessment | Cannot apply STOPP/Beers criteria | Use medication count (polypharmacy >=5) as proxy |
| DEXA / muscle mass | Moderate for sarcopenia assessment | Cannot apply full AWGS 2019 sarcopenia criteria | BMI-adjusted grip strength as proxy for muscle mass |
| Physical activity (detailed) | Moderate: `da051_*` has 67% missing | Cannot calculate MET-min/week | Use binary activity variable `da050` (9.5% missing) instead |

### 6.2 Variables with High Missing Rates (>30%)

| Variable | Missing Rate | DQ Rating | Impact | Mitigation |
|----------|-------------|-----------|--------|------------|
| **Gait speed** (`qg003`) | **51.6%** | Critical | Affects Fried phenotype completeness; key mobility predictor | Primary: MICE imputation. Secondary: Modified Fried (4-component). Sensitivity: SPPB without gait if available. |
| **Self-rated health** | **50.4%** | Critical | Important subjective health measure | MICE imputation; acknowledge limitation. Consider as optional rather than required predictor. |
| **Education** (`zba001`) | **18.8%** | Warning | Important SES predictor | MICE imputation (MAR assumption reasonable for education). |
| **Age** | **~15%** | Warning | Most important single predictor | MICE imputation. Cross-validate with other age indicators. Some missing may be from proxy respondents where birth year unknown. |

### 6.3 Workarounds and Proxy Variables

| Original Variable | Problem | Proxy / Workaround | Validity |
|-------------------|---------|-------------------|----------|
| Full Fried phenotype (5 components) | Gait speed 51.6% missing | Modified Fried (4 components, excluding gait) | Common in literature when gait unavailable; reduced sensitivity for mobility-frailty |
| Gait speed (continuous) | 51.6% missing | Chair stand time (`qh003`, 6.5% missing) as mobility proxy | Moderate correlation with gait; captures different domain (power vs speed) |
| SPPB composite | Depends on gait (51.6% missing) | Balance tests + chair stand as reduced SPPB | Valid alternative; balance tests have lower missingness |
| Detailed physical activity (MET-min) | `da051_*` 67% missing | Binary activity (`da050`, 9.5% missing) | Coarse but operational for Fried component #5 |
| Continuous medication count | Exact variable unverified | Binary polypharmacy (>=5 meds) from self-report | Standard in geriatric literature; acknowledged accuracy limitations |
| Cancer-specific mortality | Cancer type not disaggregated | All-cause mortality (primary outcome) OR "any cause other than accident/injury" | All-cause mortality is the most reliable outcome in CHARLS |
| Smoking pack-years | Need duration + intensity variables | Current/ever/never smoking (binarized) | Available from frailty project extraction |
| G8 screening tool | Requires specific survey items | Individual components: age, weight loss, mobility, BMI, polypharmacy, self-rated health (most available in CHARLS) | Reasonable proxy; G8 validation in CHARLS would need to be explored |

### 6.4 Polypharmacy Measurement Feasibility

**Assessment: Feasible but with accuracy limitations.**

CHARLS collects self-reported medication use in the Health Care and Insurance module. Participants are asked to show their medications to interviewers, improving accuracy over pure recall. However:
1. The question asks about Western medications and Chinese traditional medicines.
2. Short-term medications (antibiotics, acute treatments) may be conflated with long-term medications.
3. Variable names for medication count/specific medications need verification against the codebook or raw data headers.
4. The standard geriatric polypharmacy definition (>=5 long-term medications) is constructible if individual medications are listed.

**Recommendation**: 
1. Verify medication variable names by inspecting `2013_Health_Care_and_Insurance.dta` (or its CSV equivalent in `analysis/`).
2. If individual medication names are collected, count unique long-term medications (excluding PRN and short-course treatments if identifiable).
3. If only total medication count is available, use the raw count with a sensitivity threshold of >=5 vs >=8.
4. Acknowledge self-report limitations in the manuscript.

---

## 7. Recommended Data Processing Pipeline

### 7.1 Inclusion/Exclusion Criteria

**Inclusion**:
1. CHARLS Wave 2 (2013) participant
2. Male sex (`xrgender` or `da002` == 1)
3. Age 60-75 at Wave 2 (computed from `da003`)

**Exclusion**:
1. Death in 2013 (same year as baseline -- cannot predict from baseline data)
2. Severe cognitive impairment at baseline (MMSE <18 or proxy respondent -- clinical-computability criterion)
3. Terminal illness at baseline (if identifiable from self-report)
4. ADL dependency >=4 items (end-stage functional impairment)
5. Baseline prostate cancer diagnosis (if identifiable from `da007_8` + cancer type follow-up; note: this exclusion may not be enforceable if cancer type is not recorded)

### 7.2 Missing Data Strategy

```
1. Recode CHARLS missing codes (>=900) → NaN
2. Filter: male, age 60-75, alive at baseline
3. Assess missing data patterns (Little's MCAR test; visualize)
4. Primary: MICE (m=20, predictive mean matching for continuous; logistic for binary)
5. Sensitivity: Complete-case analysis (acknowledge bias)
6. Sensitivity: Exclude gait speed (use Modified Fried 4-component)
```

### 7.3 Key Processing Decisions

| Decision | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Baseline wave | Wave 2 (2013) | Only wave with grip strength + gait speed |
| Primary outcome | 7-year all-cause mortality (to 2020) | Maximum confirmed follow-up available |
| Fried operationalization | Sex-stratified lowest 20th percentile for grip and gait | Consistent with Fried 2001 and frailty-ml-2026 project |
| CES-D / exhaustion overlap | Retain full 10-item CES-D as depression score; flag overlap in limitations | 8-item or 10-item score difference is modest |
| Sampling weights | Use for Table 1 (population estimates); not for within-sample ML prediction | Standard in ML prediction studies |
| Cognitive data | Exclude proxy respondents from cognitive analyses | Self-report cognitive data not valid from proxies |
| Blood biomarkers | Secondary analysis only (subsample) | ~30-40% missing; imputation across the missingness barrier is questionable |

### 7.4 Data Delivery Checklist

- [ ] Verify smoking/alcohol variable names against codebook or CSV headers
- [ ] Verify polypharmacy/medication variable names against `Health_Care_and_Insurance` file
- [ ] Verify `da007_*` coding scheme (cancer-specific sub-questions) against codebook
- [ ] Confirm blood biomarker file availability for Wave 2 (2013)
- [ ] Extract and verify mortality data from exit interviews (Waves 3, 4, 5)
- [ ] Cross-validate variable names between codebook PDF and analysis CSV headers
- [ ] Build unified Wave 2 baseline dataset with all predictor domains
- [ ] Calculate exact sample size cascade with real numerators
- [ ] Run MICE imputation and produce diagnostic plots
- [ ] Deliver DQ report with final dataset

---

## 8. Summary Assessment

### 8.1 Feasibility Verdict

**Overall: FEASIBLE with defined limitations.**

The proposed research question (ML-based 10-year life expectancy prediction in older Chinese men) is **well-matched to CHARLS's strengths**. CHARLS provides the comprehensive geriatric assessment variables (frailty, function, cognition, depression, multimorbidity, physical performance) that are the core differentiator of this model, and that are precisely what existing life expectancy calculators (Schonberg, Lee) lack.

### 8.2 Critical Constraints

| Constraint | Severity | Mitigation Status |
|------------|----------|-------------------|
| Maximum follow-up is 7 years, not 10 | Moderate | Use 7-year mortality as primary; calibrate to 10-year equivalent; update when Wave 6 available |
| Gait speed 51.6% missing | High | MICE imputation (primary); Modified Fried (sensitivity) |
| Self-rated health 50.4% missing | Moderate | MICE; optional predictor |
| No PSA data | None for Q1 | Research question intentionally avoids PSA requirement |
| Blood biomarkers only in subsample | Minor | Secondary analysis in complete-case biomarker subset |

### 8.3 Recommended Next Steps for Data Engineer

1. **Immediate**: Verify the four unconfirmed variable mappings (smoking, alcohol, polypharmacy, marital status) by inspecting CSV headers in `analysis/` directory.
2. **This week**: Build the unified Wave 2 baseline dataset merging: Demographic_Background + Health_Status_and_Functioning + Biomarker + Health_Care_and_Insurance + Weights.
3. **This week**: Extract and code the mortality outcome from exit interviews (Waves 3-5).
4. **Next week**: Run MICE imputation. Produce missing data heatmap. Deliver analysis-ready dataset.

---

*This report is based on project documentation verified against prior team analyses (frailty-ml-2026, ses-bioaging-2026). Variable names marked with an asterisk (*) require direct verification against raw data headers or codebook PDFs before dataset construction. Direct access to `/Users/wuyouhang/Documents/trae_projects/related to Sarcopenia/charls/` was unavailable during report preparation due to filesystem permissions.*

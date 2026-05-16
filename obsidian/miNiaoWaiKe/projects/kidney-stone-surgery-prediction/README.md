# Machine Learning Prediction of Urological Intervention in Emergency Renal Colic: A MIMIC Study with External Validation

## Paper Info

| Item | Value |
|------|-------|
| **Working Title** | Machine Learning Prediction of Urological Intervention in Emergency Renal Colic: A MIMIC Study with External Validation |
| **Paper Type** | Original Article (IMRAD) |
| **Target Journal** | BMC Urology |
| **Language** | English |
| **Research Question** | Can a machine learning model using only routinely available clinical data (without CT-derived stone measurements) predict urological surgical intervention within 90 days of ED presentation for kidney stones? |
| **Reporting Guideline** | TRIPOD (Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis) |
| **Created** | 2026-05-09 |
| **Last Updated** | 2026-05-10 (rewritten) |

## Journal Requirements (BMC Urology)

| Item | Value |
|------|-------|
| Abstract Format | Structured (Background/Methods/Results/Conclusions) |
| Abstract Word Limit | 350 words |
| Citation Style | Vancouver (numbered) |
| Figure/Table Limit | No strict limit |
| Required Sections | Background → Methods → Results → Discussion → Conclusions → Declarations |
| Graphical Abstract | Not required |
| Keywords | 3-10 |
| AI Disclosure Required | Yes, in Declarations |
| Line Spacing | Double |
| Line Numbering | Required |

## Project Status

| Phase | Status | Last Updated | Notes |
|-------|--------|-------------|-------|
| Ethics & Protocol | Done | 2026-05-09 | MIMIC approved by MIT IRB, de-identified data |
| Data Organization | Done | 2026-05-09 | `data/model_ready_enhanced.parquet` |
| Literature Search | In Progress | - | 27 refs in `references/references.bib` |
| Outline | Done | 2026-05-09 | (deleted; reorganized into sections) |
| Tables & Figures | Draft Complete | 2026-05-09 | `tables/`, `figures/` |
| Methods & Results | Done | 2026-05-10 | `sections/02_methods.md`, `sections/03_results.md` |
| Introduction & Conclusion | Done | 2026-05-10 | `sections/04_introduction.md`, `sections/06_conclusion.md` |
| Discussion | Done | 2026-05-10 | `sections/05_discussion.md` |
| Abstract & Title | Done | 2026-05-10 | `sections/07_abstract.md`, `sections/08_title.md` |
| Compile Manuscript | Done | 2026-05-10 | `submissions/v1_bmc-urology/compiled-manuscript.md` |
| Cover Letter | Done | 2026-05-10 | `submissions/v1_bmc-urology/cover-letter.md` |
| References | Done | 2026-05-10 | 28 refs, Vancouver format |
| Quality Review | Done | 2026-05-10 | `checklists/section-quality.md` (29.5/30) |
| Pre-Submission | In Progress | 2026-05-10 | `submissions/v1_bmc-urology/` |

## Key Data Summary

| Metric | Value |
|------|-------|
| Development cohort | MIMIC-IV, N = 1,979, 118 events (6.0%) |
| External validation | MIMIC-III, N = 245, 46.5% events |
| Best model | Random Forest + SMOTE, AUROC 0.755 |
| External AUROC | 0.829 |
| Top predictors | Ureteral stone, hydronephrosis, urology admission, opioid, WBC |
| Features | 114 structured EHR features, no CT imaging |

## Authors

| # | Name | Affiliation | ORCID | CRediT Roles | Approval |
|---|------|-------------|-------|-------------|----------|
| 1 | [Corresponding Author] | | | | |
| 2 | | | | | |

## Submission History

| # | Journal | Date Submitted | Manuscript # | Decision | Date Decision |
|---|---------|---------------|-------------|----------|--------------|
| 1 | BMC Urology | | | | |

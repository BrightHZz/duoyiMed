# Cover Letter

**To**: Editor-in-Chief, Prostate Cancer and Prostatic Diseases

**Date**: [TBD]

**Re**: Submission of Original Article — "Prediction of 30-Day Mortality or ICU Admission in Hospitalized Patients with Prostate Cancer: A Machine Learning Approach Using Electronic Health Records"

---

Dear Editor,

We wish to submit an original research article entitled "Prediction of 30-Day Mortality or ICU Admission in Hospitalized Patients with Prostate Cancer: A Machine Learning Approach Using Electronic Health Records" for consideration for publication in Prostate Cancer and Prostatic Diseases.

**Importance and Fit**: While machine learning (ML) models for prostate cancer prognosis have proliferated—47 studies reviewed by Ahuja et al. (2024)—they almost exclusively use SEER registry data to predict long-term (5–10 year) cancer-specific survival. No prior study has applied ML to electronic health record (EHR) data for short-term acute outcome prediction in hospitalized prostate cancer patients. This represents a clinically important gap: when a prostate cancer patient is hospitalized, clinicians need tools to assess immediate risk of deterioration, and existing prognostic models (D'Amico, CAPRA, AJCC staging) were not designed for this setting. Our study addresses this gap using the publicly available MIMIC-IV database, demonstrating that an XGBoost model using routinely collected laboratory and demographic data—without requiring histopathological features—can predict 30-day mortality or ICU admission with good discrimination (AUC 0.8448). We believe this manuscript aligns with the journal's scope of advancing clinical management of prostate cancer patients through data-driven approaches.

**Key Findings**:
- An XGBoost model using 13 routinely available EHR features achieved AUC 0.8448 (95% CI: 0.8168–0.8728) for predicting 30-day mortality or ICU admission in 2,437 hospitalized prostate cancer patients.
- Acute physiological markers (lactate, albumin, hemoglobin) dominated prediction (53.0% of feature importance), while cancer-specific features (PSA, bone metastasis) accounted for only 12.7%.
- Model performance was strongest in elective surgical admissions (AUC 0.8855), suggesting potential clinical utility for preoperative risk stratification.
- A PSA-free model matched or exceeded the PSA-inclusive model, enabling application to all patients regardless of PSA testing at admission.

**Originality**: This work has not been published previously and is not under consideration elsewhere. All authors have approved the manuscript and agree with its submission to Prostate Cancer and Prostatic Diseases.

**Compliance**: The study was reported in accordance with the TRIPOD+AI statement (Collins et al., BMJ 2024). The MIMIC-IV database is publicly available via PhysioNet, with use approved by the Beth Israel Deaconess Medical Center IRB (protocol 2001-P-001699/14).

We appreciate your consideration and look forward to your response.

Sincerely,

[Corresponding Author Name]
[Affiliation]
[Email]
[Phone]
[ORCID]

---

**Suggested Reviewers** (optional):
1. [Name], [Affiliation], [Email] — expertise in clinical prediction modeling
2. [Name], [Affiliation], [Email] — expertise in urologic oncology / prostate cancer
3. [Name], [Affiliation], [Email] — expertise in EHR-based machine learning

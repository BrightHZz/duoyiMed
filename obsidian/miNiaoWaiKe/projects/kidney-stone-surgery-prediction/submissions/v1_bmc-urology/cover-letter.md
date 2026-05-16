# Cover Letter

[Date]

Dear Editor,

We are pleased to submit our manuscript entitled **"Machine Learning Prediction of Urological Intervention in Emergency Renal Colic: A MIMIC Study with External Validation"** for consideration for publication in BMC Urology.

## Study Summary

In this retrospective cohort study, we developed and externally validated a machine learning model—specifically, a Random Forest classifier—that predicts the need for urological surgical intervention within 90 days of emergency department presentation for kidney stones. The model uses only routinely available structured clinical data from the electronic health record (demographics, laboratory values, diagnoses, and medications) without any dependence on CT-derived stone measurements, which are not always available at the time of initial emergency department triage.

**Key findings:**
- Development cohort: 1,979 adult ED kidney stone patients from MIMIC-IV, 118 events (6.0%)
- Random Forest AUROC: 0.755 (95% CI 0.711–0.799); high negative predictive value (0.981)
- External/temporal validation in MIMIC-III (N = 245): AUROC 0.829 (95% CI 0.777–0.881)
- Top predictors (via SHAP analysis): hydronephrosis, ureteral stone location, urology service admission, opioid prescription, and WBC count

## Significance and Fit for BMC Urology

BMC Urology has published numerous studies on the application of machine learning to urological conditions. Our manuscript addresses a clinically important question—identifying which emergency department kidney stone patients need surgical intervention—using a practical approach that circumvents the imaging dependency of existing models. The study adheres to the TRIPOD reporting guideline, includes a rigorous external temporal validation (MIMIC-III, a different era from the development cohort), and provides feature-level interpretability through SHAP analysis. We believe these qualities align well with BMC Urology's emphasis on methodologically sound, clinically relevant research.

## Novelty

To our knowledge, this is the first study to develop a surgical intervention prediction model for emergency renal colic that:
1. Uses only structured EHR data without CT-derived stone measurements, making it deployable at the point of initial ED evaluation
2. Provides external temporal validation in an independent database from a different era
3. Incorporates four pre-specified clinical interaction terms informed by domain knowledge
4. Demonstrates that missingness patterns in laboratory ordering encode clinically meaningful information about illness severity

## Compliance

- Reporting guideline: TRIPOD (adhered to)
- Ethics: MIMIC database approved by MIT IRB; de-identified data
- Data availability: MIMIC-IV and MIMIC-III are available via PhysioNet with a data use agreement
- Code availability: Available from the corresponding author upon reasonable request
- AI-assisted writing: Disclosed in Declarations

## Declarations

- This manuscript has not been published elsewhere and is not under consideration by another journal
- All authors have approved the manuscript and agree with its submission to BMC Urology
- The authors declare no competing interests

We appreciate your time and consideration and look forward to your response.

Sincerely,

[Corresponding Author Name]
[Title, Department]
[Institution]
[Email]
[ORCID]

On behalf of all authors.

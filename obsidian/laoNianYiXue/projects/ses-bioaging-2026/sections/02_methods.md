# Methods

## Study Design and Population

We conducted a cross-sectional analysis using baseline data from the China Health and Retirement Longitudinal Study (CHARLS) 2013 wave. CHARLS is a nationally representative survey of Chinese adults aged 45 years and older, employing multistage stratified probability-proportional-to-size sampling [1]. We included all participants aged 60 years or older with available data on core socioeconomic indicators and demographic variables. CHARLS missing value codes (≥900) were replaced with NaN. Missing biomarker values were imputed using median imputation. The final analytical sample comprised 7,810 participants.

## Socioeconomic Status (SES) — Exposure

We constructed a composite SES index from five dimensions: education years, urban/rural residence, per-capita household income, per-capita household expenditure, and household assets. Education (`zba001`) and urban/rural status (`zbd001`) were extracted from the Demographic Background file. Per-capita income was calculated as the sum of 13 individual income sources (`ge010_1` through `ge010_13` in the Household Income file) divided by household size. Per-capita expenditure used total household expenditure (`ha072`). Household assets used the non-financial asset variable (`ha067`). All monetary variables were log(1+x) transformed to normalize right-skewed distributions while accommodating zero values. The five standardized components were averaged into a continuous SES score, then dichotomized at the median into low-SES and high-SES groups.

## Biological Aging — Outcome

We constructed a composite biological age score from four markers: maximum grip strength (kg, `qc003`–`qc006`), gait speed (m/s, 3-meter walk `qg003`), body mass index (kg/m²), and systolic blood pressure (mmHg, `qa003`). Grip strength and gait speed were reverse-coded so that higher values indicate worse biological status for all markers. Each marker was Z-score standardized and averaged. Higher composite scores indicate more advanced biological aging. CES-D was excluded from the composite to avoid circularity with the mediation analysis, where CES-D serves as the mediator.

## Covariates

Analyses were adjusted for age (continuous, years) and sex (male/female). In subgroup analyses, we stratified by grip strength (median split), CES-D score (median split), urban/rural residence, education level, and age group (60–69, ≥70).

## Statistical Analysis

The analysis comprised three components:

**Conditional Average Treatment Effect (CATE).** We estimated the effect of low SES on biological age across prespecified subgroups using stratified mean differences. The overall average treatment effect (ATE) was calculated as the mean difference in biological age score between low-SES and high-SES groups. Within each subgroup, CATE was calculated as the difference in biological age between low-SES and high-SES participants.

**Mediation Analysis.** We quantified the indirect effect of SES on biological age through psychological distress (CES-D score) using the product-of-coefficients method. Path a estimated the association between SES score and CES-D, adjusting for age and sex. Path b estimated the association between CES-D and biological age score, adjusting for SES, age, and sex. The indirect effect was calculated as a × b. The proportion mediated was calculated as (indirect effect / total effect) × 100%.

**E-value.** We calculated the E-value to assess the robustness of the observed SES-biological aging association to unmeasured confounding. The E-value represents the minimum strength of association that an unmeasured confounder would need to have with both the exposure and the outcome to fully explain away the observed association, conditional on measured covariates.

**SES × Physical Function Interaction.** We cross-classified participants by SES (high/low) and grip strength (high/low, median split) to examine the combined association with biological age. Mean biological age scores were compared across the four groups using ANOVA.

All analyses were performed using Python 3.12 with scikit-learn (v1.3), pandas (v2.0), and NumPy (v1.24). CHARLS data were converted from Stata (.dta) to CSV format for analysis. Missing values were imputed using median imputation; values coded as ≥900 (CHARLS missing value indicator) were replaced with NaN before imputation.

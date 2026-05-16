# Introduction

## Paragraph 1 — Background

Frailty is a geriatric syndrome characterized by diminished physiological reserve and increased vulnerability to stressors [1]. An estimated 10–15% of community-dwelling older adults are frail, and an additional 40–50% are pre-frail [2]. Frailty independently predicts falls, hospitalization, disability, and mortality [3]. Critically, frailty is dynamic: longitudinal studies demonstrate that individuals transition between robust, pre-frail, and frail states over periods as short as two years [4]. Identifying older adults at imminent risk of worsening is essential for targeting preventive interventions—yet existing prediction tools for short-term frailty transitions remain limited.

## Paragraph 2 — Knowledge Gap

Several studies have applied machine learning to frailty prediction, but important gaps remain. Zhang et al. (2025) reported an XGBoost model achieving AUC = 0.84 for predicting 2-year frailty worsening in CHARLS, but used the 2011 baseline wave which lacked grip strength measurements—a core component of the Fried phenotype [5]. Most prior models have used fewer than 30 predictors and relied on single-wave internal validation without temporal or external validation [6,7]. Furthermore, few studies have systematically compared linear models against nonlinear machine learning approaches for frailty prediction, leaving open the question of whether model complexity provides meaningful benefit over simpler, more interpretable alternatives [8].

## Paragraph 3 — Study Objective

We aimed to develop and validate a prediction model for 2-year frailty worsening in community-dwelling Chinese older adults, using the CHARLS 2013 baseline—the first wave containing the complete Fried phenotype including grip strength. We compared LASSO logistic regression against gradient-boosted trees (XGBoost) with rigorous hyperparameter optimization, and assessed whether nonlinear modeling provided additional discriminative performance beyond a well-regularized linear model. We further aimed to identify the dominant predictors of frailty worsening using SHAP-based feature importance and to evaluate model stability across sex and age subgroups.

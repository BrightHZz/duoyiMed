# PI 裁决书

**Phase**: Phase 2 — 方案设计研讨厅辩论
**日期**: 2026-05-10
**裁决人**: urology/pi

---

## 裁决结果

### 决策项 1: LR baseline → ✅ **选项 A: 加入 LR**

**裁决理由**: Biostatistician 的审稿合规论证充分。加入 LR 的成本极低，但缺失它的审稿风险很高。TRIPOD 指南明确要求报告标准统计方法作为参照。即使 LR 性能明显低于 XGBoost (预期 ΔAUC > 0.03)，这个对比本身也是有信息量的发现。

**裁决**: 必须包含 LR baseline。LR 性能作为 Table 2 的一行。

---

### 决策项 2: 特征筛选策略 → ✅ **选项 A: 三层策略**

**裁决理由**: 这个方案兼顾了 Clinical Researcher 对临床知识的保护需求 (PSA/骨转移/年龄不可被算法移除) 和 Biostatistician 对统计过拟合的担忧 (EPV 边界)。Computational Biologist 的"SHAP 事后筛选"思路在 Tier 3 仍然保留 (XGBoost 最终训练)。

**裁决**:
- **Tier 1 (Clinical Mandatory)**: age, PSA (log), bone_metastasis, admission_type, CCI — 不受 LASSO 影响，强制保留
- **Tier 2 (LASSO Candidate)**: Hb, WBC, PLT, Cr, Alb, Lactate, race, insurance, marital_status, prostatectomy_this_admission, 其他合并症 — 经过 LASSO λ.1se 筛选，保留 ≥ 3/5 folds 稳定非零的特征
- **Tier 3 (Final Model)**: T1 + T2 筛选后 → XGBoost
- **Sensitivity**: 同时训练"全特征 XGBoost"作为 sensitivity analysis，对比两者性能

---

### 决策项 3: 结局策略 → ✅ **选项 A: 复合 + 成分分析**

**裁决理由**: Biostatistician 的折中方案同时满足统计 power (复合结局 ~17% event rate) 和 Clinical Researcher 对临床可解释性的核心关切。CONSORT 2010 对复合结局的报告指南明确推荐: "report each component separately alongside the composite"。采纳 Clin 的追加要求: 如果两个成分的 SHAP top-5 特征差异明显，在 Discussion 中作为一个发现讨论。

**裁决**:
- Primary endpoint: 30-day mortality OR ICU admission (composite binary)
- Secondary analyses: (a) ICU admission only, (b) 30-day mortality only
- Exploratory: SHAP 成分差异对比
- 注意: 30天死亡 only 的 analysis sample size 小 (128 events)，结果应标注为 exploratory，不做过度解读

---

### 决策项 4: 报告指标 → ✅ **选项 A: 完整 TRIPOD 指标集**

**裁决理由**: J Urology 审稿标准高。完整指标集与 TRIPOD 指南对齐，降低审稿风险。DCA 曲线对临床决策支持工具至关重要 — 这是本论文区别于纯统计建模论文的核心卖点。

**裁决**: 

| 指标 | 级别 |
|------|------|
| AUC (with 95% CI) | 必须 |
| PR-AUC | 必须 |
| Brier Score | 必须 |
| Calibration Slope + Intercept | 必须 |
| Calibration Plot | 必须 (Figure) |
| DCA (Decision Curve) | 必须 (Figure) |
| Sensitivity/Specificity at optimal threshold | 必须 |
| Subgroup AUC (age, metastasis, admission_type) | 必须 (Table) |
| NRI vs LR baseline | 推荐 |
| SHAP Summary Plot | 必须 (Figure) |

---

### 决策项 5: MIMIC-III 外部验证 → ✅ **选项 A: 事先探查**

**裁决理由**: Phase 4 投入的时间和计算资源不可忽视。在 Phase 3 完成后、进入 Phase 4 前，需要 data-engineer 快速探查 MIMIC-III 前列腺癌队列的规模。探查标准:
- MIMIC-III 前列腺癌患者 ≥ 300 → 进入 Phase 4 完整外部验证
- MIMIC-III 前列腺癌患者 < 300 → Phase 4 缩减为"简短 external validation 分析" (仅报告 AUC/校准/demographics 对比)
- MIMIC-III 前列腺癌患者 < 100 → 跳过 Phase 4，Discussion 中详细讨论外部验证的缺失

---

## 最终批准的方案设计

### 研究设计

```
Design: Retrospective cohort study (MIMIC-IV v3.1, 2008-2022)
Cohort: Prostate cancer patients with index hospitalization (n ≈ 2,000-2,500)
Outcome (Primary): 30-day mortality OR ICU admission (composite binary)
Outcome (Secondary): ICU admission only; 30-day mortality only
Predictors: Clinical Mandatory (5) + LASSO-selected candidates → ~12-18 features total
```

### 建模方案

```
Baseline Model: Logistic Regression (L2 regularization)
Primary Model: XGBoost with scale_pos_weight
Hyperparameter Tuning: Optuna Bayesian, 30 trials, 5-fold CV (stratified by patient_id)
Feature Selection: 3-Tier (Clinical Mandatory → LASSO λ.1se → XGBoost)
Missing Data: MICE (m=5), within CV loop
Validation: 5-fold stratified CV → internal performance
```

### 评估指标 (TRIPOD-aligned)

```
Discrimination: AUC, PR-AUC
Calibration: Calibration slope/intercept, Brier Score, Calibration Plot
Clinical Utility: Decision Curve Analysis (DCA)
Reclassification: NRI vs LR baseline
Subgroup: AUC by age group, metastasis status, admission type
Explainability: SHAP (summary + dependence plots)
```

### 外部验证策略

```
Data: MIMIC-III prostate cancer cohort (先探查可行性)
Type: Temporal external validation
Threshold: ≥ 300 patients for full external validation
```

---

## Phase 2 Gate: ✅ PASS

方案完整性、统计严谨性、临床相关性均已通过辩论验证。
进入 **Phase 3: 执行/内部验证**。

---

*PI 裁决完成。*

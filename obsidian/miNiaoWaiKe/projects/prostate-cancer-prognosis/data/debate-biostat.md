# 辩论观点陈述: Biostatistician

**辩论主题**: 前列腺癌住院不良结局预测 — 建模方法选择 + 统计分析策略 + 协变量筛选
**日期**: 2026-05-10
**确信度标注**: [高/中/低]

---

## 我的核心观点 (按重要性排序)

### 观点 1: 必须包含 Logistic Regression 作为可解释性 baseline [确信度: 高]

**论据**:
- 医学期刊审稿人几乎必然要求"与标准统计方法比较"
- Logistic Regression 是临床预测模型的标准 baseline (TRIPOD 指南要求)
- 仅报告 XGBoost 的 AUC 会被质疑"黑箱 vs 简单模型的增量价值"
- 如果 Logistic Regression 性能已接近 XGBoost (ΔAUC < 0.03)，审稿人会质疑 ML 的必要性

**推荐**: 必须纳入 Logistic Regression baseline。如果 XGBoost vs LR 的 ΔAUC < 0.05，Discussion 中需要充分论证 ML 的替代优势 (非线性交互、特征重要性排序的可靠性)。

### 观点 2: 不同意「不做特征筛选」的立场 [确信度: 高]

**论据**:
- EPV (events per variable) 的安全范围是 ≥ 10-20。25 个特征 vs ~250-350 正例 → EPV ~10-14，处于边界
- 在边界 EPV 下，全特征模型可能 overfit
- 应该使用 **LASSO** 做特征筛选:
  - 在训练集的每个 CV fold 中独立运行 LASSO
  - 选择 λ.1se (最稀疏且在 1 SE 内的模型) 而非 λ.min
  - 保留在 ≥ 3/5 folds 中都非零的特征作为最终特征集
- LASSO 筛选后的特征再输入 XGBoost (不是用 LASSO 做最终模型)

**推荐**: LASSO pre-filtering (λ.1se) → XGBoost 最终模型。不是替代，是特征筛选步骤。

### 观点 3: 样本量 Power 需要正式计算 [确信度: 高]

**论据**:
- "~2,000 样本够吗?" 需要定量回答。凭直觉不够，审稿人会要求 power analysis
- 对于 AUC 比较 (H0: AUC=0.75 vs H1: AUC=0.82), α=0.05, power=80%:
  - 正例约需 80-100 events → 目前 ~250-350 events 足够
- 对于 calibration: 需要每个十分位 ≥ 10 events
- 对于 SHAP 稳定性: 小样本下 SHAP 排名可能不稳定，需要 bootstrap 验证

**推荐**: SAP 中明确纳入 power analysis (基于预期 AUC 增量)，同时报告 SHAP 排名的 bootstrap 95% CI。

### 观点 4: 不同意使用单一的复合结局 [确信度: 中]

**论据**:
- 复合结局 = 30天死亡 OR ICU 入院。但死亡和 ICU 的临床驱动因素可能不同
- 死亡: 更多与疾病的终末期/姑息状态相关
- ICU 入院: 更多与急性并发症相关 (感染、出血、手术并发症)
- 如果合并为一个结局，模型可能学到的是两个不同信号的平均效果，降低了临床解释性

**反建议**: 
- Primary: 复合结局 (为了统计 power)
- Secondary: 分别报告各组成部分的模型性能
- Sensitivity analysis: 仅 ICU 入院的 sub-analysis (事件更多) 和仅死亡的 sub-analysis
- 在 Discussion 中讨论两组成分预测因子的异同

### 观点 5: 需要报告更多性能指标，不只 AUC [确信度: 高]

**论据**:
- AUC 对类别不平衡不太敏感，但临床效用需要更多维度评估
- 审稿人期望的报告指标 (PMID 25569120, TRIPOD):
  - Discrimination: AUC (必须) + PR-AUC (不平衡时)
  - Calibration: Calibration slope + Brier Score + Calibration-in-the-large
  - Clinical Utility: Decision Curve Analysis (DCA) — 对投 J Urology 尤其重要
  - Reclassification: NRI (Net Reclassification Improvement) vs baseline model

**推荐**: 

| 指标 | 必须/可选 | 用途 |
|------|----------|------|
| AUC | 必须 | 区分度 |
| PR-AUC | 必须 | 不平衡下的区分度 |
| Brier Score | 必须 | 整体校准 |
| Calibration Slope | 必须 | 校准方向 |
| Calibration Plot | 必须 (图) | 视觉校准 |
| DCA | 必须 (J Urology) | 临床净收益 |
| Sensitivity/Specificity at optimal threshold | 可选 | 临床参考 |
| NRI vs LR baseline | 可选 | 增量价值 |

---

## 我的推荐方案

### 统计分析计划 (SAP) 要点

**样本量论证**:
```
AUC 比较 (H0: 0.75 vs H1: 0.82)
α = 0.05 (two-sided), power = 0.80
正例需求: ~87 events (基于 Hanley & McNeil 公式)
现有: ~250-350 events → power > 0.95 ✅
```

**缺失值处理**:
- 报告每个变量的缺失率
- 缺失率 < 5%: complete case
- 缺失率 5-30%: multiple imputation (MICE, m=5)
- 缺失率 30-50%: 标记 missing indicator + complete case sensitivity
- 缺失率 > 50%: 移除该变量
- 所有缺失处理在 CV loop 内进行 (避免信息泄漏)

**特征筛选 (LASSO pre-filtering)**:
1. 在每个 CV fold 训练集中运行 LASSO
2. 选取 λ.1se
3. 保留在 ≥ 3/5 folds 中非零的特征
4. 最终特征集输入 XGBoost

**模型比较**:
- XGBoost (主力) vs Logistic Regression (baseline)
- DeLong's test for correlated AUCs
- 如果 ΔAUC < 0.05 且不显著: Discussion 论证 ML 的替代价值

**SHAP 稳定性评估**:
- Bootstrap 1000 resamples
- 报告每个特征的 SHAP mean(|SHAP|) 的 95% CI
- Top-5 特征 CI 不重叠 → 排名稳定

---

## 关键风险

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| 实验室值缺失导致 multiple imputation 后的结果不确定 | 中 | 同时报告 complete case 结果作为敏感性分析 |
| DCA 决策曲线在小样本下不稳定 | 低 | 使用 bs=TRUE (bootstrap) 平滑 DCA 曲线 |
| LASSO 筛选在不同的 CV folds 中选择不一致的特征 | 中 | 只保留 ≥ 3/5 folds 的稳定特征 |
| 时间漂移 (2008-2022) — 早期和后期的临床实践不同 | 中 | 按时间 split (前 70% train, 后 30% test) 做敏感性分析 |

---

*独立观点陈述完成。供研讨厅主持人汇总。*

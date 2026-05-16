# 辩论观点陈述: Computational Biologist

**辩论主题**: 前列腺癌住院不良结局预测 — 建模方法选择 + 统计分析策略 + 协变量筛选
**日期**: 2026-05-10
**确信度标注**: [高/中/低]

---

## 我的核心观点 (按重要性排序)

### 观点 1: XGBoost 应为唯一主力模型，不做多模型 ensemble [确信度: 高]

**论据**:
- 本任务特征以混合类型为主 (continuous + categorical + binary)，XGBoost 原生支持混合类型
- 天然处理缺失值 (sparsity aware split)，无需事前插补
- kidney-stone 项目已验证 XGBoost 在 MIMIC-IV 数据上的效果 (AUC 0.755)
- 多模型 ensemble 在小样本场景 (n~2,000) 中的增益有限，且增加过拟合风险和审稿人的方法学复杂度质疑
- 近期前列腺癌 SEER 文献中 CatBoost 表现最好 (AUC 0.939)，但 XGBoost 与 CatBoost 在结构化数据上性能接近，且 XGBoost 的社区支持更成熟

**推荐**: 单一 XGBoost 模型，不做 stacking/ensemble。

### 观点 2: 使用 baseline-only 特征集，先不做时序聚合特征 [确信度: 高]

**论据**:
- 入院前最后/最近一次实验室值 = baseline 特征，简单可解释
- 时序特征 (入院前多次测量的均值/趋势/方差) 需要 ≥ 3 次测量才有意义，MIMIC 中 PSA 的重复测量频次未知
- 先跑 baseline → 看性能。若 AUC < 0.75 再考虑加入时序特征，避免不必要的复杂度
- kidney-stone 项目经验: 19 个 baseline 特征已经可以达到 AUC 0.755

**推荐**: v1 只使用 baseline 特征。v2 可实验时序特征。

### 观点 3: 必须包含 Charlson Comorbidity Index [确信度: 中]

**论据**:
- 前列腺癌患者多为老年人，合并症是死亡/ICU 的主要驱动因素之一
- CCI 是文献中最常用的合并症评分，便于跨研究对比
- 但需要权衡: CCI 是一个聚合指标 (信息压缩)，单独纳入每个合并症可能更好
- 可以在特征重要性分析后再决定是否拆开

**推荐**: 同时纳入 CCI 总分 + 关键单合并症变量 (心衰/肾病/转移)，看 SHAP 后决定是否保留

### 观点 4: 不做 SMOTE 或过采样 [确信度: 高]

**论据**:
- 复合结局预期事件率 ~17%，不算极度不平衡
- SMOTE 在医学研究中争议大 (合成样本不可解释，校准可能失真)
- XGBoost 的 `scale_pos_weight` 参数直接处理类别不平衡，不影响校准
- 如果需要，优先使用 `scale_pos_weight`，不使用 SMOTE

**推荐**: `scale_pos_weight = (neg_count / pos_count)`，不做 SMOTE

### 观点 5: 外部验证建议使用 MIMIC-III [确信度: 中]

**论据**:
- MIMIC-III 与 MIMIC-IV 来自同一医院 (Beth Israel)，但时间不重叠 (2001-2012 vs 2008-2022)
- 这提供了"时间外部验证" — 评价模型在实践变化下的稳定性，是有意义的验证
- kidney-stone 项目用此策略从 AUC 0.755 到 0.8286
- 但需要注意: MIMIC-III 的 prostate cancer 队列规模可能更小

**推荐**: Phase 4 使用 MIMIC-III 作为外部验证队列

---

## 我的推荐方案

### 模型架构

```
XGBoost Classifier
├── objective: binary:logistic
├── eval_metric: AUC
├── scale_pos_weight: neg/pos (自动计算)
├── max_depth: 3-6 (grid search)
├── learning_rate: 0.01-0.1
├── n_estimators: 100-500 (early stopping)
├── subsample: 0.8
├── colsample_bytree: 0.8
├── reg_alpha: 0.1 (L1 正则化，防过拟合)
├── reg_lambda: 1.0 (L2 正则化)
└── n_jobs: 2 (M4 24GB 内存约束)
```

### 特征集 (v1 baseline)

| 类别 | 变量 | 处理方式 |
|------|------|---------|
| 人口学 | age | continuous |
| | race | one-hot (5 categories) |
| | insurance | one-hot (4 categories) |
| 入院 | admission_type | one-hot (Elective/Emergency/Urgent) |
| 肿瘤 | PSA (latest pre-admission) | continuous, log1p transform |
| | bone_metastasis | binary |
| 合并症 | CCI_total | continuous (0-15) |
| | heart_failure | binary |
| | renal_disease | binary |
| 实验室 | hemoglobin | continuous |
| | wbc | continuous |
| | platelet | continuous |
| | creatinine | continuous |
| | albumin | continuous |
| | lactate | continuous (if available) |
| 手术 | prostatectomy_this_admission | binary |

**总计**: ~25 特征 (after one-hot encoding)

### 验证策略

```
内部验证: 5-fold stratified CV (by patient)
  - 按 patient_id 分层: 同一患者不出现在 train 和 validation 中
  - 报告: mean AUC ± SD across folds
  - 额外报告: PR-AUC, Brier Score, Calibration Slope

特征选择:
  - 不做事前筛选 (前向/后向选择在小样本中不稳定)
  - 使用 SHAP importance → 事后解释
  - 移除 SHAP importance = 0 的特征重新训练

超参数调优:
  - Bayesian optimization (Optuna), 30 trials
  - 搜索空间: max_depth [3,6], lr [0.01, 0.1], n_estimators [100, 500]
  - 目标: validation AUC
```

---

## 关键风险

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| PSA 测量时间窗不一致 — 有些患者入院前1天测、有些1年前测 | 中 | 定义明确的时间窗 (入院前 30 天内最近值)；30天外无 PSA 的标记为缺失 |
| 特征数/事件数比例 — 25 特征 vs ~250-350+ 正例 | 低 | EPV > 10，在安全范围内 |
| MIMIC-III 外部验证队列太小 | 中 | 先探查 MIMIC-III 前列腺癌规模；若 < 300 人则放弃外部验证 |
| 实验室值缺失率可能较高 (如乳酸) | 中 | 缺失率 > 50% 的变量直接移除；30-50% 的标记缺失指示变量 |

---

*独立观点陈述完成。供研讨厅主持人汇总。*

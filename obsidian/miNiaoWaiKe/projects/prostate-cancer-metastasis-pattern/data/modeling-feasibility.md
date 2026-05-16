# 建模可行性评估

**项目**: prostate-cancer-metastasis-pattern
**执行者**: computational-biologist (urology)
**日期**: 2026-05-14

---

## 1. 建模任务定义

### 主要 ML 任务

| 维度 | 规格 |
|------|------|
| 任务类型 | Binary classification: 3 年 OS (死亡 vs 存活) |
| 分层策略 | 全 M1 队列 + Bone-only 子集 + Visceral 子集 |
| 模型 | XGBoost (主) + Logistic Regression (baseline) |
| 验证 | 5-fold stratified CV (按年份 + met_pattern 分层) |
| 时间外验 | 2020-2023 hold-out |

### 为什么选 3 年 OS 而非 5 年?

- M1 队列中位 OS ≈ 20-31 月，5 年事件率太低 (~25% alive at 5y)
- 3 年事件率更平衡 (~55-65% event rate)，适合 binary classification
- 同时产出 5 年 OS 作为 Cox 生存分析补充

---

## 2. 特征工程计划

### 基础特征矩阵

| 类别 | 特征数 | 说明 |
|------|:------:|------|
| Demographics | 5 | age, race, marital, income_quartile, urban_rural |
| Tumor characteristics | 6 | psa_cat, gleason_gg, histology, t_stage, n_stage |
| Metastasis pattern | 5 | met_pattern, n_met_sites, liver_inv, lung_inv, multi_organ |
| Treatment | 3 | surgery, radiation, chemo |
| Era | 1 | era_group (2010-2015 / 2016-2023) |
| **Total** | **20** | |

### 衍生特征 (Phase 3 探索)

- age × n_met_sites (年龄与转移负荷交互)
- gleason_gg × met_pattern (Gleason 在不同转移模式中的效应)
- income × race (社会经济-种族交互)

---

## 3. ML 模型设计

### 主模型 (XGBoost)

```python
xgb_params = {
    'n_estimators': 200,
    'max_depth': 5,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'scale_pos_weight': 'auto',  # 自动处理类别不平衡
    'random_state': 42,
    'n_jobs': 2,                  # 安全约束
    'eval_metric': 'auc',
}
```

### 三个子模型

| 模型 | 训练集 | N (估) | 预期 AUC |
|------|--------|--------|:--:|
| Model_full | 全 M1 (2010-2019 train) | ~55,000 | 0.78-0.82 |
| Model_bone | Bone-only 子集 | ~38,000 | 0.75-0.79 |
| Model_visceral | Visceral ± Bone 子集 | ~10,000 | 0.72-0.76 |

### Baseline (Logistic Regression)

- L2 regularization (penalty='l2', C=1.0)
- 与 ML 模型相同特征集
- 用于区分"数据预测能力" vs "模型复杂度增益"

---

## 4. 评估指标 (按公司标准 — 所有模型统一输出)

| 指标 | key | 目标 | 强制 |
|------|-----|------|:--:|
| AUC (ROC) + 95% CI | auc.mean, auc.ci_low, auc.ci_high | ≥ 0.70 | ✅ |
| PR-AUC | pr_auc | — | ✅ |
| Brier Score | brier | ≤ 0.25 | ✅ |
| Calibration Slope | calibration_slope | [0.85, 1.15] | ✅ |
| Calibration Intercept | calibration_intercept | [-0.15, 0.15] | ✅ |
| Sensitivity | sensitivity | — | ✅ |
| Specificity | specificity | — | ✅ |
| PPV | ppv | — | ✅ |
| NPV | npv | — | ✅ |
| F1 Score | f1 | — | ✅ |
| CV AUC std | auc_cv_std | — | ✅ |

---

## 5. 可解释性计划

### 全模型 SHAP

- SHAP summary plot (全队列)
- SHAP dependence plot (top 5 features)

### 跨模式 SHAP 对比 (核心创新)

- 热力图: 相同特征在 Bone vs Visceral 模型中的 SHAP 排名
- 森林图: top 10 特征在两个模型中的 effect direction 对比
- 临床意义: "Gleason 在骨转移中仍是顶级预后因子, 但在内脏转移中被治疗选择取代"

---

## 6. 可行性结论

| 检查项 | 状态 |
|--------|:--:|
| 样本量充足 (n > 50,000 train) | ✅ |
| 特征维度合理 (20 features, 无高维问题) | ✅ |
| 任务复杂度适中 (binary classification) | ✅ |
| 安全约束满足 (n_jobs=2, Windows 无需 forkserver) | ✅ |
| 外验方案可行 (时间 hold-out) | ✅ |
| 创新性充足 (跨模式 SHAP 对比) | ✅ |
| SAP 需求明确 | ✅ → 待 Phase 2 biostatistician |

**建模可行性**: ✅ 可行。建议进入 Phase 2 研讨厅辩论。

---

*computational-biologist (urology) 产出于 Phase 1 Round 1*

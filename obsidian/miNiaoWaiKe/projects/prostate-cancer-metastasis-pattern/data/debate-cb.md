# 方案设计辩论 — Computational Biologist 独立意见

**项目**: prostate-cancer-metastasis-pattern
**辩论方**: computational-biologist (urology)
**辩论阶段**: Phase 2 Round 1 (独立输出, 未参考其他方意见)
**日期**: 2026-05-14

---

## 1. 建模方案

### 1.1 模型架构选择

**推荐: XGBoost (主) + Logistic Regression (baseline)**

| 候选算法 | 优势 | 劣势 | 结论 |
|----------|------|------|:--:|
| **XGBoost** | 表格数据 SOTA，天然处理缺失，非线性交互，SHAP 原生支持 | 超参调优耗时 | ✅ 主模型 |
| Logistic Regression (L2) | 可解释性极强，训练快，系数=效应方向 | 无法捕获非线性交互 | ✅ baseline |
| Random Forest | 鲁棒性强 | 内存消耗大 (树结构展开)，速度慢 | ❌ 备选 |
| LightGBM | 内存效率更高 | Windows 兼容性问题 | ❌ 备选 |

### 1.2 分层训练策略

```
全队列 M1 (N≈55K train) ─→ Model_full
    │
    ├── Bone-only (N≈38K) ─→ Model_bone
    │
    └── Visceral ± Bone (N≈10K) ─→ Model_visceral
```

**理由**: 
- 全模型学"M1 通用的"预后模式
- 子模型学"转移模式特异的"预后模式
- Bone vs Visceral 的 SHAP 对比 → 论文核心创新点

### 1.3 特征工程

#### 主特征集 (20 个)

```
人口学 (5):   age, race, marital_status, income_quartile, urban_rural
肿瘤特征 (6):  psa_cat, gleason_gg, histology_type, t_stage, n_stage, m_stage_detail  
治疗 (3):     surgery_type, radiation_type, chemo
转移 (4):     met_pattern, n_met_sites, liver_involvement, lung_involvement
时间 (2):     era_group, year_of_diagnosis
```

#### 衍生特征 (在子模型中排除 met_pattern 以避免标签泄露)

- `age × n_met_sites`: 年龄-转移负荷交互
- `gleason_gg × liver_involvement`: 高危病理+高危部位的叠加效应

### 1.4 类别不平衡处理

M1 3 年 OS 预期 event rate ~55-65%，不平衡程度中等。

**策略**: `scale_pos_weight` 自动调整（不推荐 SMOTE — 在 M1 子集中 SMOTE 的合成样本可能不合理，且违反内存安全规则 2）

---

## 2. 特征选择策略

### LASSO 预筛选 (可选)

- 用 `LogisticRegressionCV(penalty='l1', Cs=20, n_jobs=2)` 做特征选择
- 保留系数非零的特征进入 XGBoost
- **但在子模型中**，特征数仅 20，可能不需要预筛选

### SHAP-based 事后选择 (推荐)

- XGBoost 全特征训练
- 事后 SHAP 重要性排序
- 将 SHAP mean(|value|) < 0.01 的特征标记为低贡献，但不删除（论文中可讨论）

---

## 3. 超参调优策略

### RandomizedSearchCV (推荐，避免 GridSearch 的维度爆炸)

```python
param_dist = {
    'n_estimators': [100, 200, 300],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.05, 0.1],
    'subsample': [0.7, 0.8, 1.0],
    'colsample_bytree': [0.6, 0.8, 1.0],
    'min_child_weight': [1, 3, 5],
    'gamma': [0, 0.1, 0.5],
}
RandomizedSearchCV(
    xgb.XGBClassifier(random_state=42, n_jobs=2),
    param_distributions=param_dist,
    n_iter=50,
    cv=5,
    scoring='roc_auc',
    n_jobs=2,            # 安全约束 — 必须显式传
    random_state=42,
)
```

**⚠️ 注意**: 三个子模型各自独立调优。不允许用全模型的超参直接套用于子模型。

---

## 4. 模型评估与验证

### 4.1 内部 CV

- 5-fold stratified CV (按 year + met_pattern 分层)
- 输出 `cv_results.json`（符合公司标准结构）

### 4.2 时间外验

- Train: 2010-2019
- Test: 2020-2023 (时间 hold-out，严格无信息泄露)

### 4.3 过拟合检测

- CV AUC > Test AUC 超过 0.10 → 标记 WARNING
- CV AUC > Test AUC 超过 0.15 → B环触发，回退 Phase 3

---

## 5. 内存安全声明

- 平台: Windows 11 → `JOBLIB_START_METHOD=forkserver` 跳过 (spawn 已等效)
- n_jobs: 全局 2
- 所有 `cross_val_score/cross_val_predict/cross_validate` 显式传 `n_jobs=2`
- 禁止 SMOTE + Pipeline + 并行 CV 组合
- 预检: Phase 3 执行前必须运行 `python engine/scripts/run_preflight.py`
- 三个子模型串行训练（节省内存峰值）

---

*computational-biologist (urology) — Phase 2 Round 1 独立意见*

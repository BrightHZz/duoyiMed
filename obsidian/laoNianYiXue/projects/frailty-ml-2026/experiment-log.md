---
type: experiment_log
project: "[[project-brief|衰弱预测项目]]"
---

# 实验记录 — 衰弱预测 ML

---

## 实验 1: Baseline — Logistic Regression

---
type: experiment
experiment_id: "exp_001_lr_baseline"
date: 
mlflow_run_id: ""
model: "Logistic Regression"
status: pending
---

### 目标
建立最简基线模型（Logistic Regression + 年龄+性别），作为后续模型性能的锚点。

### 配置
```yaml
model: LogisticRegression
features: [age, sex]
preprocessing: StandardScaler
```

### 结果
| 指标 | 训练 (CV) | 测试 |
|------|-----------|------|
| AUC-ROC | - | - |

### 结论
待执行。

---

## 实验 2: Baseline — LASSO Logistic Regression

---
type: experiment
experiment_id: "exp_002_lasso"
date: 
mlflow_run_id: ""
model: "LASSO Logistic Regression"
status: pending
---

### 目标
在全部候选特征上使用 LASSO 正则化，作为线性方法的性能上限。

### 配置
```yaml
model: LogisticRegression(penalty='l1', solver='saga', C tuned via CV)
features: all ~80 candidates
preprocessing: StandardScaler + MICE imputation
```

### 结果
待执行。

---

## 实验 3: XGBoost (主模型)

---
type: experiment
experiment_id: "exp_003_xgboost_main"
date: 
mlflow_run_id: ""
model: "XGBoost"
status: pending
---

### 目标
训练主力 XGBoost 模型，预期在 AUC 上超越 LASSO。

### 配置
```yaml
model: XGBClassifier
parameters:
  n_estimators: [100, 200, 500]
  max_depth: [3, 5, 7]
  learning_rate: [0.01, 0.05, 0.1]
  subsample: [0.8, 1.0]
  colsample_bytree: [0.8, 1.0]
  scale_pos_weight: tuned  # 处理类别不平衡
optimization: Bayesian (Optuna)
```

### 结果
待执行。

---

## 实验 4: 可解释性分析

---
type: experiment
experiment_id: "exp_004_shap_analysis"
date: 
mlflow_run_id: ""
model: "SHAP (XGBoost)"
status: pending
---

### 目标
对 exp_003 的最佳 XGBoost 模型进行 SHAP 分析。

### 输出
- SHAP 全局特征重要性 (bar plot + beeswarm)
- SHAP Dependence Plot (top 10 features)
- SHAP Interaction Values (top 10 pairs)
- 个体 Waterfall Plot (抽样 20 例，含 TP/FP/FN)

### 结果
待执行。

---

## 实验 5: 敏感性分析

---
type: experiment
experiment_id: "exp_005_sensitivity"
date: 
mlflow_run_id: ""
model: "XGBoost + 多种設定"
status: pending
---

### 目标
对主要结果进行敏感性分析。
1. 完整案例分析 vs MICE
2. 排除极端 SHAP 值的样本
3. 不同年龄分层 (60-69/70-79/80+)

### 结果
待执行。

---
type: method
topic: model_selection
status: reference
last_updated: 2026-05-04
---

# ML 模型选型指南

计算老年医学常见问题的模型选择决策树。

## 分类问题（衰弱/跌倒/死亡 是/否）

```
N < 1000, 特征 < 100
  → Logistic Regression (基线必做) + XGBoost

N > 1000, 特征 > 100
  → XGBoost / LightGBM / CatBoost

极度类别不平衡 (<1:10)
  → SMOTE + class_weight + PR-AUC 为主指标

需要不确定性估计
  → Gaussian Process / Bayesian NN（谨慎）
```

## 生存分析

```
比例风险假设成立
  → Cox PH + Elastic Net (glmnet)

比例风险假设不成立
  → Random Survival Forest / DeepSurv / DeepHit

竞争风险存在
  → Cause-specific Cox / Fine-Gray

时变协变量
  → Joint Model / Landmarking / LSTM
```

## 聚类（多病共存亚型）

```
连续变量       → K-means / GMM / Hierarchical
混合变量       → K-prototypes / Latent Class Analysis
高维稀疏       → PCA/t-SNE/UMAP 降维 → 聚类
确定簇数       → Silhouette + Elbow + Gap statistic
```

## 回归（衰老时钟/生物年龄）

```
高维特征 + N<1000   → Elastic Net (alpha=0.5)
高维特征 + N>1000   → XGBoost / LightGBM
需要非线性交互      → MLP (2-3层, BN+Dropout)
需要置信区间        → Quantile Regression / Conformal Prediction
```

## 纵向预测

```
固定间隔       → Mixed Effects (lme4) / GEE
不规则间隔     → Functional PCA / GP
联合建模       → JMbayes2 / joineRML
```

## 关键原则

1. **先做简单 baseline** — Logistic/Cox + 年龄+性别, 再做复杂模型
2. **特征选择在 CV 内** — 绝对不能先筛特征再做 CV
3. **测试集只用一次** — 调参用验证集，最终评估才用测试集
4. **区分度+校准度同时报告** — 只报 AUC 是不够的
5. **可解释性必做** — SHAP/Grad-CAM 让临床同事理解模型

## 相关资源
- [[methods/causal-inference-choices|因果推断方法选择]]
- [[methods/omop-cdm-mapping|OMOP CDM 映射]]
- [[methods/survival-analysis-notes|生存分析笔记]]

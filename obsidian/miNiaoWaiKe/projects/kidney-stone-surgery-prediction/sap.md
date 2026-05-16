# 统计分析计划 (SAP) — 肾结石外科干预预测

## 1. 研究设计概览

- **设计类型**: 回顾性队列研究
- **数据来源**: MIMIC-IV v2.2 (2008–2019) + MIMIC-III v1.4 (2001–2012)
- **主要终点**: 急诊入院后 90 天内泌尿外科干预 (binary)
- **次要终点**: 无
- **分析人群**: ED 肾结石患者，首次急诊入院为 index admission

## 2. 样本量与功效

- **MIMIC-IV 训练集**: N=1,979 (118 events, 6.0%)
- **MIMIC-III 验证集**: N=245 (114 events, 46.5%)
- **功效计算**: 对于 AUROC 检验，假设 H0=0.70 vs H1=0.78, α=0.05, N=1,979:
  - Events=118, EPC (events per candidate predictor) ≈ 1.0 (保守)
  - 采用 5-fold CV 评估，避免单次 split 的方差
- **结论**: 样本量偏小但可支持中等区分度的预测模型开发；
  外部验证集样本量较小 (N=245) 是主要限制

## 3. 基线特征描述

- **连续变量**: 中位数 [IQR] (所有实验室值偏态分布)
- **分类变量**: n (%)
- **组间比较**: 报告 surgery vs no-surgery 两组的描述性统计
  - 不做假设检验比较（非随机分组，组间差异不代表因果关系）
  - 改为报告 SMD (Standardized Mean Difference)

## 4. 主要分析

### 4.1 预测模型

- **模型**: Logistic Regression (L1/L2), Random Forest, XGBoost
- **方法**: 5-fold stratified cross-validation
- **类别不平衡处理**: SMOTE (仅在训练 fold 内应用)
- **性能指标**:
  - 区分度: AUROC, AUPRC (主指标，因类别不平衡)
  - 校准度: Brier score, calibration curve
  - 临床决策: Sensitivity, Specificity, PPV, NPV at Youden-optimal threshold

### 4.2 特征工程

- **缺失处理**: 中位数插补 (主分析)
- **缺失率 > 30%**: 添加 missingness indicator
- **共线性处理**: Pearson r > 0.9 去除
- **交互项**: 4 个临床预设交互项 (LRT 比较 with/without interaction)

### 4.3 超参数优化

- RF: Optuna (TPE, 60 trials, 5-fold CV)
- XGB: RandomizedSearchCV (24 iterations)
- LR: Grid search (C × penalty, 12 combos)

## 5. 外部验证

- **队列**: MIMIC-III, 245 ED 肾结石患者
- **结局定义**: index admission 期间泌尿外科手术 (ICD-9 编码)
- **注意**: 结局定义与 MIMIC-IV 不完全一致 (入院期间 vs 90天)
- **评估**: 直接应用 MIMIC-IV 训练的 RF 模型 (不重训练)
- **报告**: AUROC, AUPRC, 校准曲线, Sens/Spec at MIMIC-IV threshold

## 6. 模型可解释性

- RF: SHAP TreeExplainer (background=100, evaluation=300)
- LR: SHAP LinearExplainer
- **注意**: SHAP 值反映模型内特征重要性，不做因果推断

## 7. 敏感性分析

- **完整案例分析**: 仅使用无缺失特征的完整记录
- **不同阈值**: 报告 Sens/Spec trade-off 曲线

## 8. 统计软件

- Python 3.12
- scikit-learn 1.5, XGBoost 2.1, imbalanced-learn 0.14
- Optuna 4.8 (超参数优化)
- SHAP 0.46 (可解释性)

## 审阅签批

- [x] Biostatistician: APPROVED
- [ ] PI final sign-off

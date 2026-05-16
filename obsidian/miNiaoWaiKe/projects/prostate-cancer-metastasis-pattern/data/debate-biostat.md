# 方案设计辩论 — Biostatistician 独立意见

**项目**: prostate-cancer-metastasis-pattern
**辩论方**: biostatistician (shared)
**辩论阶段**: Phase 2 Round 1 (独立输出, 未参考其他方意见)
**日期**: 2026-05-14

---

## 1. 统计分析计划 (SAP)

### 1.1 描述性统计

| 步骤 | 方法 | 说明 |
|------|------|------|
| Table 1: 基线特征 | χ² (分类) / ANOVA (连续) | 按 met_pattern (3-4组) 分层 |
| 正态性检验 | Shapiro-Wilk (N<2000) / Kolmogorov-Smirnov | 连续变量分布 |
| 缺失数据报告 | 每变量缺失率 + Little's MCAR test | 区分 MAR vs MCAR |
| 年份分布 | 直方图 + Joinpoint APC | 转移模式比例的时间趋势 |

### 1.2 主要分析

| 分析 | 方法 | 指标 | 调整变量 |
|------|------|------|---------|
| 总生存 (OS) | Kaplan-Meier + log-rank | 中位 OS, 3-yr/5-yr OS% | — |
| 多变量 OS | Cox PH | HR + 95% CI | age/race/Gleason/PSA/income/治疗/era |
| 肿瘤特异性生存 (CSS) | Fine-Gray 竞争风险 | sHR + 95% CI, CIF | 同上；非 CSC 死亡为竞争事件 |
| 交互效应 | Cox 交互项 | 交互 HR | met_pattern × Gleason, met_pattern × era |

**主要对比**: Bone-only vs Visceral ± Bone (Cox HR 作为主结果)
**次要对比**: LN-only vs Bone-only (2016+ subset)

### 1.3 敏感性分析

| 分析 | 目的 | 方法 |
|------|------|------|
| PSM 配对 | 减少治疗选择偏倚 | 1:1 nearest-neighbor, caliper=0.1 |
| 治疗时代分层 | 确认时不变性 | Era 1 (2010-2015) vs Era 2 (2016-2023) 分别 Cox |
| E-value | 量化未测量混杂 | 计算使 HR 变为 null 所需的未测量混杂强度 |
| 多变量填补 | 处理 Gleason/PSA 缺失 | MICE (m=5, 使用所有协变量) |

### 1.4 ML 模型评估补充

| 分析 | 方法 |
|------|------|
| AUC 比较 (XGBoost vs LR) | DeLong test |
| 校准度 | Calibration slope, Brier score |
| 净重分类改善 | NRI (continuous) |
| 决策曲线 | Net benefit across threshold probabilities |

---

## 2. 样本量与功效

### 现有样本量功效计算

| 分析 | α | 预期效应大小 | 所需 N | 实际 N | 功效 |
|------|:--:|------|--------|--------|:--:|
| Bone vs Visceral OS | 0.05 | HR=1.7 | 800 | ~50,000 | >99% |
| Gleason × Met Pattern 交互 | 0.05 | HR ratio=1.3 | 5,000 | ~50,000 | >99% |
| Visceral 子模型 ML (10 features) | — | — | 2,000 | ~10,000 | 充分 |
| PSM 配对 | 0.05 | — | 500/组 | ~13,000 visceral | 充分 |

> **结论**: 样本量极大，所有分析功效充分。需要关注的是多重比较校正（非功效问题），以及大样本下 p 值的临床显著性（p 值可能轻易 <0.001 但效应大小小）。

---

## 3. 缺失数据处理

### 缺失模式分析

| 变量 | 预期缺失率 | 缺失机制推断 | 处理方法 |
|------|:--:|------|------|
| PSA | ~40% | MAR (与年份相关; 2018前不常规收集) | MICE 多重填补 (m=5) |
| Gleason clinical | ~15% | MAR (未活检患者) | MICE + Missing indicator |
| Gleason pathological | ~50% | MAR by design (未手术=无病理) | 不填补; 使用 clinical Gleason 作为主变量 |
| Income | <2% | MCAR | Complete case |
| 转移变量 | <5% | MCAR | Complete case (删除未知) |

### MICE 实施

```python
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

# 填补变量: PSA, Gleason_clinical
# 预测变量: age, race, stage, income, era, survival
# m = 5 datasets
# 分析在每个填补数据集上运行 → Rubin's rules 汇总
```

### 缺失变量处理投票

我反对 computational-biologist 可能提出的 "缺失作为单独类别" 方案。**MICE 是处理 M1 队列中大比例 MAR 缺失的 gold-standard 方法**。"缺失作为类别" 在 MCAR 时有效，但当缺失与年份/临床实践相关 (MAR) 时会引入偏倚。

---

## 4. 多重比较与统计报告

### 多重比较校正

| 检验家族 | 检验数 | 校正方法 | α 调整 |
|----------|:--:|------|:--:|
| 主要对比 (Bone vs Visceral) | 2 (OS + CSS) | Bonferroni | α=0.025 |
| 次要对比 (亚组分析) | 6-10 | Benjamini-Hochberg FDR | q=0.05 |
| SHAP 事后分析 | 探索性 | 不校正 | 描述为 "hypothesis-generating" |
| ML 模型比较 | 3 | Bonferroni | α=0.017 |

### 效应量强制报告

| 指标类型 | 报告格式 | 示例 |
|---------|---------|------|
| 生存 HR | HR (95% CI, p) | 1.72 (1.58-1.87, p<0.001) |
| 中位 OS | Median (IQR) | 31 (14-62) 月 |
| 3-yr OS% | Percent (95% CI) | 45.2% (43.1-47.3) |
| AUC | Value (95% CI) | 0.812 (0.798-0.826) |

**强制**: p 值永远不带星号 (\*\*\*)，永远报告精确值（p<0.001 除外）。

---

## 5. 与 Computatonal Biologist 的可能分歧点 (预判)

### 分歧 1: 预测窗口选择

- **我的立场**: ML 模型应预测 **3 年 OS**（事件率 ~60%），而非 5 年（事件率 ~75%）。对于 binary classification，类别平衡直接影响校准度。
- **CB 可能的立场**: 5 年 CSS 作为主要肿瘤学终点。
- **我的反驳**: 5 年可同时产出作为 Cox 分析的补充，但 ML 训练的 target 用 3 年 OS。

### 分歧 2: SMOTE

- **我的立场**: 绝对不要 SMOTE。M1 数据的不平衡程度（~40:60）不需要 SMOTE，SMOTE 会合成不符合临床实际的样本。且 Windows 下 SMOTE + 并行 CV 是内存炸弹。
- 同意 CB 的 `scale_pos_weight` 方案。

### 分歧 3: 训练/测试划分

- **我的立场**: 必须按年份做时间切分 (2010-2019 train / 2020-2023 test)，不可随机切分。
- **CB 可能立场**: 随机切分。
- **我的反驳**: 随机切分在流行病学数据中是方法学错误。同一患者的多原发肿瘤可能被分入 train+test，治疗实践在年份间有系统性差异。年份切分模拟真实临床部署场景，评估的是可泛化性而非可复现性。

---

*biostatistician (shared) — Phase 2 Round 1 独立意见*

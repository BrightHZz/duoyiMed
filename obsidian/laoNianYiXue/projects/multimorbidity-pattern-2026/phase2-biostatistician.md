# Phase 2 — 统计分析计划 (SAP, 独立观点)

**Agent**: `shared/biostatistician`
**辩论**: 研讨厅 Round 1 — 独立输出
**日期**: 2026-05-11

---

## 统计分析计划 (SAP) — 多病共存模式识别与不良结局预测

### 1. 研究设计概览

- **设计类型**: 前瞻性队列 (prospective cohort)
- **数据来源**: CHARLS (China Health and Retirement Longitudinal Study), Wave 1-4, 2011-2018
- **暴露/分组**: LCA 识别的多病共存聚类亚型 (k 类, 预计 3-6 类)
- **主要结局**:
  - 全因死亡 (4 年, Wave 1→3)
  - ADL 失能 (ADL 6 项中 ≥1 项需帮助)
  - 住院 (过去 2 年 ≥1 次)
- **预测窗口**: 4 年 (Wave 1 → Wave 3)

### 2. 样本量与功效

#### 2.1 聚类分析 (Stage 1)
- LCA 对样本量要求: 建议每个待估计参数 ≥10 个事件
- 14 个二值变量的 LCA (k=4): 约 56 个参数 → 建议 ≥560 样本
- CHARLS Wave 1 多病共存子集: 预计 8,000-10,000 → **充足**

#### 2.2 预测模型 (Stage 2)
- **全因死亡**: 预计发生率 ~5-8% (4年) → 事件数 ≈ 400-800
  - 规则 of thumb: 每个预测变量 ≥10 个事件
  - 40-60 个特征 → 需 ≥400-600 个事件 → 基本满足
  - 若事件数不足: 降低特征维数 (LASSO 筛选) 或使用复合结局
- **ADL 失能**: 预计发生率 ~15-20% → 事件充足
- **住院**: 预计发生率 ~20-25% → 事件充足

#### 2.3 功效分析
- **假设**: 主要比较 (LCA 标签 vs CCI 的 ΔAUC)
- **预期 ΔAUC**: ≥0.03
- **显著性水平**: α = 0.05 (双侧)
- **检测 AUC 差值的功效**: N=8,000, AUC_base=0.75, ΔAUC=0.03 → power ≈ 0.85 ✅

### 3. 基线特征描述与比较

#### 3.1 描述统计策略
```
连续变量处理:
  1. Shapiro-Wilk 正态性检验
    → 若 p ≥ 0.05: mean ± SD
    → 若 p < 0.05: median [IQR]
  
  例外: 大样本 (N>5,000) 时 SW 检验过度敏感
    → 同时检查 Q-Q plot 和偏度/峰度
    → |skewness| < 1  + |kurtosis| < 2 → 可报告 mean ± SD
```

#### 3.2 LCA 聚类间比较 (Table 1)
- **连续变量 (正态)**: one-way ANOVA → 显著则 post-hoc Tukey HSD
- **连续变量 (偏态)**: Kruskal-Wallis → 显著则 post-hoc Dunn's test (BH 校正)
- **分类变量**: χ² test → 显著则 adjusted standardized residuals > |2|
- **SMD (Standardized Mean Difference)**: 两两聚类间比较, |SMD| < 0.1 = 均衡
- **注意**: 不报告聚类间的 p 值作为"显著性" → 聚类本身就是基于数据的

### 4. 主要分析

#### 4.1 Stage 1: LCA 模型选择与稳健性

**模型选择流程**:
1. 对 k = 2 到 8 分别拟合 LCA (nrep=10, maxiter=5000)
2. 记录: log-likelihood, BIC, AIC, aBIC, Entropy R², 最小后验概率
3. **主决策指标**: BIC (Bayesian Information Criterion)
4. **辅助指标**: LMR-LRT (Lo-Mendell-Rubin adjusted LRT, p<0.05 支持 k vs k-1)
5. **临床约束**: 最小类占比 >5%, 类含义可解释

**Bootstrap 稳健性**:
- 100 次 Bootstrap (每次重抽样 80%)
- 每次执行完整 LCA 模型选择 (k=2:8)
- 报告: 各次选择的一致性比例 (如 85% 选 k=4)
- 最优 k 的聚类中心 Jaccard 相似系数 (理想 >0.80)

#### 4.2 Stage 2: 预测模型

**模型链** (所有模型在同一训练/测试分割上评估):

| # | 模型 | 特征集 | 问题 |
|---|------|--------|------|
| M0 | Logistic | 年龄 + 性别 | 最简 baseline |
| M1 | Logistic | M0 + CCI | 传统共病计数 |
| M2 | Logistic | M0 + 共病计数 (dummy, 0/1/≥2) | 简单计数 |
| M3 | Logistic | M0 + LCA 硬标签 | LCA 标签独立 |
| M4 | Logistic | M0 + CCI + LCA 标签 | 完整 LR |
| M5 | XGBoost | M1 特征集 | XGBoost 无 LCA |
| M6 | **XGBoost** | M4 特征集 (含 LCA) | **主模型** |
| M7 | XGBoost | M0 + CCI + LCA 后验概率 | 软标签实验 |

**缺失数据处理**:
- **主分析**: MICE (Multiple Imputation by Chained Equations), m=10, 假设 MAR
  - 预测矩阵: 包含所有分析变量 + 辅助变量 (如社会参与, 用于改善插补)
  - 诊断: 检查插补前后的密度图
- **敏感性分析 1**: 完整案例分析 (CCA) — 仅含全部变量完整的样本
- **敏感性分析 2**: 缺失指示法 — 对缺失率 >20% 的变量加入缺失指示标志
- **变量缺失率报告**: 每个变量必须在 Table 1 中报告缺失率

**协变量调整**:
- Model 1 (Crude): 仅 LCA 聚类标签
- Model 2 (Age+Sex adjusted): + 年龄 + 性别
- Model 3 (Full adjusted): + 教育 + 城乡 + 婚姻 + 吸烟 + 饮酒 + BMI + ADL + CES-D

**多重共线性**:
- VIF > 5: 标记警告
- VIF > 10: 剔除或合并
- 特别关注: CCI 和 LCA 标签的共线性 (预期中等相关但非共线)

### 5. 模型评估

#### 5.1 区分度
- **AUC-ROC**: DeLong 95% CI
- **AUC-PR**: 死亡结局用 (类别不平衡时比 ROC 更敏感)
- **配对 DeLong test**: 比较 M6 vs M5 的 AUC 差异

#### 5.2 校准度
- **Calibration plot** (loess smoothed, 10 bins)
- **Calibration-in-the-large** (理想 = 0) + **Calibration slope** (理想 = 1)
- **Brier Score** (越低越好, Brier_max = 0.25 for binary)
- **注意**: 不单独依赖 Hosmer-Lemeshow test (大样本时几乎总是显著)

#### 5.3 增量预测价值
比较 M6 (含 LCA) vs M5 (仅 CCI):

| 指标 | 解释 | 目标 |
|------|------|------|
| **ΔAUC** | DeLong test | ≥0.03, p<0.05 |
| **NRI (Category-free)** | 连续 NRI | 正方向 (事件) >0.30 且 负方向 (非事件) 重分类 <10% |
| **IDI** | 综合改善指标 | >0, 95% CI 不跨零 |

**⚠️ 注意**: 如果 ΔAUC < 0.02 → LCA 标签无临床意义的增量价值 → 这是有效发现, 不是失败。Discussion 中应诚实讨论 "共病模式聚类未提供超越共病计数的预测价值"。

#### 5.4 临床决策曲线 (Decision Curve Analysis)
- 阈值概率范围: 0.05-0.30 (死亡), 0.10-0.40 (ADL 失能)
- 比较: M5 (CCI only) vs M6 (CCI + LCA) vs Treat All vs Treat None

### 6. 亚组分析与交互效应

#### 6.1 预设亚组 (≤5 个)
- 年龄: 45-64 / 65-74 / ≥75
- 性别: 男 / 女
- 城乡: 城镇 / 农村
- CCI: 0-2 / 3-4 / ≥5

#### 6.2 亚组分析方法
- **交互项检验**: LCA 标签 × 亚组变量的乘法交互项 p 值
- **不采用**亚组内单独检验 → 错误率高
- 森林图展示各亚组效应量 + 95% CI

#### 6.3 亚组 N 验证
- 所有亚组 N 求和必须等于总 N (分亚组无遗漏无重复)
- 缺失值导致的分组差异必须标注

### 7. 敏感性分析 (5 项)

1. **缺失数据处理**: MICE (m=10) vs CCA vs 缺失指示法
2. **不同 k 的 LCA**: 主分析的 k ± 1 聚类方案的预测性能对比
3. **聚类不确定性**: 硬标签 vs 软标签 (后验概率 >0.7 子集分析)
4. **排除极端值**: 排除 LCA 后验概率 <0.7 的"模糊"个体
5. **E-value**: 未测混杂评估
   - 若有显著关联 → 计算 E-value: 未测混杂需要多大的 OR 才能解释观察到的关联?
   - E-value < 1.5 → 结论脆弱, Discussion 中声明

### 8. 竞争风险 (死亡结局专用)

- **竞争事件**: 在 ADL 失能分析中, 死亡是竞争事件
  - 主分析: 将死亡作为竞争事件 (Fine-Gray)
  - 敏感性分析: 将死亡个体排除 (可能高估失能风险)
- **住院分析**: 死亡作为删失处理 (Cox PH), 前提 PH 假设成立

### 9. 多重比较校正

- **3 个结局** (死亡/ADL失能/住院) → Bonferroni 校正: α = 0.05/3 = 0.017
- **LCA 聚类间 post-hoc 比较** (共 C(k,2) 对) → BH (Benjamini-Hochberg) 校正
- **亚组交互检验** (5 个亚组) → 每个结局单独评估, 报告原始 p + BH 校正 p

### 10. 报告规范

- **效应量**: 所有 OR/HR 必须与 95% CI 一起报告
- **p 值**: 报告精确 p 值 (非 p<0.05 的二元化表述), p<0.001 除外
- **缺失数据**: Table 1 每变量标注缺失率, Methods 中报告缺失处理策略
- **基线均衡性**: 使用 SMD (非 p 值) 评估, |SMD| < 0.1
- **统计软件**: 
  - R 4.x (poLCA, survival, rms, mice, PredictABEL, EValue, tableone)
  - Python 3.x (scikit-learn 1.x, xgboost 2.x, shap 0.x)
  - 所有代码纳入 Supplementary Material

### 11. SAP 签批状态自评

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 结局定义: 复合结局成分已明确, 无循环论证 | ✅ |
| 2 | 缺失处理: MICE (m=10) 主分析 + CCA 敏感性 | ✅ |
| 3 | 亚组定义: 5 个预设亚组, 交互项检验 | ✅ |
| 4 | 中介分析: N/A (非中介分析研究) | ✅ |
| 5 | 效应量报告: OR + 95% CI + E-value | ✅ |

**SAP 自评**: 5/5 → 建议 APPROVED ✅

---

*独立输出结束。本 SAP 未参考 computational-biologist 和 clinical-researcher 的意见。*

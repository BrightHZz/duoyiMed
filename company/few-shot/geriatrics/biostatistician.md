# Few-Shot 示例 — Biostatistician Agent

## Example 1: 撰写统计分析计划 (SAP)

### Input

```
项目: CHARLS 衰弱转换预测
研究设计: 前瞻性队列, 2013→2015 (主分析)
样本: ~6,500 (60+, 基线非衰弱)
结局: 二分类 (2年衰弱恶化: 是/否)
预测因子: ~78 个候选特征
缺失: 预估 5-15% 各变量, 血液数据仅 ~50% 完整
主要模型: XGBoost vs LASSO Logistic

请撰写完整 SAP。
```

### Reasoning (Chain of Thought)

```
1. 研究设计:
   - 前瞻性队列, 2013 是基线, 2015 是结局
   - 非 RCT, 所有因果声明需谨慎

2. 样本量/功效:
   - 这是预测模型研究, 不是假设检验
   - 关键是: 事件数/候选特征数 的比值
   - 若衰弱恶化率 ~25% → ~1,625 events / 78 features = ~21:1
   → 足够, 一般要求 EPV (events per variable) >10

3. 缺失数据:
   - 血液数据 50% 完整 → 考虑两套分析
   - 主模型: 所有特征但排除血液变量 → 样本量大
   - 子分析: 含血液变量 → 样本量 ~3,300

4. 评估指标:
   - 分类: AUC-ROC + AUC-PR
   - 校准: Brier Score + calibration plot
   - 模型比较: DeLong test (AUC), IDI + NRI

5. 敏感性分析: 至少 3 项
```

### Output

```markdown
## 统计分析计划 (SAP) — CHARLS 衰弱转换预测

### 1. 研究设计概览
| | |
|---|---|
| 设计 | 前瞻性队列 |
| 数据 | CHARLS Wave 2 (2013) → Wave 3 (2015) |
| 时间验证 | CHARLS Wave 3 (2015) → Wave 4 (2018) |
| 报告指南 | TRIPOD (Type 2a) |

### 2. 样本量与功效
预测模型研究使用 EPV (events per variable)，不适用传统功效分析:

- 预估样本: N ≈ 5,500 (60+ & 基线非衰弱 & 完成随访)
- 预估事件率: ~25% (2年恶化)
- 预估事件数: ~1,375
- 候选特征数: 78
- **EPV = 1375/78 ≈ 17.6** → ✓ (>10, 满足要求)

### 3. 基线特征描述
- 连续: Shapiro-Wilk 检验 → 正态: mean±SD; 偏态: median [IQR]
- 分类: n (%)
- 组间比较 (恶化 vs 稳定): t-test/Mann-Whitney/χ²
- **使用 SMD** (Standardized Mean Difference) 而非 p 值评估组间差异
  - |SMD|<0.1: 均衡; 0.1-0.2: 轻度差异; >0.2: 显著差异

### 4. 缺失数据处理

#### 主分析 — MICE
- 方法: Multiple Imputation by Chained Equations
- 插补次数: m=10
- 假设: MAR (Missing At Random)
- 纳入插补模型的变量: 全部特征 + 结局 + 抽样权重
- 注意: 不插补结局变量 —— 缺失结局的排除

#### 敏感性分析
| 分析 | 方法 | 目的 |
|------|------|------|
| S1 | 完整案例分析 | 检验 MICE 的稳健性 |
| S2 | 排除血液特征 (<50% 完整) | 扩大有效样本量 |
| S3 | 最差/最佳情况分析 | 检验对非随机缺失的敏感性 |

### 5. 模型开发

#### 主分析流程
```
Step 1: 10-fold nested CV
  - 外环: 10-fold, 用于模型评估
  - 内环: 5-fold, 用于超参数调优 (Bayesian Optimization)
  
Step 2: LASSO (Baseline)
  - 特征选择: LASSO 正则化在 CV 内进行
  - 超参 λ: 1-SE rule (简约模型) 或 min CV error

Step 3: XGBoost (主模型)
  - 超参: n_estimators, max_depth, learning_rate, subsample, 
    colsample_bytree, scale_pos_weight
  - 调优: Optuna (100 trials)
```

### 6. 评估指标

| 维度 | 指标 | 解释 |
|------|------|------|
| 区分度 | AUC-ROC | 整体区分能力 |
| 区分度 | AUC-PR | 类别不平衡时更敏感 (推荐) |
| 校准度 | Brier Score | 整体校准误差 |
| 校准度 | Calibration slope | 接近 1 = 好 |
| 校准度 | ECI (Estimated Calibration Index) | 模型校准的汇总指标 |
| 临床效用 | Decision Curve | 净获益 vs 阈值概率 |

#### 模型比较
- AUC: DeLong test
- 综合: IDI (Integrated Discrimination Improvement)
- 重分类: Category-free NRI (仅当有临床相关的风险分界点时)

### 7. 亚组分析 (预设)
| 亚组 | 检验方式 |
|------|----------|
| 性别 (男/女) | 交互项 p 值 |
| 年龄 (60-69/70-79/80+) | 交互项 + 森林图 |
| 城乡 | 交互项 p 值 |

**重要**: 不要在亚组内部单独检验显著性! 报告交互效应。

### 8. 敏感性分析 (5 项)
1. 完整案例分析 vs MICE
2. 不同时间窗: 2011→2013 (无握力)
3. 不同结局: Frailty Index (≥0.25) 替代 Fried
4. 含死亡: Fine-Gray 竞争风险 (死亡 vs 衰弱恶化)
5. 极端值: 排除 SHAP 异常值的 bootstrap 分析

### 9. 软件
- R 4.x: mice, tableone, gtsummary, pROC, rms, MatchIt
- Python 3.x: scikit-learn, xgboost, shap, optuna
- 可重复性: 所有分析代码在 Git 仓库中
```

---

## Example 2: 快速统计咨询

### Input

```
问题: 审稿人说应该用 Bonferroni 校正多重比较，
但我们只做了 3 个预设亚组分析。需要校正吗？
```

### Reasoning

```
1. 场景分析: 3 个预设亚组分析, 每个通过交互项检验
2. 核心原则: Bonferroni 适用于"探索性"多重比较,
   预设亚组分析 (hypothesis-driven) 有明确先验理由, 
   不需要严格的 Bonferroni
3. 但: 如果审稿人坚持, 可以报告校正后的结果作为敏感性,
   同时解释为什么预设亚组不需要校正
```

### Output

```
预设的 3 个亚组分析通常不需要 Bonferroni 校正, 理由:

1. Bonferroni 的设计初衷是控制"探索性多重比较"的 FWER,
   而你的亚组是基于先验假设 (生物学/临床理由), 不是数据驱动
   
2. 老年医学和流行病学文献中, 预设亚组分析 (<5个) 的标准做法
   是报告交互项 p 值, 不做多重比较校正

对审稿人的回应建议:
  "We conducted three pre-specified subgroup analyses based on 
   prior evidence that frailty prediction performance may differ 
   by sex, age, and urban/rural residence. As these were 
   hypothesis-driven rather than exploratory, we did not apply 
   Bonferroni correction. However, applying Bonferroni 
   (threshold p<0.017) does not change our conclusions 
   [如果确实没变的话]."

关键: 如果你有 >5 个亚组或做了"数据驱动"的亚组发现,
那就需要校正了。
```

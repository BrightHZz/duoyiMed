# Phase 2 — 建模方案 (独立观点)

**Agent**: `geriatrics/computational-biologist`
**辩论**: 研讨厅 Round 1 — 独立输出
**日期**: 2026-05-11

---

## 建模方案 — 多病共存模式识别与不良结局预测

### 1. 临床问题 → ML 任务映射

| 阶段 | 临床问题 | ML 任务 | 核心方法 | 备选方法 |
|------|---------|---------|---------|---------|
| Stage 1 | CHARLS 老年人有哪些多病共存聚类亚型? | 无监督聚类 (二值变量) | **LCA (poLCA)** | K-prototypes (clustMixType) |
| Stage 2 | 不同共病亚型能否预测 4 年不良结局? | 二分类 (死亡/ADL失能/住院) | **XGBoost** | Logistic Regression (基线), MLP |
| 增量验证 | 聚类标签比 CCI 有增量预测价值吗? | 嵌套模型比较 | **ΔAUC + NRI + IDI** | — |

### 2. 数据概述

- **训练队列**: Wave 1 (2011) 基线 → Wave 3 (2015) 结局
- **时间验证**: Wave 2 (2013) 基线 → Wave 4 (2018) 结局
- **估计样本量**: N ≈ 17,000 (Wave 1), 多病共存 (≥2 种慢病) 子集约 8,000-10,000
- **候选特征**: 14 种慢性病 (二值, LCA 输入) + 30-50 个协变量 (预测模型输入)
- **⚠️ 关键约束**: Wave 1 无握力 → 预测模型不能依赖握力

### 3. Stage 1 — LCA 聚类方案

#### 3.1 方法选择理由
选择 **LCA (Latent Class Analysis)** 作为主方法:
- 14 种慢性病均为**二值变量** → LCA 天然适合 (伯努利分布假设)
- 相比 K-means: 基于概率模型, 有正式的模型选择标准 (BIC/BLRT)
- 相比层次聚类: 分类更稳健, 成员概率可解释
- **M4 Pro 可行**: R poLCA 包对 N=17,000 无性能压力

**备选方法**: K-prototypes (clustMixType, Python) 作为稳健性检验
- 如果 LCA 和 K-prototypes 得出的聚类模式一致 → 结论稳健
- 场景: 聚类中心模式相似度 >80% → 接受 LCA 结果

#### 3.2 聚类数选择
```r
# 模型选择流程
for (k in 2:8) {
  fit <- poLCA(cbind(htn, dyslip, dm, cancer, copd, liver, hd, stroke, 
                     kidney, digest, mental, arthritis, asthma, thyroid) ~ 1,
               data = charls_w1, nclass = k, nrep = 10, maxiter = 5000)
  # 记录: BIC, AIC, Entropy, 最小后验概率
}
```

**决策指标** (按优先级):
1. **BIC 最低** (主要指标, 惩罚模型复杂度)
2. **LMR-LRT p < 0.05** (k vs k-1 的显著性)
3. **Entropy > 0.7** (分类确定性, 理想 >0.8)
4. **最小类占比 > 5%** (临床实用性, 避免小类)
5. **临床可解释性** (最终裁量: PI + clinical-researcher)

**Bootstrap 稳健性**:
- 100 次 Bootstrap, 每次重抽样 80% 样本
- 各次 LCA 聚类中心与主分析的 Jaccard 相似系数中位数 >0.80 → 稳健

#### 3.3 输出格式
- 每个类的条件概率热力图 (14 种慢病 × k 类)
- 基于条件概率 >0.5 的疾病组合命名聚类亚型
- t-SNE 降维可视化 (用于直观展示分类)
- 每类的人口学 + 临床特征描述表 (Table 1)

### 4. Stage 2 — XGBoost 预测方案

#### 4.1 方法选择理由
选择 **XGBoost** 作为主模型:
- N ≈ 8,000-10,000 (多病共存子集), F ≈ 40-60 → XGBoost 是表格数据的最佳选择
- frailty-ml-2026 已证明 XGBoost 在 CHARLS 上可达 AUC 0.86
- SHAP 可解释性成熟, 适合临床场景
- M4 Pro CPU 训练 XGBoost 足够 (early_stopping + GPU not needed)
- **不需要 DL**: 表格数据 + 经典方法够用 + N 非超大 + 可解释性优先

**基线模型**: Logistic Regression (年龄+性别+CCI), 必须做:
- 如果 XGBoost AUC 不显著高于 Logistic → XGBoost 不必要
- 如果 Logistic baseline 已接近 SOTA → 说明问题简单

#### 4.2 特征工程

**特征组** (按优先级):

| 优先级 | 特征组 | 变量数 | 说明 |
|--------|-------|--------|------|
| **核心** | LCA 聚类标签 | 1 (k 分类) | One-hot 编码, 本研究核心创新 |
| **核心** | CCI + 共病计数 | 2 | 对比基线 |
| **核心** | 人口学 | 5 | 年龄/性别/教育/城乡/婚姻 |
| **一级** | 功能指标 | 6-10 | ADL(6) + IADL(5) |
| **一级** | 生活方式 | 3 | 吸烟/饮酒/体力活动 |
| **一级** | 体格测量 | 3 | BMI/血压/腰围 |
| **二级** | 认知+心理 | 3-5 | MMSE + CES-D-10 |
| **二级** | 社会 | 2 | 社会参与/独居 |
| **可选** | 实验室 | 5-8 | CRP/HbA1c/血脂/肌酐 (缺失率 40-50%) |

**特征处理**:
- 连续变量: StandardScaler (XGBoost 不需要但统一处理)
- LCA 后验概率作为软标签 (可选, 捕获聚类不确定性)
  - 实验对比: 硬标签 (most likely class) vs 软标签 (k 个后验概率) 对 AUC 的影响

#### 4.3 训练策略

```
训练/测试分割:
  ├── 训练集 (80%): 含 10-fold nested CV
  │   ├── 外环: 10-fold, 用于模型选择 + 性能估计
  │   └── 内环: 3-fold GridSearchCV, 超参调优
  └── 测试集 (20%): 仅评估最终模型, 只用一次

超参搜索空间:
  n_estimators: [100, 200, 500]
  max_depth: [3, 5, 7]
  learning_rate: [0.01, 0.05, 0.1]
  subsample: [0.7, 0.8, 1.0]
  colsample_bytree: [0.7, 0.8, 1.0]
  scale_pos_weight: [1, auto]  (类别不平衡时)
```

#### 4.4 模型对比矩阵

| 模型 | 特征集 | 说明 |
|------|--------|------|
| LR_baseline | 年龄+性别 | 最简 baseline |
| LR_cci | 年龄+性别+CCI | 传统共病度量的表现 |
| LR_full | 全特征 (含 CCI, 不含 LCA 标签) | CCI 的完整表现 |
| LR_lca | 全特征 (含 LCA 硬标签, 不含 CCI) | LCA 标签的独立表现 |
| LR_full_lca | 全特征 (含 CCI + LCA 标签) | 最佳 LR |
| XGB_baseline | 年龄+性别 | XGBoost baseline |
| XGB_full | 全特征 (含 CCI, 不含 LCA 标签) | XGBoost 无 LCA |
| **XGB_full_lca** | 全特征 (含 CCI + LCA 标签) | **主模型** |
| XGB_soft_lca | 全特征 (含 CCI + LCA 后验概率) | 软标签实验 |

### 5. 评估方案

#### 5.1 主要指标
- **AUC-ROC**: 区分度主指标
- **AUC-PR**: 类别不平衡时的补充 (死亡结局预计 ~5-8%)
- **Brier Score**: 综合校准度
- **Calibration Curve**: loess 平滑, calibration-in-the-large + slope

#### 5.2 增量价值评估 (核心)
比较 XGB_full vs XGB_full_lca:
- **ΔAUC**: DeLong test, p < 0.05
- **NRI**: Category-free NRI, 正负两方向分别报告
- **IDI**: 连续指标, 不依赖分类阈值
- **目标**: ΔAUC ≥ 0.03 且 NRI 中 >50% 的重分类方向正确 → LCA 标签有增量预测价值

#### 5.3 可解释性
- **SHAP 全局**: 特征重要性 bar plot + summary plot
- **SHAP 个体**: Waterfall plot (选典型个体)
- **重点关注**: LCA 聚类标签的 SHAP 排名 — 是否在 Top 10?
- **交互效应**: SHAP dependence plot (age × LCA class, CCI × LCA class)

#### 5.4 亚组分析
- 按年龄组 (45-64 / 65-74 / ≥75)
- 按性别
- 按城乡
- 每个亚组内重复主分析 (AUC + 特征重要性)

### 6. 时间验证 (Wave 2 → Wave 4)

1. 将 Wave 1 的 LCA 模型**参数固定** (不重新拟合)
2. 用固定的 LCA 参数对 Wave 2 样本分配类别 (后验概率 → 最可能类)
3. 将 Wave 1 训练的 XGBoost 模型直接应用于 Wave 2
4. 评估: ΔAUC (Wave 2 验证 - Wave 1 CV 平均)
   - 若 |ΔAUC| < 0.05 → 模型泛化良好
   - 若 ΔAUC < -0.10 → Gate 4 FAIL, 触发 Phase 3 返工

### 7. 预期风险与缓解

| 风险 | 概率 | 缓解 |
|------|------|------|
| LCA 聚类数不确定 (BIC 持续下降) | 中 (30%) | 联合 LMR-LRT + Entropy + 临床可解释性 |
| ΔAUC < 0.02 (LCA 无增量价值) | 中 (25%) | 转为横断面描述性论文 (纯 LCA 模式识别) |
| 死亡事件数不足 (<2%) | 低 (10%) | 使用复合结局 (死亡+ADL+住院) |
| 样本中多病共存占比低 | 低 (5%) | 降低多病共存阈值从 ≥2 到 ≥1 慢病 |
| 自报慢病偏倚导致聚类不稳定 | 低 (5%) | Bootstrap 稳健性检验 |

### 8. 时间估算

| 任务 | 预计时间 |
|------|---------|
| 数据清洗 + 特征工程 | 2-3 h |
| LCA 模型选择 (k=2:8) | 2-3 h |
| LCA Bootstrap 稳健性 | 1-2 h |
| LR baseline + XGBoost CV | 2-3 h |
| 增量价值评估 (ΔAUC/NRI/IDI) | 1 h |
| SHAP 分析 + 可视化 | 2-3 h |
| 时间验证 (Wave 2→4) | 1-2 h |
| **总计** | **11-17 h** |

### 9. 技术栈

- **LCA**: R 4.x (poLCA), Jupyter notebook
- **ML**: Python 3.x (scikit-learn, xgboost, shap, imbalanced-learn)
- **增量价值**: R (PredictABEL) 或 Python (numpy 手动实现)
- **可视化**: matplotlib, seaborn, shap
- **报告**: Jupyter notebook → markdown → 交付给 scientific-writer

---

*独立输出结束。本方案未参考 biostatistician 和 clinical-researcher 的意见。*

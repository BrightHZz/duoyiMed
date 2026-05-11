# ⚠️ DEPRECATED — 计算老年医学研究团队 · 岗位职责与工作方法手册

> **此文件已弃用。** 项目已升级为公司模式。新的公司级运营手册位于 `company/company-sop.md`。
> 各事业部和共享服务的 Agent 定义位于 `company/` 目录下。
> 本文件保留作为历史参考。

---

## (以下为原始内容)

# 计算老年医学研究团队 — 岗位职责与工作方法手册

> **设计目标**：每个岗位的职责描述遵循「输入→工作方法→输出→接口」的统一格式，为未来研究流程的自动化编排（LLM-agent 驱动）奠定基础。

---

## 目录

1. [首席研究员 (PI)](#1-首席研究员-pi)
2. [计算生物学研究员 (Senior Computational Biologist)](#2-计算生物学研究员-senior-computational-biologist)
3. [老年医学临床研究员 (Clinical Researcher in Geriatrics)](#3-老年医学临床研究员-clinical-researcher-in-geriatrics)
4. [机器学习工程师 (ML Engineer)](#4-机器学习工程师-ml-engineer)
5. [生物统计学家 (Biostatistician)](#5-生物统计学家-biostatistician)
6. [数据工程师 (Data Engineer)](#6-数据工程师-data-engineer)
7. [学术写作与编辑专员 (Scientific Writer & Editor)](#7-学术写作与编辑专员-scientific-writer--editor)
8. [科研助理 / 博士生 (Research Assistant / PhD Student)](#8-科研助理--博士生-research-assistant--phd-student)
9. [岗位接口矩阵](#9-岗位接口矩阵)

---

## 1. 首席研究员 (PI)

### 1.1 核心职责

| 维度 | 内容 |
|------|------|
| 研究方向制定 | 确定团队的 3-5 年科研路线图，聚焦计算老年医学的关键科学问题 |
| 资源获取 | 基金申请（国自然面上/重点、科技部重点研发、国际联合基金） |
| 质量控制 | 对所有产出的科学质量负责，最终审定论文 |
| 合作网络 | 建立与维持临床医院、队列平台、国际学术组织关系 |
| 人才培养 | 指导团队成员职业发展，建设梯队 |

### 1.2 工作方法

#### 1.2.1 科研方向决策框架 — "FRAME" 法

```
F — Field scan（领域扫描）：每季度系统性扫描计算老年医学五大子领域的最新进展
R — Resource audit（资源审计）：评估团队当前数据、算力、人力能否支撑该方向
A — Alignment check（对齐检查）：该方向是否与国家老龄化战略、基金指南对齐
M — Market gap（发表缺口）：目标期刊近期是否缺乏该方向高质量稿件
E — Edge assessment（优势评估）：团队在该方向是否具有 6 个月内出成果的比较优势
```

**自动化潜力**：F（领域扫描）可由 LLM agent 每月自动抓取 PubMed/arXiv/bioRxiv 最新预印本，生成趋势简报。

#### 1.2.2 基金申请书标准流水线

```
第 1-2 周：文献计分析 → 确定科学假说与研究目标
第 3-4 周：撰写立项依据（科学问题重要性 + 国内外现状 + 团队基础）
第 5-6 周：研究方案设计（研究内容 → 技术路线 → 关键科学问题 → 可行性分析）
第 7-8 周：预算编制 + 成员简历 + 伦理声明 + 形式审查
```

**关键技巧**：
- 立项依据采用「漏斗式」结构：老龄化大背景 → 特定疾病负担 → 现有方法不足 → 团队的新方案
- 技术路线图使用「分层架构图」：数据层 → 方法层 → 验证层 → 应用层
- 可行性分析从「已有数据、已有方法、已有合作、已有发表」四个维度逐一论述

#### 1.2.3 目标期刊分级与投稿策略

建立三级期刊矩阵：

| 级别 | IF 区间 | 典型期刊 | 投稿策略 |
|------|---------|----------|----------|
| Tier 1 | >15 | Lancet Healthy Longevity, Nature Aging, JAMA IM | 仅当有大规模多中心验证 + 机制解释时冲击 |
| Tier 2 | 8-15 | Aging Cell, GeroScience, JAGS, PLoS Med | 主力投稿目标，新方法 + 良好验证即可 |
| Tier 3 | 4-8 | BMC Geriatrics, Frontiers in Aging, JAMDA | 探索性研究、小样本方法学验证 |

**投稿决策树**：
```
新方法 + 多中心外部验证 + 机制解释 → Tier 1
新方法 + 单中心验证 → Tier 2
已有方法的新应用 / 小样本探索 → Tier 3
```

**自动化潜力**：定期抓取目标期刊的发表列表，分析与团队方向的匹配度，推荐投稿目标。

### 1.3 输入/输出规范

| | 内容 |
|---|---|
| **输入 (from)** | 各岗位周报、领域趋势简报、基金指南更新、合作方需求 |
| **输出 (to)** | 研究方向决策（→ 全员）、基金申请任务分解（→ 各岗位负责人）、论文投稿审批（→ 学术写作与编辑） |

---

## 2. 计算生物学研究员 (Senior Computational Biologist)

### 2.1 核心职责

- 设计机器学习/深度学习方法解决老年医学核心问题
- 主导组学数据（基因组、表观组、蛋白质组、代谢组）的整合分析
- 开发衰老时钟、衰弱评估模型、疾病风险预测模型
- 担任方法学论文的第一/通讯作者

### 2.2 工作方法

#### 2.2.1 老年医学 ML 问题建模框架 — "PICO-ML" 映射法

将临床问题转化为机器学习任务的标准模板：

```
Problem (临床问题)     →  ML Task (机器学习任务)
─────────────────────────────────────────────────
衰弱早期识别           →  二分类/多分类（衰弱前期/衰弱期/健壮）
跌倒风险预测           →  生存分析（time-to-fall）
多病共存亚型发现       →  无监督聚类/LDA topic modeling
衰老轨迹建模           →  纵向数据 + 潜在增长曲线
衰老时钟构建           →  回归（甲基化年龄 vs 实际年龄）
药物不良反应预测       →  二分类 + SHAP 解释
```

**转化核对清单**：
- [ ] 临床结局变量是否可可靠测量？（需与临床研究员确认）
- [ ] 预测窗口（prediction window）是否明确定义？
- [ ] 模型的使用场景是筛查、诊断还是预后？
- [ ] 是否存在数据泄露（data leakage）风险（如用未来信息预测过去）？

#### 2.2.2 衰老时钟开发标准流水线

```
Step 1: 特征选择
  - 方法 1: Elastic Net (alpha=0.5) 对 CpG 位点初筛
  - 方法 2: Boruta 算法稳健特征筛选
  - 输出：top 100-500 CpG sites

Step 2: 模型训练
  - 主模型: Elastic Net / Gradient Boosting / Deep Learning (MLP)
  - 交叉验证: 5-fold nested CV（外环做模型选择，内环做超参调优）
  - 评估指标: MAE, RMSE, R², Median Absolute Deviation

Step 3: 泛化验证
  - 内部验证: 留一队列交叉验证
  - 外部验证: 独立队列（如用 UK Biobank 训练的模型在 CHARLS 验证）
  - 跨组织验证: 血液模型在唾液/脑组织中的表现

Step 4: 生物学解释
  - GSEA/KEGG 通路富集分析（对选中的 CpG 位点映射基因）
  - 与已知衰老标志（Hallmarks of Aging）关联
  - 年龄加速（Age Acceleration）与临床结局的关联分析
```

#### 2.2.3 组学数据整合策略

**融合层级决策矩阵**：

| 融合策略 | 适用场景 | 方法举例 | 优缺点 |
|----------|----------|----------|--------|
| 早期融合 | 各模态维度相近、同质性高 | 拼接后输入模型 | 简单但易过拟合 |
| 中期融合 | 各模态需要先提取各自的潜在表示 | 多模态自编码器、MOFA | 灵活但需调优 |
| 晚期融合 | 各模态已有独立的专家预测器 | Stacking ensemble | 可解释、模块化 |
| 图融合 | 模态间存在已知的生物学关系 | 知识图谱 + GNN | 引入先验知识 |

**推荐选择规则**：
- 多组学 + 中等样本量 (~500) → MOFA (Multi-Omics Factor Analysis)
- 两组学 + 大样本量 (>5000) → 晚期融合 stacking
- 带有已知通路信息 → 图融合

#### 2.2.4 关键技术栈速查

```
生存分析: scikit-survival, DeepSurv, DeepHit, pycox
组学分析: methylpy, DESeq2 (R), limma (R), MOFA2 (R/Python)
可解释性: SHAP, LIME, Integrated Gradients, Captum
特征选择: Boruta (R), BorutaShap (Python), Elastic Net
图方法 : PyG (PyTorch Geometric), DGL, NetworkX
```

### 2.3 输入/输出规范

| | 内容 |
|---|---|
| **输入 (from)** | 临床问题定义（→ 临床研究员）、清洗后数据（→ 数据工程师）、统计分析计划（→ 统计学家） |
| **输出 (to)** | 模型方案设计文档（→ ML 工程师 + 统计学家）、模型结果解读（→ 临床研究员 + 写作编辑）、方法学部分初稿（→ 写作编辑） |

---

## 3. 老年医学临床研究员 (Clinical Researcher in Geriatrics)

### 3.1 核心职责

- 提供老年综合征的临床定义与可计算表型
- 指导队列研究的入排标准与终点设定
- 解读模型结果的临床意义与转化价值
- 协调临床数据采集、数据使用协议与伦理审批

### 3.2 工作方法

#### 3.2.1 临床问题 → 计算问题转化模板

```
┌─────────────────────────────────────────────────────────┐
│ 临床场景描述：                                          │
│   e.g. "门诊中如何快速识别可能在未来 6 个月内衰弱的老人"     │
├─────────────────────────────────────────────────────────┤
│ Step 1: 定义目标人群 (Target Population)                 │
│   - 年龄 ≥ 60 / ≥ 65 / ≥ 80?                            │
│   - 社区居住 (community-dwelling) vs 住院 vs 养老机构？   │
│   - 排除标准：已确诊衰弱？终末期疾病？严重认知障碍？         │
├─────────────────────────────────────────────────────────┤
│ Step 2: 操作化结局变量 (Outcome Operationalization)       │
│   - 衰弱：Fried Phenotype (5项) vs Frailty Index (30+项)  │
│   - 跌倒：自报 vs EHR 记录？一次 vs 多次？                 │
│   - 预测窗口：3个月 / 6个月 / 1年 / 2年？                 │
├─────────────────────────────────────────────────────────┤
│ Step 3: 候选预测因子池 (Candidate Predictors)            │
│   - 人口学：年龄、性别、教育、婚姻                         │
│   - 临床：慢性病数量、多重用药(≥5种)、BMI、SBP             │
│   - 功能：ADL、IADL、步速、握力、SPPB                     │
│   - 认知：MMSE/MoCA                                       │
│   - 心理：GDS-15 (抑郁)                                   │
│   - 社会：Lubben Social Network Scale                    │
│   - 实验室：Hb、Alb、Cr、CRP、25(OH)D                     │
├─────────────────────────────────────────────────────────┤
│ Step 4: 数据可用性映射                                    │
│   - 哪个队列/数据库包含以上变量？                          │
│   - 缺失率预估？缺失机制 (MCAR/MAR/MNAR)？                │
├─────────────────────────────────────────────────────────┤
│ Step 5: 临床效用阈值 (Clinical Utility Threshold)        │
│   - 最小临床重要差异 (MCID)                               │
│   - 可接受的灵敏度/特异度下界                             │
│   - NNS (Number Needed to Screen) 最大可接受值            │
└─────────────────────────────────────────────────────────┘
```

#### 3.2.2 老年综合征的可计算表型库

建立标准化的表型定义字典，每种表型提供多种计算方式：

**衰弱 (Frailty) — 三种操作化定义**：

| 定义方式 | 所需变量 | 计算公式 | 适用场景 |
|----------|----------|----------|----------|
| Fried Phenotype | 体重下降、疲乏、握力、步速、活动量 | 5 项满足 ≥3 = 衰弱；1-2 = 前期 | 前瞻性队列 |
| Frailty Index (FI) | 30+ 健康缺陷项 | FI = 缺陷数 / 总项数；FI ≥ 0.25 = 衰弱 | EHR 回顾性数据 |
| FRAIL Scale | 疲劳、抗阻、移动、疾病、体重 | 5 项满足 ≥3 = 衰弱 | 快速筛查 |

**肌少症 (Sarcopenia) — AWGS 2019 标准**：

```
诊断流程：
  Step 1 筛查: SARC-F ≥ 4 或小腿围 (男 <34cm, 女 <33cm)
  Step 2 肌肉力量: 握力 (男 <28kg, 女 <18kg)
  Step 3 肌肉质量: DXA/BIA 测量 ASM/height² (男 <7.0, 女 <5.7 kg/m²)
  Step 4 身体功能: 步速 <1.0 m/s, SPPB ≤ 9, TUG ≥ 12s, 5次坐站 ≥ 12s
  
  诊断: Step1 + Step2 + Step3 = 肌少症
        Step1 + Step2 + Step3 + Step4 = 严重肌少症
```

#### 3.2.3 EHR 数据到研究数据的映射方法

```
原始 EHR 字段              →      标准化研究变量
┌─────────────────────┐        ┌─────────────────────┐
│ ICD-10 编码列表      │   →    │ Charlson CCI /      │
│ (多个诊断编码)        │        │ Elixhauser 合并症   │
├─────────────────────┤        ├─────────────────────┤
│ 处方药物记录          │   →    │ 多重用药 (≥5种)     │
│                     │        │ PIM (Beers criteria)│
│                     │        │ 抗胆碱能负担 (ARS)   │
├─────────────────────┤        ├─────────────────────┤
│ 实验室检验 (纵向)     │   →    │ eGFR (CKD-EPI)      │
│ 肌酐、尿蛋白等        │        │ 贫血 (WHO标准)      │
│                     │        │ 营养状态 (CONUT)     │
├─────────────────────┤        ├─────────────────────┤
│ 生命体征 (纵向)       │   →    │ 血压变异系数        │
│                     │        │ BMI 变化率           │
│                     │        │ 体位性低血压         │
└─────────────────────┘        └─────────────────────┘
```

#### 3.2.4 模型临床可解释性审查清单

接收计算团队的模型结果后，临床研究员需要回答：

1. **预测因子是否临床合理？** 模型选出的 top predictors 是否与已知老年医学病理生理机制一致？
2. **效应方向是否正确？** 例如握力高应当与衰弱风险负相关，若方向相反则需要排查
3. **区分度是否满足筛查需求？** AUC < 0.7 的模型不适合临床筛查；AUC ≥ 0.85 可考虑诊断辅助
4. **校准度是否合格？** 校准曲线（calibration plot）截距是否接近 0、斜率是否接近 1
5. **决策曲线是否显示净获益？** 在合理的阈值概率范围内，模型是否比"全治"或"不治"策略更好
6. **是否存在年龄混淆？** 模型是否只是学到了"年龄大 → 风险高"的简单映射而非真正有意义的生物信号

### 3.3 输入/输出规范

| | 内容 |
|---|---|
| **输入 (from)** | 研究假说（→ PI）、模型结果与特征重要性（→ 计算生物学/ML 工程师）、文献综述（→ 科研助理） |
| **输出 (to)** | 临床问题定义文档 + 表型计算方案（→ 计算生物学 + 数据工程师）、模型临床解读（→ 写作编辑）、伦理申请材料 |

---

## 4. 机器学习工程师 (ML Engineer)

### 4.1 核心职责

- 实现与调优各类模型（XGBoost、DeepSurv、Transformer、GNN 等）
- 搭建自动化训练/验证/测试流水线
- 特征工程：从 EHR、可穿戴、影像、组学数据中提取高维特征
- 模型版本管理与实验追踪

### 4.2 工作方法

#### 4.2.1 老年医学 ML 项目标准目录结构

```
project_name/
├── data/
│   ├── raw/              # 原始数据（只读，永不修改）
│   ├── interim/          # 中间处理数据
│   └── processed/        # 建模就绪数据
├── notebooks/
│   ├── 01_eda.ipynb      # 探索性数据分析
│   ├── 02_preprocessing.ipynb
│   └── 03_modeling.ipynb
├── src/
│   ├── data/             # 数据加载与预处理脚本
│   │   ├── make_dataset.py
│   │   └── preprocess.py
│   ├── features/         # 特征工程
│   │   ├── build_features.py
│   │   └── feature_selection.py
│   ├── models/           # 模型定义、训练、评估
│   │   ├── train_model.py
│   │   ├── predict_model.py
│   │   └── evaluate.py
│   └── visualization/    # 可视化
│       ├── visualize.py
│       └── plot_metrics.py
├── config/
│   ├── model_config.yaml
│   └── feature_config.yaml
├── experiments/          # MLflow 实验记录
├── outputs/
│   ├── models/           # 训练好的模型文件
│   ├── figures/          # 图表输出
│   └── reports/          # 报告输出
├── tests/
├── requirements.txt
├── dvc.yaml              # DVC 数据版本管理
└── README.md
```

#### 4.2.2 模型选型决策树

```
问题类型？

├── 分类（衰弱 是/否）
│   ├── N < 1000, 特征 < 100  → Logistic Regression (baseline) + XGBoost
│   ├── N > 1000, 特征 > 100  → XGBoost / LightGBM / CatBoost
│   └── 需要不确定性估计      → Gaussian Process / Bayesian NN
│
├── 生存分析（time-to-死亡/衰弱/跌倒）
│   ├── 比例风险假设成立       → Cox PH + Elastic Net (glmnet)
│   ├── 比例风险假设不成立     → Random Survival Forest / DeepSurv / DeepHit
│   ├── 竞争风险存在           → Cause-specific Cox / Fine-Gray + 离散时间模型
│   └── 时变协变量             → Joint Model / Landmarking / LSTM
│
├── 聚类（多病共存亚型）
│   ├── 探索性, 连续变量       → K-means / GMM
│   ├── 探索性, 混合变量       → K-prototypes / Latent Class Analysis (poLCA, R)
│   ├── 需要不确定性           → Dirichlet Process Mixture
│   └── 高维稀疏数据           → 自编码器降维 + 聚类
│
├── 回归（衰老时钟/生物年龄）
│   ├── 高维组学特征           → Elastic Net (稳妥baseline)
│   ├── 非线性关系明确         → XGBoost / Random Forest
│   ├── 需要深度特征交互       → MLP / TabNet
│   └── 需要置信区间           → Quantile Regression / Conformal Prediction
│
└── 纵向预测（功能衰退轨迹）
    ├── 固定时间间隔           → Mixed Effects Model / GEE
    ├── 不规则时间间隔         → Functional PCA / Gaussian Process
    └── 联合建模               → Joint Model (JM, rstanarm)
```

#### 4.2.3 特征工程标准流程

**a) 时间窗口特征工程（EHR/纵向数据专用）**：

```
预测时间点 t0（如：基线评估日期）
├── 回溯窗口 1: [t0 - 30天,  t0]     → 近期急性变化
├── 回溯窗口 2: [t0 - 1年,   t0]     → 短期趋势
├── 回溯窗口 3: [t0 - 3年,   t0]     → 中期趋势
└── 回溯窗口 4: [t0 - 5年,   t0]     → 长期积累

每个窗口内对每个变量提取：
  - 聚合: mean, min, max, std, first, last
  - 趋势: slope (线性回归系数), 变化百分比
  - 变异性: CV (变异系数), 相邻测量差的标准差
  - 缺失: 缺失率, 最近一次测量距今时间
```

**b) 老年医学专用特征**：

```python
# 示例：衰弱相关衍生特征
def compute_frailty_features(df):
    features = {}
    # 多重用药：统计唯一药物类别数
    features['n_drug_classes'] = df['atc_codes'].nunique()
    # 体重下降速率（过去一年）
    features['weight_loss_rate'] = (df['weight'].iloc[-1] - df['weight'].iloc[0]) / df['weight'].iloc[0]
    # eGFR 下降斜率
    features['egfr_slope'] = np.polyfit(df['time'], df['egfr'], 1)[0]
    # 炎症指数
    features['nlr'] = df['neutrophil'] / df['lymphocyte']  # NLR
    features['plr'] = df['platelet'] / df['lymphocyte']     # PLR
    # 累积疾病负担
    features['charlson_cci'] = compute_charlson(df['icd_codes'])
    return features
```

#### 4.2.4 实验管理与 MLOps 实践

**a) 每一个实验必须记录（MLflow）**：

```yaml
experiment:
  name: "frailty_prediction_v2"
  tags:
    task: "classification"
    cohort: "CHARLS_2011_2018"
    target: "fried_frailty_2y"
  parameters:
    model: "xgboost"
    n_estimators: 200
    max_depth: 5
    learning_rate: 0.05
    subsample: 0.8
    colsample_bytree: 0.8
  metrics:
    auc_roc: 0.842
    auc_pr: 0.671
    sensitivity: 0.78
    specificity: 0.81
    brier_score: 0.142
  artifacts:
    - feature_importance.csv
    - shap_summary_plot.png
    - calibration_plot.png
    - model.pkl
```

**b) 模型版本管理规则**：

- `model_name/v1.0` — 初次训练完成，内部验证通过
- `model_name/v1.1` — 超参数调优改进
- `model_name/v2.0` — 新增特征或更换模型架构
- `model_name/v2.0-charls` — 在特定数据集上微调
- 使用 `dvc` 追踪数据版本，与模型版本一一对应

#### 4.2.5 模型可解释性报告标准模板

```markdown
## 模型可解释性报告 — [模型名称]

### 1. 全局解释（哪些特征最重要？）
- SHAP 均值排名前 20 特征 + 特征定义
- 特征类别分布（人口学/临床/功能/实验室各占多少？）

### 2. 方向性解释（每个特征的方向是否符合临床预期？）
- SHAP dependence plot + 临床研究员确认 ✓/✗

### 3. 交互效应
- SHAP interaction values top 10 特征对

### 4. 个体解释（为什么这个老人被预测为高风险？）
- 随机抽取 3 个 TP、3 个 FP、3 个 FN 案例
- waterfall plot 展示各特征贡献
- 提交临床研究员审阅

### 5. 公平性评估
- 按年龄组 (60-69/70-79/80+) 分层 AUC
- 按性别的敏感度/特异度差异
- Equal Opportunity Difference < 0.1?
```

### 4.3 输入/输出规范

| | 内容 |
|---|---|
| **输入 (from)** | 建模方案设计（→ 计算生物学）、表型定义与数据字典（→ 临床研究员）、清洗后数据（→ 数据工程师）、统计假设（→ 统计学家） |
| **输出 (to)** | 训练好的模型 + 评估报告 + 可解释性报告（→ 计算生物学 + 统计学家）、特征工程文档（→ 全员复用）、模型 API 或序列化文件（→ 数据工程师） |

---

## 5. 生物统计学家 (Biostatistician)

### 5.1 核心职责

- 研究设计：样本量估算、统计功效分析、偏倚控制
- 纵向数据分析与生存分析
- 因果推断：倾向性评分、工具变量、DID、中介分析
- 荟萃分析
- 审查所有产出的统计方法部分

### 5.2 工作方法

#### 5.2.1 统计分析计划 (SAP) 标准模板

```markdown
## 统计分析计划 — [研究标题]

### 1. 研究设计概览
- 设计类型: 前瞻性队列 / 回顾性病例对照 / 横断面
- 数据来源: 
- 样本量与统计功效: 见第 2 节

### 2. 样本量与功效分析
- 主要终点: 
- 预期效应量: (Cohen's d / OR / HR)
- α = 0.05, Power = 0.80
- 所需样本量: N = ___
- 考虑 20% 失访, 最终纳入: N = ___
- 软件: G*Power / PASS / R (pwr package)

### 3. 基线特征描述
- 连续变量: 正态用 mean ± SD, 偏态用 median [IQR]
- 分类变量: n (%)
- 组间比较: 正态用 t-test/ANOVA, 偏态用 Mann-Whitney/Kruskal-Wallis, 分类用 χ²/Fisher

### 4. 主要分析
- 模型: 
- 协变量调整:
- 亚组分析 (预设): 
- 缺失数据处理: MICE (多重插补), m = __, 假设 MAR
- 敏感性分析: 完整案例分析 + 最差/最佳情况分析

### 5. 模型评估
- 区分度: C-statistic / AUC / Harrell's C
- 校准度: Calibration plot + Hosmer-Lemeshow / Gronnesby-Borgan
- 综合判别改善: IDI, NRI (category-free)

### 6. 竞争风险 (如适用)
- 竞争事件定义: e.g. 非衰弱相关死亡
- 方法: Fine-Gray subdistribution hazard / Cause-specific hazard

### 7. 多重比较校正
- 方法: Bonferroni / Benjamini-Hochberg (FDR)
- 校正范围:

### 8. 软件与版本
- R 4.x, packages: survival (3.x), rms (6.x), mice (3.x), cmprsk (2.x)
```

#### 5.2.2 因果推断方法选择指南

```
需要回答的因果问题？

├── "这个干预/暴露对结局的平均效应是多少？"
│   ├── RCT 数据         → ITT / PP / AT (standard)
│   ├── 观察性数据, 有可测混杂 → Propensity Score Matching / IPTW
│   ├── 观察性数据, 有未测混杂 → Instrumental Variable (IV) / DiD
│   └── 时变处理/暴露      → Marginal Structural Model (MSM) + IPTW
│
├── "效应是如何传递的？（机制/中介）"
│   ├── 单中介            → Baron-Kenny / Product of Coefficients + Bootstrap
│   ├── 多中介            → VanderWeele 多中介框架
│   ├── 高维中介 (组学)    → HIMA (High-dimensional Mediation Analysis)
│   └── 因果中介          → Natural Direct/Indirect Effect (mediation R package)
│
├── "效应在谁身上更强？（异质性）"
│   ├── 预设亚组           → 交互作用检验 (不要用亚组内显著性！)
│   ├── 数据驱动亚组       → Causal Forest / FindIt / MOB
│   └── 个体化效应         → BART / Causal Forest (grf)
│
└── "如果有未测混杂, 结论有多稳健？"
    └── E-value (VanderWeele & Ding, 2017) → "未测混杂因子需要多大才能推翻结论？"
```

#### 5.2.3 纵向衰老数据分析专项方法

**联合模型 (Joint Model) 标准流程**：

```
场景：重复测量的生物标志物（如步速逐年下降）预测死亡/衰弱风险

Step 1: 拟合纵向子模型
  步速_ij = β₀ + β₁*时间_ij + β₂*年龄_i + β₃*性别_i + b₀ᵢ + b₁ᵢ*时间_ij + ε_ij
  (线性混合效应模型, 随机截距 + 随机斜率)

Step 2: 拟合生存子模型
  h_i(t) = h₀(t) * exp(γ₁*年龄_i + γ₂*性别_i + α * 步速真实值_i(t))
  (Cox 比例风险模型, 步速真实值来自纵向子模型的估计)

Step 3: 联合似然估计
  使用 JMbayes2 (R) 或 rstanarm 进行贝叶斯估计

Step 4: 动态预测
  给定个体前 k 次测量, 预测其未来 t 年的衰弱/死亡风险
  输出动态风险曲线 + 置信带
```

**常用 R Package 速查**：

```
研究设计:   pwr, gsDesign, TrialSize
描述统计:   tableone, gtsummary, arsenal
回归模型:   lm, glm, lme4 (mixed), gee (GEE)
生存分析:   survival, rms, survminer
竞争风险:   cmprsk, riskRegression, timereg
联合模型:   JMbayes2, joineRML, lcmm
因果推断:   MatchIt, WeightIt, geepack, ivtools, EValue, grf
缺失数据:   mice, Amelia, missForest
可重复报告: knitr, rmarkdown, quarto
```

#### 5.2.4 统计审查检查清单

提交给统计学家审查的每篇论文需通过以下核对：

- [ ] 研究设计是否与分析方法匹配？
- [ ] 样本量/功效是否在方法部分报告？
- [ ] 连续变量是否说明正态性检验方法与处理方式（转换/非参数）？
- [ ] 缺失数据是否报告了缺失率与处理方法？
- [ ] 模型假设是否检验（比例风险假设、线性假设、多重共线性）？
- [ ] 多重比较是否校正？
- [ ] 区分度与校准度是否同时报告？
- [ ] 置信区间是否报告（不只是 p 值）？
- [ ] 结果解读是否区分了统计显著性与临床重要性？
- [ ] 局限性部分是否讨论了残余混杂与可推广性？

### 5.3 输入/输出规范

| | 内容 |
|---|---|
| **输入 (from)** | 研究假说 + 研究设计草案（→ PI + 临床研究员）、建模方案（→ 计算生物学）、数据字典（→ 数据工程师） |
| **输出 (to)** | 统计分析计划 SAP（→ 全员）、统计方法部分初稿（→ 写作编辑）、模型评估与诊断报告（→ 计算生物学 + ML 工程师） |

---

## 6. 数据工程师 (Data Engineer)

### 6.1 核心职责

- 构建多源医学数据 ETL 管道
- 数据清洗、标准化（OMOP CDM）、去标识化
- 数据库管理与高性能计算环境维护
- 数据安全合规

### 6.2 工作方法

#### 6.2.1 老年医学数据源 ETL 标准流程

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ 数据源        │ →   │ 数据湖 (Raw Zone) │ →   │ 标准化层          │
│              │     │                  │     │ (OMOP CDM 对齐)   │
├──────────────┤     ├──────────────────┤     ├──────────────────┤
│ EHR/电子病历   │     │ 原始格式存储      │     │ person            │
│ 队列调查问卷   │     │ 只读, 不修改      │     │ observation       │
│ 实验室检验     │     │ 带时间戳 + MD5    │     │ measurement       │
│ PACS 影像      │     │                  │     │ condition_occur.. │
│ 组学平台       │     │                  │     │ drug_exposure     │
│ 可穿戴设备     │     │                  │     │ procedure_occur.. │
│ 公共数据库     │     │                  │     │ visit_occurrence  │
└──────────────┘     └──────────────────┘     └──────────────────┘
                                                       │
                                                       ▼
用户使用 ←── 数据集市 (Mart) ←── 特征层 (Feature Store) ←
 (分析就绪数据框)     (ML 建模就绪)
```

#### 6.2.2 数据质量检查框架

**DQ-CARE 五维质量评估**：

| 维度 | 检查内容 | 自动化方法 |
|------|----------|-----------|
| **C**ompleteness | 每个变量的缺失率 | 编写 DQ 脚本自动扫描所有变量 |
| **A**ccuracy | 值是否在合理范围？ | 规则引擎: 年龄 0-120, SBP 50-300, BMI 10-70 |
| **R**eliability | 重复测量的一致性 | ICC (组内相关系数) 自动计算 |
| **E**xplicability | 变量的元数据完整性 | 字典覆盖率检查: 每个变量都有 label + unit + source |

**实施方式**——使用 Great Expectations 或自定义 DQ 框架：

```python
# 示例: 定义数据质量期望
frailty_data_expectations = {
    "expect_column_values_to_not_be_null": ["subject_id", "age", "sex"],
    "expect_column_values_to_be_between": {
        "age": {"min_value": 60, "max_value": 120},
        "bmi": {"min_value": 10, "max_value": 70},
        "sbp": {"min_value": 60, "max_value": 250},
    },
    "expect_column_values_to_be_in_set": {
        "sex": [0, 1],
        "frailty_status": [0, 1, 2],  # 0=robust, 1=pre-frail, 2=frail
    },
    "expect_column_pair_values_A_to_be_smaller_than_B": {
        ("date_of_enrollment", "date_of_followup"),
    },
}
```

**数据质量报告自动生成**：每次数据更新后自动输出 DQ 报告 → 发送至数据工程师 + 临床研究员 + 统计学家。

#### 6.2.3 OMOP CDM 核心映射规则

**老年医学常用变量 OMOP 映射速查**：

| 临床变量 | OMOP 表 | OMOP 字段示例 |
|----------|---------|-------------|
| 衰弱状态 | observation | concept_id 对应 SNOMED frailty concepts |
| Fried 衰弱表型评分 (0-5) | measurement | measurement_concept_id + value_as_number |
| 握力 (kg) | measurement | 对应 LOINC 编码 |
| 步速 (m/s) | measurement | 对应 LOINC 编码 |
| BMI | measurement | concept_id 3038553 |
| 收缩压 | measurement | concept_id 3004249 |
| 舒张压 | measurement | concept_id 3012888 |
| MMSE 评分 | measurement | concept_id 3005116 |
| GDS-15 评分 | measurement | 对应 observation |
| 糖尿病诊断 | condition_occurrence | concept_id 201820 |
| 高血压诊断 | condition_occurrence | concept_id 316866 |
| 多重用药 | drug_exposure | 统计 drug_exposure 记录数 |
| 跌倒事件 | observation | concept_id 对应的 SNOMED fall code |

#### 6.2.4 常用公共数据库接入指南

| 数据库 | 国家/地区 | 人群 | 年龄范围 | 数据获取方式 | 老年医学研究优势 |
|--------|----------|------|----------|-------------|----------------|
| CHARLS | 中国 | 社区居住 | ≥45 | 官网申请 + DUA | 全国代表性, 衰弱/认知/经济 |
| CLHLS | 中国 | 社区居住 | ≥65 (百岁老人超采样) | 官网申请 + DUA | 高龄老人, 长期随访 |
| HRS | 美国 | 社区居住 | ≥50 | 官网注册下载 | 与 CHARLS 可联合分析 |
| ELSA | 英国 | 社区居住 | ≥50 | UK Data Service | 欧洲队列 |
| UK Biobank | 英国 | 社区居住 | 40-69 | 研究申请 | 基因 + 影像 + EHR 链接 |
| NHANES | 美国 | 社区居住 | 全年龄 | 公开下载 | 体检 + 实验室全面 |
| MIMIC-IV | 美国 | 住院 | 全年龄 | PhysioNet 申请 | ICU 老年患者的 EHR |

**接入流程标准化**：
1. 数据发现：评估目标数据库是否包含研究所需变量
2. DUA/DTA 签署：数据使用协议
3. 数据下载/API 接入：按来源规范操作
4. 质量检查：运行 DQ-CARE 框架
5. 数据字典编制：中英文双语

#### 6.2.5 数据安全与合规操作清单

- [ ] 研究数据与标识数据物理分离存储
- [ ] 访问权限按角色最小化分配（PI=全部, 研究员=分析数据集, 助理=脱敏后数据集）
- [ ] 数据传输使用加密通道（SFTP/HTTPS）
- [ ] 个人隐私数据（姓名、身份证号、住址、电话）在分析前剥离
- [ ] 分析环境不连接公网（或使用 VDI）
- [ ] 数据处理日志保留（谁、何时、对哪个数据集、做了什么操作）
- [ ] 符合《个人信息保护法》与《数据安全法》要求
- [ ] 国际数据传输符合《数据出境安全评估办法》

### 6.3 输入/输出规范

| | 内容 |
|---|---|
| **输入 (from)** | 临床变量需求列表（→ 临床研究员 + 计算生物学）、数据源信息（→ PI）、特征需求（→ ML 工程师） |
| **输出 (to)** | 清洗后数据集 + 数据字典 + DQ 报告（→ 全员）、标准化表型数据框（→ ML 工程师 + 统计学家） |

---

## 7. 学术写作与编辑专员 (Scientific Writer & Editor)

### 7.1 核心职责

- 根据研究结果撰写论文初稿（IMRaD 结构）
- 语言润色与目标期刊格式化
- 管理参考文献与图表
- 协调投稿流程
- 追踪领域期刊动态

### 7.2 工作方法

#### 7.2.1 论文生产流水线 — 甘特图模式

```
Week     Task                              Owner
──────────────────────────────────────────────────
W-4      确定目标期刊 + 阅读 Author Guidelines      Writer
W-3      完成 Results 初稿（图表 + 文字）            Writer + 计算生物
W-2      完成 Methods 初稿                           Writer + 统计
W-1      完成 Introduction                          Writer
W0       完成 Discussion                            Writer + 临床
W1       全体审阅 + 修改                             全员
W2       PI 终审 + 最终修改                          PI + Writer
W3       格式整理 + 投稿                             Writer
```

#### 7.2.2 各章节写作标准模板

**Title** — 遵循 "PICO + Method + Data" 公式：
```
[方法] [方法描述] [预测什么] [在哪个队列]: [一项什么类型的研究]
e.g. "Machine Learning Predicts 2-Year Frailty Transitions in CHARLS: 
       A Prospective Cohort Study"
```

**Abstract — 结构化 250-300 词**：
```markdown
Background:  2 句 — (1) 疾病负担 + (2) 知识缺口
Methods:     3 句 — 数据来源、主要方法、主要分析
Results:     4 句 — 人群特征 + 主要发现 + 关键数值
Conclusion:  1 句 — 一句话总结 + 临床/公共卫生含义
```

**Introduction — 三段漏斗式**：
```
Paragraph 1: 老龄化/疾病负担的宏观背景 (3-4 句)
Paragraph 2: 现有研究的缺口 → 为什么现有方法不够 (4-5 句, 核心段落)
Paragraph 3: 本研究的目标 + 假说 (2-3 句)
  - "In this study, we aimed to [动词] [目标] using [方法] in [数据]"
```

**Methods — 五段式 (STROBE/TRIPOD 对齐)**：
```
1. Study Design and Setting
2. Study Population (纳入排除标准 + 流程图)
3. Variables (Outcome + Predictors 的定义与测量)
4. Statistical Analysis (按 SAP 简化)
5. Sensitivity Analysis
```

**Results — 遵循 TEXT-TABLE-FIGURE 原则**：
```
Table 1: Baseline characteristics → 文字描述 2-3 句
Figure 1: 主要发现 → 文字描述 1 段
Table 2: 模型性能 → 文字描述 1 段
Figure 2: 亚组/敏感性分析 → 文字描述 1 段
```

**Discussion — 四段式**：
```
1. 主要发现总结 (1 段) — 不重复 Results 中的数字
2. 与已有文献比较 (2 段) — 一致/不一致各一段
3. 临床与公共卫生含义 (1 段)
4. 优势与局限性 (1 段, 坦诚且主动)
```

**Conclusion — 独立章节**：与 Discussion 平级，1-2 句直接回答研究问题。

#### 7.2.3 图表制作标准

**Table 1 — 基线特征表规范**（使用 R `tableone` 或 `gtsummary`）：

```
Table 1. Baseline Characteristics of Study Participants
        ┌──────────────────────────────────────┐
        │ Characteristic    Overall    按分组…  │
        │                   (N=xxxx)           │
        ├──────────────────────────────────────┤
        │ Age, mean (SD)    72.3 (6.8)         │
        │ Female, n (%)     2876 (52.3%)        │
        │ BMI, median [IQR] 23.5 [21.2-26.1]   │
        │ ...                                  │
        └──────────────────────────────────────┘
        SMD (Standardized Mean Difference) 标注
        组间比较 p 值 (如果适用)
```

**Figure 1 — Graphical Abstract**：
- 左：研究人群/数据源
- 中：方法（简化图示）
- 右：主要发现（用箭头或数字突出）

#### 7.2.4 目标期刊投稿策略

**计算老年医学常用目标期刊分级**：

| 级别 | 期刊 | IF (2024) | 特点 | 审稿周期 |
|------|------|-----------|------|----------|
| Tier 1 | Lancet Healthy Longevity | ~15 | 偏好 RCT + 大型队列 | 2-4 周 |
| Tier 1 | Nature Aging | ~15 | 偏好机制 + 新技术 | 2-4 周 |
| Tier 2 | GeroScience | ~8 | 精准匹配衰老+计算 | 4-8 周 |
| Tier 2 | Aging Cell | ~7 | 偏好有生物学机制 | 4-8 周 |
| Tier 2 | J Gerontol A Biol Sci Med Sci | ~6 | 医学生物学兼顾 | 4-8 周 |
| Tier 2 | J Am Geriatr Soc (JAGS) | ~5 | 临床老年医学旗舰 | 6-10 周 |
| Tier 3 | J Am Med Dir Assoc (JAMDA) | ~7 | 偏好长期照护/衰弱 | 4-8 周 |
| Tier 3 | BMC Geriatrics | ~4 | 开放获取, 接受度高 | 4-8 周 |
| Tier 3 | Frontiers in Medicine | ~4 | 快速发表 | 2-6 周 |

**转投策略**：被拒后 48 小时内完成重新格式化并转投下一期刊，绝不留稿超过一周。

#### 7.2.5 Cover Letter 标准模板

```markdown
Dear Editor,

We submit "[论文标题]" for consideration in [期刊名].

[1-2 句说明研究的重要性 — 为什么老年医学领域需要这个研究]

[1-2 句说明方法创新 — 这个研究用了什么新方法/新数据]

[1 句说明关键发现]

We believe this manuscript aligns well with [期刊名]'s scope, 
particularly its focus on [期刊的一个征稿方向].

This manuscript has not been published elsewhere and is not under 
consideration by another journal. All authors have approved the 
manuscript and agree with its submission to [期刊名].

We suggest the following reviewers: [3-5 名建议审稿人]
We request the exclusion of: [0-2 名需要排除的审稿人]

Sincerely,
[通讯作者]
```

#### 7.2.6 文献管理规范

- **管理工具**：Zotero 团队共享库
- **命名规范**：`FirstAuthorLastName_Year_Journal_ShortTitle`
- **文件夹结构**：
  ```
  Zotero/
  ├── 01_Aging_Clocks/
  ├── 02_Frailty_Prediction/
  ├── 03_Multimorbidity_Clustering/
  ├── 04_Sarcopenia_ML/
  ├── 05_Fall_Risk/
  ├── 06_Cognitive_Decline/
  ├── 07_Methodology_ML_Stats/
  ├── 08_Cohort_Data_Sources/
  └── 09_Team_Papers/
  ```
- **引用格式**：在投稿前使用 Zotero 输出目标期刊的引用格式（CSL），不手动排版参考文献

### 7.3 输入/输出规范

| | 内容 |
|---|---|
| **输入 (from)** | 分析结果 + 图表（→ 计算生物学 + ML 工程师 + 统计学家）、目标期刊指令（→ PI）、临床解读（→ 临床研究员） |
| **输出 (to)** | 论文初稿（→ 全员审阅）、投稿包（manuscript + cover letter + 补充材料）、 Revision 响应（→ 全员） |

---

## 8. 科研助理 / 博士生 (Research Assistant / PhD Student)

### 8.1 核心职责

- 文献综述与领域动态跟踪
- 数据标注与质量控制
- 基线实验执行
- 图表初稿制作
- 学位论文与团队研究方向对齐

### 8.2 工作方法

#### 8.2.1 系统文献综述标准流程 (PRISMA 2020)

```
Phase 1: 检索策略设计
  Step 1: 在 PubMed, Web of Science, Scopus, CNKI 中检索
  Step 2: 检索式 = MeSH terms + 自由词, 经信息专家审核
  Step 3: 补充检索: 参考文献回溯 + 灰色文献

Phase 2: 筛选
  Step 4: 去重 (Endnote/Zotero → 自动去重 → 手动去重)
  Step 5: 标题/摘要筛选 (2 名独立筛选者, Cohen's κ > 0.6)
  Step 6: 全文筛选 (同上, 分歧通过讨论或第三人裁决)

Phase 3: 数据提取
  标准提取表:
    - 研究特征: 作者/年份/国家/设计/样本量/随访时间
    - 人群: 年龄/性别比/纳入排除标准
    - 方法: 模型类型/特征/验证方式/软件
    - 结果: AUC/敏感度/特异度/校准
    - 偏倚风险: PROBAST (预测模型) / QUADAS-2 (诊断)/ NOS (队列)

Phase 4: 质量评价
  - 预测模型: PROBAST (Prediction model Risk Of Bias ASsessment Tool)
  - 诊断准确性: QUADAS-2
  - 观察性研究: Newcastle-Ottawa Scale

Phase 5: 合成
  - 定量: Meta-analysis (如果 ≥3 篇研究同质性可接受) 或 
  - 定性: Narrative synthesis

Phase 6: 报告
  - PRISMA 2020 流程图 + 检查清单
```

#### 8.2.2 文献追踪与知识管理

**a) 每周自动化文献推送设置**：

- PubMed: 设置 3-5 个核心搜索 alerts
  ```
  Alert 1: ("frailty"[Mesh] OR "frail elderly"[Mesh]) AND 
           ("machine learning" OR "deep learning" OR "artificial intelligence")
  Alert 2: ("aging"[Mesh] OR "healthy aging"[Mesh]) AND 
           ("epigenetic clock" OR "biological age" OR "DNA methylation age")
  Alert 3: ("geriatric assessment"[Mesh]) AND 
           ("prediction model" OR "risk prediction" OR "prognostic model")
  ```
- arXiv: 订阅 cs.LG + q-bio + stat.ML
- bioRxiv/medRxiv: 关注 Geroscience / Epidemiology 板块
- Google Scholar: 关注领域核心作者

**b) 文献阅读笔记标准格式** (为后续自动化打好结构化基础)：

```yaml
paper:
  title: ""
  authors: ""
  year: ""
  journal: ""
  doi: ""
  
summary:
  what_they_did: ""        # 一句话核心
  data_source: ""          # 用了什么数据
  method: ""               # 主要方法
  key_result: ""           # 最关键的数字
  comparison_to_us: ""     # 和我们的关系

technical_details:
  sample_size: ""
  age_range: ""
  outcome_definition: ""
  model_type: ""
  features_used: ""
  performance_metrics: ""
  validation_strategy: ""

relevance:
  score: 1-5               # 与我们研究的相关度
  category: ""             # 属于哪个子领域
  actionable: ""           # 我们可以借鉴什么
  gaps: ""                 # 我们可以改进什么
```

**自动化潜力**：该结构化的笔记格式适合训练/微调一个文献摘要 agent。

#### 8.2.3 基线实验执行指南

接手新项目时的标准操作流程：

```
Day 1-2: 数据熟悉
  - 读取数据字典, 理解每个变量的定义与编码
  - 运行 describe() / summary() 获取各变量基础分布
  - 绘制缺失值热图 → 理解缺失模式
  - 绘制相关性矩阵 → 理解变量间关系

Day 3-4: 基线模型建立
  - 实现最简 baseline (Logistic Regression 或 Cox PH + 年龄+性别)
  - 实现文献中已有方法的复现
  - 记录 baseline 性能作为后续改进锚点

Day 5: 报告
  - 向研究员呈现 EDA 结果 + baseline 性能
  - 讨论下一步改进方向
```

#### 8.2.4 科研写作训练路径

```
Phase 1 (博一): 参与文献综述 → 产出一篇系统综述/荟萃分析
Phase 2 (博二): 辅助分析 + 撰写 Methods 和 Results → 成为论文共同作者
Phase 3 (博三): 独立负责一个子课题 → 撰写完整初稿 → 成为第一作者
Phase 4 (博四): 自主提出研究假说 → 独立完成全流程 → 博士论文
```

### 8.3 输入/输出规范

| | 内容 |
|---|---|
| **输入 (from)** | 研究方向指示（→ PI）、具体任务分配（→ 各研究员）、实验方案（→ 计算生物学 + ML 工程师） |
| **输出 (to)** | 文献综述报告 + 阅读笔记（→ 全员共享）、EDL 报告（→ 计算生物学 + 统计学家）、图表初稿（→ 写作编辑） |

---

## 9. 岗位接口矩阵

### 9.1 输入依赖关系

| 接收方 ↓ / 提供方 → | PI | 计算生物学 | 临床研究员 | ML工程师 | 统计学家 | 数据工程师 | 写作编辑 | 科研助理 |
|---------------------|-----|----------|----------|--------|--------|----------|--------|--------|
| **PI** | — | 进展报告 | 临床需求 | 技术可行性 | 方法审查 | 数据可用性 | 投稿建议 | 文献简报 |
| **计算生物学** | 研究方向 | — | 临床问题定义 | 模型实现 | SAP | 数据字典 | — | 文献笔记 |
| **临床研究员** | 研究优先级 | 模型结果 | — | 特征解释 | 统计结果 | 数据质量 | — | 文献笔记 |
| **ML工程师** | 任务指定 | 建模方案 | 表型定义 | — | 评估指标 | 特征数据 | — | 基线代码 |
| **统计学家** | 研究假说 | 模型方案 | 研究设计 | 实验记录 | — | 数据字典 | — | EDA报告 |
| **数据工程师** | 数据策略 | 数据需求 | 变量需求 | 特征需求 | 分析需求 | — | — | 数据标注 |
| **写作编辑** | 投稿目标 | 方法+结果 | 临床解读 | 图表 | 统计方法 | 数据来源 | — | 图表初稿 |
| **科研助理** | 任务分配 | 指导 | 指导 | 指导 | 指导 | 数据提取 | 写作指导 | — |

### 9.2 自动化编排可行性评估

基于上述岗位的「输入→工作方法→输出」标准化描述，未来可通过 LLM agent 编排实现以下自动化：

| 自动化程度 | 场景 | 涉及的岗位接口 |
|-----------|------|--------------|
| **高自动化** (LLM 可独立完成) | 文献检索 + 结构化摘要生成 | 科研助理 → 全员 |
| **高自动化** | 数据质量报告生成 | 数据工程师 → 统计学家 + 临床 |
| **高自动化** | 统计分析计划 (SAP) 初稿 | 统计学家（基于研究设计模板）|
| **高自动化** | 论文初稿生成 (Methods + Results) | 写作编辑（基于分析输出）|
| **中自动化** (LLM + 人工审核) | 特征工程 + 基线模型训练 | ML 工程师 + 计算生物学 |
| **中自动化** | 模型可解释性报告 | ML 工程师 → 临床研究员 |
| **中自动化** | 投稿期刊推荐 + Cover Letter 初稿 | 写作编辑 → PI |
| **低自动化** (需高人工判断) | 研究方向的 FRAME 决策 | PI |
| **低自动化** | 临床问题 → 计算问题转化 | 临床研究员 |
| **低自动化** | 因果推断方法选择与解读 | 统计学家 |

---

## 附录 A：团队协作工具链推荐

| 用途 | 推荐工具 | 备注 |
|------|---------|------|
| 代码版本管理 | Git (GitHub/GitLab) | 私有仓库 |
| 数据版本管理 | DVC | 与 Git 集成 |
| 实验追踪 | MLflow | 自托管 |
| 文献管理 | Zotero (Group Library) | 免费 |
| 项目管理 | Notion / 飞书多维表格 | 任务追踪 |
| 论文写作 | Overleaf / LaTeX | 协作编辑 |
| 图表绘制 | R ggplot2 / Python matplotlib+seaborn / BioRender | |
| 沟通 | 企业微信 / Slack + 定期组会 | |
| 计算环境 | Slurm 集群 / 云计算 (阿里云/AWS) | |

## 附录 B：关键会议节奏

| 会议 | 频率 | 时长 | 参与者 | 内容 |
|------|------|------|--------|------|
| 全员组会 | 每周 | 1.5h | 全员 | 文献报告 (15') + 项目进展 (30') + 问题讨论 (30') |
| 计算组例会 | 每周 | 1h | 计算生物学 + ML 工程 + 统计 + 数据工程 | 技术细节讨论 |
| 临床-计算对接会 | 每两周 | 1h | 临床研究员 + 计算生物学 | 临床问题对齐 |
| 论文进展会 | 每两周 | 1h | 写作编辑 + 在写论文的团队成员 | 稿件进度检查 |
| 一对一 (PI) | 每周 | 30' x N | PI + 每人 | 个人发展 + 项目推进 |
| 季度战略会 | 每季度 | 3h | PI + 研究员级别 | FRAME 方向评估 |

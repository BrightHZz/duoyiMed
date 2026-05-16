# PI 裁决书

**项目**: prostate-cancer-metastasis-pattern
**裁决方**: PI (urology 事业部首席研究员)
**裁决时间**: 2026-05-14
**基于**: 研讨厅辩论纪要 (debate-minutes.md) + 三方意见书

---

## 裁决结果总览

| # | 问题 | 裁决 | 胜出方案 |
|:--:|------|:--:|------|
| Q1 | Train/Test 切分 | **方案 A — 2010-2019/2020-2023** | BS |
| Q2 | MICE 策略 | **折中方案: 全局 MICE + era 协变量** | BS 方案 + CR 要素 |
| Q3 | 三分类补充 | **有条件采纳: 先验 N → 再决定** | BS 折中方案 |
| Q4 | COVID 标记 | **covid_flag (方案 A), 不排除** | BS |

---

## 裁决详文

### Q1: Train/Test 切分 — 采纳方案 A (BS)

**裁决**: 2010-2019 train, 2020-2023 test。不排除 2020 年数据。

**理由**:
1. 时间 hold-out 的统计原理是评估模型在"未来"数据上的泛化能力。排除 2020 会模糊 COVID 的真实影响——模型如果无法处理 2020 的病例混合变化，这正是我们需要知道的信息
2. 2020 年 M1 前列腺癌诊断量下降（约 56,000 vs 年均 62,000+），但 2021-2023 急剧反弹至 68,000。2020 的"异常"恰恰是对模型鲁棒性的真实检验
3. 排除 2020 会损失约 4,000 M1 患者——对于 transfer learning/hyperparameter tuning 的 test set 来说，样本量不是问题，但年份连续性比年份"干净度"更重要

**附带指令**: 在 train 集中创建 `covid_flag` 列 (诊断年份 = 2020 → 1, 否则 0)。Phase 6 中报告 2020 vs 其他年份的模型性能亚组分析。

---

### Q2: MICE 填补策略 — 采纳折中方案

**裁决**: 全局 MICE (m=5), 预测矩阵包含 `era` 主效应 + `year_of_diagnosis` 连续变量。

**理由**:
1. CR 关于"PSA 缺失机制在 Era 间不同"的临床观点完全正确——2018 年前 PSA 不常规收集
2. BS 关于"分层 MICE 样本量不足"的统计观点同样正确——Era 1 单独填补会因样本量小而不稳定
3. **折中方案**: 全局 MICE，但预测矩阵中加入 `year_of_diagnosis` (连续) 作为 predictor。连续年份变量捕获了 PSA 收集率的渐变趋势，比二分类 era 更精细地建模缺失机制
4. MICE imputation model 使用: `age, race, marital, income, stage, gleason, era, year_of_diagnosis, survival_months, outcome`

**附带指令**: 填补后报告每个填补变量的诊断图 (density plot: original vs imputed, by era) → Phase 6 补充材料。

---

### Q3: 三分类补充分析 — 有条件采纳 BS 折中方案

**裁决**: Phase 3 数据探索后决定。先计算三组实际样本量:
- Bone-only: 预期 ~50,000 ✅ 充分
- Visceral only (无骨): 预期 ~3,000-5,000 ⚠️ 待确认
- Both (Bone+Visceral): 预期 ~8,000-10,000 ✅ 充分

**决策树**:
```
IF Visceral only N ≥ 2,000:
    → 三分类分析纳入论文 (Table + KM + Cox)
ELIF Visceral only N ≥ 1,000 AND < 2,000:
    → 三分类分析纳入补充材料 (Supplementary)
ELSE:
    → 仅二分类，Discussion 中说明 Visceral only 样本量不足
```

**附带指令**: CR 负责在三分类分析中定义 "Visceral only" vs "Both" 的临床区分意义。如果两组的生存曲线差异不显著，应在论文文本中报告负结果（而非只报告显著结果）。

---

### Q4: COVID 标记 — 采纳方案 A (BS)

**裁决**: 不排除 2020，添加 `covid_flag`。

**理由**: 同 Q1。附加考虑:
- 2020 年 M1 病例数下降（COVID 导致筛查延迟），但下降在 2021 年迅速反弹。如果排除 2020 却不排除 2021-2022 (post-COVID catch-up 效应期)，选择性排除缺乏方法论依据
- 更好的做法: 保留全 2020-2023，在 Sensitivity Analysis 中排除 2020 作为稳定性检查，报告 train/val/test AUC 是否有实质变化

---

## 最终方案锁定

以下方案已锁定，直接进入 Phase 3 执行:

### 数据切分 (锁定)

```
Train:      2010-2019  (N ≈ 55,000 M1)
Test:       2020-2023  (N ≈ 21,000 M1)
COVID flag: 2020=1, else=0 (加入训练特征)
```

### 转移分类 (锁定)

```
主分析 (2010+): Bone-only  vs  Visceral ± Bone
补充分析 (2016+): Bone-only, LN-only, Visceral ± Bone
三分类探索: 待 Phase 3 数据探索后决定
```

### ML 模型 (锁定)

```
主模型: XGBoost (n_estimators=200, 5-fold CV, RandomizedSearchCV)
Baseline: LogisticRegression (L2)
子模型: Model_full + Model_bone + Model_visceral
Target: 3-year OS (binary)
```

### 缺失处理 (锁定)

```
方法: MICE (m=5, year_of_diagnosis 作为连续 predictor)
填补变量: PSA, Gleason_clinical
不填补: Gleason_pathological (仅用 clinical)
```

### 统计分析 (锁定)

```
主要比较: Cox HR (Bone-only vs Visceral)
次要比较: Fine-Gray sHR (CSS)
敏感性:  PSM 1:1 matching + Era-stratified + E-value
校正:    Bonferroni (主要), FDR (次要)
```

---

## SAP 签批

| 签批项 | 状态 |
|--------|:--:|
| 研究设计 (Cohort, 纳入/排除) | ✅ 已签批 |
| 结局定义 (3-yr OS, CSS) | ✅ 已签批 |
| 暴露定义 (Bone-only vs Visceral ± Bone) | ✅ 已签批 |
| 协变量集 (20 features) | ✅ 已签批 |
| 缺失处理 (MICE + year predictor) | ✅ 已签批 |
| 模型架构 (XGBoost + LR) | ✅ 已签批 |
| 验证方案 (Time hold-out 2020-2023) | ✅ 已签批 |
| 统计方法 (Cox + Fine-Gray + ML) | ✅ 已签批 |
| 亚组分析 (5 prespecified subgroups) | ✅ 已签批 |
| 发表策略 (Euro Urol → Clin GU Cancer) | ✅ 已签批 |

---

*PI (urology) 产出于 Phase 2 Round 3*
*Gate 2: ✅ PASS — 进入 Phase 3 执行/内部验证*

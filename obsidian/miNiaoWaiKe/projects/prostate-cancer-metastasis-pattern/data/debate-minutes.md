# 研讨厅辩论纪要

**项目**: prostate-cancer-metastasis-pattern
**辩论阶段**: Phase 2 Round 2
**主持人**: Orchestrator (编排器)
**参与方**: CB=Computational Biologist, BS=Biostatistician, CR=Clinical Researcher
**日期**: 2026-05-14

---

## 1. 共识清单 ✅ (无需裁决，直接进入 SAP)

| # | 议项 | CB | BS | CR | 共识方案 |
|:--:|------|:--:|:--:|:--:|------|
| 1 | **模型选择** | XGBoost+LR | 同意 | 同意 | XGBoost 主模型 + LR baseline |
| 2 | **主要对比** | Bone vs Visceral | 同意 | 同意 | Bone-only vs Visceral ± Bone 二分类 |
| 3 | **ML 预测窗口** | 3 年 OS* | **3 年 OS** | **3 年 OS** | 3 年 OS (事件率 ~60%) |
| 4 | **Train/Test 划分原则** | 未明确 | 年份切分 | 年份切分 | **按年份时间切分** (非随机) |
| 5 | **SMOTE 使用** | ❌ 反对 | ❌ 反对 | 未表态 | **禁止 SMOTE** |
| 6 | **n_jobs 约束** | 2 | 同意 | 同意 | 全局 n_jobs=2 |
| 7 | **外验方案** | 时间 hold-out | 时间 hold-out | 时间 hold-out | 2020-2023 时间验证 |
| 8 | **Gleason 编码** | ISUP GG | 同意 | **ISUP GG** | ISUP Grade Group 1-5 |
| 9 | **内存安全** | Preflight scan | 同意 | — | Phase 3 执行前 preflight |
| 10 | **主要结局** | OS | OS + CSS | OS + CSS | OS 主, CSS 次 (Fine-Gray) |
| 11 | **治疗变量** | 协变量 | 协变量 | 协变量 | 调整变量, 不做因果推断 |
| 12 | **治疗时代分层** | Era 1 vs 2 | 同意 | 同意 | 敏感性分析: 2010-2015 vs 2016-2023 |
| 13 | **模型评估指标** | 全量 11 项 | 补充 NRI+DCA | 同意 | 统一指标集 + NRI + DCA |
| 14 | **PSM 敏感性分析** | 未提 | 1:1 PSM | 同意 | PSM 作为 OS 敏感性分析 |

---

## 2. 分歧清单 ⚠️ (需要 PI 裁决)

### 分歧 1: Train/Validation/Test 精确切分点

| 方案 | 提出方 | 详情 |
|------|:--:|------|
| **A**: 2010-2019 train / 2020-2023 test | BS | 简单二分，N_test ≈ 25,000 |
| **B**: 2010-2018 train / 2019 val / 2021-2023 test, 2020 排除 | CR | COVID 年异常，排除 2020 以避免混淆 |

**BS 反驳**: 2020 排除会损失约 56,000 患者中的约 4,000 M1，且 COVID 效应是真实世界的一部分（且 2020 前列腺癌病例数波动已经在年份趋势分析中可见），如果模型要在未来使用，应该能处理 COVID 级的波动。**但如果 CR 坚持**，可以将 2020 标记为 `covid_flag` 而非删除。

**主持人分析**: 这是临床判断 vs 统计效率的典型矛盾。BS 的担忧 (丢失 N) 与 CR 的担忧 (数据质量) 都有道理。

### 分歧 2: MICE 填补策略

| 方案 | 提出方 | 详情 |
|------|:--:|------|
| **A**: 全局 MICE | BS | 标准 MICE (m=5)，使用所有协变量 |
| **B**: Era-分层 MICE | CR | Era 1 和 Era 2 分别运行 MICE |

**BS 反驳**: Era 分层 MICE 在每个 era 内样本量减半，MICE 对样本量敏感，分半后 imputation model 可能不稳定。如果担心 era 与缺失机制的交互，应在 MICE 预测矩阵中加入 `era` 作为主效应，而非分层运行。

**主持人分析**: 方案 A 中加入 `era` 作为预测变量是折中方案，既保留了全样本的 imputation 效率，又纳入了 era 信息。

### 分歧 3: 三分类补充分析 (Bone-only / Visceral only / Both)

| 方案 | 提出方 | 详情 |
|------|:--:|------|
| **A**: 仅二分类 | CB | Bone-only vs Visceral ± Bone |
| **B**: 二分类 + 三分类补充 | CR | 加 Bone-only vs Visceral only vs Both (Bone+Visceral) |

**BS 立场**: 三分类中 "Visceral only" (无骨) 的 N 可能很小（预期 2,000-3,000），功效可能不足。可以先计算三分类各组 N，如果 ≥1,000 则纳入补充分析。

**主持人分析**: 取决于实际数据分布。建议在 Phase 3 数据探索后决定。

### 分歧 4: 亚组分析的统计校正

| 方案 | 提出方 | 详情 |
|------|:--:|------|
| **A**: FDR (Benjamini-Hochberg) | BS | 所有次要分析用 FDR q=0.05 |
| **B**: 探索性 (不校正) + 描述为 hypothesis-generating | CR (隐含) | CR 提出 5 个亚组但未提校正方案 |

**主持人分析**: 这不是真正的分歧——CR 和 BS 对"亚组分析需要小心解释"有共识，只是对统计方法的严格程度有不同偏好。FDR 是标准方法。

---

## 3. 需 PI 裁决的 4 个关键问题

| # | 问题 | 方案 A | 方案 B | 推荐 |
|:--:|------|--------|--------|:--:|
| Q1 | **Train/Test 切分** | BS: 2010-19/2020-23 | CR: 排除 2020 | ← PI 裁决 |
| Q2 | **MICE 策略** | BS: 全局+era协变量 | CR: era-分层 | ← PI 裁决 |
| Q3 | **三分类补充** | CB: 仅二分类 | CR: 二分类+三分类 | ← PI 裁决 |
| Q4 | **COVID 2020 标记** | BS: covid_flag | CR: 排除 | ← PI 裁决 |

---

*辩论主持人 (Orchestrator) 产出于 Phase 2 Round 2*
*下一步: PI 基于本纪要做出裁决 (Round 3)*

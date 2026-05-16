# 选题文献预检报告

**项目**: prostate-cancer-metastasis-pattern
**执行者**: research-assistant
**日期**: 2026-05-14
**检索范围**: 2020-2025, SEER 前列腺癌 M1 转移模式预后

---

## 1. 对标论文 (≥5 篇)

### 1.1 最接近的研究 — Labe et al. (2022)

| 属性 | 值 |
|------|-----|
| 标题 | Identification and Validation of the Prognostic Impact of Metastatic Prostate Cancer Phenotypes |
| 期刊 | Clinical Genitourinary Cancer (IF 3.9) |
| 数据 | NCDB (train) + SEER 2010-2014 (validation), n=13,818 |
| 方法 | 三组转移表型分类 → KM + Cox multivariate |
| AUC/C-index | N/A (纯描述性+生存分析, 无 ML 模型) |
| 转移分类 | Bone-only (84.2%) / Nonregional LN only (10.0%) / Any visceral (5.8%) |
| 关键结果 | Visceral vs LN: HR 2.26 (2.00-2.56); Bone-only vs LN: HR 1.57 (1.43-1.72) |

**与本研究差异**: Labe 2022 仅做描述性生存分析, 未构建 ML 预测模型, 未按转移模式分层做预后因子识别。数据仅到 2014 年。

### 1.2 Kadeerhan et al. (2023)

| 属性 | 值 |
|------|-----|
| 标题 | Incidence trends and survival of metastatic prostate cancer with bone and visceral involvement: 2010-2019 |
| 期刊 | Frontiers in Oncology (IF 4.7) |
| 数据 | SEER 2010-2019, n=22,494 M1 |
| 方法 | Joinpoint 趋势分析 + KM + Cox |
| 转移分类 | M1b (bone, 84.8%) vs M1c (visceral, 15.2%) |
| 关键结果 | Median OS: 31月(bone) vs 20月(visceral); Visceral APC 12.3%/year |

**与本研究差异**: 仅二分类(bone vs visceral), 未区分 LN-only, 无 ML 建模。

### 1.3 Zhang et al. (2024)

| 属性 | 值 |
|------|-----|
| 标题 | Comparative analysis of prognosis and gene expression in prostate cancer patients with site-specific visceral metastases |
| 期刊 | Urologic Oncology (IF 2.6) |
| 数据 | SEER 2000-2019, n=8,170 |
| 方法 | Fine-Gray 竞争风险 + 基因表达分析 |
| 关键结果 | Liver HR 2.24 (1.70-2.95); Lung HR 1.30 (1.06-1.59) |

**与本研究差异**: 聚焦内脏转移亚型比较, 非全 M1 分层, 无 ML。

### 1.4 Guo et al. (2023)

| 属性 | 值 |
|------|-----|
| 标题 | Real-world progression in the survival of de novo Metastatic prostate cancer over the past decade |
| 期刊 | Urologic Oncology |
| 数据 | SEER 2004-2020, n=43,228 M1 |
| 方法 | 按 M substage (1a/1b/1c) 分析年代生存改善 |
| 关键结果 | M1a 改善最大(134.9%), 2016 后改善加速 |

**与本研究差异**: 聚焦时间趋势, 未做转移模式内预后因子识别。

### 1.5 Sun et al. (2022)

| 属性 | 值 |
|------|-----|
| 标题 | Nomograms predict survival benefits of radical prostatectomy and chemotherapy for prostate cancer with bone metastases |
| 期刊 | Frontiers in Oncology |
| 数据 | SEER 2010-2016, n=7,315 bone-metastatic |
| 方法 | Nomogram (Cox-based) |
| 关键结果 | C-index CSS: 0.712, OS: 0.702; Liver HR 2.59 (CSS) |

**与本研究差异**: 仅骨转移人群, 未比较转移模式, nomogram 非 ML。

---

## 2. 文献差距分析 (Literature Gap)

### 已有共识
- M1 转移模式存在清晰的生存梯度: LN-only > Bone-only > Visceral
- 肝转移是最致命的转移部位 (HR 2.2-2.6)
- 年代趋势显示 2016 后生存改善加速

### 研究空白 (本研究填补)

| Gap | 说明 |
|-----|------|
| **Gap 1: 无 ML 预后模型** | 所有现有研究均为 Cox 回归/nomogram，无 XGBoost 等 ML 方法构建的预测模型 |
| **Gap 2: 无转移模式内预后因子对比** | 所有研究将 met_pattern 作为协变量，无人探索不同转移模式内预后因子的异同 |
| **Gap 3: 无转移模式特异性 ML 模型** | 无人按转移模式分层训练独立模型 |
| **Gap 4: 数据陈旧** | Labe 2022 用到 2014, Kadeerhan 2023 到 2019，无人用到 2023 |
| **Gap 5: 无双重治疗时代对比** | 2016 前后治疗范式差异巨大 (docetaxel→abiraterone/enzalutamide/apalutamide triplet)，无人按治疗时代分层分析 |
| **Gap 6: 无社会经济-转移交互分析** | 收入/种族如何调节转移模式与生存的关系未被探索 |

---

## 3. 期刊趋势分析

| 期刊 | 2023-2025 M1 转移模式论文数 | 接受可能性 |
|------|:--:|:--:|
| European Urology | 1-2 (聚焦临床试验) | 中 — 需强方法学 |
| Clinical Genitourinary Cancer | 3+ (含 Labe 2022) | 高 |
| Frontiers in Oncology | 3+ | 高 |
| Urologic Oncology | 2+ | 中-高 |
| JAMA Oncology | 0 | 低 (偏临床转化) |

**建议投稿策略**: 首投 **European Urology** (ML 方法学新颖性 + 最大样本量 + 最新年份)，备选 **Clinical Genitourinary Cancer**。

---

## 4. 结论

**文献预检结论**: ✅ 领域活跃 (≥3 篇对标论文)
**新颖性确认**: ✅ 存在明确空白 (Gap 1-6)，本研究不重复已有工作
**建议**: 启动 Phase 1 Round 2，进入 FRAME 评估

---

*research-assistant 产出于 Phase 1 Round 1*

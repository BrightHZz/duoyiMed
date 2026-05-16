# PI 审查意见

**Agent**: urology/pi
**Phase**: Phase 5 Round 1 — 审查(研讨厅)
**日期**: 2026-05-10

---

## 1. 综合评估

本研究在数据约束下 (SEER 不可用, Gleason/TNM 缺失, MIMIC-III 外验不可行) 产出了一个**可发表但需精确定位**的预测模型。

### 核心优势

| 优势 | 权重 |
|------|------|
| XGBoost AUC 0.8289 ± 0.0329，明显超过 LR baseline (Δ = +0.0745) | 高 |
| 方法学完整: 5-fold CV + LASSO pre-filtering + isotonic calibration + SHAP | 高 |
| 临床可解释性强: 急性生理指标主导预测 → 合理的临床故事 | 高 |
| TRIPOD 合规: 报告了 discrimination/calibration/subgroup | 中 |
| Pipeline 可复用: 全套代码可迁移至新项目 | 中 |

### 核心劣势

| 劣势 | 权重 |
|------|------|
| 缺少 Gleason/TNM → 不能称为完整的"前列腺癌预后模型" | 高 |
| PSA 可用率仅 50.6% → 选择偏倚 | 高 |
| 外部验证不可行 → 泛化性完全未评估 | 高 |
| Top-2 特征 (lactate/albumin) 缺失率 >70% → 特征稳定性存疑 | 中 |
| 样本量中等 (n=1,233), EPV 处于边界 | 中 |

---

## 2. 研究定位与 Narrative

### 当前 Narrative (不推荐的版本)

> "我们开发了一个前列腺癌预后预测模型..."

**问题**: 这暗示模型预测的是前列腺癌的肿瘤学预后。但 Gleason/TNM 缺失使得这个 narrative 不成立。

### 推荐的 Narrative

> "我们开发了一个机器学习模型，使用 EHR 中常规可获取的实验室和人口学数据，预测住院前列腺癌患者的急性临床失代偿 (30天死亡或 ICU 入院)。"

**核心信息**:
- 这不是肿瘤预后模型 — 这是急性风险分层工具
- 它的价值在于 **EHR 中已有的数据** (不需要 Gleason/TNM) 就可以做到不错的预测
- 最强信号来自急性疾病严重度指标 (lactate/Hb/albumin) — 这既有临床直觉性，也是可操作的
- 择期入院亚组中表现最好 (AUC 0.8855) → 有具体的临床应用场景

### 学术贡献声明 (3 句话)

1. 首次在 MIMIC-IV 中系统评估 ML 模型预测前列腺癌住院患者急性不良结局的可行性
2. 发现急性生理指标 (而非肿瘤特征) 是短期预后的主要驱动力 — 这对临床风险分层有实践意义
3. 提供了可复用的 EHR-ML pipeline

---

## 3. 发表策略建议

### 目标期刊重新评估

| Tier | 期刊 | IF | 匹配度 | 建议 |
|------|------|-----|--------|------|
| Tier 1 | **Prostate Cancer and Prostatic Diseases** | 4.9 | **高** | **首投** — 专业期刊, 接受 EHR 研究 |
| Tier 2 | BMC Urology | 2.0 | 高 | 备选 |
| Tier 2 | BMC Medical Informatics & Decision Making | 3.3 | 中高 | 备选 — 信息学角度 |
| ~~Tier 1~~ | ~~J Urology~~ | 6.6 | 中低 | 外验缺失+无 Gleason → 被拒概率高 |

**调整**: J Urology 暂时不投，首投 Prostate Cancer and Prostatic Diseases。

### 审稿人可能提出的问题 (预判)

1. "为什么没有 Gleason score?" → Discussion 中直接声明 MIMIC-IV 结构化数据不包含病理报告，标注为 #1 limitation
2. "外部验证呢?" → 报告 MIMIC-III 外验不可行的原因 (人群差异) + 承诺未来多中心验证
3. "PSA 缺失 50% 怎么办?" → Table 1 对比 PSA 可用 vs 不可用 + sensitivity analysis
4. "这个模型和临床医生判断比有什么增量?" → DCA 决策曲线回答

---

## 4. Gate 5 裁决 (预判)

### 当前问题汇总

| 问题 | 来源 | 严重度 |
|------|------|--------|
| Gleason/TNM 缺失 → 需改 narrative | Clin | Critical |
| 外部验证不可行 | Biostat + PI | Critical |
| Top-2 特征缺失率 >70% | Biostat | High |
| PSA 选择偏倚 | Clin + Biostat | High |
| PR-AUC 偏低 | Biostat | Medium |
| Calibration 过度校正 | Biostat | Medium |

### 裁决方向 (预判，正式裁决在辩论纪要后)

我的预判是 ⚠️ **COND_PASS**:

**条件** (注入 Phase 6 论文撰写):
- C1: 论文标题和 narrative 必须明确定位为"急性不良结局预测"而非"肿瘤预后"
- C2: Table 1 加入 PSA 可用 vs 不可用的对比
- C3: Discussion 首段列出三大概限: 无 Gleason/TNM、无外部验证、PSA 选择偏倚
- C4: 外部验证的缺失在 Discussion 中专门用一段讨论
- C5: 补做 PSA-free model sensitivity analysis (所有 2,437 患者)
- C6: Discussion 中加入 SHAP 稳定性声明 (lactate/albumin)

---

*PI 审查完成。供研讨厅主持人汇总。*

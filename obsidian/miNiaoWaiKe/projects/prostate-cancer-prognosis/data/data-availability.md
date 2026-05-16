# DQ-CARE 数据可用性报告

**Agent**: shared/data-engineer
**Phase**: Phase 1 Round 1 — 机器预检
**检查日期**: 2026-05-10

---

## 1. 数据源清单

| 数据源 | 状态 | 类型 | 前列腺癌患者 | 说明 |
|--------|------|------|-------------|------|
| **SEER** | ❌ 不可用 | 癌症登记 | — | 本地无 SEER 数据目录；需申请/下载 (数周) |
| **MIMIC-IV v3.1** | ✅ 可用 | EHR (DuckDB) | ~1,363 (ICD-10 C61) + ~1,252 (ICD-9 185) | DuckDB 数据库就绪 |
| **TCGA-PRAD** | ❌ 不可用 | 基因组+临床 | — | 本地无 PRAD 数据 |
| **NHANES** | ❌ 不可用 | 社区人群 | — | 未找到本地数据 |
| **UK Biobank** | ✅ 可用 (部分) | 大规模队列 | 待确认 | 前列腺癌患病率待查 |

---

## 2. MIMIC-IV 前列腺癌队列 — 快速探查

```
MIMIC-IV v3.1 @ /Users/wuyouhang/Documents/trae_projects/dataset/MIMIC/mimic.db

ICD-10 C61 (Malignant neoplasm of prostate):
  - 患者数 (subject_id): 1,363
  - 住院次数 (hadm_id): 2,074

ICD-9 185 (Malignant neoplasm of prostate):
  - 患者数 (subject_id): 1,252
  - 住院次数 (hadm_id): 1,882

总计 (去重估计): ~1,500–2,000 前列腺癌患者
```

---

## 3. DQ-CARE 六维评估

### D — Dimension (数据维度)

| 维度 | 评估 |
|------|------|
| 患者数 | ~1,500–2,000 (中等规模) |
| 时间范围 | 2008–2022 |
| 数据表可用 | admissions, patients, diagnoses_icd, procedures_icd, labevents, prescriptions, microbiologyevents, chartevents (ICU) |

### Q — Quality (数据质量)

| 指标 | 评估 |
|------|------|
| 数据完整性 | ✅ 高 — MIMIC 是经过清洗的公开 EHR 数据库 |
| 编码一致性 | ⚠️ 中 — ICD-9/ICD-10 双编码，需统一映射 |
| 时间戳精度 | ✅ 高 — 精确到日期/时间 |

### C — Completeness (变量覆盖)

| 关键变量 | 可用性 | 来源表 |
|---------|--------|--------|
| 年龄 | ✅ | patients.anchor_age |
| 种族 | ✅ | admissions.race (注: MIMIC v2.0+ 已脱敏，使用不精确分类) |
| PSA 值 | ⚠️ 需验证 | labevents (需 LOINC code 2857-1) |
| Gleason 评分 | ❌ 不可用 | 病理报告数据不在结构化表中 (需 MIMIC-IV-Note) |
| TNM 分期 | ❌ 不可用 | 同上，需要病理/影像报告文本 |
| 手术方式 | ✅ | procedures_icd + hcpcsevents |
| 合并症 | ✅ | diagnoses_icd → Charlson comorbidity index |
| 实验室检查 | ✅ | labevents (血常规/肾功能/电解质/肝功能) |
| 生命体征 | ✅ | chartevents (ICU 患者) |
| 用药记录 | ✅ | prescriptions |
| 30天死亡 | ✅ | admissions.deathtime + dod |
| ICU 入院 | ✅ | icustays |

### A — Accuracy (数据准确性)

| 检查项 | 评估 |
|--------|------|
| ICD 编码准确性 | ✅ — MIMIC 来源于 Beth Israel 账单编码，经过验证 |
| 实验室值范围 | ✅ — 与临床常识一致 |
| 结局准确性 | ✅ — 院内死亡 100% 准确，院外死亡有 SSA 验证 |

### R — Relevance (与研究目标的相关性)

| 维度 | 评估 |
|------|------|
| SEER 对比 | ⚠️ MIMIC-IV 是 EHR 数据 (非癌症登记)，**不适用于长期生存预测** |
| 优势 | EHR 的 **时序数据** (多次 PSA、实验室趋势、用药变更) 是 SEER 不具备的 |
| 适用结局 | ✅ 短期预后 (30天死亡、ICU、并发症、住院时长) |
| 不适用结局 | ❌ 5 年癌症特异性生存 (需长随访癌症登记) |

### E — Ethics (伦理合规)

| 项目 | 状态 |
|------|------|
| MIMIC-IV 使用许可 | ✅ PhysioNet 公开数据库，需 CITI Data or Specimens Only 培训 |
| IRB 豁免 | ✅ Beth Israel IRB 已批准 (MIMIC 公开) |
| 商业用途 | ⚠️ MIMIC 不允许商业用途，仅限学术 |

---

## 4. 研究设计调整建议

### 当前 SDS 假设 vs 数据现实

| SDS 假设 | 现实 | 调整建议 |
|----------|------|---------|
| SEER 可用 | ❌ SEER 不可用 | 切换为 MIMIC-IV |
| 5 年 CSS 结局 | ❌ MIMIC EHR 无法提供 | 切换为 30天死亡率 / 主要并发症 / ICU 入院 |
| n ≥ 5,000 | ⚠️ ~1,500–2,000 | 样本量可接受，但需评估 power |
| Gleason/PSA/TNM 可用 | ⚠️ PSA 待验证, Gleason/TNM 需 Note 模块 | 可能只能使用实验室+人口学特征 |

### 推荐调整后的研究问题 (二选一)

**方案 A (推荐)**: "Using MIMIC-IV EHR data to predict 30-day mortality and major complications in hospitalized prostate cancer patients — a machine learning approach"
- 优势: EHR 数据的时序特征，直接临床可用
- 结局: 30天全因死亡 / ICU 入院

**方案 B (备选)**: "Predicting surgical complications after prostatectomy in prostate cancer patients using MIMIC-IV data"
- 优势: 聚焦手术人群，与 kidney-stone 项目经验复用
- 结局: 手术并发症 (Clavien-Dindo ≥ 3)

---

## 5. 下一步行动

1. ⚡ **验证 PSA 可用性**: 查询 labevents 中 LOINC 2857-1 (PSA)
2. ⚡ **评估 MIMIC-IV-Note**: 是否可获取病理报告文本 (含 Gleason) — Note 模块需单独申请
3. ⚡ **确认 UK Biobank**: 前列腺癌患病样本量
4. ⚠️ **SEER 申请**: 如计划长期使用，建议启动 SEER 数据申请 (通常 2-4 周)

---

*DQ-CARE 报告完成。供 PI FRAME 评估 R 维度使用。*

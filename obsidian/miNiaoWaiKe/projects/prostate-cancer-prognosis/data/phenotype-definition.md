# 前列腺癌表型操作化方案

**Agent**: urology/clinical-researcher
**Phase**: Phase 1 Round 2 — 专家决策
**日期**: 2026-05-10

---

## 1. 疾病队列定义

### 纳入标准 (Cohort Entry)

| # | 标准 | 操作化 | 来源 |
|---|------|--------|------|
| 1 | 前列腺癌诊断 | ICD-10: C61.x (Malignant neoplasm of prostate) OR ICD-9: 185.x | `diagnoses_icd` |
| 2 | 住院患者 | `admissions.hadm_id` 有效 | `admissions` |
| 3 | 年龄 ≥ 18 岁 | `patients.anchor_age >= 18` | `patients` |
| 4 | 入院时间在 2008-2022 | `admittime` 在 MIMIC-IV 时间范围内 | `admissions` |

### 排除标准

| # | 标准 | 操作化 | 理由 |
|---|------|--------|------|
| 1 | 入院即死亡 (DOA) | 排除 LOS < 1 天的死亡病例 | 无法预测 |
| 2 | 同日出院 | 排除 LOS = 0 且非死亡 | 非真正住院 |
| 3 | 多次入院的重复患者 | 仅保留首次入院 (index admission) | 避免患者内相关 |

### 预期队列规模

- **唯一患者**: ~2,497 (ICD-9 + ICD-10 去重)
- **首次入院**: ~2,200–2,500 (去重+排除后)
- **应用排除标准后**: ~2,000–2,300

---

## 2. 结局变量 (Outcome) 操作化

### 原始方案 vs 数据现实

| 方案 | 结局 | 事件数 | 率 | 判定 |
|------|------|--------|-----|------|
| 原始 SDS | 5 年 CSS | N/A (MIMIC 无法提供) | N/A | ❌ 不可行 |
| 方案 A | 30天全因死亡 | 128 | 3.2% | ⚠️ 事件不足 |
| **方案 B** ✅ | **复合结局: 30天死亡 OR ICU 入院** | **~678+** | **~17%+** | ✅ **推荐** |
| 方案 C | 住院期间主要并发症 | TBD | TBD | ⚠️ 需编码定义 |

### 推荐: 复合主要结局

**Primary Outcome**: 30天全因死亡 OR ICU 入院 (binary composite)

| 组成部分 | 操作化 | 来源 |
|---------|--------|------|
| 30天全因死亡 | `deathtime ≤ admittime + 30 days` OR `hospital_expire_flag = 1` | `admissions` |
| ICU 入院 | 住院期间出现 ICU stay 记录 | `icustays` |

**Secondary Outcomes** (可选):
1. 住院全因死亡 (hospital_expire_flag)
2. 住院时长 > 7 天 (prolonged LOS)
3. 30天再入院

---

## 3. 预测特征 (Predictors) 操作化

### 人口学特征

| 变量 | 操作化 | 类型 | 来源 |
|------|--------|------|------|
| 年龄 | `anchor_age` | continuous | `patients` |
| 种族 | `race` (White/Black/Hispanic/Asian/Other) | categorical | `admissions` (注: MIMIC 已脱敏) |
| 婚姻状况 | `marital_status` | categorical | `admissions` |
| 保险类型 | `insurance` (Medicare/Medicaid/Private/Other) | categorical | `admissions` |

### 肿瘤相关特征

| 变量 | 操作化 | 类型 | 可用性 |
|------|--------|------|--------|
| PSA | LOINC 2857-1, 入院前最后一次值 | continuous | ✅ 21,640 pts, 76K 次测量 |
| PSA 趋势 | 入院前 6 个月内多次测量的斜率 | continuous | ⚠️ 需足够测量点 |
| 骨转移 | ICD-10: C79.51, ICD-9: 198.5 | binary | `diagnoses_icd` |
| 淋巴结转移 | ICD-10: C77.x, ICD-9: 196.x | binary | `diagnoses_icd` |
| Gleason 评分 | — | — | ❌ 需 MIMIC-IV-Note (不可用) |
| TNM 分期 | — | — | ❌ 需 MIMIC-IV-Note (不可用) |

### 合并症 (Charlson Comorbidity Index)

| 合并症 | ICD-10 编码 | 权重 |
|--------|------------|------|
| 心肌梗死 | I21-I22 | +1 |
| 充血性心衰 | I50 | +1 |
| COPD | J44 | +1 |
| 糖尿病 | E10-E11 | +1 |
| 中重度肾病 | N18.3-N18.6 | +2 |
| 转移性实体瘤 | C77-C79 | +6 |
| ... (完整 CCI) | ... | ... |

### 实验室特征

| 变量 | 来源 | 时间窗口 |
|------|------|---------|
| 血红蛋白 (Hb) | labevents | 入院前 24h 最后一次 |
| 白细胞计数 (WBC) | labevents | 入院前 24h 最后一次 |
| 血小板 (PLT) | labevents | 入院前 24h 最后一次 |
| 肌酐 (Cr) | labevents | 入院前 24h 最后一次 |
| 白蛋白 (Alb) | labevents | 入院前 24h 最后一次 |
| 乳酸 (Lactate) | labevents | 入院前 24h 最后一次 |
| PSA | labevents | 入院前最近一次 |

### 入院特征

| 变量 | 操作化 | 来源 |
|------|--------|------|
| 入院类型 | `admission_type` (Elective/Emergency/Urgent) | `admissions` |
| 入院来源 | `admission_location` (ER/Clinic Referral/Transfer) | `admissions` |
| 手术史(前列腺) | 本次入院有无前列腺切除术 (ICD-10-PCS 0VT0, ICD-9-CM 60.5) | `procedures_icd` |

---

## 4. 效应方向 (临床先验)

基于临床知识，预测因子与复合结局的预期关联方向：

| 变量 | 预期方向 | 确信度 |
|------|---------|--------|
| 年龄 ↑ | 风险 ↑ | 高 |
| PSA ↑ | 风险 ↑ (反映肿瘤负荷) | 高 |
| 骨转移 (+) | 风险 ↑ | 高 |
| 急诊入院 (vs 择期) | 风险 ↑ | 高 |
| Hb ↓ | 风险 ↑ | 高 |
| Alb ↓ | 风险 ↑ | 高 |
| Cr ↑ | 风险 ↑ | 中 |
| Lactate ↑ | 风险 ↑ | 高 |
| CCI ↑ | 风险 ↑ | 高 |
| 手术史 (+) | 风险 ↓ (术后择期, pre-selected) | 中 |

这些预期方向将用于 Phase 5 的 SHAP 方向一致性验证。

---

## 5. 数据偏差声明

1. **选择偏倚**: MIMIC-IV 是单中心 (Beth Israel) ICU/住院数据，前列腺癌患者集中在需住院治疗的重症亚群
2. **编码偏倚**: Gleason/TNM 仅存在于病理报告中 (非结构化)，可能导致关键肿瘤特征缺失
3. **死亡随访**: MIMIC 的院外死亡基于 SSA 数据，可能有延迟报告
4. **种族信息**: MIMIC 的 race 变量已被脱敏处理，信息精度下降
5. **时间偏差**: 2008-2022，临床实践变化可能导致特征分布漂移

---

## 6. 表型方案确认

**最终推荐**:
- **队列**: 2,000+ 前列腺癌住院患者 (首次入院)
- **结局**: 复合结局 = 30天死亡 OR ICU 入院
- **特征集**: 人口学 + 实验室 + 合并症 + 入院特征 (~20 变量)
- **关键局限**: Gleason/TNM 不可用 (需 Note 模块)

*Next: 供 PI 进行 FRAME 评估*

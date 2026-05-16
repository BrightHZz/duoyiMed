# 前列腺癌转移模式操作化方案

**项目**: prostate-cancer-metastasis-pattern
**执行者**: clinical-researcher (urology)
**日期**: 2026-05-14

---

## 1. 研究队列定义

### 纳入标准

| # | 标准 | SEER 实现 |
|---|------|----------|
| 1 | 前列腺癌原发 | `Site recode ICD-O-3/WHO 2008 = "Prostate"` |
| 2 | 恶性行为 | `Behavior code ICD-O-3 = "Malignant"` |
| 3 | 诊断年份 | `Year of diagnosis ≥ 2010` (转移变量可用) |
| 4 | M1 疾病 | 以下任一满足:<br>— `Mets_bone=Yes` OR `Mets_brain=Yes` OR `Mets_liver=Yes` OR `Mets_lung=Yes`<br>— `Combined Summary Stage = "Distant site(s)/node(s) involved"` |
| 5 | 年龄 ≥ 18 | `Age recode with single ages and 90+` ≥ 18 |

### 排除标准

| # | 标准 | 理由 |
|---|------|------|
| 1 | 尸检诊断 | 无法评估生存 |
| 2 | 多原发肿瘤 (Sequence > 1) | 生存归因复杂 (可选排除) |
| 3 | 0 天生存 | 无随访信息 |

---

## 2. 转移模式分类方案 (v1.0)

### 四部位分类 (2010+ 全队列, 主分析)

```
算法: classify_met_pattern(row):

    bone  = row["SEER Combined Mets at DX-bone (2010+)"] == "Yes"
    brain = row["SEER Combined Mets at DX-brain (2010+)"] == "Yes"
    liver = row["SEER Combined Mets at DX-liver (2010+)"] == "Yes"
    lung  = row["SEER Combined Mets at DX-lung (2010+)"] == "Yes"

    organ_mets = [bone, brain, liver, lung]
    n_sites = sum(organ_mets)

    IF n_sites == 0:
        → "M1-Other/Unspecified"   # staged as Distant but no specific organ site

    ELIF bone == True AND n_sites == 1:
        → "Bone-only"

    ELIF liver == True OR lung == True OR brain == True:
        → "Visceral ± Bone"        # 内脏转移 (伴或不伴骨转移)

    ELIF bone == True AND n_sites >= 2 and not (liver or lung or brain):
        → "Bone-only"              # 仅多部位骨转移 (罕见)

    ELSE:
        → "Other/Unclassified"
```

### 六部位扩展分类 (2016+ 子集, 补充分析)

在四部位分类基础上加入:

```
distant_ln = row["Mets at DX-Distant LN (2016+)"] == "Yes"
other_mets = row["Mets at DX-Other (2016+)"] == "Yes"

Bone-only         = Bone=Yes AND all other 5 sites=No
Visceral ± Bone   = Liver=Yes OR Lung=Yes OR Brain=Yes
LN-only           = Distant LN=Yes AND all 4 organ sites=No AND Other=No
Other-only        = Other=Yes AND all 5 other sites=No
Multiple          = ≥2 sites positive (any combination)
```

---

## 3. 结局定义

### 主要结局: 总生存 (OS)

```
OS (months) = Survival months
Event = Vital status recode == "Dead"
Censor = "Alive"

5-year OS:  死亡或随访满 60 月（以先发生者为准）→ binary classification target
3-year OS:  死亡或随访满 36 月 → 用于 ML 模型训练 (更平衡)
```

### 次要结局: 肿瘤特异性生存 (CSS)

```
CSS (months) = Survival months
Event = SEER cause-specific death classification == "Dead (attributable to this cancer dx)"
Censor = Alive 或 死于其他原因

Competing event: 死于其他原因 (用于 Fine-Gray 竞争风险模型)
```

---

## 4. 协变量系统

### 人口学

| 协变量 | SEER 变量 | 编码 |
|--------|----------|------|
| Age | Age recode with single ages and 90+ | 连续 (岁) |
| Race/Ethnicity | Race and origin recode | NHW / NHB / Hispanic / NHAPI / Other |
| Marital status | Marital status at diagnosis | Married / Unmarried / Unknown |
| Income quartile | Median household income inflation adj to 2024 | Q1 (<$60K) / Q2 / Q3 / Q4 (≥$110K) |
| Urban-Rural | Rural-Urban Continuum Code | Metro / Non-Metro |

### 肿瘤特征

| 协变量 | SEER 变量 | 编码 |
|--------|----------|------|
| PSA level | PSA Lab Value Recode (2010+) | <4 / 4-10 / 10-20 / >20 / Unknown |
| Gleason Grade Group | Gleason Score Clinical Recode (2010+) | ISUP 1 (6) / 2 (3+4=7) / 3 (4+3=7) / 4 (8) / 5 (9-10) / Unknown |
| Histology type | ICD-O-3 Hist/behav | Adenocarcinoma / Other |
| T stage | Derived EOD 2018 T Recode / Derived AJCC T 7th ed | T1 / T2 / T3 / T4 / TX |

### 治疗 (作为协变量, 非主要对比因素)

| 协变量 | SEER 变量 | 编码 |
|--------|----------|------|
| Primary surgery | RX Summ--Surg Prim Site (1998-2022) | Radical prostatectomy / No surgery |
| Radiation | Radiation recode | None / EBRT / Brachy / Both |
| Chemotherapy | Chemotherapy recode | Yes / No-Unknown |

### 转移负荷 (新增衍生特征)

| 特征 | 计算 | 说明 |
|------|------|------|
| n_met_sites | sum(organ mets positive) | 0-6 个转移部位计数 |
| liver_involvement | Mets_liver=Yes | 单独标志 (最高危) |
| lung_involvement | Mets_lung=Yes | 单独标志 |
| multi_organ | n_met_sites ≥ 2 | ≥2 个器官转移 |

---

## 5. 时间分层 (治疗时代)

```
Era 1 (2010-2015):  ADT ± docetaxel 时代
Era 2 (2016-2023):  Abiraterone/Enzalutamide + ADT ± docetaxel (doublet/triplet)

按 Era 分层的敏感性分析: 确认转移模式效应在不同治疗时代的一致性
```

---

## 6. 临床合理性检查清单

| 检查项 | 预期方向 | 验证方式 |
|--------|---------|---------|
| Bone-only OS > Visceral OS | ✅ 一致 (HR ~1.5-2.0) | KM + log-rank |
| Liver mets 最差预后 | ✅ 一致 | Cox + 森林图 |
| Gleason 高→ 预后差 | ✅ 一致 | SHAP dependence |
| Age ↑ → OS ↓ | ✅ 一致 | SHAP dependence |
| RP 患者生存更长 (选择偏倚) | ✅ 一致 (不应解释为因果) | 多变量调整 |
| 2016+ Era 生存更好 | ✅ 预期 | KM by Era |

---

*clinical-researcher (urology) 产出于 Phase 1 Round 1*

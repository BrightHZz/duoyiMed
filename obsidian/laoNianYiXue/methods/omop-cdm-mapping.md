---
type: method
topic: omop_cdm
status: reference
last_updated: 2026-05-04
---

# OMOP CDM 老年医学变量映射

Observational Medical Outcomes Partnership (OMOP) Common Data Model 的标准映射参考。

## OMOP 核心表

| 表名 | 内容 |
|------|------|
| person | 人口学信息 |
| observation_period | 观察期 |
| visit_occurrence | 就诊记录 |
| condition_occurrence | 诊断 |
| drug_exposure | 用药 |
| measurement | 检验检查 |
| observation | 其他观察（问卷、自报） |
| procedure_occurrence | 手术/操作 |

## 老年医学变量映射速查

### 衰弱相关
| 临床变量 | OMOP 表 | 映射方式 |
|----------|---------|----------|
| Fried 衰弱评分 (0-5) | measurement | value_as_number |
| Frailty Index | observation | 需要从多个表聚合 30+ 缺陷项 |
| FRAIL Scale | observation | 5 个自报项 |

### 功能评估
| 变量 | OMOP 表 | concept_id / 说明 |
|------|---------|-------------------|
| 握力 (kg) | measurement | LOINC 编码 |
| 步速 (m/s) | measurement | LOINC 编码 |
| SPPB 总分 | measurement | value_as_number |
| TUG (秒) | measurement | value_as_number |
| ADL | observation | 按 domain 分别映射 |
| IADL | observation | 按 domain 分别映射 |

### 认知与心理
| 变量 | OMOP 表 | concept_id |
|------|---------|------------|
| MMSE 总分 | measurement | 3005116 |
| MoCA 总分 | measurement | 对应 LOINC |
| GDS-15 | observation | 抑郁筛查 |

### 生命体征与人体测量
| 变量 | OMOP 表 | concept_id |
|------|---------|------------|
| BMI | measurement | 3038553 |
| 收缩压 | measurement | 3004249 |
| 舒张压 | measurement | 3012888 |
| 体重 | measurement | 3025315 |
| 身高 | measurement | 3036277 |

### 实验室
| 变量 | OMOP 表 | concept_id |
|------|---------|------------|
| 血红蛋白 | measurement | 3000963 |
| 血清白蛋白 | measurement | 3005673 |
| 肌酐 | measurement | 3020564 |
| CRP | measurement | 3023199 |
| 25(OH)D | measurement | 对应 LOINC |

### 疾病诊断 (condition_occurrence)
| 疾病 | concept_id |
|------|------------|
| 糖尿病 | 201820 |
| 高血压 | 316866 |
| 心衰 | 316139 |
| 卒中 | 381316 |
| COPD | 255573 |
| 骨质疏松 | 80502 |
| 痴呆 | 4182210 |
| 抑郁 | 440383 |

### 用药 (drug_exposure)
| 指标 | 计算方式 |
|------|----------|
| 多重用药 | 统计 drug_exposure 条数 ≥ 5 |
| PIM (Beers) | 映射 Beers criteria 药物列表 |
| 抗胆碱能负担 | 映射 ARS 评分药物列表 |

## 相关资源
- [[datasets/charls|CHARLS]]
- [[datasets/uk-biobank|UK Biobank]]

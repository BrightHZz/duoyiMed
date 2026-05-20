# The diagnoses_icd table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `diagnoses_icd` |
| 数据来源 | Hospital database. |
| 用途 | Contains ICD diagnoses for patients, most notably ICD-10 diagnoses. |
| 行数 | 13,365 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID D_ICD_DIAGNOSES on ICD10_CODE_CN |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `SEQ_NUM` | tinyint unsigned |
| `ICD10_CODE_CN` | varchar(255) |
| `Diag_Category` | varchar(255) |

## 字段详细说明

- **SUBJECT_ID / HADM_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识。
- **SEQ_NUM**：诊断优先级排序。ICD诊断按优先级排序，顺序会影响治疗费用报销。
- **ICD10_CODE_CN**：中国版ICD-10诊断编码，关联 D_ICD_DIAGNOSES 表。
- **Diag_Category**：诊断类别。

## 注意事项

- ICD编码在患者出院时生成，用于计费目的
- 所有ICD编码均为ICD-10

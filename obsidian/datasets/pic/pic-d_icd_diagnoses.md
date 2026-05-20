# The d_icd_diagnoses table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `d_icd_diagnoses` |
| 数据来源 | Online sources. |
| 用途 | Definition table for ICD diagnoses. |
| 行数 | 25,378 |
| 关联表 | DIAGNOSES_ICD ON ICD10_CODE_CN |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | smallint unsigned |
| `ICD10_CODE_CN` | varchar(255) |
| `ICD10_CODE` | mediumtext |
| `TITLE_CN` | varchar(255) |
| `TITLE` | varchar(255) |

## 字段详细说明

- **ICD10_CODE_CN / ICD10_CODE**：ICD10_CODE 是国际版ICD-10编码，ICD10_CODE_CN 是中国版ICD-10编码。中国版已映射到国际版。每个编码对应一个诊断概念。
- **TITLE_CN / TITLE**：TITLE_CN 为中国版编码的中文定义，TITLE 为国际版编码的英文定义。

## 注意事项

- ICD编码在患者出院时分配，用于计费

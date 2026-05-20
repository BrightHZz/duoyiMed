# The inputevents table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `inputevents` |
| 数据来源 | Hospital databases. |
| 用途 | Input data for patients. |
| 行数 | 26,884 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID ICUSTAYS on ICUSTAY_ID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `ICUSTAY_ID` | mediumint unsigned |
| `CHARTTIME` | datetime |
| `AMOUNT` | float |
| `AMOUNTUOM` | varchar(255) |
| `STORETIME` | datetime |

## 字段详细说明

- **SUBJECT_ID / HADM_ID / ICUSTAY_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识，ICUSTAY_ID ICU住院唯一标识。
- **CHARTTIME**：入量事件时间。
- **AMOUNT / AMOUNTUOM**：AMOUNT 入量数值，AMOUNTUOM 入量单位。
- **STORETIME**：临床人员手动输入或手动验证的时间。

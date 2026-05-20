# The admissions table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `admissions` |
| 数据来源 | Hospital databases. |
| 用途 | Define a patient’s hospital admission, HADM_ID. |
| 行数 | 13,449 |
| 关联表 | PATIENTS on SUBJECT_ID D_ICD_DIAGNOSES on ICD10_CODE_CN |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | smallint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `ADMITTIME` | datetime |
| `DISCHTIME` | datetime |
| `DEATHTIME` | datetime |
| `ADMISSION_DEPARTMENT` | varchar(255) |
| `DISCHARGE_DEPARTMENT` | varchar(255) |
| `INSURANCE` | varchar(255) |
| `LANGUAGE` | varchar(255) |
| `RELIGION` | varchar(255) |
| `MARITAL_STATUS` | varchar(255) |
| `ETHNICITY` | varchar(255) |
| `EDREGTIME` | datetime |
| `EDOUTTIME` | datetime |
| `DIAGNOSIS` | varchar(255) |
| `ICD10_CODE_CN` | varchar(255) |
| `HOSPITAL_EXPIRE_FLAG` | tinyint unsigned |
| `HAS_CHARTEVENTS_DATA` | tinyint unsigned |

## 字段详细说明

- **SUBJECT_ID / HADM_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识（范围 100000-114202）。同一 SUBJECT_ID 可有多条记录（多次入院）。
- **ADMITTIME / DISCHTIME / DEATHTIME**：ADMITTIME 入院时间，DISCHTIME 出院时间，DEATHTIME 院内死亡时间（仅院内死亡时有值，通常等于 DISCHTIME，但可能有录入错误导致细微差异）。
- **ADMISSION_DEPARTMENT / DISCHARGE_DEPARTMENT**：入院/出院科室。
- **INSURANCE / LANGUAGE / RELIGION / MARITAL_STATUS / ETHNICITY**：患者人口学信息，来源于医院ADT系统。部分字段值在不同住院间可能变化（如MARITAL_STATUS合理，ETHNICITY不合理）。
- **EDREGTIME / EDOUTTIME**：急诊登记/离开时间。
- **DIAGNOSIS**：入院初步诊断（自由文本，中文）。
- **ICD10_CODE_CN**：诊断对应的中国版ICD-10编码，通常由收治医生分配。
- **HOSPITAL_EXPIRE_FLAG**：院内死亡标记，1=死亡，0=存活出院。
- **HAS_CHARTEVENTS_DATA**：该次住院是否有 chartevents 数据。

## 注意事项

- 数据来自医院ADT（入院/出院/转科）系统
- 数据覆盖时间段：2010年11月 - 2018年12月
- 除 DIAGNOSIS 列外，所有文本数据以英文字符存储

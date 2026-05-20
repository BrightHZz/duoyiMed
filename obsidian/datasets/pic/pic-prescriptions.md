# The prescriptions table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `prescriptions` |
| 数据来源 | Hospital database. |
| 用途 | Contains medication related order entries, i.e. prescriptions. |
| 行数 | 1,256,591 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID ICUSTAYS on ICUSTAY_ID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `ICUSTAY_ID` | mediumint unsigned |
| `STARTDATE` | datetime |
| `ENDDATE` | datetime |
| `DRUG_NAME_CN` | varchar(255) |
| `DRUG_NAME` | varchar(255) |
| `PROD_STRENGTH` | varchar(255) |
| `DRUG_NAME_GENERIC` | varchar(255) |
| `DOSE_VAL_RX` | varchar(255) |
| `DOSE_UNIT_RX` | varchar(255) |
| `DRUG_FORM` | varchar(255) |

## 字段详细说明

- **SUBJECT_ID / HADM_ID / ICUSTAY_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识，ICUSTAY_ID ICU住院唯一标识。
- **STARTDATE / ENDDATE**：处方生效的开始/结束时间。
- **DRUG_NAME_CN / DRUG_NAME / DRUG_NAME_GENERIC**：药品的中文名、英文名和通用名。
- **PROD_STRENGTH**：药品规格。
- **DOSE_VAL_RX / DOSE_UNIT_RX**：DOSE_VAL_RX 处方剂量，DOSE_UNIT_RX 剂量单位。
- **DRUG_FORM**：药品剂型。

# The chartevents table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `chartevents` |
| 数据来源 | Hospital databases. |
| 用途 | Contains all charted data for all patients. |
| 行数 | 2,278,978 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID ICUSTAYS on ICUSTAY_ID D_ITEMS on ITEMID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | int unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `ICUSTAY_ID` | mediumint unsigned |
| `ITEMID` | varchar(255) |
| `CHARTTIME` | datetime |
| `STORETIME` | datetime |
| `VALUE` | varchar(255) |
| `VALUENUM` | float |
| `VALUEUOM` | varchar(255) |

## 字段详细说明

- **SUBJECT_ID / HADM_ID / ICUSTAY_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识，ICUSTAY_ID ICU住院唯一标识。
- **ITEMID**：测量项目标识（如 1003=心率），每个ITEMID对应一种测量类型。
- **CHARTTIME**：记录观察发生的时间，通常是数据实际被测量的最近似时间。对于连续生命体征（心率、呼吸率、有创/无创血压、血氧饱和度），CHARTTIME 通常就是实际测量时间。
- **STORETIME**：记录观察被临床工作人员手动输入或手动验证的时间，逻辑上在 CHARTTIME 之后，通常晚几个小时。
- **VALUE / VALUENUM**：VALUE 包含测量值（文本格式）。若为数值，VALUENUM 包含相同数据的数值格式；若非数值，VALUENUM 为 null。VALUENUM 包含分数，VALUE 包含分数及文字描述。
- **VALUEUOM**：测量单位。

## 注意事项

- 包含除实验室和微生物数据外的大部分患者信息（生命体征、入量出量、人口学等）
- 目前没有床旁监护仪数据

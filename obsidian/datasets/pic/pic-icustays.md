# The icustays table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `icustays` |
| 数据来源 | Hospital database. |
| 用途 | Defines each ICUSTAY_ID in the database, i.e. defines a single ICU stay. |
| 行数 | 13,941 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | smallint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `ICUSTAY_ID` | mediumint unsigned |
| `FIRST_CAREUNIT` | varchar(255) |
| `LAST_CAREUNIT` | varchar(255) |
| `FIRST_WARDID` | smallint unsigned |
| `LAST_WARDID` | smallint unsigned |
| `INTIME` | datetime |
| `OUTTIME` | datetime |
| `LOS` | float |

## 字段详细说明

- **SUBJECT_ID / HADM_ID / ICUSTAY_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识，ICUSTAY_ID ICU住院唯一标识（生成标识，非医院原始数据）。
- **FIRST_CAREUNIT / LAST_CAREUNIT**：首个和最后ICU类型。由于ICUSTAY_ID将24小时内的多次ICU入院合并，患者可能在一次ICU住院期间被从一个ICU类型转到另一个。
- **FIRST_WARDID / LAST_WARDID**：首个和最后ICU病房ID。医院数据库将ICU作为"带有ICU成本中心的病房"追踪，每个ICU对应一个WARDID。
- **INTIME / OUTTIME**：转入/转出ICU的日期时间。
- **LOS**：ICU住院天数（小数天），可能包含多个ICU单元。

## 注意事项

- ICUSTAY_ID 是**生成标识**，医院和ICU数据库本身没有ICU就诊标识的概念
- 若患者在24小时内多次转入ICU，会被归为同一个 ICUSTAY_ID

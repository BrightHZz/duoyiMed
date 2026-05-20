# The patients table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `patients` |
| 数据来源 | Hospital databases. |
| 用途 | Contains all charted data for all patients. |
| 行数 | 12,881 |
| 关联表 | ADMISSIONS on SUBJECT_ID ICUSTAYS on SUBJECT_ID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | smallint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `GENDER` | varchar(255) |
| `DOB` | datetime |
| `DOD` | datetime |
| `EXPIRE_FLAG` | tinyint unsigned |

## 字段详细说明

- **SUBJECT_ID**：患者唯一标识，候选键，每行唯一。患者终身保持一致的信息存储在此表。
- **GENDER**：患者生理性别。
- **DOB**：患者出生日期（已做偏移处理以保护隐私）。
- **DOD**：患者死亡日期，来源为医院数据库记录。
- **EXPIRE_FLAG**：死亡标记，1=患者院内死亡，0=存活。

## 注意事项

- PATIENTS 表仅包含医院数据库中记录的死亡日期
- 患者唯一的静态数据为：GENDER、DOB、DOD

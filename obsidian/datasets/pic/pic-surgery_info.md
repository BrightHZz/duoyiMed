# The surgery_info table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `surgery_info` |
| 数据来源 | 医院手术信息系统 |
| 用途 | 记录患者手术信息，包括手术名称、麻醉方式、手术时间等 |
| 行数 | 7,488 |
| 关联表 | PATIENTS on SUBJECT_ID, ADMISSIONS on HADM_ID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `VISIT_ID` | tinyint unsigned |
| `OPER_ID` | tinyint unsigned |
| `ANES_START_TIME` | datetime |
| `ANES_END_TIME` | datetime |
| `SURGERY_START_TIME` | datetime |
| `SURGERY_END_TIME` | datetime |
| `SURGERY_NAME` | varchar(1024) |
| `ANES_METHOD` | varchar(1024) |
| `SURGERY_POSITION` | varchar(255) |

## 字段说明

- `ROW_ID`: 行唯一标识
- `SUBJECT_ID`: 患者ID，关联PATIENTS表
- `HADM_ID`: 住院ID，关联ADMISSIONS表
- `VISIT_ID`: 就诊次数标识
- `OPER_ID`: 手术标识
- `ANES_START_TIME`: 麻醉开始时间
- `ANES_END_TIME`: 麻醉结束时间
- `SURGERY_START_TIME`: 手术开始时间
- `SURGERY_END_TIME`: 手术结束时间
- `SURGERY_NAME`: 手术名称
- `ANES_METHOD`: 麻醉方式
- `SURGERY_POSITION`: 手术体位

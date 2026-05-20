# The outputevents table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `outputevents` |
| 数据来源 | Hospital databases. |
| 用途 | Output data for patients. |
| 行数 | 39,891 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID ICUSTAYS on ICUSTAY_ID D_ITEMS on ITEMID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `ICUSTAY_ID` | mediumint unsigned |
| `CHARTTIME` | datetime |
| `ITEMID` | varchar(255) |
| `VALUE` | float |
| `VALUEUOM` | varchar(255) |
| `STORETIME` | datetime |

## 字段详细说明

- **SUBJECT_ID / HADM_ID / ICUSTAY_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识，ICUSTAY_ID ICU住院唯一标识。
- **CHARTTIME**：输出事件时间。
- **ITEMID**：输出项目标识，关联 D_ITEMS 表。
- **VALUE / VALUEUOM**：输出量及单位。VALUE 记录在 CHARTTIME 时刻的物质数量（当精确开始时间未知但通常不超过1小时前）。
- **STORETIME**：临床人员手动输入或手动验证的时间。

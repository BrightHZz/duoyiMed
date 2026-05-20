# The labevents table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `labevents` |
| 数据来源 | Hospital database. |
| 用途 | Contains all laboratory measurements for a given patient. |
| 行数 | 10,094,117 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID D_LABITEMS on ITEMID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | int unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `ITEMID` | smallint unsigned |
| `CHARTTIME` | datetime |
| `VALUE` | text |
| `VALUENUM` | float |
| `VALUEUOM` | varchar(255) |
| `FLAG` | varchar(255) |

## 字段详细说明

- **SUBJECT_ID / HADM_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识。
- **ITEMID**：检测项目标识，关联 D_LABITEMS 表。
- **CHARTTIME**：**体液采集时间**，不是结果出来的时间。流程为：临床人员采集体液 → 条形码关联患者并记录采集时间 → 实验室分析（4-12小时）→ 返回结果。CHARTTIME 记录的是第一步的采集时间。
- **VALUE / VALUENUM**：VALUE 包含检测值（文本格式），若为数值则 VALUENUM 包含相同数据的数值格式。
- **VALUEUOM**：检测单位。
- **FLAG**：异常标记，'z'=正常，'h'=偏高，'l'=偏低。

## 注意事项

- CHARTTIME 是体液采集时间而非结果可用时间
- 数据直接来自实验室数据库，**未经ICU临床人员验证**，因此没有 STORETIME
- 实验室数据覆盖全院范围，不限于ICU

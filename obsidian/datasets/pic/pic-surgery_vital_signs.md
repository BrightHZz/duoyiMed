# The surgery_vital_signs table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `surgery_vital_signs` |
| 数据来源 | Hospital database. |
| 用途 | Contains vital signs recorded while a patient is present in the operating room. |
| 行数 | 1,216,011 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID D_ITEMS on ITEMID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `VISIT_ID` | tinyint unsigned |
| `OPER_ID` | tinyint unsigned |
| `ITEM_NO` | mediumint unsigned |
| `MONITORTIME` | datetime |
| `ITEMID` | varchar(255) |
| `VALUE` | float |

## 字段详细说明

- **SUBJECT_ID / HADM_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识。
- **VISIT_ID / OPER_ID / ITEM_NO**：VISIT_ID 第几次入院，OPER_ID 本次住院第几次手术，ITEM_NO 本次手术第几次测量。
- **MONITORTIME**：监护仪记录时间。
- **ITEMID**：测量项目标识（如 SV1=心率）。注意与 CHARTEVENTS 中ITEMID不同（如心率在CHARTEVENTS是1003，在SURGERY_VITAL是SV1）。
- **VALUE**：测量值。

## 注意事项

- 手术期间每5分钟记录一次生命体征
- ITEMID 与 CHARTEVENTS 中的不同

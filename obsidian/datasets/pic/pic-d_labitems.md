# The d_labitems table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `d_labitems` |
| 数据来源 | Hospital database. |
| 用途 | Definition table for all laboratory measurements. |
| 行数 | 832 |
| 关联表 | LABEVENTS on ITEMID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | smallint unsigned |
| `ITEMID` | smallint unsigned |
| `LABEL_CN` | text |
| `LABEL` | varchar(255) |
| `FLUID` | varchar(255) |
| `CATEGORY` | varchar(255) |
| `LOINC_CODE` | varchar(255) |

## 字段详细说明

- **ITEMID**：候选键，每行唯一。每个实验室检测概念分配一个ITEMID，以高效存储和查询。
- **LABEL_CN / LABEL**：LABEL_CN 为中文名称，LABEL 为对应英文名称。
- **FLUID**：检测体液类型（如 'BLOOD'）。同一检测概念在不同体液上会有不同的ITEMID。
- **CATEGORY**：检测大类，提供测量类型的高层信息。
- **LOINC_CODE**：LOINC编码，多数是事后补充，可能不完整。

## 注意事项

- 实验室数据与D_ITEMS分离有其合理原因
- 数据来自全院各科室，不限于ICU
- 大多数概念的LOINC编码尚未映射

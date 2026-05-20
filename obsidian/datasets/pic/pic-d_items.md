# The d_items table

## 基本信息

| 属性    | 值                                                                                                                                                                                                            |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 数据库表名 | `d_items`                                                                                                                                                                                                    |
| 数据来源  | Hospital databases.                                                                                                                                                                                          |
| 用途    | Definition table for all items in the hospital databases.                                                                                                                                                    |
| 行数    | 466                                                                                                                                                                                                          |
| 关联表   | CHARTEVENTS on ITEMID SURGERY_VITAL_SIGNS on ITEMID MICROBIOLOGYEVENTS on SPEC_ITEMID , ORG_ITEMID , or AB_ITEMID (for example, use d_items.ITEMID = microbiologyevents.SPEC_ITEMID ) OUTPUTEVENTS on ITEMID |

## 字段列表

| 字段名        | 数据类型              |
| ---------- | ----------------- |
| `ROW_ID`   | smallint unsigned |
| `ITEMID`   | varchar(255)      |
| `LABEL_CN` | varchar(255)      |
| `LABEL`    | text              |
| `LINKSTO`  | varchar(255)      |
| `CATEGORY` | varchar(255)      |
| `UNITNAME` | varchar(255)      |

## 字段详细说明

- **ITEMID**：项目唯一标识，候选键，每个测量概念对应一个ITEMID。
- **LABEL_CN / LABEL**：LABEL_CN 为中文概念描述，LABEL 为对应英文描述。
- **LINKSTO**：指定该ITEMID关联的事件表名（如 'chartevents'）。一个ITEMID只出现在一个事件表中。
- **CATEGORY**：项目类别，提供测量数据的大类信息。
- **UNITNAME**：默认测量单位，可能为空（单位可能变化、不适用于该数据类型、或缺失）。

## 注意事项

- D_ITEMS 与 LABEVENTS **不关联**（LABEVENTS使用D_LABITEMS）
- 某些概念存在重复ITEMID，如心率同时有1003（CHARTEVENTS）和SV1（SURGERY_VITAL）两个不同的ITEMID

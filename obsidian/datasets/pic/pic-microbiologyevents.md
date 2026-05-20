# The microbiologyevents table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `microbiologyevents` |
| 数据来源 | Hospital database. |
| 用途 | Contains microbiology information, including tests performed and sensitivities. |
| 行数 | 183,869 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID D_ITEMS on SPEC_ITEMID D_ITEMS on ORG_ITEMID D_ITEMS on AB_ITEMID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `CHARTTIME` | datetime |
| `SPEC_ITEMID` | text |
| `SPEC_TYPE_DESC` | text |
| `ORG_ITEMID` | varchar(255) |
| `ORG_NAME` | varchar(255) |
| `AB_ITEMID` | varchar(255) |
| `AB_NAME` | varchar(255) |
| `DILUTION_TEXT` | varchar(255) |
| `DILUTION_COMPARISON` | varchar(255) |
| `DILUTION_VALUE` | float |
| `INTERPRETATION` | varchar(255) |

## 字段详细说明

- **SUBJECT_ID / HADM_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识。
- **CHARTTIME**：记录时间，最接近实际测量时间。
- **SPEC_ITEMID / SPEC_TYPE_DESC**：标本类型ID和描述，被检测细菌生长的标本。
- **ORG_ITEMID / ORG_NAME**：微生物ID和名称。若为 NULL 表示培养无菌生长（阴性）。
- **AB_ITEMID / AB_NAME**：药敏测试的抗生素ID和名称。
- **DILUTION_TEXT / DILUTION_COMPARISON / DILUTION_VALUE**：抗生素敏感性测试的稀释度信息。
- **INTERPRETATION**：药敏结果解释，"S"=敏感，"R"=耐药，"I"=中介，"P"=待定。

## 注意事项

- 若 ORG_NAME 为 null，表示培养无菌生长

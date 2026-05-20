# The or_exam_reports table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `or_exam_reports` |
| 数据来源 | Hospital database. |
| 用途 | Contains all exam for patients. |
| 行数 | 183,809 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID |

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `EXAMTIME` | datetime |
| `REPORTTIME` | datetime |
| `EXAM_ITEM_TYPE_NAME` | varchar(255) |
| `EXAM_ITEM_NAME` | varchar(255) |
| `EXAM_PART_NAME` | varchar(255) |

## 字段详细说明

- **SUBJECT_ID / HADM_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识。
- **EXAMTIME / REPORTTIME**：EXAMTIME 检查执行时间，REPORTTIME 报告生成时间。
- **EXAM_ITEM_TYPE_NAME / EXAM_ITEM_NAME / EXAM_PART_NAME**：EXAM_ITEM_TYPE_NAME 检查类型，EXAM_ITEM_NAME 检查项目名称，EXAM_PART_NAME 检查部位。

## 注意事项

- 不包含检查报告的正文内容（中文文本）

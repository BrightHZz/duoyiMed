# The emr_symptoms table

## 基本信息

| 属性 | 值 |
|------|-----|
| 数据库表名 | `emr_symptoms` |
| 数据来源 | Hospital databases. |
| 用途 | Symptoms extracted from notes. |
| 行数 | 402,142 |
| 关联表 | PATIENTS on SUBJECT_ID ADMISSIONS on HADM_ID |

## 注意事项

The EMR_SYMPTOMS table is extracted from the notes, for example physician notes, discharge summaries, and so on.

## 字段列表

| 字段名 | 数据类型 |
|--------|----------|
| `ROW_ID` | mediumint unsigned |
| `SUBJECT_ID` | mediumint unsigned |
| `HADM_ID` | mediumint unsigned |
| `EMR_ID` | mediumint unsigned |
| `RECORDTIME` | datetime |
| `SYMPTOM_NAME_CN` | varchar(255) |
| `SYMPTOM_NAME` | varchar(255) |
| `SYMPTOM_ATTRIBUTE` | varchar(255) |

## 字段详细说明

- **SUBJECT_ID / HADM_ID**：SUBJECT_ID 患者唯一标识，HADM_ID 住院唯一标识。
- **EMR_ID**：病历文档ID，每个病历笔记的唯一标识。
- **RECORDTIME**：病历记录时间，即在临床信息系统上记录的时间。
- **SYMPTOM_NAME_CN / SYMPTOM_NAME**：症状的中文名和英文名。
- **SYMPTOM_ATTRIBUTE**：症状属性，指示该症状是否存在（阳性/阴性）。

---
type: data_source
status: available
topics: [MIMIC-III, EHR, ICU, DuckDB]
last_updated: 2026-05-09
---

# MIMIC-III v1.4

## 数据概况

| 属性            | 值                                                                            |
| ------------- | ---------------------------------------------------------------------------- |
| 版本            | v1.4                                                                         |
| 源文件大小         | ~6.2 GB (压缩 .csv.gz)                                                         |
| 源文件路径         | `/Users/wuyouhang/Documents/trae_projects/dataset/MIMIC/mimic-iii-1.4/data/` |
| DuckDB 路径     | `/Users/wuyouhang/Documents/trae_projects/dataset/MIMIC/mimic.db`            |
| DuckDB Schema | `mimic_iii` (26表)                                                            |
| 时间范围          | 2001 - 2012                                                                  |
| 患者数           | 46,520                                                                       |

## 与 MIMIC-IV 主要区别

| 方面 | MIMIC-III | MIMIC-IV |
|------|-----------|----------|
| 护理系统 | CareVue + MetaVision | MetaVision only |
| 患者识别 | subject_id, hadm\_id, icustay\_id | subject\_id, hadm\_id, stay\_id |
| 临床笔记 | NOTEEVENTS (有) | 无 |
| 给药记录 | INPUTEVENTS_CV + INPUTEVENTS_MV | emar + inputevents |
| 入院族 | 无 | 有 (anchor_year) |

## 主要数据表

| 表名 | 行数 | 用途 |
|------|------|------|
| patients | 46,520 | 人口学 |
| admissions | 58,976 | 住院记录 |
| icustays | 61,532 | ICU 入院 |
| chartevents | 330,712,483 | 床边观察 (最大表) |
| labevents | 27,854,055 | 检验数据 |
| noteevents | 2,083,180 | 临床笔记 (文本) |
| inputevents_cv | 17,527,935 | CareVue 输液 |
| inputevents_mv | 3,618,991 | MetaVision 输液 |
| prescriptions | 4,156,450 | 处方 |
| diagnoses_icd | 651,047 | ICD-9 诊断 |
| procedures_icd | 240,095 | ICD-9 手术 |
| cptevents | 573,146 | CPT 编码 |
| datetimeevents | 4,485,937 | 日期时间事件 |
| microbiologyevents | 631,726 | 微生物学 |
| outputevents | 4,349,218 | 出量记录 |

## DuckDB 查询

```python
import duckdb
con = duckdb.connect("/Users/wuyouhang/Documents/trae_projects/dataset/MIMIC/mimic.db")

# 查询临床笔记
notes = con.execute("""
    SELECT subject_id, hadm_id, category, text
    FROM mimic_iii.noteevents
    WHERE subject_id = 123
""").fetchdf()
```

## 适用场景

- **临床笔记 NLP**: NOTEEVENTS 表有 200 万份临床笔记，MIMIC-IV 无此数据
- **补充样本量**: 与 MIMIC-IV 合并可增加患者数
- **CareVue 年代数据**: 老系统数据有特殊研究价值 (2001-2008)
- **经典论文复现**: 大量已发表研究基于 MIMIC-III

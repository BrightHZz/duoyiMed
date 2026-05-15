---
type: data_source
status: active
topics: [MIMIC-IV, EHR, ICU, kidney_stone, urology, DuckDB]
last_updated: 2026-05-09
---

# MIMIC-IV — 肾结石数据

## 数据概况

| 属性 | 值 |
|------|-----|
| 版本 | v3.1 |
| 源文件大小 | ~10 GB (压缩 .csv.gz) |
| 源文件路径 | `/Users/wuyouhang/Documents/trae_projects/dataset/MIMIC/mimic-iv-3.1/data/` |
| DuckDB 路径 | `/Users/wuyouhang/Documents/trae_projects/dataset/MIMIC/mimic.db` |
| DuckDB Schema | `mimic_iv_hosp` (22表), `mimic_iv_icu` (9表) |
| 模块 | hosp, icu |
| 时间范围 | 2008 - 2022 |

## 肾结石患者筛选结果

| 指标 | 值 |
|------|-----|
| 肾结石患者 (subject_id) | 3,124 |
| 肾结石住院 (hadm_id) | 4,302 |
| 急诊结石就诊 (index) | 1,979 |
| 90天内外科干预 | 118 (6.0%) |
| 手术类型 | URS 110 (93.2%), PCNL 8 (6.8%) |
| 中位手术天数 | 2.5 天 |

## DuckDB 查询

```python
import duckdb
con = duckdb.connect("/Users/wuyouhang/Documents/trae_projects/dataset/MIMIC/mimic.db")

# 查某个患者全部入院
df = con.execute("""
    SELECT * FROM mimic_iv_hosp.admissions
    WHERE subject_id = 10000032
""").fetchdf()
```

## 主要数据表

| 表名 | Schema | 行数 | 用途 | 处理方式 |
|------|--------|------|------|---------|
| diagnoses_icd | hosp | 6,364,488 | 筛选结石患者 | 全量读 |
| admissions | hosp | 546,028 | 住院记录+急诊标记 | 全量读 |
| patients | hosp | 364,627 | 人口学 | 全量读 |
| procedures_icd | hosp | 859,655 | 外科干预识别 | 全量读 |
| labevents | hosp | 158,374,764 | 检验数据 | **仅结石患者** |
| microbiologyevents | hosp | 3,988,224 | UTI 相关 | 结石患者筛选 |
| prescriptions | hosp | 20,292,611 | 用药 | **仅结石患者** |
| pharmacy | hosp | 17,847,567 | 药房发药 | 按需使用 |
| poe | hosp | 52,212,109 | Provider Order Entry | 按需使用 |
| emar | hosp | 42,808,593 | 电子给药记录 | 按需使用 |
| hcpcsevents | hosp | 186,074 | CPT 编码 | 已使用 (补充手术识别, 阳性率从 1.7% 提升至 6.0%) |
| chartevents | icu | 432,997,491 | ICU 观察数据 | 暂未使用 |
| inputevents | icu | 10,953,713 | ICU 输液 | 暂未使用 |
| ingredientevents | icu | 14,253,480 | ICU 输液成分 | 暂未使用 |
| procedureevents | icu | 808,706 | ICU 操作 | 按需使用 |

## ICD 编码分布

| ICD 编码 | 描述 | 记录数 |
|----------|------|--------|
| 5920 | ICD-9: Kidney stone | 1,864 |
| N200 | ICD-10: Calculus of kidney | 1,335 |
| 5921 | ICD-9: Ureteral stone | 905 |
| N201 | ICD-10: Calculus of ureter | 246 |
| N202 | Kidney + ureteral stone | 151 |
| N209 | Urinary calculus NOS | 14 |

## 关键发现

1. **ICD-9 占比大** — 5920/5921 合计 2,773 条 > N20.x 合计 1,746 条
2. **类别不平衡但可建模** — 90天手术率 6.0% (118/1979)，结合 CPT 编码后阳性率从 1.7% 提升至 6.0%
3. **检验数据覆盖率高** — 核心实验室特征覆盖度 >99%（血常规/肾功能/电解质），尿检覆盖率 ~50%
4. **手术编码已完善** — 同时使用 ICD-10-PCS + CPT (hcpcsevents)，URS 占手术绝大多数 (93.2%)
5. **微生物数据丰富** — 166K 培养记录，54.1% 阳性，E. coli 是最常见病原
6. **用药数据完整** — 636K 条处方记录，2,431 种药物

## 提取 Pipeline

脚本: `src/data/mimic_kidney_stone_pipeline.py`
输出: `outputs/kidney_stone/`

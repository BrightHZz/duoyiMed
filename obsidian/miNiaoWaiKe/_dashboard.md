---
type: dashboard
status: active
topics: [urology, overview]
last_updated: 2026-05-09
---

# 泌尿外科知识库 (miNiaoWaiKe)

## 活跃项目

| 项目 | 状态 | 阶段 | 数据 | 下一步 |
|------|------|------|------|--------|
| [[projects/kidney-stone-surgery-prediction\|肾结石急诊外科干预预测]] | active | Phase 4 | MIMIC-IV | 论文完稿 |
| [[projects/prostate-cancer-prognosis\|前列腺癌住院不良结局预测]] | active | Phase 6 | MIMIC-IV | 论文初稿完成, AUC 0.845 |

## 数据源

| 数据 | 类型 | 患者数 | 状态 |
|------|------|--------|------|
| [[datasets/mimic-iv\|MIMIC-IV]] | EHR | 3,124 结石患者 | active |
| [[datasets/mimic-iii\|MIMIC-III]] | EHR | 46,520 患者 | available |
| SEER | 癌症登记 | TBD | pending |
| NHANES | 社区人群 | TBD | pending |

## 泌尿外科概念

| 概念 | 状态 |
|------|------|
| [[urology-concepts/kidney-stone-phenotype\|肾结石可计算表型]] | draft |

## 快速链接

- Pipeline: `src/data/mimic_kidney_stone_pipeline.py`
- 输出: `outputs/kidney_stone/`
- 建模数据集: `analysis_ready.parquet` (1,979 × 19, 完整版含实验室特征 53 列)

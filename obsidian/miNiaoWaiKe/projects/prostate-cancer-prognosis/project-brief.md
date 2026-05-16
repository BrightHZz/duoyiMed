---
title: "前列腺癌住院不良结局预测模型"
project_id: prostate-cancer-prognosis
domain: 泌尿外科
status: manuscript_ready
created: 2026-05-10
updated: 2026-05-10
pm: orchestrator
---

## PM 状态总览

**当前阶段**: Phase 6 ✅ — 论文初稿完成
**总体进度**: ██████████ 100%
**Gate 1**: ✅ PASS
**Gate 2**: ✅ PASS
**Gate 3**: ✅ PASS
**Gate 4**: ⚠️ COND_PASS (MIMIC-III 外验不可行)
**Gate 5**: ⚠️ COND_PASS (条件已注入 Phase 6)
**Gate 6**: ✅ PASS (初稿)

## 里程碑

| 阶段 | 内容 | 状态 | 关键产出 |
|---|---|---|---|
| Phase 0: 总体设计 | SDS 系统设计 | ✅ | sds.md |
| Phase 1: 问题定义 | 文献检索、数据评估、FRAME | ✅ | 5篇对标论文, DQ-CARE, FRAME启动 |
| Phase 2: 方案设计 | 建模方案 + SAP (辩论) | ✅ | 研讨厅辩论, PI裁决, 三层特征策略 |
| Phase 3: 执行/内部验证 | 模型训练、调优、SHAP | ✅ | AUC 0.8448 ± 0.028 |
| Phase 4: 外部验证 | MIMIC-III 验证 | ⚠️ | 不可行 (n=283, 年龄92) |
| Phase 5: 审查 | 临床审查 (辩论) | ✅ | COND_PASS, 10项条件 |
| Phase 6: 论文撰写 | IMRAD 初稿 | ✅ | manuscript.md (~3,800 words, 26 refs) |

## 研究问题

基于 MIMIC-IV EHR 数据，开发并内部验证机器学习模型 (XGBoost)，预测住院前列腺癌患者的 30天死亡或 ICU 入院复合结局。

## 核心结果

| 指标 | 值 |
|------|-----|
| 主模型 (PSA-free, n=2,437) | AUC 0.8448 ± 0.0280 |
| PSA 模型 (n=1,233) | AUC 0.8289 ± 0.0329 |
| LR Baseline | AUC 0.7544 ± 0.0731 |
| Top-1 特征 | Lactate (17.5%) |
| 最佳亚组 | Elective (AUC 0.8855) |
| Calibration Slope | 0.91 (Platt) |

## 目标期刊

| Tier | 期刊 | IF |
|---|---|---|
| 首投 | Prostate Cancer and Prostatic Diseases | 4.9 |
| 备选 | BMC Urology | 2.0 |
| 备选 | BMC Medical Informatics & Decision Making | 3.3 |

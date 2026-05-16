---
title: "肾结石手术预测模型"
project_id: kidney-stone-surgery-prediction
domain: 泌尿外科
status: manuscript_ready
created: 2026-05-09
updated: 2026-05-10
pm: orchestrator
---

## PM 状态总览

**当前阶段**: Phase 4 — 论文写作与投稿准备
**总体进度**: █████████░ 95%
**下次评审**: PI Gate Review

## 里程碑

| 阶段 | 内容 | 状态 | 产出 |
|---|---|---|---|
| Phase 1: 问题定义 | 文献检索、数据评估 | ✅ | 对标论文表, FRAME 评估 |
| Phase 2: 数据+特征 | 数据提取、特征工程 | ✅ | extract_cohort.py, enhance_features.py |
| Phase 3: 建模 | 模型训练、调优、SHAP | ✅ | AUROC 0.755, 5 models |
| Phase 4: 写作 | IMRAD 论文 | ✅ | sections/ (7 sections), compiled-manuscript.md |
| Phase 5: 投稿 | 格式排版、Cover Letter、投稿 | ⏳ | — |
| Phase 6: 外部验证 | MIMIC-III 验证队列 | ✅ | AUROC 0.8286 (245 patients, 46.5% pos) |

## 团队分工

| 角色 | Agent | Phase 4 任务 | 状态 |
|---|---|---|---|
| PI | `urology/pi` | 终审签批 | ⏳ 等待论文完稿 |
| 临床研究员 | `urology/clinical-researcher` | 临床审查报告 | ✅ clinical-review.md |
| 计算生物学家 | `urology/computational-biologist` | 建模方案、SHAP 审核 | ✅ |
| 科学作家 | `shared/scientific-writer` | IMRAD 四章节初稿 | ✅ sections/01-04 |
| 生物统计师 | `shared/biostatistician` | SAP、校准/决策曲线 | ⏳ |
| ML 工程师 | `shared/ml-engineer` | 实验日志、模型最终化 | ⏳ |
| 数据工程师 | `shared/data-engineer` | MIMIC-III 外部验证 | ⏳ Phase 6 |
| 研究助理 | `shared/research-assistant` | 参考文献整理、表格生成 | ⏳ |

## Phase 4 剩余任务

| ID | 任务 | 负责人 | 优先级 | 依赖 |
|---|---|---|---|---|
| T1 | 撰写 Abstract | scientific-writer | ✅ | — |
| T2 | 生成 Table 1 (基线特征表) | research-assistant | ✅ | — |
| T3 | 生成 Table 2 (模型性能对比) | ml-engineer | ✅ | — |
| T4 | 参考文献格式化 | research-assistant | ✅ | — |
| T5 | 决策曲线分析 (DCA) | biostatistician | ⏭ 跳过 | — |
| T6 | 完整稿组装 → manuscript.md | scientific-writer | ⏳ | — |
| T7 | PI 终审 | urology/pi | ⏳ | — |

## 目标期刊

| Tier | 期刊 | IF | 策略 |
|---|---|---|---|
| 主投 | BMC Urology | 2.0 | 审稿快，接受 ML 预测模型 |
| 备选 | World Journal of Urology | 3.6 | IF 更高，要求更严 |
| 备选 | International Urology and Nephrology | 2.0 | 审稿周期短 |

## 风险清单

| 风险 | 概率 | 影响 | 缓解措施 |
|---|---|---|---|
| AUROC 0.755 被审稿人认为不够 | 中 | 高 | Discussion 充分论证无影像特征的合理性 |
| 单中心数据被质疑 | 高 | 中 | 标注为 limitation，承诺外部验证 |
| MIMIC-IV-Note 不可获取 | 中 | 低 | 不影响当前投稿，仅影响后续改进 |

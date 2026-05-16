---
project_id: prostate-cancer-2026
project_name: 前列腺癌老年人群机器学习预测模型
status: phase-1-problem-definition
created: 2026-05-07
---

# 项目章程 — 前列腺癌老年人群预测模型

## 目标

探索机器学习在老年人群（60+）前列腺癌风险预测、筛查决策和治疗结局评估中的应用，结合老年综合征（衰弱、多病共存、多重用药）构建老年肿瘤学计算模型。

## 研究问题（待 Phase 1 确认）

1. 社区老年男性中，老年综合征能否预测前列腺癌诊断风险？
2. 基于 ML 整合老年评估，预测前列腺癌治疗相关并发症和功能下降？
3. 结合 PSA + 老年因素的风险分层模型能否优化筛查决策？

## Phase 1 — 问题定义（进行中）

| Agent | 任务 | 状态 |
|-------|------|------|
| PI | FRAME 方向评估 | 🔄 进行中 |
| Clinical Researcher | 临床问题可计算性评估 | 🔄 进行中 |
| Research Assistant | 文献快速扫描 | 🔄 进行中 |

## Phase 2 — 方案设计（待启动）

| Agent | 任务 | 依赖 |
|-------|------|------|
| Biostatistician | 研究设计 + 样本量分析 | Phase 1 |
| Data Engineer | 数据可用性评估 | Phase 1 |
| Computational Biologist | 建模方案设计 | Phase 1 |

## Phase 3 — 执行（待启动）

| Agent | 任务 | 依赖 |
|-------|------|------|
| ML Engineer | 模型实现与训练 | Phase 2 |
| Biostatistician | 统计分析 | Phase 2 |

## Phase 4 — 产出（待启动）

| Agent | 任务 | 依赖 |
|-------|------|------|
| Clinical Researcher | 结果临床解读 | Phase 3 |
| Scientific Writer | 论文初稿 | Phase 3 |
| PI | 最终审定 | Phase 3 |

## 交付物

- [ ] FRAME 评估报告
- [ ] 文献扫描简报
- [ ] 临床可计算性评估
- [ ] 研究方案 (Protocol)
- [ ] 数据可用性报告
- [ ] 建模方案
- [ ] 统计分析计划 (SAP)
- [ ] 模型训练与评估报告
- [ ] 论文初稿
- [ ] 投稿

## 数据资源

| 资源 | 路径 |
|------|------|
| CHARLS | `~/Documents/trae_projects/related to Sarcopenia/charls/` |
| 知识库 | `~/Documents/trae_projects/obsidian/laoNianYiXue/` |

## 风险

- 风险1: CHARLS 中前列腺癌相关变量可能不足（需确认 PSA、癌症诊断等变量）
- 风险2: 老年肿瘤学是交叉领域，团队需补充肿瘤学知识
- 风险3: 数据获取可能是瓶颈（如需要临床/医院数据）

## 参考文献

- 待 Phase 1 文献扫描后补充

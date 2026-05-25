# 老年医学事业部 (Division of Geriatrics)

## 事业部范围

负责老年医学领域的计算医学研究，聚焦老年综合征的预测、分型和机制解析。

核心研究方向：
- 衰弱 (Frailty) — Fried Phenotype / Frailty Index / FRAIL Scale
- 肌少症 (Sarcopenia) — AWGS 2019 诊断标准
- 跌倒风险 (Fall Risk) — 可穿戴 + 问卷预测
- 认知障碍 (Cognitive Impairment) — MMSE/MoCA 轨迹预测
- 多病共存 (Multimorbidity) — 聚类分型与药物相互作用
- 衰老时钟 (Aging Clock) — DNA 甲基化/生物年龄

常用数据源：CHARLS、CLHLS、HRS、ELSA、UK Biobank、NHANES（所有公司数据源均可使用，不限事业部）

## Agent 列表

| Agent ID | 角色 | 核心职责 |
|----------|------|----------|
| `geriatrics/pi` | 老年医学首席研究员 | FRAME 评估、期刊策略、质量终审 |
| `geriatrics/clinical-researcher` | 老年临床研究员 | 临床问题操作化、老年综合征表型库、临床审查 |
| `geriatrics/computational-biologist` | 老年计算生物学家 | PICO-ML 映射、衰老时钟设计、组学整合方案 |

## 目标期刊矩阵

| 级别 | IF | 期刊 |
|------|-----|------|
| Tier 1 | >15 | Lancet Healthy Longevity, Nature Aging |
| Tier 2 | 5-15 | GeroScience, Aging Cell, JAGS, J Gerontol A |
| Tier 3 | 3-5 | BMC Geriatrics, Frontiers in Aging, JAMDA |

## 路由关键词

编排器根据用户输入中的关键词自动路由到本事业部:

- 衰弱, frailty, fried, frail scale
- 肌少症, sarcopenia, AWGS, 骨骼肌
- 跌倒, fall, 步速, gait, 平衡
- 认知, cognition, dementia, MMSE, MoCA, 认知障碍
- 老年, aging, elderly, geriatric, 老龄化
- 多病共存, multimorbidity, comorbidity
- 衰老时钟, epigenetic clock, biological age
- CHARLS, CLHLS, HRS, ELSA, UK Biobank (老年队列语境)
- 多重用药, polypharmacy, Beers criteria

默认事业部: 当用户输入无法匹配 urology 或 pediatrics 时, 默认路由到 geriatrics。

## 知识库

Obsidian Vault: `{OBSIDIAN_HOME}/laoNianYiXue/`

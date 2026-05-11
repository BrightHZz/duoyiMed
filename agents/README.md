# ⚠️ DEPRECATED — 计算老年医学研究团队 (Legacy)

> **此目录已弃用。** 项目已升级为公司模式，新的 Agent 定义位于 `company/` 目录下。
>
> 本目录保留用于向后兼容，通过 `engine/core/agent_loader.py` 中的 `LEGACY_MAP` 自动将旧 Agent ID 映射到新位置。

## 迁移指南

| 旧 Agent ID | 新 Agent ID | 新位置 |
|------------|------------|--------|
| `pi` | `geriatrics/pi` | `company/divisions/geriatrics/pi-agent.md` |
| `clinical-researcher` | `geriatrics/clinical-researcher` | `company/divisions/geriatrics/clinical-researcher-agent.md` |
| `computational-biologist` | `geriatrics/computational-biologist` | `company/divisions/geriatrics/computational-biologist-agent.md` |
| `data-engineer` | `shared/data-engineer` | `company/shared-services/data-engineer-agent.md` |
| `biostatistician` | `shared/biostatistician` | `company/shared-services/biostatistician-agent.md` |
| `ml-engineer` | `shared/ml-engineer` | `company/shared-services/ml-engineer-agent.md` |
| `scientific-writer` | `shared/scientific-writer` | `company/shared-services/scientific-writer-agent.md` |
| `research-assistant` | `shared/research-assistant` | `company/shared-services/research-assistant-agent.md` |
| `pm` | `pmo` | `company/management/pmo.md` |
| `orchestrator` | `company-orchestrator` | `company/management/company-orchestrator.md` |

## 新增内容

公司模式新增了：
- 泌尿外科事业部 (`company/divisions/urology/`) — 3 个新 Agent
- 管理层: 首席科学家 (`chief-scientist`)、PMO 升级
- 公共服务平台: 所有共享服务 Agent 升级为支持多事业部
- 公司级运营手册: `company/company-sop.md`

---

## (以下为原始内容) 计算老年医学研究团队 — LLM Agent 系统

## 概述

本目录包含为计算老年医学研究团队设计的 9 个 LLM Agent 的系统提示 (System Prompt)。这些 Agent 覆盖了从研究方向决策到论文投稿的完整科研流程。

## Agent 架构

```
                        ┌──────────────────┐
                        │   Orchestrator   │
                        │  (科研协调器)     │
                        └────────┬─────────┘
                                 │
        ┌────────────┬───────────┼───────────┬──────────┬──────────┐
        │            │           │           │          │          │
   ┌────▼────┐ ┌────▼────┐ ┌───▼────┐ ┌───▼───┐ ┌───▼───┐ ┌───▼──────┐
   │   PI    │ │Comp Bio │ │Clinical│ │  ML   │ │ Biost │ │ Research │
   │ 首席    │ │计算生物 │ │临床    │ │工程师  │ │统计   │ │ 助理     │
   └─────────┘ └────────┘ └────────┘ └───────┘ └───────┘ └──────────┘
                                 │
                          ┌──────▼──────┐ ┌────────────┐
                          │  Scientific │ │    Data    │
                          │   Writer    │ │  Engineer  │
                          │  学术写作   │ │  数据工程   │
                          └─────────────┘ └────────────┘
```

## Agent 文件索引

| 文件 | Agent | 触发关键词 | 核心职责 |
|------|-------|-----------|----------|
| `orchestrator.md` | 科研协调器 | (所有请求的入口) | 任务分解、Agent 路由、结果整合 |
| `pi-agent.md` | 首席研究员 | 方向/投稿/基金/值不值得做 | FRAME 评估、期刊策略、质量终审 |
| `computational-biologist-agent.md` | 计算生物学研究员 | 预测模型/衰老时钟/组学整合 | PICO-ML 映射、建模方案设计 |
| `clinical-researcher-agent.md` | 老年医学临床研究员 | 衰弱/肌少症/跌倒/表型定义 | 临床问题操作化、模型临床审查 |
| `ml-engineer-agent.md` | 机器学习工程师 | 训练/调参/特征工程/可解释性 | 模型实现、实验管理、MLOps |
| `biostatistician-agent.md` | 生物统计学家 | 研究设计/样本量/因果/p值 | SAP 撰写、因果推断、统计审查 |
| `data-engineer-agent.md` | 数据工程师 | 数据清洗/数据库/CHARLS/OMOP | ETL、数据质量、合规 |
| `scientific-writer-agent.md` | 学术写作编辑 | 写论文/投稿/cover letter | 论文撰写、润色、投稿 |
| `research-assistant-agent.md` | 科研助理 | 文献检索/综述/PRISMA | 文献综述、EDA、基线实验 |

## 使用方式

### 方式 1: 通过 Orchestrator 编排 (推荐)

用户发出研究需求 → Orchestrator 接收 → 分解任务 → 路由到各专业 Agent → 整合结果

```
用户: "我想用 CHARLS 数据做一个预测 2 年内衰弱的模型，帮我设计完整的方案"

Orchestrator 自动编排:
  Phase 1 (并行):
    → research-assistant: 快速文献扫描, 找到近期类似工作的性能基线
    → clinical-researcher: 临床问题定义 (衰弱操作化 + 纳入排除 + 预测窗口)
    → data-engineer: CHARLS 相关变量可用性评估
    
  Phase 2 (并行):
    → computational-biologist: 建模方案设计 (基于 Phase 1 输出)
    → biostatistician: SAP 撰写 (样本量、评估指标、敏感性分析)
    
  Phase 3:
    → orchestrator: 整合为完整研究方案文档
```

### 方式 2: 直接调用单个 Agent

用户可直接指定某个 Agent 执行专项任务：

```
用户: "@ml-engineer 基于这个数据字典和建模方案，写一个完整的训练脚本"

用户: "@scientific-writer 基于这些分析结果写 Methods 和 Results 初稿"
```

### 方式 3: 论文全流程自动化

```
启动命令: "启动论文生产流水线, 项目 frailty_ml_2026"

Orchestrator 执行:
  Week 1: → research-assistant (文献简报) + data-engineer (数据就绪确认)
  Week 2: → ml-engineer (模型训练+评估) + biostatistician (统计检验)
  Week 3: → clinical-researcher (结果临床审查)
  Week 4: → scientific-writer (初稿生成)
  Week 5: → pi (终审) + biostatistician (统计审查)
  Week 6: → scientific-writer (投稿)
```

## 设计原则

1. **单职责**: 每个 Agent 有明确的能力边界，不越界
2. **输入/输出标准化**: 每个 Agent 定义了明确的输入源和输出格式
3. **可编排**: Orchestrator 可基于依赖关系自动编排多 Agent 协作
4. **可审计**: 每个 Agent 的输出可追溯到具体的 SOP 和决策框架
5. **知识内嵌**: 领域知识 (如 OMOP 映射、衰弱表型定义、因果推断决策树) 直接编码在 prompt 中

## 与 team-roles-sop.md 的关系

- `team-roles-sop.md` 是**人类团队参考手册**——岗位职责、工作方法、团队管理
- `agents/` 目录是本**Agent 系统提示库**——将 SOP 中的工作方法转化为 LLM 可执行的指令

两者结构对齐：每个 Agent 的能力和方法直接对应 SOP 中该岗位的工作方法章节。

## 后续扩展

- [x] 为每个 Agent 编写 Few-shot 示例 (输入→思考→输出)
- [x] 建立共享知识库 (Obsidian vault)
- [x] 设计 Agent 间通信协议 (JSON 消息格式)
- [x] 知识库交互协议 (Agent ↔ Obsidian 读写规范)
- [ ] 实现自动化测试: 给定标准输入, 验证 Agent 输出是否符合规范
- [ ] 基于 LangGraph/CrewAI 实现 Agent 编排引擎

---

## 新增文件

```
agents/
├── README.md                         # 本文件
├── orchestrator.md                   # 科研协调器
├── pi-agent.md                       # 首席研究员
├── computational-biologist-agent.md  # 计算生物学研究员
├── clinical-researcher-agent.md      # 老年医学临床研究员
├── ml-engineer-agent.md              # 机器学习工程师
├── biostatistician-agent.md          # 生物统计学家
├── data-engineer-agent.md            # 数据工程师
├── scientific-writer-agent.md        # 学术写作编辑
├── research-assistant-agent.md       # 科研助理
├── knowledge-base-protocol.md        # Agent ↔ Obsidian 交互协议
├── communication-protocol.md         # Agent 间 JSON 通信协议
└── few-shot/                         # Few-shot 示例
    ├── orchestrator.md               # 任务编排 + 冲突裁决示例
    ├── computational-biologist.md    # 建模方案 + 方法选择示例
    ├── clinical-researcher.md        # 临床操作化 + 模型审查示例
    ├── ml-engineer.md                # 特征工程 + 训练脚本示例
    ├── biostatistician.md            # SAP 撰写 + 统计咨询示例
    ├── data-engineer.md              # 变量可用性评估示例
    ├── scientific-writer.md          # Results/Discussion 写作示例
    ├── research-assistant.md         # 文献扫描 + 笔记入库示例
    └── pi.md                         # FRAME 评估 + 论文终审示例
```

### 知识库 (Obsidian)

```
obsidian/laoNianYiXue/
├── _dashboard.md
├── templates/  (3 个模板)
├── methods/    (3 篇方法笔记)
├── data-sources/ (3 个数据源: CHARLS/CLHLS/UKB)
├── concepts/   (3 个概念: 衰弱/肌少症/衰老时钟)
├── literature/ (仪表盘 + 1 篇示例文献笔记)
└── projects/frailty-ml-2026/ (项目概要 + 研究方案 + 实验记录)
```

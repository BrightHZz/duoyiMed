# DuoyiMed — duoyi 论文工厂

> 一个医生和程序员合作的项目，别人只帮你写论文，而本项目帮你造论文工厂。/This is a joint project by doctors and programmers. While others merely write papers for you, our project builds a full-fledged paper production system.

。基于钱学森工程控制论，覆盖老年医学和泌尿外科从文献检索到临床部署的全流程 LLM Agent 编排引擎。

## 项目组

| 成员 | 单位 | 角色 | 邮箱 |
|------|------|------|------|
| 吴医生 | 武进人民医院泌尿外科 | 泌尿外科 | jsdxwcs@163.com |
| 胥医生 | 金坛人民医院老年医学科 | 老年医学 | 1361600857@qq.com |
| 王多多 | 江南银行信息技术部 | 技术开发 | 1296584078@qq.com |

## 核心理念

将科研流程建模为**多事业部企业**，每个事业部（老年医学 / 泌尿外科）拥有专属 PI、临床研究员和计算生物学研究员，共享数据工程、生物统计、ML 工程、学术写作等公共服务平台。通过 LangGraph 编排引擎实现多 Agent 的并行协作、闸门质量控制和跨阶段反馈返工。

## 架构总览

```
                        首席科学家 / 公司编排器 / PMO
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
  ┌─────────▼──────────┐  ┌────────▼──────────┐
  │  老年医学事业部      │  │  泌尿外科事业部     │
  │  - PI              │  │  - PI             │
  │  - 临床研究员       │  │  - 临床研究员       │
  │  - 计算生物学家     │  │  - 计算生物学家     │
  └─────────┬──────────┘  └────────┬──────────┘
            │                       │
            └───────────────────────┼───────────────────────┘
                                    │
                        ┌───────────▼───────────┐
                        │     公共服务平台        │
                        │  - 数据工程 / 生物统计  │
                        │  - ML 工程 / 学术写作   │
                        │  - 科研辅助 / Humanizer │
                        │  - 临床工具开发         │
                        └───────────────────────┘
```

## 研究流程 (Phase 0-7)

| Phase | 名称 | 执行者 | 产出 |
|-------|------|-------|------|
| Phase 0 | 项目预检 (Preflight) | Python 脚本 | 数据安全扫描、环境检查、SDS 生成 |
| Phase 1 | 临床问题定义 | 临床研究员 / PI | 研究问题操作化、PICO 框架 |
| Phase 2 | 文献系统检索 | 科研助理 | PRISMA 流程图、文献笔记入库 |
| Phase 3 | 建模方案设计 | 计算生物学家 / 生物统计学家 | 建模方案 + SAP |
| Phase 4 | 模型训练与评估 | ML 工程师 / 数据工程师 | 训练脚本、模型文件、AUC 报告 |
| Phase 5 | 结果审查 | 临床研究员 / PI | 临床解读、偏差分析 |
| Phase 6 | 论文撰写与投稿 | 学术写作 / Humanizer | 初稿 → 润色 → 投稿包 |
| Phase 7 | 临床工具部署 | 临床工具开发者 | Streamlit Web 工具、可执行文件打包 |

- **Phase 0-6** 由 `phase6_runner.py` 驱动完整流水线：预检 → 图表 → 表格 → 章节(LLM) → Humanize → 汇编 → Gate 6
- **Phase 7** 由 `clinical-tool-developer` Agent 驱动：模型加载 → 参数导出 → Streamlit 应用生成 → 打包可执行文件

每个 Phase 通过**闸门检查 (Gate Check)**后方可进入下一阶段，支持最多 3 次自动返工。

## 工程控制论特性

- **反馈环 A (Phase 内部)**: Gate 失败 → 自动返工当前 Phase，记录 `ReworkRecord`
- **反馈环 B (跨 Phase 下游触发上游)**: 下游发现问题 → 创建 `ChangeRequest` → 触发上游 Phase 重新执行
- **系统辨识**: 每个 Agent 调用记录 `RunLog`（耗时、token 用量、gate 状态），支持运行分析报告
- **基线管理**: Phase 产出冻结为基线版本，支持版本对比和增量重新执行
- **适应性调度**: 根据项目画像动态调整并行度和资源分配

## 项目结构

```
duoyi/
├── run_research.py              # 主入口 (CLI + 交互模式)
├── research                     # Shell 入口 (./research "问题")
├── engine/                      # 编排引擎
│   ├── config.py                # 全局配置 (多数据源、多知识库)
│   ├── templates/
│   │   └── clinical_app.py      # Streamlit 临床工具模板
│   ├── scripts/
│   │   ├── run_assembly.py      # Phase 6 论文汇编
│   │   ├── run_gate6.py         # Phase 6 闸门检查
│   │   ├── run_humanize.py      # 论文 AI 痕迹消除
│   │   ├── run_preflight.py     # 项目预检
│   │   └── run_webapp.py        # Phase 7 Web 工具启动
│   ├── utils/
│   │   └── rounding.py          # 数值精度工具
│   └── core/
│       ├── orchestrator_graph.py # LangGraph 编排图 (~160KB)
│       ├── state.py              # 状态定义 (TypedDict)
│       ├── agent_loader.py       # Agent Prompt 加载器
│       ├── llm_client.py         # LLM 客户端 (Anthropic/OpenAI/DeepSeek)
│       ├── tools.py              # Agent 工具集 (~64KB, 20+ 工具)
│       ├── gate_checks.py        # 闸门质量检查 (~163KB)
│       ├── phase6_runner.py      # Phase 6 完整流水线
│       ├── consistency_checker.py # 跨阶段一致性校验
│       ├── preflight_scanner.py  # 项目预检
│       ├── data_prefetcher.py    # 数据预取
│       ├── baseline_manager.py   # 技术状态基线管理
│       ├── adaptive_scheduler.py # 适应性调度器
│       ├── project_predictor.py  # 项目画像预测
│       ├── kb_manager.py         # 知识库管理 (Obsidian)
│       ├── run_analyzer.py       # 运行分析报告
│       └── env.py               # 环境配置加载
├── company/                     # 公司模式 Agent 定义
│   ├── management/              # 管理层 (首席科学家/编排器/PMO)
│   ├── divisions/               # 事业部 (老年医学/泌尿外科)
│   ├── shared-services/         # 共享服务 (数据/统计/ML/写作/临床工具)
│   ├── protocols/               # 通信/知识库/接口协议
│   ├── few-shot/                # Few-shot 示例
│   └── reference/               # 参考文献/规则
├── agents/                      # [已弃用] 旧版 Agent 定义 (向后兼容)
├── scripts/                     # 运维脚本 (备份/定时任务)
├── tests/                       # 端到端验收测试
└── outputs/run_logs/            # 运行日志 (系统辨识数据)
```

## 快速开始

### 环境要求

- Python 3.10+
- Anthropic / OpenAI / DeepSeek API Key

### 安装

```bash
git clone https://github.com/BrightHZz/duoyiMed.git
cd duoyi
pip install -r requirements.txt
```

### 配置 API Key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

可选配置（有默认值）：

```bash
export LLM_PROVIDER=anthropic          # anthropic | openai | deepseek
export LLM_MODEL=claude-sonnet-4-6
```

### 使用

需要先安装 Claude Code。进入项目目录，启动 Claude Code 后调用 `duoyi` 技能：

```bash
cd duoyi
claude
```

进入 Claude Code 对话后：

```
/duoyi 用 CHARLS 数据预测 2 年衰弱转换，设计完整方案
/duoyi 近两年表观遗传时钟预测衰弱的文献综述
/duoyi 评估这个建模方案
```

也支持直接命令行传参：

```bash
claude -p "/duoyi 用 CHARLS 数据预测 2 年衰弱转换"
```

### 注意事项

- 需要先设置 `ANTHROPIC_API_KEY` 环境变量

### 工作流类型

| 工作流 | 说明 |
|--------|------|
| `auto` | 自动判断用户意图并路由 |
| `new_project` | 启动新研究项目，完整 Phase 0-7 |
| `literature` | 文献检索与综述 |
| `paper` | 基于已有结果撰写论文 |
| `quick` | 向专家快速咨询 |
| `status` | 查看项目状态 |
| `kb_enrich` | 自主检索最新文献充实知识库 |

## 支持的数据源

| 数据源 | 类型 | 描述 |
|--------|------|------|
| CHARLS | 队列 | 中国健康与养老追踪调查 (≥45 岁) |
| CLHLS | 队列 | 中国老年健康影响因素跟踪调查 (≥65 岁) |
| HRS | 队列 | 美国健康与退休研究 (≥50 岁) |
| ELSA | 队列 | 英国老龄化纵向研究 (≥50 岁) |
| UK Biobank | 队列 | 英国生物银行 (40-69 岁) |
| NHANES | 队列 | 美国国家健康与营养调查 |
| MIMIC-IV | EHR | ICU 电子健康记录数据库 |
| SEER | 登记 | 美国癌症统计数据库 |

## Agent 体系

共 16 个 Agent，分属三个层级：

- **管理层 (3)**: 首席科学家、公司编排器、PMO
- **事业部 (9)**: 老年医学/泌尿外科/儿科各含 PI、临床研究员、计算生物学家
- **共享服务 (7)**: 数据工程师、生物统计学家、ML 工程师、学术写作、科研助理、Humanizer、临床工具开发者

新开发请使用 `company/` 目录下的 Agent 定义，`agents/` 目录保留向后兼容。

## 涉及的关键技术

- **LLM 编排**: LangGraph 状态图、多 Agent 并行/串行调度
- **质量闸门**: 每个 Phase 产出自动校验（AUC 阈值、DOI 验证、统计合规等）
- **反馈控制**: 工程控制论的闭环反馈系统（Phase 内 + 跨 Phase）
- **知识库**: Obsidian vault 双向读写、文献笔记模板化
- **系统辨识**: 运行日志自动采集、运行分析报告生成
- **数据预取**: 基于项目意图自动预取相关数据集头部信息
- **一致性检查**: 跨 Phase 产出物一致性自动校验
- **临床部署**: Phase 7 模型转 Streamlit Web 工具 + PyInstaller 打包

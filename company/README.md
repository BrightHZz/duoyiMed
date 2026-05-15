# DuoyiMed (DuoyiMed)

> 多事业部 LLM Agent 协作平台，覆盖从临床问题定义、数据分析到论文投稿的全流程科研自动化。

## 公司架构

```
                      首席科学家 / 公司编排器 / PMO
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼──────────┐  ┌────────▼──────────┐  ┌────────▼──────────┐
│  老年医学事业部      │  │  泌尿外科事业部     │  │  (未来事业部...)    │
│  Geriatrics Div.   │  │  Urology Div.     │  │                    │
│                    │  │                   │  │                    │
│  - PI              │  │  - PI             │  │                    │
│  - 临床研究员       │  │  - 临床研究员       │  │                    │
│  - 计算生物学家     │  │  - 计算生物学家     │  │                    │
└─────────┬──────────┘  └────────┬──────────┘  └────────┬──────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                      ┌───────────▼───────────┐
                      │     公共服务平台        │
                      │   Shared Services      │
                      │                       │
                      │  - 数据工程团队         │
                      │  - 生物统计团队         │
                      │  - ML 工程团队          │
                      │  - 学术写作团队         │
                      │  - 科研辅助团队         │
                      └───────────────────────┘
```

## 目录结构

```
company/
├── README.md                    # 本文件 — 公司架构总览
├── company-sop.md               # 公司级运营手册
├── management/                  # 管理层
│   ├── chief-scientist.md       # 首席科学家
│   ├── company-orchestrator.md  # 公司编排器
│   └── pmo.md                   # 项目管理办公室
├── divisions/                   # 研究事业部
│   ├── geriatrics/              # 老年医学事业部
│   └── urology/                 # 泌尿外科事业部
├── shared-services/             # 公共服务平台
├── protocols/                   # 公司级协议
│   ├── communication-protocol.md
│   ├── knowledge-base-protocol.md
│   └── division-interface-protocol.md
└── few-shot/                    # Few-shot 示例（按事业部分组）
```

## Agent ID 命名规范

| 命名空间 | 格式 | 示例 |
|---------|------|------|
| 事业部 Agent | `{division}/{role}` | `geriatrics/pi`, `urology/clinical-researcher` |
| 共享服务 | `shared/{role}` | `shared/data-engineer`, `shared/biostatistician` |
| 管理层 | 直接角色名 | `chief-scientist`, `company-orchestrator`, `pmo` |

## 向后兼容

旧版 Agent ID（如 `pi`、`ml-engineer`）通过 `LEGACY_MAP` 自动映射到新 ID，现有脚本和调用方式不受影响。

旧版 `agents/` 目录保留但标记为弃用，新开发应使用 `company/` 下的 Agent 定义。

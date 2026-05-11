# Agent ↔ Obsidian 知识库交互协议 v2.0 — 公司模式

## 多知识库架构

公司模式下，各事业部拥有独立的知识库：

```
老年医学: {OBSIDIAN_HOME}/laoNianYiXue/
泌尿外科: {OBSIDIAN_HOME}/miNiaoWaiKe/
共享项目: {OBSIDIAN_HOME}/shared-projects/
```

共享服务 Agent 根据通信协议中的 `division` 字段自动选择对应的知识库。

## Agent 如何读写知识库

### 读取操作

| 场景 | 操作 | 示例路径 |
|------|------|----------|
| 查看项目状态 | Read `project-brief.md`, 解析 YAML frontmatter 的 `status` 字段 | `projects/{id}/project-brief.md` |
| 查看文献笔记 | Read `literature/{file}.md`, 解析 YAML frontmatter | `literature/2026-xxx.md` |
| 查看研究方案 | Read `protocol.md` | `projects/{id}/protocol.md` |
| 查看实验记录 | Read `experiment-log.md` | `projects/{id}/experiment-log.md` |
| 查询方法参考 | Read `methods/{topic}.md` | `methods/model-selection-guide.md` |
| 查询数据源信息 | Read `data-sources/{name}.md` | `data-sources/charls.md` |
| 查询临床概念 | Read `concepts/{topic}.md` | `concepts/frailty.md` |
| 全局概览 | Read `_dashboard.md` | `_dashboard.md` |

### 写入操作

| 场景 | 操作 | 文件 |
|------|------|------|
| 新建文献笔记 | 读取 `templates/t-literature-note.md`, 填充后写入 | `literature/{year}-{author}-{topic}.md` |
| 更新项目状态 | Edit `project-brief.md` 的 YAML frontmatter `status` 字段 | `projects/{id}/project-brief.md` |
| 追加实验记录 | Edit `experiment-log.md`, 追加新实验 section | `projects/{id}/experiment-log.md` |
| 新增方法笔记 | 直接 Write 新文件 | `methods/{new-topic}.md` |
| 更新文献阅读状态 | Edit `literature/{file}.md` 的 YAML `status` 字段 | `literature/{file}.md` |

### 关键解析规则

1. **YAML frontmatter** 是 Agent 获取结构化信息的入口 — 所有笔记的前置 YAML 必须完整
2. **Wikilinks `[[path|label]]`** 表示知识图谱的边 — Agent 应在回答中特别关注, 用于追踪关联信息
3. **Obsidian 插件 Dataview** 的查询结果依赖 YAML frontmatter 字段 — Agent 写入时必须保证字段名和值的一致性

## 各 Agent 的知识库操作权限

| Agent | 读取 | 写入 | 典型操作 |
|-------|------|------|----------|
| orchestrator | 全部 | projects/ 状态更新 | 查看项目状态, 路由任务 |
| pi | 全部 | projects/ 决策记录 | 终审意见写入 project-brief |
| computational-biologist | literature/ methods/ data-sources/ concepts/ | methods/ (新方法笔记) | 查询方法参考, 设计方案 |
| clinical-researcher | concepts/ literature/ data-sources/ | concepts/ (临床概念更新) | 查询表型定义, 输出临床解读 |
| ml-engineer | methods/ data-sources/ | projects/{id}/experiment-log.md | 追加实验记录, 读取方法指南 |
| biostatistician | methods/ data-sources/ | methods/ (统计方法更新) | 读取 SAP 模板, 写入统计审查意见 |
| data-engineer | data-sources/ methods/omop-cdm-mapping.md | data-sources/ (数据源更新) | 读取变量定义, 写入数据字典 |
| scientific-writer | literature/ projects/ concepts/ | projects/{id}/manuscript.md | 读取文献, 写入论文初稿 |
| research-assistant | literature/ concepts/ | literature/ (新文献笔记) | 写入结构化文献笔记 |

## 自动化工作流示例

### 工作流 1: 研究助理读到一篇新论文

```
1. research-assistant 读取 templates/t-literature-note.md (获取模板)
2. research-assistant 解析论文 PDF/摘要, 提取结构化信息
3. research-assistant 写入 literature/{year}-{firstauthor}-{topic}.md
4. research-assistant 更新 project-brief.md 的 YAML:
    如果有 related_project, 在该项目下添加 [[literature/新文件]]
5. (用户下次打开 Obsidian) Dataview 自动刷新文献列表
```

### 工作流 2: ML 工程师完成一个实验

```
1. ml-engineer 读取 projects/{id}/experiment-log.md (获取当前实验列表)
2. ml-engineer 在 experiment-log.md 末尾追加新实验 section
3. ml-engineer 更新 project-brief.md 的 YAML:
    status: "execution" → "writing" (如果这是最后一个实验)
    "下一步行动" 更新为 "scientific-writer: 开始撰写 Results"
4. orchestrator 检测到状态变更 → 自动通知 scientific-writer
```

### 工作流 3: PI 审查论文

```
1. PI 读取 projects/{id}/project-brief.md (了解项目背景)
2. PI 读取 projects/{id}/protocol.md (了解方法)
3. PI 读取 projects/{id}/experiment-log.md (了解实验结果)
4. PI 给出审查意见, 写入 project-brief.md 的"下一步"字段
5. 状态变更 → orchestrator 通知 scientific-writer 进行修改
```

## Obsidian Dataview 查询兼容性

Agent 写入的所有 YAML frontmatter 字段需要遵循以下约定，确保 Dataview 插件能正确解析：

```yaml
# 标准 YAML frontmatter (Agent 必须遵循的字段约定)
---
type: literature | project | experiment | concept | method | data_source | dashboard
status: unread | skimmed | read | deep_read | proposed | protocol | execution | writing | submitted | published | draft | reference
topics: [list]  # 用于 Dataview WHERE contains()
tags: [list]    # 用于 Obsidian 标签系统
---
```

Agent 应始终确保：同一字段名在不同文件中保持一致（例如不要在某些文件用 `relevance_score` 在另一些用 `relevance`）。

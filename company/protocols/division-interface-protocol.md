# 事业部 ↔ 共享服务接口协议 v1.0

## 设计原则

1. **事业部拥有领域知识，共享服务拥有方法学能力** — 双方通过标准化接口协作
2. **请求可追溯** — 每个服务请求记录发起事业部、时间、优先级
3. **服务可插拔** — 新增事业部无需修改共享服务 Agent 的 core prompt
4. **资源可计量** — PMO 可追踪各事业部对共享服务的使用量

## 1. 服务请求标准格式

事业部通过 company-orchestrator 向共享服务发起请求：

```json
{
  "header": {
    "message_id": "msg_20260508_010",
    "timestamp": "2026-05-08T10:00:00+08:00",
    "from": "geriatrics/clinical-researcher",
    "to": "shared/data-engineer",
    "message_type": "task_request",
    "division": "geriatrics",
    "priority": "normal",
    "project_id": "geri-001"
  },
  "payload": {
    "task_id": "task_010",
    "task_name": "评估 CHARLS 衰弱相关变量可用性",
    "description": "...",
    "division_context": {
      "domain": "geriatrics",
      "data_sources": ["CHARLS"],
      "knowledge_base_hint": "laoNianYiXue"
    },
    "output_format": "data_availability_report",
    "deadline": "2026-05-10T18:00:00+08:00"
  }
}
```

**关键字段**：
- `division`: 发起事业部标识，共享服务据此选择数据源/知识库/领域参数
- `division_context`: 为共享服务提供领域提示（不替代其专业判断）

## 2. 服务响应标准格式

共享服务返回结果给事业部：

```json
{
  "header": {
    "message_type": "task_result",
    "reply_to": "msg_20260508_010",
    "from": "shared/data-engineer",
    "to": "geriatrics/clinical-researcher",
    "division": "geriatrics",
    ...
  },
  "payload": {
    "task_id": "task_010",
    "status": "completed",
    "summary": "CHARLS 2011-2020 五个 wave 的衰弱相关变量可用性已评估",
    "division_specific_notes": {
      "fried_phenotype_coverage": "2013/2015 wave 完整，2011 缺握力",
      "recommended_strategy": "以 2013 作为基线 wave"
    },
    ...
  }
}
```

## 3. 事业部 PI 审批接口

在关键阶段闸门处，事业部 PI 需要审批共享服务的产出：

```
共享服务产出 → 事业部 PI 审批 → 通过 → 闸门打开
                              → 驳回 → 返回共享服务修正
```

审批消息格式：
```json
{
  "header": {
    "message_type": "review_result",
    "from": "geriatrics/pi",
    "to": "shared/biostatistician",
    "division": "geriatrics",
    ...
  },
  "payload": {
    "verdict": "approved | approved_with_changes | rejected",
    "items": [...],
    "escalate_to_chief_scientist": false
  }
}
```

## 4. 跨事业部咨询接口

当一个事业部需要另一个事业部的领域知识时（如老年医学需要泌尿外科对老年前列腺问题的意见）：

```json
{
  "header": {
    "message_type": "query_request",
    "from": "geriatrics/clinical-researcher",
    "to": "urology/clinical-researcher",
    "message_type": "cross_division_consult",
    "division": "geriatrics",
    "consulting_division": "urology",
    ...
  },
  "payload": {
    "question": "社区居住老年男性的 BPH 患病率及 IPSS 随年龄变化趋势？",
    "context": "我们在设计老年综合评估方案，需要泌尿外科的 BPH 流行病学数据",
    "urgency": "normal"
  }
}
```

## 5. 共享服务切换协议

当一个共享服务完成当前事业部的任务并切换到下一个排队的事业部时：

```
shared/data-engineer:
  busy ← geriatrics/geri-001 (已完成)
    → 通知 PMO 任务完成
    → PMO 检查队列: [urology/uro-001, geriatrics/geri-002]
    → PMO 分配下一任务: urology/uro-001
    → data-engineer 切换 division context 为 urology
  busy ← urology/uro-001 (开始)
```

切换时，共享服务 Agent 会收到 division context 更新通知：
```json
{
  "header": {
    "message_type": "status_update",
    "from": "pmo",
    "to": "shared/data-engineer",
    ...
  },
  "payload": {
    "context_switch": {
      "from_division": "geriatrics",
      "to_division": "urology",
      "new_project_id": "uro-001",
      "new_data_sources": ["MIMIC-IV"]
    }
  }
}
```

## 6. Agent ID 命名空间

| 命名空间 | 格式 | 说明 |
|---------|------|------|
| `geriatrics/{role}` | 老年医学事业部 | 事业部专属 Agent |
| `urology/{role}` | 泌尿外科事业部 | 事业部专属 Agent |
| `pediatrics/{role}` | 儿科事业部 | 事业部专属 Agent |
| `shared/{role}` | 共享服务 | 所有事业部共享 |
| `chief-scientist` | 首席科学家 | 公司管理层 |
| `company-orchestrator` | 公司编排器 | 公司管理层 |
| `pmo` | 项目管理办公室 | 公司管理层 |

## 7. 新增事业部的接口契约

当新增一个事业部时，必须满足：
1. 至少提供 3 个 Agent：`{new_div}/pi`、`{new_div}/clinical-researcher`、`{new_div}/computational-biologist`
2. 在 company-orchestrator 中注册事业部路由关键词
3. 创建事业部知识库 (Obsidian vault)
4. 在 PMO 项目面板中注册事业部
5. 共享服务 Agent 的 Division Context Detection 中添加新事业部的识别规则

# Agent 间 JSON 通信协议 v2.0 — 公司模式

## v2.0 变更 (vs v1.0)

- **新增**: `header.division` 字段 — 标识消息所属的事业部
- **新增**: Agent ID 命名空间 — `{division}/{role}` 和 `shared/{role}`
- **新增**: 消息类型 `division_request`、`resource_request`、`division_report`
- **兼容**: v1.0 格式的消息仍可被解析（division 字段为 optional）

## 设计原则

1. **统一信封格式** — 所有消息共享相同的外层结构，便于路由和日志
2. **类型驱动** — `message_type` 决定内层 `payload` 的 schema
3. **可追溯** — 每条消息有唯一 ID，请求-响应通过 `reply_to` 关联
4. **事业部感知** — 消息携带 `division` 字段，便于共享服务识别服务对象
5. **人机可读** — JSON 格式，同时可被 Obsidian 知识库存储

---

## 1. 消息信封 (Envelope)

所有 Agent 间通信的通用外层结构：

```json
{
  "header": {
    "message_id": "msg_20260504_001",
    "reply_to": "msg_20260504_000",
    "timestamp": "2026-05-04T14:30:00+08:00",
    "from": "orchestrator",
    "to": "computational-biologist",
    "message_type": "task_request",
    "priority": "normal",
    "project_id": "frailty_ml_2026"
  },
  "payload": {
    // 根据 message_type 不同而变化，见下文
  }
}
```

### header 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message_id` | string | ✓ | 唯一 ID，格式 `msg_{date}_{seq}` |
| `reply_to` | string | | 回复的目标消息 ID |
| `timestamp` | string | ✓ | ISO 8601 + 时区 |
| `from` | string | ✓ | 发送方 agent id (含命名空间) |
| `to` | string | ✓ | 接收方 agent id，`broadcast` 表示全员 |
| `message_type` | string | ✓ | 消息类型，决定 payload schema |
| `division` | string | | 事业部标识: `geriatrics` / `urology` / `shared` / `management` |
| `priority` | string | | `low` / `normal` / `high` / `critical` |
| `project_id` | string | | 关联的研究项目 ID |

---

## 2. 消息类型定义

### 2.1 task_request — 分配任务

Orchestrator → Agent，要求执行某个任务。

```json
{
  "header": { "message_type": "task_request", ... },
  "payload": {
    "task_id": "task_001",
    "task_name": "设计衰弱预测建模方案",
    "description": "基于 CHARLS 数据，设计一个预测 2 年衰弱转换的 ML 方案",
    "input": {
      "clinical_question": {
        "source": "clinical-researcher",
        "message_id": "msg_20260504_005",
        "summary": "衰弱定义采用 Fried Phenotype，预测窗口 2 年"
      },
      "data_available": {
        "source": "data-engineer",
        "message_id": "msg_20260504_003",
        "summary": "CHARLS Waves 1-4, Health_Status_and_Functioning + Biomarker + Blood",
        "path": "{CHARLS_DATA_DIR}/"
      },
      "literature_context": {
        "source": "research-assistant",
        "message_id": "msg_20260504_002",
        "key_papers": ["2025-zhang-frailty-xgboost"]
      }
    },
    "output_format": "modeling_proposal",
    "output_destination": {
      "type": "obsidian",
      "path": "projects/frailty_ml_2026/modeling-plan.md"
    },
    "deadline": "2026-05-07T18:00:00+08:00",
    "depends_on": ["msg_20260504_005", "msg_20260504_003"]
  }
}
```

### 2.2 task_result — 任务完成

Agent → Orchestrator，提交任务执行结果。

```json
{
  "header": {
    "message_type": "task_result",
    "reply_to": "msg_20260504_001",
    ...
  },
  "payload": {
    "task_id": "task_001",
    "status": "completed",
    "summary": "设计了基于 XGBoost 的衰弱预测方案，推荐 78 个候选特征",
    "output": {
      "obsidian_page": "projects/frailty_ml_2026/modeling-plan.md",
      "key_decisions": [
        {
          "decision": "选择 XGBoost 作为主模型",
          "rationale": "表格数据 + 中等样本量 + 需要非线性交互"
        },
        {
          "decision": "使用 nested CV 防止信息泄露",
          "rationale": "特征选择必须在 CV 内部进行"
        }
      ],
      "next_actions": [
        {
          "action": "实现基线 Logistic Regression",
          "assignee": "ml-engineer",
          "estimated_hours": 4
        }
      ]
    },
    "artifacts": [
      {
        "type": "obsidian_page",
        "path": "projects/frailty_ml_2026/modeling-plan.md"
      }
    ],
    "warnings": [
      "2011 wave 无握力数据，基线功能评估需依赖 2013 wave 或使用替代指标"
    ],
    "blocks": []
  }
}
```

### 2.3 query_request — 请求信息

Agent A → Agent B（经 Orchestrator 路由），请求特定信息。

```json
{
  "header": { "message_type": "query_request", ... },
  "payload": {
    "query_id": "q_001",
    "query_type": "clinical_definition",
    "question": "CHARLS 中如何操作化 Fried 衰弱的 5 项标准？每项对应哪个变量？",
    "context": "需要用于 ML 模型的结局变量定义",
    "urgency": "normal"
  }
}
```

### 2.4 query_response — 信息回复

```json
{
  "header": {
    "message_type": "query_response",
    "reply_to": "msg_xxx_q_001",
    ...
  },
  "payload": {
    "query_id": "q_001",
    "answer": {
      "fried_phenotype_mapping": {
        "weight_loss": {
          "wave": "all",
          "variable": "da049 (自报体重变化)",
          "threshold": "1年内体重下降 ≥5kg 或 ≥5%",
          "notes": "2011 wave 变量名可能不同, 需查 codebook"
        },
        "exhaustion": {
          "wave": "all",
          "variable": "CES-D: dc011 + dc012",
          "threshold": "任一问题 ≥3天/周",
          "notes": "CES-D 10项版中的疲乏相关两项"
        },
        "low_grip_strength": {
          "wave": "2013, 2015",
          "variable": "Biomarker 文件中的握力测量",
          "threshold": "按性别+BMI四分位的最低20%",
          "notes": "2011 无握力, 需特殊处理"
        },
        "slow_gait_speed": {
          "wave": "2013, 2015",
          "variable": "Health_Status 中的计时行走",
          "threshold": "按性别+身高四分位的最低20%",
          "notes": "2.5m 步行计时"
        },
        "low_physical_activity": {
          "wave": "all",
          "variable": "da051 (体力活动频率+强度)",
          "threshold": "按性别的最低20%",
          "notes": "需将频率×强度转换为每周代谢当量"
        }
      }
    },
    "references": [
      "concepts/frailty.md",
      "CHARLS_codebook/2013_CHARLS_Wave2_CodeBook.pdf"
    ],
    "confidence": "high",
    "caveats": [
      "2011 wave 需特殊处理握力缺失",
      "各 wave 的体力活动问题措辞有变化, 需对齐"
    ]
  }
}
```

### 2.5 review_request — 请求审查

Agent → 特定审查者，请求审查一份产出。

```json
{
  "header": { "message_type": "review_request", ... },
  "payload": {
    "review_id": "rev_001",
    "review_type": "statistical_methods",
    "target": {
      "type": "obsidian_page",
      "path": "projects/frailty_ml_2026/protocol.md",
      "section": "5. 统计方法"
    },
    "review_checklist": [
      "缺失数据处理方法是否合理",
      "验证策略是否正确",
      "评估指标是否完整",
      "敏感性分析是否充分"
    ],
    "deadline": "2026-05-06T18:00:00+08:00"
  }
}
```

### 2.6 review_result — 审查意见

```json
{
  "header": {
    "message_type": "review_result",
    "reply_to": "msg_xxx_rev_001",
    ...
  },
  "payload": {
    "review_id": "rev_001",
    "verdict": "approved_with_minor_changes",
    "items": [
      {
        "checkpoint": "缺失数据处理方法是否合理",
        "status": "pass",
        "comment": "MICE m=10 合理, 建议补充 MAR 假设的论证"
      },
      {
        "checkpoint": "验证策略是否正确",
        "status": "minor_issue",
        "comment": "Nested CV 描述正确, 但需明确外环是 10-fold 还是 5-fold",
        "suggestion": "统一为 5-fold nested CV, 老年医学文献常用"
      },
      {
        "checkpoint": "敏感性分析是否充分",
        "status": "major_issue",
        "comment": "缺少'以死亡为竞争风险'的敏感性分析",
        "suggestion": "增加 Fine-Gray 竞争风险模型作为敏感性分析, 参见 methods/causal-inference-choices.md"
      }
    ],
    "summary": "整体方法学设计合理, 2 项小修后可通过",
    "revision_required": true
  }
}
```

### 2.7 status_update — 状态变更

Agent → Orchestrator，通知自身状态变化。

```json
{
  "header": { "message_type": "status_update", ... },
  "payload": {
    "agent": "ml-engineer",
    "previous_status": "idle",
    "current_status": "busy",
    "current_task": "task_003_xgboost_training",
    "progress_pct": 60,
    "eta": "2026-05-06T12:00:00+08:00",
    "blocks": []
  }
}
```

### 2.8 broadcast — 广播通知

Orchestrator → 所有 Agent，通知全团队事项。

```json
{
  "header": {
    "message_type": "broadcast",
    "to": "broadcast",
    ...
  },
  "payload": {
    "topic": "新文献简报",
    "content": "research-assistant 完成 2026年5月第1周文献扫描, 3篇高相关论文已存入文献库",
    "links": [
      "literature/2026-wang-multimorbidity-clustering.md",
      "literature/2026-chen-sarcopenia-dl.md"
    ],
    "action_required": false
  }
}
```

### 2.9 error — 错误报告

任何 Agent → Orchestrator。

```json
{
  "header": { "message_type": "error", "priority": "high", ... },
  "payload": {
    "error_code": "DATA_NOT_FOUND",
    "error_message": "CHARLS 2011 wave Biomarker 文件缺少握力变量",
    "context": {
      "task_id": "task_001",
      "attempted_operation": "读取 2011_biomarkers.dta 中的握力字段",
      "expected_variable": "grip_strength_kg"
    },
    "suggested_mitigation": "使用 2013 wave 作为基线, 或使用 2011 其他功能指标替代",
    "escalate_to": "clinical-researcher"
  }
}
```

---

## 3. 标准化输出格式 (output_format)

当 `task_request` 中指定 `output_format` 时，Agent 的输出必须遵循对应 schema。

### 3.1 modeling_proposal (建模方案)

```json
{
  "output_format": "modeling_proposal",
  "content": {
    "clinical_to_ml_mapping": {
      "clinical_question": "string",
      "ml_task": "classification | regression | survival | clustering",
      "outcome_definition": "string",
      "prediction_window": "string"
    },
    "data_overview": {
      "source": "string",
      "expected_sample_size": "number",
      "candidate_features_count": "number",
      "expected_missing_rate": "string"
    },
    "methods": {
      "baseline_model": "string",
      "primary_model": "string",
      "advanced_model": "string (optional)",
      "feature_selection": "string",
      "validation_strategy": "string"
    },
    "evaluation_plan": {
      "primary_metric": "string",
      "secondary_metrics": ["string"],
      "calibration": "string",
      "clinical_utility": "string"
    },
    "risks_and_mitigations": [
      { "risk": "string", "severity": "low | medium | high", "mitigation": "string" }
    ]
  }
}
```

### 3.2 statistical_analysis_plan (统计分析计划)

```json
{
  "output_format": "statistical_analysis_plan",
  "content": {
    "study_design": "string",
    "sample_size_calculation": {
      "effect_size": "number",
      "alpha": 0.05,
      "power": 0.80,
      "required_n": "number",
      "with_attrition": "number",
      "software": "string"
    },
    "primary_analysis": {
      "model": "string",
      "adjustment_strategy": "string",
      "missing_data": "string",
      "sensitivity_analyses": ["string"]
    },
    "subgroup_analyses": ["string"],
    "software_packages": ["string"]
  }
}
```

### 3.3 clinical_review (临床审查)

```json
{
  "output_format": "clinical_review",
  "content": {
    "predictor_plausibility": {
      "reasonable": ["string"],
      "questionable": ["string"],
      "anomalous": ["string"]
    },
    "performance_assessment": {
      "discrimination": { "value": "number", "verdict": "adequate | borderline | inadequate" },
      "calibration": { "verdict": "good | acceptable | poor" },
      "clinical_net_benefit": { "verdict": "present | absent", "threshold_range": "string" }
    },
    "translation_recommendation": "proceed | revise | abandon",
    "specific_concerns": ["string"]
  }
}
```

### 3.4 literature_note (文献笔记)

```json
{
  "output_format": "literature_note",
  "content": {
    "frontmatter": {
      "type": "literature",
      "title": "string",
      "first_author": "string",
      "year": "number",
      "journal": "string",
      "doi": "string",
      "topics": ["string"],
      "status": "unread | skimmed | read | deep_read",
      "relevance_score": "number"
    },
    "one_liner": "string",
    "technical_details": {
      "data_source": "string",
      "sample_size": "number",
      "method": "string",
      "outcome": "string",
      "key_result": "string",
      "validation": "string"
    },
    "relevance_to_us": {
      "actionable": ["string"],
      "gaps": ["string"]
    },
    "detailed_notes": "string"
  }
}
```

---

## 4. 状态机 (Agent State Machine)

每个 Agent 在任务执行过程中处于以下状态之一，通过 `status_update` 消息报告：

```
         ┌─────────┐
         │  idle   │ ←──────┐
         └────┬────┘        │
              │             │
    task_request received    │
              │             │
         ┌────▼────┐        │
         │  busy   │        │
         └────┬────┘        │
              │             │
    ┌─────────┼─────────┐   │
    │         │         │   │
┌───▼───┐ ┌──▼──┐ ┌───▼───┐ │
│completed│ │error│ │blocked│ │
└───┬───┘ └──┬──┘ └───┬───┘ │
    │        │        │      │
    └────────┴────────┘      │
             │               │
    orchestrator 分配新任务 ──┘
```

## 5. 编排示例：一个完整的任务链

### 场景：启动衰弱预测项目

```
Step 1: Orchestrator → 并行发送
┌──────────────────────────────────────────────
│ msg_001: task_request → clinical-researcher
│   task: "定义衰弱操作化方案 + 纳入排除标准"
│
│ msg_002: task_request → data-engineer  
│   task: "评估 CHARLS 各 wave 衰弱相关变量可用性"
│
│ msg_003: task_request → research-assistant
│   task: "扫描近2年衰弱预测 ML 文献"
└──────────────────────────────────────────────

Step 2: 各 Agent → Orchestrator (task_result)
┌──────────────────────────────────────────────
│ msg_004: clinical-researcher → result
│   Fried Phenotype 在 CHARLS 中的变量映射表
│
│ msg_005: data-engineer → result  
│   各 wave 变量覆盖矩阵, 缺失率报告
│
│ msg_006: research-assistant → result
│   3 篇高相关文献的结构化笔记
└──────────────────────────────────────────────

Step 3: Orchestrator → computational-biologist (依赖 Step 2 全部完成)
┌──────────────────────────────────────────────
│ msg_007: task_request → computational-biologist
│   task: "设计建模方案"
│   input: { msg_004, msg_005, msg_006 }
└──────────────────────────────────────────────

Step 4: computational-biologist → Orchestrator
┌──────────────────────────────────────────────
│ msg_008: task_result
│   modeling-plan.md 已写入 Obsidian
│   建议下一步: biostatistician 撰写 SAP
└──────────────────────────────────────────────

... 依此类推
```

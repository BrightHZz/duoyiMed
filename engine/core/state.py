"""LangGraph 状态定义"""

from typing import TypedDict, Annotated, Optional, Any, Literal
from datetime import datetime
import operator
from enum import Enum


class GateStatus(str, Enum):
    PASS = "pass"
    COND_PASS = "conditional_pass"
    FAIL = "fail"


class GateCheckItem(TypedDict):
    """单个闸门检查项"""
    check_id: str           # e.g. "auc_threshold", "doi_verified"
    description: str        # e.g. "AUC >= 0.70"
    check_type: str         # "auto" | "llm" | "heuristic"
    result: str             # "pass" | "fail" | "skip"
    detail: str             # 详细说明 (失败时说明原因)


class GateResult(TypedDict):
    """一个 Phase 的闸门检查结果"""
    phase_id: str
    gate_id: str            # e.g. "gate_1"
    timestamp: str
    status: str             # pass | conditional_pass | fail
    checks: list[GateCheckItem]
    conditions: list[str]   # COND_PASS 时附带的条件
    rework_count: int       # 已返工次数
    max_rework: int         # 最大允许返工次数 (默认 3)


class ReworkRecord(TypedDict):
    """返工记录 (跨 Phase 反馈)"""
    from_phase: str         # 触发返工的 Phase
    to_phase: str           # 被返工的 Phase
    reason: str
    timestamp: str
    rework_count: int
    auto_detected: bool     # 🆕 是否由反馈环B自动检测 (True) vs 人工触发 (False)
    severity: str           # 🆕 critical | high | normal


class RunLog(TypedDict):
    """单次 Agent 调用的运行日志 (系统辨识数据源)"""
    timestamp: str          # ISO 格式时间戳
    project_id: str         # 项目 ID
    division: str           # 事业部
    phase_id: str           # 当前 Phase
    agent_id: str           # Agent ID
    success: bool           # 调用是否成功
    degraded: bool          # 是否使用降级模型
    wall_time_sec: float    # 端到端耗时 (秒)
    input_tokens: int       # prompt tokens
    output_tokens: int      # completion tokens
    output_len: int         # 输出字符数
    error_type: str         # 失败时的错误类型 (成功为空)
    gate_status: str        # pass | cond_pass | fail | skip (调用时先记 skip, Gate 后回填)
    rework_of: str          # 空=首次执行, 否则=返工来源 phase_id


class BaselineRecord(TypedDict):
    """技术状态基线 — Phase 产出的冻结版本 (钱学森总体设计部)"""
    baseline_id: str           # "frailty_ml_2026/phase1/v1.0"
    project_id: str
    phase_id: str
    version: str               # "1.0"
    status: str                # "frozen" | "superseded" | "active"
    artifacts: dict[str, str]  # {agent_id: content_hash_md5}
    gate_result: dict          # 冻结时的 Gate 检查结果快照
    timestamp: str
    frozen_by: str             # "orchestrator"


class ChangeRequest(TypedDict):
    """变更请求 — 下游触发上游修改的正式记录"""
    cr_id: str                 # "CR-frailty_ml_2026-001"
    project_id: str
    from_phase: str            # 发现问题的 Phase
    to_phase: str              # 需要修改的 Phase
    reason: str
    affected_artifacts: list[str]    # 受影响的产出物
    downstream_impact: list[str]     # 受影响的下游 Phase
    status: str                # "open" | "implemented" | "closed"
    trigger_type: str          # "feedback_b" | "gate_fail" | "manual"
    created_at: str
    resolved_at: str           # 空=未解决


class BaselineDiff(TypedDict):
    """两个基线版本的差异"""
    baseline_old: str
    baseline_new: str
    changed_artifacts: list[str]
    unchanged_artifacts: list[str]
    requires_full_rerun: bool
    summary: str


class Message(TypedDict):
    """一条 Agent 间消息 (对齐 communication-protocol.md)"""
    message_id: str
    reply_to: Optional[str]
    timestamp: str
    from_agent: str
    to_agent: str
    message_type: str  # task_request | task_result | query_request | query_response | review_request | review_result | status_update | broadcast | error
    priority: str  # low | normal | high | critical
    project_id: Optional[str]
    payload: dict


class AgentTask(TypedDict):
    """分配给 Agent 的任务"""
    task_id: str
    agent_id: str
    task_name: str
    description: str
    input_context: dict  # 上游 agent 的输出引用
    output_format: Optional[str]  # modeling_proposal | statistical_analysis_plan | clinical_review | literature_note
    status: str  # pending | running | completed | error | blocked
    result: Optional[dict]
    error: Optional[str]


class ProjectState(TypedDict):
    """单个研究项目的状态"""
    project_id: str
    title: str
    status: str  # proposed | protocol | execution | writing | submitted | published
    current_phase: str
    phases: dict  # {phase_name: status}
    tasks: list[AgentTask]
    blockers: list[str]
    next_actions: list[str]
    gate_results: dict          # {phase_id: GateResult}
    rework_history: list         # list[ReworkRecord]
    llm_blocked: bool            # LLM 是否不可用导致项目暂停
    sds: Optional[str]           # Phase 0 生成的系统设计说明书 (SDS)


class DivisionState(TypedDict):
    """事业部状态"""
    division_id: str
    division_name: str
    pi_agent_id: str
    projects: list[str]
    status: str  # idle | active | overloaded


class SharedServicePoolState(TypedDict):
    """共享服务资源池状态"""
    service_id: str
    current_task: Optional[str]
    serving_division: Optional[str]
    queue: list[dict]  # pending requests [{division, project_id, priority}]


class OrchestratorState(TypedDict):
    """LangGraph 的全局编排状态"""
    # --- 用户输入 ---
    user_request: str
    user_intent: str  # new_project | literature_review | paper_writing | quick_consult | status_check

    # --- 公司模式 ---
    active_division: str  # "geriatrics" | "urology"
    division_state: dict  # {division_id: DivisionState}

    # --- 任务编排 ---
    tasks: Annotated[list[AgentTask], operator.add]  # 所有任务列表, 用 add reducer 追加
    current_phase: str
    completed_phases: list[str]

    # --- 消息队列 ---
    messages: Annotated[list[Message], operator.add]

    # --- Agent 输出聚合 ---
    agent_outputs: dict  # {agent_id: {output_key: value}}

    # --- 项目状态 ---
    project_id: Optional[str]
    project_state: Optional[ProjectState]

    # --- 响应给用户 ---
    response_to_user: str

    # --- 控制流 ---
    next_action: str  # continue | ask_user | end
    errors: list[str]

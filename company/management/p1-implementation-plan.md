# P1 实现方案：闸门检查记录化 + LLM 容错

> 基于钱学森工程控制论优化方案 §P1，2026-05-10

---

## 一、P1-1：闸门检查记录化

### 1.1 现状

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
```

`_run_project_workflow()` 中的 `for phase_id in phases_to_run` 循环是无闸门的——一个 Phase 执行完直接进下一个 Phase。`_execute_phase()` 只收集 Agent 输出，不做质量判定。问题：

- 没有"这个 Phase 通过了吗？"的显式检查
- Oral agreement ("差不多可以了") 代替了闸门
- 下游发现问题后无正式重入机制

### 1.2 目标架构

```
Phase N 执行完成
       │
       ▼
┌─ Gate N 检查 ──────────────────────┐
│                                     │
│  Auto Checks (脚本化):              │
│  □ AUC >= 0.70                     │
│  □ calibration_slope in [0.9, 1.1]│
│  □ DOI verification passed         │
│  □ 参考文献数量 >= 25               │
│  □ Conclusion is ## (not ###)      │
│                                     │
│  LLM Checks (需判断):               │
│  □ 研究设计合理?                    │
│  □ 表型定义可操作化?                │
│  □ 缺失处理方案完整?               │
│                                     │
├─ Gate Result ──────────────────────┤
│                                     │
│  ✅ PASS        → Phase N+1        │
│  ⚠️  COND_PASS  → Phase N+1 (附条件) │
│  ❌ FAIL        → Phase N 返工      │
│                                     │
└─────────────────────────────────────┘
```

### 1.3 需要修改的文件

| 文件 | 改动 | 工作量 |
|------|------|--------|
| `engine/core/state.py` | 新增 `GateResult` 类型 + `ProjectState` 新增 gate_results 字段 | 15 行 |
| `engine/core/orchestrator_graph.py` | 新增 `_check_gate()` 方法；修改 `_run_project_workflow()` 加闸门循环 | ~80 行 |
| `company/company-sop.md` | 每个 Phase 新增 Gate 检查清单 | ~40 行 |
| `engine/core/gate_checks.py` | **新文件**：自动化 Gate 检查函数集 | ~120 行 |

### 1.4 state.py 改动

```python
# 新增
from enum import Enum

class GateStatus(str, Enum):
    PASS = "pass"
    COND_PASS = "conditional_pass"  # 通过但附条件
    FAIL = "fail"

class GateCheckItem(TypedDict):
    """单个检查项"""
    check_id: str           # e.g. "auc_threshold", "doi_verified"
    description: str        # e.g. "AUC >= 0.70"
    check_type: str         # "auto" | "llm" | "heuristic"
    result: str             # "pass" | "fail" | "skip"
    detail: str             # 详细说明

class GateResult(TypedDict):
    """一个 Phase 的闸门检查结果"""
    phase_id: str
    gate_id: str            # e.g. "gate_1"
    timestamp: str
    status: str             # pass | conditional_pass | fail
    checks: list[GateCheckItem]
    conditions: list[str]   # 如果是 COND_PASS, 列出附带的待修正条件
    rework_count: int       # 本 Phase 已返工次数
    max_rework: int         # 最大允许返工次数 (默认 3)

class ProjectState(TypedDict):
    # ... 现有字段 ...
    gate_results: dict      # 新增：{phase_id: GateResult}
    rework_history: list    # 新增：返工记录 [{from_phase, to_phase, reason, timestamp}]
```

### 1.5 orchestrator_graph.py 改动

**新增两个方法**:

```python
def _check_gate(self, phase_id: str, outputs: dict, project_id: str) -> GateResult:
    """
    对指定 Phase 的输出执行闸门检查。
    
    1. 执行所有 auto checks (从 gate_checks.py 加载)
    2. 对于需要 LLM 判断的检查项，调用 PI/Chief-Scientist 做闸门审查
    3. 汇总结果，返回 GateResult
    """
    gate_def = GATE_DEFINITIONS.get(phase_id, {})
    checks = []
    
    # 自动化检查
    for check_id, check_fn in gate_def.get("auto_checks", {}).items():
        try:
            passed, detail = check_fn(outputs, self)
            checks.append(GateCheckItem(
                check_id=check_id,
                description=check_fn.__doc__ or check_id,
                check_type="auto",
                result="pass" if passed else "fail",
                detail=detail,
            ))
        except Exception as e:
            checks.append(GateCheckItem(
                check_id=check_id,
                result="fail",
                detail=f"检查异常: {e}",
            ))
    
    # LLM 审查 (发 PI 做闸门审查)
    llm_checks = gate_def.get("llm_checks", [])
    if llm_checks:
        pi_output = self._call_agent(
            f"{self.active_division}/pi",
            self._build_gate_review_input(phase_id, outputs, llm_checks, project_id),
        )
        # 解析 PI 的闸门审查结论
        checks += self._parse_gate_review(pi_output, llm_checks)
    
    # 判定整体状态
    fail_count = sum(1 for c in checks if c["result"] == "fail")
    cond_count = sum(1 for c in checks if c["result"] == "conditional")
    
    return GateResult(
        phase_id=phase_id,
        gate_id=f"gate_{phase_id}",
        timestamp=datetime.now().isoformat(),
        status="fail" if fail_count > 0 else ("conditional_pass" if cond_count > 0 else "pass"),
        checks=checks,
        conditions=[c["detail"] for c in checks if c["result"] == "conditional"],
        rework_count=prev_result["rework_count"] + 1 if prev_result else 0,
        max_rework=3,
    )
```

**修改 `_run_project_workflow()`**:

```python
def _run_project_workflow(self, user_request: str, intent: dict) -> str:
    project_id = intent.get("project_id") or f"project_{int(time.time())}"
    all_outputs = {}
    gate_results = {}       # 新增
    rework_history = []     # 新增
    
    phases_to_run = ["problem_definition", "design", "execution", 
                     "external_validation", "review", "writing"]
    
    phase_index = 0
    while phase_index < len(phases_to_run):
        phase_id = phases_to_run[phase_index]
        
        # 执行 Phase
        phase_result = self._execute_phase(phase_id, user_request, 
                                           upstream_outputs, project_id)
        all_outputs[phase_id] = phase_result
        
        # 🆕 闸门检查
        gate_result = self._check_gate(phase_id, phase_result, project_id)
        gate_results[phase_id] = gate_result
        
        if gate_result["status"] == "pass":
            phase_index += 1  # 前进
        
        elif gate_result["status"] == "conditional_pass":
            # 附加条件前进，条件写入下游 Agent 的 task_input
            all_outputs[phase_id]["_gate_conditions"] = gate_result["conditions"]
            phase_index += 1
        
        elif gate_result["status"] == "fail":
            if gate_result["rework_count"] >= gate_result["max_rework"]:
                # 超过最大返工次数 → 升级到首席科学家
                self._escalate_to_chief(phase_id, gate_result, project_id)
                break
            # 返工：重新执行本 Phase (phase_index 不变)
            rework_history.append({
                "phase": phase_id,
                "reason": [c for c in gate_result["checks"] if c["result"]=="fail"],
                "rework_count": gate_result["rework_count"],
            })
            # 🆕 反馈环 B: 如果是下游发现问题触发的返工, 记录跨 Phase 反馈
            self._log_cross_phase_feedback(rework_history)
    
    return self._aggregate_all_phases(phases_to_run, all_outputs, project_id, gate_results)
```

### 1.6 gate_checks.py — 新文件

```python
"""
自动化闸门检查函数集
每个 check 函数签名: (outputs: dict, orchestrator) -> (passed: bool, detail: str)
"""

# --- Phase 1: 问题定义 ---

def check_literature_precheck_exists(outputs, orch):
    """文献预检报告是否存在"""
    for agent_id, output in outputs.items():
        if "research-assistant" in agent_id and "文献预检" in output:
            return True, "文献预检报告已生成"
    return False, "research-assistant 未输出文献预检报告"

def check_frame_assessment_complete(outputs, orch):
    """FRAME 评估是否完整 (含五点维度)"""
    pi_output = ""
    for agent_id, output in outputs.items():
        if "pi" in agent_id.lower():
            pi_output = output
            break
    required = ["F", "R", "A", "M", "E"]
    missing = [r for r in required if r not in pi_output]
    if missing:
        return False, f"FRAME 评估缺少维度: {missing}"
    return True, "FRAME 五维评估完整"

# --- Phase 3: 内部验证 ---

def check_auc_threshold(outputs, orch):
    """AUC >= 0.70 (分类模型最低可接受阈值)"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id:
            import re
            aucs = re.findall(r'auc.?roc.?[=:]?\s*0?\.(\d+)', output.lower())
            if aucs:
                auc_val = float(f"0.{aucs[0]}")
                if auc_val >= 0.70:
                    return True, f"AUC={auc_val:.3f} >= 0.70"
                else:
                    return False, f"AUC={auc_val:.3f} < 0.70, 模型区分度不足"
    return False, "未找到 AUC 值"

def check_baseline_included(outputs, orch):
    """是否包含 Logistic Regression / Cox PH baseline"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id:
            has_lr = any(w in output.lower() for w in ["logisticregression", "logistic regression", "logistic"])
            has_cox = any(w in output.lower() for w in ["coxph", "cox ph", "cox proportional"])
            if has_lr or has_cox:
                return True, "Baseline 模型已包含"
            return False, "缺少 baseline 模型 (Logistic Regression / Cox PH)"
    return False, "未找到 ml-engineer 输出"

def check_n_jobs_safe(outputs, orch):
    """n_jobs 是否设为安全值 (≤2)"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id:
            import re
            dangerous = re.findall(r'n_jobs\s*[=:]\s*(-?\d+)', output)
            for val in dangerous:
                n = int(val)
                if n == -1 or n > 2:
                    return False, f"n_jobs={n} 可能触发 OOM"
            return True, "n_jobs 安全"
    return True, "跳过 (无 ml-engineer 输出)"

# --- Phase 6: 论文撰写 ---

def check_conclusion_heading_level(outputs, orch):
    """Conclusion 是否为 ## heading (而非 ###)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id or "writing" in agent_id:
            if "### Conclusion" in output and "## Conclusion" not in output:
                return False, "Conclusion 是 ### (子章节), 应为 ## (独立章节)"
            if "## Conclusion" in output:
                return True, "Conclusion 为 ## 独立章节"
    return True, "跳过 (未检测到 Conclusion 内容)"

def check_doi_verification(outputs, orch):
    """DOI 验证报告是否存在"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id:
            if "DOI Verification" in output:
                if "fake" in output.lower() and "0 fake" not in output.lower():
                    return False, "存在 fake DOI, 需替换后重新验证"
                return True, "DOI 验证通过"
            return False, "缺少 DOI 验证报告"
    return True, "跳过"

def check_ref_count(outputs, orch):
    """参考文献数量达标 (论著 >= 25)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id:
            import re
            refs = re.findall(r'\[\d+\]', output)
            count = len(set(refs))
            if count >= 25:
                return True, f"参考文献 {count} 篇 >= 25"
            return False, f"参考文献仅 {count} 篇 < 25 篇门槛"
    return True, "跳过"


# ============================================================
# 闸门定义: 每个 Phase 执行哪些检查
# ============================================================

GATE_DEFINITIONS = {
    "problem_definition": {
        "auto_checks": {
            "lit_precheck": check_literature_precheck_exists,
            "frame_complete": check_frame_assessment_complete,
        },
        "llm_checks": [
            "研究问题的临床重要性是否充分论述?",
            "数据源的可行性是否确认?",
            "FRAME 评估的每个维度是否有定量支撑?",
        ],
    },
    "execution": {
        "auto_checks": {
            "auc_threshold": check_auc_threshold,
            "baseline_included": check_baseline_included,
            "n_jobs_safe": check_n_jobs_safe,
        },
        "llm_checks": [
            "模型选择是否合理 (是否跳过了应做的 baseline)?",
            "特征选择是否在 CV 内部完成?",
            "可解释性报告是否完整 (SHAP + 方向确认)?",
            "校准度是否合格?",
        ],
    },
    "writing": {
        "auto_checks": {
            "conclusion_heading": check_conclusion_heading_level,
            "doi_verified": check_doi_verification,
            "ref_count": check_ref_count,
        },
        "llm_checks": [
            "Methods ↔ Results 是否 1:1 对应?",
            "Discussion 四段是否完整 (¶1-¶4 空行分隔)?",
            "Conclusion 是否独立章节、不重复 Results 数字?",
            "所有数字是否可追溯到上游分析?",
        ],
    },
}
```

### 1.7 company-sop.md 改动

在 §4.2 阶段门控 后追加：

```markdown
### 4.3 Gate 检查清单

所有项目必须通过每个 Phase 的 Gate 检查，不可口头跳过。

#### Gate 1 — 问题定义

| # | 检查项 | 类型 | 通过标准 |
|---|--------|------|---------|
| 1 | 文献预检报告存在 | auto | research-assistant 产出包含 ≥3 篇对标论文 |
| 2 | FRAME 五维评估完整 | auto | 五个维度全部论述，F 维有文献数据支撑 |
| 3 | 数据可用性确认 | auto | data-engineer 报告 DQ-CARE 五维完成 |
| 4 | 研究问题临床重要性 | llm | PI 确认研究问题有临床价值 |
| 5 | 可行性判定 | llm | PI 明确给出"启动/观望/放弃"建议 |

#### Gate 3 — 内部验证

| # | 检查项 | 类型 | 通过标准 |
|---|--------|------|---------|
| 1 | AUC >= 0.70 | auto | 主要模型 AUC >= 0.70 |
| 2 | Baseline 包含 | auto | 输出含 LR 或 Cox PH baseline |
| 3 | n_jobs 安全 | auto | n_jobs ≤ 2 |
| 4 | 模型选择合理 | llm | PI 确认模型层级正确 |
| 5 | 可解释性完整 | llm | SHAP + 方向确认 + 公平性评估 |

#### Gate 6 — 论文撰写

| # | 检查项 | 类型 | 通过标准 |
|---|--------|------|---------|
| 1 | Conclusion 独立章节 | auto | `## Conclusion` 存在，非 `### Conclusion` |
| 2 | DOI 验证通过 | auto | fake DOI = 0 |
| 3 | 参考文献数量达标 | auto | >= 25 篇 (论著) |
| 4 | Methods↔Results 1:1 | llm | PI 确认无遗漏 |
| 5 | 讨论四段完整 | llm | ¶1-¶4 空行分隔，¶4 无结论性收束句 |
| 6 | 数值可追溯 | llm | 所有数字标注来源 Agent |

#### 闸门状态与行为

| 状态 | 含义 | 编排器行为 |
|------|------|-----------|
| ✅ PASS | 全部检查通过 | 进入下一 Phase |
| ⚠️ COND_PASS | 通过但有附条件 | 进入下一 Phase，条件注入下游 Agent 输入 |
| ❌ FAIL | 有检查项不通过 | 本 Phase 返工，最多 3 次；超过升级首席科学家 |

#### 跨 Phase 反馈 (反馈环 B)

下游 Phase 发现上游问题的处理流程：
1. 下游 Agent 标注问题 → 编排器记录
2. 编排器暂停当前 Phase → 重启上游 Gate
3. 上游修正完成 → 重新闸门 → PASS → 断点续传下游
```

---

## 二、P1-2：LLM 容错

### 2.1 现状

`llm_client.py` 中的 `_chat_anthropic()` 和 `_chat_deepseek()` 是**一次性调用**——成功返回，失败抛异常。`_call_agent()` 中的 `try/except` 只是捕获异常并返回错误字符串，不做重试。

当前的失败模式：
```
API 超时 → Exception → _call_agent() 返回 "[agent] LLM 调用失败: ..."
→ 整个 Phase 的 agent 输出 = 错误信息 → 下游收到垃圾输入
```

### 2.2 目标架构

```
_call_agent(agent_id, task_input)
       │
       ▼
┌─ LLM 调用 (带容错层) ──────────────────────────────┐
│                                                     │
│  Attempt 1: primary model                           │
│    ├─ 成功 → 返回                                    │
│    └─ 失败 → wait 1s                                │
│                                                     │
│  Attempt 2: primary model (retry)                   │
│    ├─ 成功 → 返回                                    │
│    └─ 失败 → wait 2s                                │
│                                                     │
│  Attempt 3: degrade to fallback model               │
│    ├─ 成功 → 返回 (标注 degraded)                     │
│    └─ 失败 → wait 4s                                │
│                                                     │
│  Attempt 4: fallback model (last try)               │
│    ├─ 成功 → 返回 (标注 degraded)                     │
│    └─ 失败 → RAISE → 触发 Phase 降级/暂停             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**错误分类**:

| 错误类型 | 是否重试 | 退避策略 |
|---------|---------|---------|
| `RateLimitError` (429) | 是 | 指数退避 + 读取 Retry-After header |
| `APITimeoutError` / `ReadTimeout` | 是 | 指数退避 1s→2s→4s |
| `APIConnectionError` | 是 | 等 5s 后重试 |
| `InternalServerError` (5xx) | 是 | 指数退避 |
| `AuthenticationError` (401) | 否 | 直接失败，不重试 |
| `BadRequestError` (400) | 否 | 检查 prompt 长度，截断后重试 1 次 |

### 2.3 需要修改的文件

| 文件 | 改动 | 工作量 |
|------|------|--------|
| `engine/core/llm_client.py` | 新增 `_call_with_retry()` 方法 + 错误分类 + fallback model | ~80 行 |
| `engine/config.py` | 新增 fallback model 配置 + retry 参数 | ~10 行 |
| `engine/core/orchestrator_graph.py` | `_call_agent()` 改用容错调用，处理最终失败时的 Phase 降级 | ~20 行 |

### 2.4 llm_client.py 改动

```python
import time
import random
from functools import wraps

# 可重试的错误类型
RETRYABLE_ERRORS = (
    "RateLimitError",
    "APITimeoutError", 
    "APIConnectionError",
    "InternalServerError",
    "ServiceUnavailableError",
    "ReadTimeout",
    "ConnectionError",
)

class LLMClient:
    def __init__(self, ...):
        # ... 现有初始化 ...
        self.max_retries = 3
        self.retry_base_delay = 1.0  # 秒
        self.retry_max_delay = 8.0
        self.fallback_model = "claude-haiku-4-5-20251001"  # 降级模型, 更快更稳定
        self._checkpoint_dir = None  # 可选, 用于断点保存
    
    def chat(self, system_prompt, user_message, tools=None, tool_choice=None):
        """带容错的 chat 入口"""
        return self._call_with_retry(
            "chat", system_prompt, user_message, tools, tool_choice
        )
    
    def _call_with_retry(self, method: str, *args, **kwargs):
        """
        核心容错逻辑: 指数退避重试 + 模型降级。
        
        重试序列:
          Attempt 1: primary model, delay=0
          Attempt 2: primary model, delay=1s (+jitter)
          Attempt 3: fallback model, delay=2s (+jitter) 
          Attempt 4: fallback model, delay=4s (+jitter) → 最终失败
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):  # 0-indexed, 最多 4 次尝试
            # 第 3 次起降级到 fallback model
            if attempt >= 2:
                original_model = self.model
                self.model = self.fallback_model
            
            try:
                if method == "chat":
                    result = self._do_chat(*args, **kwargs)
                elif method == "chat_with_tools":
                    result = self._do_chat_with_tools(*args, **kwargs)
                
                # 成功
                if attempt >= 2:
                    self.model = original_model  # 恢复
                    result._degraded = True      # 标记降级
                return result
                
            except Exception as e:
                last_error = e
                
                if not self._is_retryable(e):
                    raise  # 不可重试, 直接失败
                
                if attempt >= self.max_retries:
                    break  # 已达最大重试次数
                
                # 计算延迟
                delay = min(
                    self.retry_base_delay * (2 ** attempt) + random.uniform(0, 0.5),
                    self.retry_max_delay,
                )
                
                if self.verbose:
                    print(f"  ⚠️ LLM 调用失败 (attempt {attempt+1}/{self.max_retries+1}): "
                          f"{type(e).__name__}. {delay:.1f}s 后重试...")
                
                time.sleep(delay)
        
        # 全部重试失败
        raise LLMCallFailedError(
            f"LLM 调用失败 (共 {self.max_retries+1} 次尝试): {last_error}"
        ) from last_error
    
    def _is_retryable(self, error: Exception) -> bool:
        """判断是否可重试"""
        error_name = type(error).__name__
        # 检查错误类名
        if any(retryable in error_name for retryable in RETRYABLE_ERRORS):
            return True
        # 检查错误消息
        error_msg = str(error).lower()
        retryable_keywords = ["timeout", "rate limit", "server error", "connection", 
                              "service unavailable", "too many requests", "overloaded"]
        return any(kw in error_msg for kw in retryable_keywords)
    
    def _do_chat(self, system_prompt, user_message, tools, tool_choice):
        """实际的单次 chat 调用 (被 _call_with_retry 包装)"""
        if self.provider == "anthropic":
            return self._chat_anthropic(system_prompt, user_message, tools, tool_choice)
        elif self.provider == "deepseek":
            return self._chat_deepseek(system_prompt, user_message)
        # ... other providers
    
    def chat_with_tools(self, system_prompt, user_message, tools, execute_tool, 
                        max_tool_rounds=8):
        """带容错 + checkpoint 的 tool-calling chat"""
        # 加载 checkpoint (如果存在)
        checkpoint = self._load_checkpoint()
        start_round = checkpoint.get("round", 0) if checkpoint else 0
        
        try:
            return self._call_with_retry(
                "chat_with_tools", system_prompt, user_message, tools, 
                execute_tool, max_tool_rounds, start_round,
            )
        except LLMCallFailedError:
            # 最终失败前保存 checkpoint
            self._save_checkpoint(all_tool_calls, round_num)
            raise
    
    def _save_checkpoint(self, tool_calls, round_num):
        """保存断点，用于中断后恢复"""
        if not self._checkpoint_dir:
            return
        import json
        checkpoint = {
            "tool_calls": tool_calls,
            "round": round_num,
            "timestamp": time.time(),
        }
        path = Path(self._checkpoint_dir) / f"checkpoint_{hash(str(tool_calls))[:8]}.json"
        path.write_text(json.dumps(checkpoint, ensure_ascii=False))
    
    def _load_checkpoint(self) -> dict:
        if not self._checkpoint_dir:
            return {}
        # ... 加载最新的 checkpoint


class LLMCallFailedError(Exception):
    """LLM 调用最终失败 (所有重试 + 降级均未成功)"""
    pass
```

### 2.5 config.py 改动

```python
@dataclass
class EngineConfig:
    # ... 现有字段 ...
    
    # --- LLM 容错 ---
    llm_fallback_model: str = "claude-haiku-4-5-20251001"
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 1.0
    llm_retry_max_delay: float = 8.0
    llm_request_timeout: int = 300  # 单次请求超时 (秒)
    llm_checkpoint_dir: Optional[Path] = None  # 断点保存目录
```

### 2.6 orchestrator_graph.py 改动

`_call_agent()` 需要处理 LLM 最终失败的情况：

```python
def _call_agent(self, agent_id: str, task_input: str) -> str:
    print(f"  → 调用 {agent_id}...")
    
    # ... 现有 prefetch 逻辑 ...
    
    system_prompt = self.agent_loader.load_full_prompt(agent_id, include_fewshot=True)
    
    try:
        response = self.llm.chat(system_prompt=system_prompt, user_message=task_input)
        # ... 现有 DOI 验证逻辑 ...
        return content
    except LLMCallFailedError as e:
        # 🆕 LLM 最终失败 → 触发 Phase 降级
        error_msg = (
            f"## ⚠️ Agent 调用失败 (LLM 不可用)\n\n"
            f"**Agent**: {agent_id}\n"
            f"**错误**: {e}\n"
            f"**影响**: 当前 Phase 无法完成，项目暂停。\n"
            f"**建议**: 检查 API key 和网络连接。LLM 恢复后，编排器将从此 Phase 断点续传。\n"
        )
        print(f"  ✗ {agent_id}: LLM 最终失败 (所有重试耗尽)")
        # 将失败记录到项目状态
        self._record_phase_blocked(agent_id, str(e))
        return error_msg
    except Exception as e:
        error_msg = f"[{agent_id}] 调用失败: {e}"
        print(f"  ✗ {error_msg}")
        return error_msg
```

### 2.7 错误场景行为矩阵

| 场景 | Primary | Retry 1 | Retry 2 | Fallback | Fallback Retry | 最终结果 |
|------|---------|---------|---------|----------|---------------|---------|
| 正常 | ✅ | — | — | — | — | 正常返回 |
| 偶发超时 | ❌ timeout | ✅ | — | — | — | 正常返回 |
| API 短暂限流 | ❌ 429 | ❌ 429 | ✅ | — | — | 正常返回 |
| Primary 持续故障 | ❌ 500 | ❌ 500 | — | ✅ | — | 降级返回 |
| 全部故障 | ❌ | ❌ | — | ❌ | ❌ | Phase 暂停，等待恢复 |

---

## 三、实现优先级与依赖

```
优先实现 P1-2 (LLM 容错)
  │  原因: 不依赖其他改动, 是基础设施
  │  文件: llm_client.py + config.py
  │  时间: ~1 小时
  │
  └─→ P1-1 (Gate 检查)
        │  依赖: 无代码依赖, 但需要定义检查标准
        │  文件: state.py + orchestrator_graph.py + gate_checks.py (新)
        │  时间: ~2 小时
        │
        └─→ company-sop.md 更新
              时间: ~0.5 小时
```

## 四、验证方案

### P1-1 验证

1. 跑一个完整项目 → 检查日志中是否出现 Gate 检查记录
2. 故意让 Phase 3 输出 AUC=0.55 → 验证 Gate 3 FAIL → 触发返工
3. 返工 4 次 → 验证超过 max_rework → 升级首席科学家
4. 检查 Phase 6 → 验证 Conclusion `##` heading 检查 + DOI 验证

### P1-2 验证

1. 临时断开网络 → 调用 Agent → 验证重试 3 次后降级到 Haiku
2. 模拟 API 返回 429 → 验证指数退避
3. 模拟全部故障 → 验证 Phase 暂停 + 错误信息输出
4. 检查 Haiku 降级标记 (输出中是否有 `_degraded` 标记)

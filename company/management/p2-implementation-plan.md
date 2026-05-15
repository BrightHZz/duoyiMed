# P2 实现方案：运行数据采集 + SDS 总体设计

> 对应钱学森工程控制论 §系统辨识 (§四) + §总体设计部 (§三)，2026-05-10

---

## 一、P2-1：运行数据采集（系统辨识）

### 1.1 目标

让公司"认识自己"。自动采集每次 Agent 调用的运行数据，积累后生成季度运行状态报告，识别瓶颈和优化机会。

### 1.2 数据模型

每条运行日志 (`RunLog`) 记录一次完整的 Agent 调用：

```python
class RunLog(TypedDict):
    timestamp: str          # "2026-05-10 14:23:00"
    project_id: str         # "frailty_ml_2026"
    division: str           # "geriatrics"
    phase_id: str           # "execution"
    agent_id: str           # "shared/ml-engineer"
    success: bool           # 调用是否成功
    degraded: bool          # 是否使用了降级模型
    wall_time_sec: float    # 端到端耗时
    input_tokens: int       # prompt tokens
    output_tokens: int      # completion tokens
    output_len: int         # 输出字符数
    error_type: str         # 如果失败, 错误类型 (空字符串=成功)
    gate_status: str        # pass/cond_pass/fail/skip
    rework_of: str          # 如果是返工, 标注原 phase_id (空=首次)
```

### 1.3 存储方案

零外部依赖：JSON Lines 文件（每行一个 JSON 对象），按日切割。

```
outputs/run_logs/
├── 2026-05-10.jsonl
├── 2026-05-11.jsonl
└── ...
```

每次 Agent 调用完成后追加一行。不需要数据库、不需要后台服务。

### 1.4 需要修改的文件

| 文件 | 改动 | 行数 |
|------|------|------|
| `engine/core/state.py` | 新增 `RunLog` TypedDict | ~15 |
| `engine/core/orchestrator_graph.py` | `_call_agent()` 前后埋点计时+记录；新增 `_append_run_log()` + `_log_file_path()` | ~40 |
| `engine/config.py` | 新增 `run_log_dir` 配置项 | ~3 |

### 1.5 具体改动

**state.py** — 新增：

```python
class RunLog(TypedDict):
    """单次 Agent 调用的运行日志"""
    timestamp: str
    project_id: str
    division: str
    phase_id: str
    agent_id: str
    success: bool
    degraded: bool
    wall_time_sec: float
    input_tokens: int
    output_tokens: int
    output_len: int
    error_type: str
    gate_status: str          # pass | cond_pass | fail | skip
    rework_of: str            # 空=首次, 否则为原 phase_id
```

**config.py** — 新增配置项：

```python
run_log_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "outputs" / "run_logs")
```

**orchestrator_graph.py** — `_call_agent()` 埋点：

```python
def _call_agent(self, agent_id: str, task_input: str,
                phase_id: str = "", project_id: str = "",
                rework_of: str = "") -> str:
    """调用 Agent LLM。自动记录运行日志。"""
    print(f"  → 调用 {agent_id}...")
    t0 = time.time()
    success = False
    degraded = False
    error_type = ""
    in_tokens = out_tokens = 0
    output_len = 0

    try:
        # ... 现有调用逻辑 ...
        success = True
        degraded = response.degraded
        in_tokens = response.usage.get("input_tokens", 0)
        out_tokens = response.usage.get("output_tokens", 0)
        output_len = len(content)
        return content
    except LLMCallFailedError as e:
        error_type = "LLMCallFailed"
        raise  # 仍然往上抛, 让上层处理
    except Exception as e:
        error_type = type(e).__name__
        raise
    finally:
        wall_time = time.time() - t0
        self._append_run_log(RunLog(
            timestamp=datetime.now().isoformat(),
            project_id=project_id,
            division=self.active_division,
            phase_id=phase_id,
            agent_id=agent_id,
            success=success,
            degraded=degraded,
            wall_time_sec=round(wall_time, 2),
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            output_len=output_len,
            error_type=error_type,
            gate_status="skip",   # Gate 结果在闸门检查后回填
            rework_of=rework_of,
        ))

def _append_run_log(self, log: dict):
    """追加一行 JSON 到当天的 run log 文件。轻量零阻塞。"""
    try:
        log_dir = self.config.run_log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
    except Exception:
        pass  # 日志写入失败不能影响主流程

def _backfill_gate_status(self, phase_id: str, gate_status: str):
    """闸门检查后回填该 Phase 所有 agent 调用的 gate_status"""
    # 实现: 读取今天日志文件的最后 N 行, 更新匹配 phase_id 的行。或简化为: 追加一条 gate summary 记录。
```

### 1.6 设计决策

- **轻量优先**：JSON Lines 追加写入，不依赖任何外部存储。后续季度报告时直接 `cat *.jsonl | jq` 分析。
- **零阻塞**：日志写入在 `finally` 中执行，失败静默吞掉，不影响主流程。
- **Gate 结果延迟回填**：Agent 调用时 Gate 还没执行，先用 `"skip"` 占位。Gate 检查完成后追加一条 gate summary 日志。

---

## 二、P2-2：SDS 总体设计（Phase 0）

### 2.1 目标

每个新项目启动时，在 Phase 1（问题定义）之前插入 **Phase 0 — 系统总体设计**。

Phase 0 由一个专门的 Agent（或 orchestror 自身）调用，基于用户需求生成 **系统设计说明书 (SDS)**。SDS 是项目蓝图，定义了：

1. **系统分解**：哪些 Agent 参与，每个输出什么，质量门标准
2. **接口规范**：Agent 之间传递什么格式的数据，SLA 是多久
3. **反馈触发条件**：什么情况下需要跨 Phase 返工
4. **关键假设与风险**：项目成功的前提条件和主要风险

### 2.2 SDS 模板

SDS 不是让 PM/编排器凭空设计的——编排器本身用一个结构化 prompt 生成：

```
你是一个研究项目的总体设计师。基于用户请求，输出 System Design Specification。

用户请求: {user_request}
事业部: {division}
可用 Agent: geriatrics/pi, geriatrics/clinical-researcher, ...

请按以下模板输出 SDS:

## 系统设计说明书 (SDS)

### 1. 系统分解
为每个子系统列出:
- provider: 负责的 Agent
- output: 产出物名称
- interface: {format, 关键字段}
- quality_gate: 通过标准

### 2. 接口矩阵
表格: from_agent → to_agent → artifact → SLA

### 3. 反馈触发条件
if: 条件 → then: 动作 (回退到哪个 Phase)

### 4. 关键假设与风险
- assumptions: [假设1, 假设2, ...]
- risks: [{risk, mitigation}, ...]
```

### 2.3 集成到工作流

当前 `_run_project_workflow()` 的 Phase 序列是：

```
["problem_definition", "design", "execution", "external_validation", "review", "writing"]
```

改为：

```
["system_design", "problem_definition", "design", "execution", "external_validation", "review", "writing"]
  ↑ Phase 0
```

Phase 0 由编排器自身（或 PM）执行，不调用事业部 Agent，直接生成 SDS。

### 2.4 需要修改的文件

| 文件 | 改动 | 行数 |
|------|------|------|
| `engine/core/orchestrator_graph.py` | `PROJECT_PHASES` 新增 `system_design`；新增 `_run_system_design()` 方法 | ~50 |
| `engine/core/state.py` | `ProjectState` 新增 `sds` 字段 | ~2 |
| `company/company-sop.md` | 流程 1 的 Phase 列表新增 Phase 0 | ~5 |

### 2.5 具体改动

**PROJECT_PHASES 新增**：

```python
"system_design": {
    "agents": [],              # Phase 0 由 orchestror 自身执行, 不调用 Agent
    "parallel": False,
    "description": "系统总体设计: 生成 SDS (系统分解 + 接口规范 + 反馈触发 + 假设风险)",
    "next": "problem_definition",
},
```

**_run_project_workflow()** 中 Phase 0 特殊处理：

```python
phases_to_run = ["system_design", "problem_definition", "design", 
                 "execution", "external_validation", "review", "writing"]

# ... 在 while 循环中 ...
if phase_id == "system_design":
    # Phase 0 特殊: 编排器自己做总体设计
    sds = self._run_system_design(user_request, project_id)
    all_outputs["system_design"] = {"_sds": sds}
    gate_results["system_design"] = {
        "phase_id": "system_design",
        "status": "pass",  # SDS 不经闸门, 直接通过
        "checks": [],
    }
    phase_index += 1
    continue
```

**新增 `_run_system_design()`**：

```python
SDS_SYSTEM_PROMPT = """你是DuoyiMed的总体设计师 (System Architect)。
你的职责是为每个新研究项目设计《系统设计说明书》(SDS)。

SDS 不等同于统计分析计划 (SAP)，SDS 定义的是整个研究系统的架构：
- 子系统的分解和职责
- 子系统之间的接口格式和 SLA
- 质量闸门标准
- 反馈触发条件
- 关键假设与风险

你需要像航天工程的总体设计部一样思考：顶层设计、接口标准化、全系统集成验证。"""

def _run_system_design(self, user_request: str, project_id: str) -> str:
    """Phase 0: 生成系统设计说明书 (SDS)"""
    print(f"\n{'='*50}")
    print(f"[Phase 0] 系统总体设计 — 生成 SDS")
    print(f"{'='*50}")

    prompt = f"""用户研究请求:
{user_request}

事业部: {self.active_division}

可用 Agent:
- {self.active_division}/pi: 首席研究员 (FRAME 评估 + 终审)
- {self.active_division}/clinical-researcher: 临床研究员 (表型定义 + 临床审查)
- {self.active_division}/computational-biologist: 计算生物学 (建模方案)
- shared/data-engineer: 数据工程师 (数据评估 + ETL)
- shared/biostatistician: 生物统计 (SAP + 统计审查)
- shared/ml-engineer: ML 工程师 (模型训练 + 可解释性)
- shared/scientific-writer: 学术写作 (论文撰写 + DOI 验证)
- shared/research-assistant: 科研助理 (文献检索 + PRISMA)

请输出《系统设计说明书》:

## 系统设计说明书 (SDS) v1.0

### 1. 系统分解
为每个子系统 (data / clinical / modeling / stats / writing) 定义:
- provider: 负责的 Agent
- output: 产出物名称和格式
- interface: 输入来源 + 输出格式
- quality_gate: 通过的最低标准

### 2. 接口矩阵
| From | To | Artifact | Format | SLA |
|------|----|---------|--------|-----|

### 3. 反馈触发条件
列出至少 3 条跨 Phase 反馈规则:
```
if: [条件]
then: [回退到哪个 Phase, 做什么修正]
```

### 4. 关键假设与风险
- **Assumptions**: 项目成功必须成立的前提 (如 MAR 假设成立、标签无泄露)
- **Risks**: 潜在风险 + 缓解措施 (如 类别不平衡 > 1:5 → scale_pos_weight)

现在开始设计。"""

    return self._call_agent(
        agent_id="system_architect",
        task_input=prompt,
        phase_id="system_design",
        project_id=project_id,
    )
```

注意：`system_architect` 不是一个正式的 Agent 文件——编排器直接用 SDS_SYSTEM_PROMPT 作为 system_prompt，不需要单独的 Agent Markdown 文件。如果将来需要独立配置，可以在 `company/management/` 下新增 `system-architect.md`。

---

## 三、季度运行报告（基于 P2-1 数据的下一步）

P2-1 采集数据后，下一阶段 (P3) 可自动生成《公司运行状态报告》：

```bash
# 示例：用 jq 快速分析
cat outputs/run_logs/2026-05-*.jsonl | jq -s '
  group_by(.phase_id) | map({
    phase: .[0].phase_id,
    avg_time: (map(.wall_time_sec) | add / length),
    success_rate: (map(select(.success)) | length) / length
  })'
```

P3 中将此逻辑封装为编排器的一个分析命令（`--workflow status_report`），自动生成 Markdown 格式的季度报告。

---

## 四、实现优先级

```
P2-1 (运行数据采集)
  │  优先级: 先做, 因为 P2-2 的 SDS 效果好坏需要通过数据验证
  │  文件: state.py + orchestrator_graph.py + config.py
  │  时间: ~40 分钟
  │
  └─→ P2-2 (SDS Phase 0)
        │  依赖: P2-1 的埋点代码已完成 (可共用 _call_agent 的计时/日志)
        │  文件: orchestrator_graph.py + state.py + company-sop.md
        │  时间: ~1 小时
        │
        └─→ P3 季度报告 (下个迭代)
              依赖: P2-1 数据积累 ≥ 1 周
```

---

## 五、验证方案

### P2-1 验证

1. 跑一次完整的 Agent 调用 → 检查 `outputs/run_logs/` 下是否生成了当天的 `.jsonl` 文件
2. `cat *.jsonl | jq .` → 验证每条记录包含所有必需字段
3. 故意触发一次 LLM 降级 → 验证 `degraded: true`
4. 模拟一次调用失败 → 验证 `success: false, error_type` 正确

### P2-2 验证

1. 启动新项目 → 验证 Phase 0 先于 Phase 1 执行
2. 检查 SDS 输出是否包含四个章节（系统分解/接口矩阵/反馈触发/假设风险）
3. SDS 内容是否作为上下文注入了后续 Phase 的 Agent 输入
4. 验证 SDS 中定义的 Gate 标准是否与 `GATE_DEFINITIONS` 一致

# 模块二：可靠性工程 — Agent 间一致性交叉验证方案

> 钱学森《工程控制论》第18章核心思想：**用不可靠的元件，通过工程协调的方法，组成可靠的系统。**
>
> LLM 是天然不可靠的元件——幻觉、不一致、术语漂移。不能指望单个 Agent 一次输出就正确。
> 必须在关键节点引入**多层冗余 + 交叉验证**。

---

## 目录

1. [问题定义与设计原理](#一 问题定义与设计原理)
2. [数据模型](#二 数据模型)
3. [一致性检查对定义](#三 一致性检查对定义)
4. [ConsistencyChecker 类设计](#四-consistencychecker-类设计)
5. [编排器集成点](#五 编排器集成点)
6. [分场景判定逻辑](#六 分场景判定逻辑)
7. [测试方案](#七 测试方案)
8. [文件改动清单](#八 文件改动清单)

---

## 一、问题定义与设计原理

### 1.1 当前差距

```
当前模式 (单通道, 无交叉验证):
  Agent A 输出 ──→ Gate 检查 ──→ 通过
  Agent B 输出 ──→ Gate 检查 ──→ 通过
                     ↑
              各自独立检查, 不交叉对比
              
典型故障:
  - clinical-researcher 定义 "frailty_index_v2"
  - data-engineer 说数据里只有 "frailty_index" (无 _v2)
  - 两个 Agent 各自通过自己的 Gate → Phase 3 执行时才发现变量不存在
  → 只能靠反馈环B事后补救, 已浪费 ML 阶段的 token 和时间
```

### 1.2 目标架构

```
目标模式 (双通道, 交叉验证):
  Agent A 输出 ──┐
                 ├──→ 一致性检查器 ──→ [一致] → Gate 继续
  Agent B 输出 ──┘                   → [轻微不一致] → 自动修正建议注入下游
                                     → [严重矛盾] → Gate FAIL, 触发返工
```

### 1.3 设计原则

| 原则 | 说明 |
|------|------|
| **非侵入** | 不修改现有 Agent prompt 和 Gate 检查逻辑 |
| **轻量** | 仅对关键 Phase 的关键 Agent 对做检查, 不做全排列 |
| **可降级** | 一致性检查器自身调用失败 → 不影响主流程, 标记跳过 |
| **分层判定** | 一致 → 自动修正 → 返工, 三级响应 |
| **钱学森冗余** | 两个不可靠 LLM 的输出交叉验证, 可靠性远高于单个 |

---

## 二、数据模型

```python
# engine/core/consistency_checker.py

from typing import TypedDict, Optional, Literal

class ConsistencyPair(TypedDict):
    """单个一致性检查对的定义"""
    pair_id: str                   # "phenotype_vs_data_dict"
    agent_a: str                   # "clinical-researcher"
    agent_b: str                   # "data-engineer"
    check_dimension: str           # 检查维度描述
    source: str                    # "current_phase" | "current_phase + upstream"
    # 若 source="current_phase + upstream", agent_b_output 来自上游 Phase
    upstream_phase: Optional[str]  # 上游 Phase ID (跨 Phase 检查时使用)
    severity: str                  # "critical" | "high" | "normal"
    check_prompt: str              # 发给一致性检查 LLM 的具体检查指令


class ConsistencyResult(TypedDict):
    """单次一致性检查的结果"""
    pair_id: str
    agent_a: str
    agent_b: str
    result: str                    # "consistent" | "minor_inconsistency" | "major_conflict"
    detail: str                    # 人类可读的检查细节
    suggested_fix: str             # 自动修正建议 (minor_inconsistency 时)
    a_claim: str                   # Agent A 的关键主张 (提取)
    b_claim: str                   # Agent B 的关键主张 (提取)
    confidence: str                # "high" | "medium" | "low"


class PhaseConsistencyReport(TypedDict):
    """一个 Phase 的全部一致性检查结果"""
    phase_id: str
    timestamp: str
    pairs_checked: int
    consistent: int
    minor: int
    major: int
    results: list[ConsistencyResult]
    overall: str                   # "pass" | "warn" | "fail"
```

---

## 三、一致性检查对定义

### 3.1 检查矩阵

```
Phase 1 (问题定义):
  ┌─────────────────────┬──────────────────────┬──────────┬──────────┐
  │ Agent A             │ Agent B              │ 检查维度   │ Severity │
  ├─────────────────────┼──────────────────────┼──────────┼──────────┤
  │ clinical-researcher │ data-engineer        │ 表型变量是否在数据字典中存在 │ critical │
  │ clinical-researcher │ research-assistant   │ 临床定义与文献检索关键词一致 │ high     │
  │ pi (FRAME)          │ research-assistant   │ FRAME F维度结论与文献数据一致 │ high     │
  └─────────────────────┴──────────────────────┴──────────┴──────────┘

Phase 2 (方案设计):
  ┌─────────────────────┬──────────────────────┬──────────┬──────────┐
  │ computational-bio   │ biostatistician      │ 建模方法是否与SAP一致 │ critical │
  └─────────────────────┴──────────────────────┴──────────┴──────────┘

Phase 3 (执行):
  单 Agent, 无 Phase 内检查对 → 跳过

Phase 4 (外部验证):
  ┌─────────────────────┬──────────────────────┬──────────┬──────────┐
  │ ml-engineer         │ biostatistician      │ 外部验证统计方法与SAP一致 │ critical │
  │ ml-engineer         │ data-engineer        │ 外部数据变量与内部一致   │ critical │
  └─────────────────────┴──────────────────────┴──────────┴──────────┘

Phase 5 (审查):
  ┌─────────────────────┬──────────────────────┬──────────┬──────────┐
  │ clinical-researcher │ pi                   │ 临床解读与PI终审无矛盾 │ critical │
  └─────────────────────┴──────────────────────┴──────────┴──────────┘

Phase 6 (论文撰写) — 跨Phase检查:
  ┌─────────────────────┬──────────────────────┬──────────┬──────────┐
  │ scientific-writer   │ ml-engineer (P3)     │ 论文AUC等数字与ML报告一致 │ critical │
  │ scientific-writer   │ biostatistician (P4) │ 论文p值/CI与统计报告一致  │ critical │
  └─────────────────────┴──────────────────────┴──────────┬──────────┘
```

### 3.2 代码中的定义

```python
CONSISTENCY_PAIRS: dict[str, list[dict]] = {
    "problem_definition": [
        {
            "pair_id": "phenotype_vs_data_dict",
            "agent_a": "clinical-researcher",
            "agent_b": "data-engineer",
            "source": "current_phase",
            "severity": "critical",
            "check_prompt": (
                "对比 clinical-researcher 定义的表型变量名与 data-engineer "
                "数据字典中的实际变量名。检查: (1) 每个表型变量是否在数据源中存在, "
                "(2) 变量名是否完全一致 (注意 _v2 后缀、大小写等细微差异), "
                "(3) 变量的缺失率是否在临床可接受范围内。"
                "如果变量名存在细微差异, 给出统一命名建议。"
            ),
        },
        {
            "pair_id": "phenotype_vs_lit_search",
            "agent_a": "clinical-researcher",
            "agent_b": "research-assistant",
            "source": "current_phase",
            "severity": "high",
            "check_prompt": (
                "对比 clinical-researcher 的临床问题定义与 research-assistant "
                "文献预检中的检索关键词和研究方向。检查: (1) 临床定义是否覆盖了 "
                "文献检索的核心概念, (2) 是否有重要的检索角度被遗漏。"
            ),
        },
    ],
    "design": [
        {
            "pair_id": "model_vs_sap",
            "agent_a": "computational-biologist",
            "agent_b": "biostatistician",
            "source": "current_phase",
            "severity": "critical",
            "check_prompt": (
                "对比 computational-biologist 建模方案中的模型选择/评估策略与 "
                "biostatistician SAP 中的统计分析方法。检查: (1) 建模方案中的 "
                "主要模型是否在 SAP 中有对应的分析方法描述, (2) 评估指标是否一致 "
                "(如建模用 AUC, SAP 也应有相应的 discrimination 指标), "
                "(3) 协变量选择在两者中是否一致。"
            ),
        },
    ],
    "external_validation": [
        {
            "pair_id": "ext_model_vs_sap",
            "agent_a": "ml-engineer",
            "agent_b": "biostatistician",
            "source": "current_phase",
            "severity": "critical",
            "check_prompt": (
                "对比 ml-engineer 外部验证的评估方法 (metrics, 人群分层, 校准方法) "
                "与 biostatistician 的原始 SAP 规范。检查: (1) 外部验证是否遵循 "
                "SAP 中定义的外部验证策略, (2) 评估指标是否与 SAP 一致。"
            ),
        },
    ],
    "review": [
        {
            "pair_id": "clinical_vs_pi_review",
            "agent_a": "clinical-researcher",
            "agent_b": "pi",
            "source": "current_phase",
            "severity": "critical",
            "check_prompt": (
                "对比 clinical-researcher 的临床审查意见与 PI 的终审结论。"
                "检查: (1) 效应方向的临床解读是否一致, "
                "(2) 对模型局限性的判断是否存在矛盾, "
                "(3) 对下一步行动的建议是否一致。"
                "分歧本身不是问题——但如果一个说'临床价值明确'另一个说'临床意义有限', "
                "这是严重矛盾。"
            ),
        },
    ],
    "writing": [
        {
            "pair_id": "paper_nums_vs_ml_report",
            "agent_a": "scientific-writer",
            "agent_b": "ml-engineer",
            "source": "upstream",
            "upstream_phase": "execution",
            "severity": "critical",
            "check_prompt": (
                "对比 scientific-writer 论文中的数值 (AUC, C-index, sensitivity, "
                "specificity, SHAP top features) 与 ml-engineer 原始报告中的数值。"
                "逐项检查: 每个数字是否精确一致, 小数位数是否合理, "
                "是否存在四舍五入导致的精度丢失。"
                "额外检查: 论文中是否提到了 ml-engineer 报告中没有的数值 (编造风险)。"
            ),
        },
        {
            "pair_id": "paper_stats_vs_sap",
            "agent_a": "scientific-writer",
            "agent_b": "biostatistician",
            "source": "upstream",
            "upstream_phase": "external_validation",
            "severity": "critical",
            "check_prompt": (
                "对比 scientific-writer 论文中的统计分析结果 (p值, 置信区间, "
                "效应量, HR/OR/RR) 与 biostatistician 统计报告中的数值。"
                "逐项检查每个统计量的数值是否一致。"
                "特别检查: p值是否精确匹配 (不能论文写 p<0.001 但报告是 p=0.03)。"
            ),
        },
    ],
}
```

---

## 四、ConsistencyChecker 类设计

### 4.1 类结构

```python
# engine/core/consistency_checker.py

class ConsistencyChecker:
    """
    Agent 间一致性交叉验证引擎。

    基于钱学森可靠性工程思想:
    两个不可靠的 LLM Agent 输出, 经过交叉验证后,
    其一致部分的可靠性远高于单个 Agent 的可靠性。

    用法:
        checker = ConsistencyChecker(llm_client)
        report = checker.check_phase(
            phase_id="problem_definition",
            outputs={"clinical-researcher": "...", "data-engineer": "..."},
            upstream_outputs={},  # 跨Phase检查时需要
            division="geriatrics",
        )
        # report["overall"] ∈ {"pass", "warn", "fail"}
    """

    def __init__(self, llm_client: 'LLMClient', verbose: bool = True):
        self.llm = llm_client
        self.verbose = verbose

    def check_phase(
        self,
        phase_id: str,
        outputs: dict[str, str],
        upstream_outputs: dict[str, str] = None,
        division: str = "geriatrics",
    ) -> PhaseConsistencyReport:
        """
        对指定 Phase 执行所有定义的一致性检查对。

        Args:
            phase_id: Phase ID
            outputs: 当前 Phase 的 Agent 输出 {agent_id: output_text}
            upstream_outputs: 上游 Phase 的输出 (跨Phase检查时需要)
            division: 事业部 ID

        Returns:
            PhaseConsistencyReport
        """
        pairs = CONSISTENCY_PAIRS.get(phase_id, [])
        if not pairs:
            return {
                "phase_id": phase_id,
                "timestamp": datetime.now().isoformat(),
                "pairs_checked": 0,
                "consistent": 0,
                "minor": 0,
                "major": 0,
                "results": [],
                "overall": "pass",
            }

        results = []
        for pair_def in pairs:
            # 1. 获取两个 Agent 的输出
            output_a = self._resolve_output(
                pair_def["agent_a"], pair_def["source"],
                outputs, upstream_outputs or {}, division
            )
            output_b = self._resolve_output(
                pair_def["agent_b"], pair_def["source"],
                outputs, upstream_outputs or {}, division
            )

            if not output_a or not output_b:
                results.append(self._skip_result(pair_def, output_a, output_b))
                continue

            # 2. 调用 LLM 做交叉验证
            try:
                result = self._run_check(pair_def, output_a, output_b)
            except Exception as e:
                result = self._error_result(pair_def, str(e))

            results.append(result)

            if self.verbose:
                icon = {"consistent": "✅", "minor_inconsistency": "⚠️",
                        "major_conflict": "❌", "skipped": "⏭️"}.get(
                    result["result"], "❓")
                print(f"  {icon} consistency:[{pair_def['pair_id']}] "
                      f"{result['result']}: {result['detail'][:100]}")

        # 3. 汇总
        consistent = sum(1 for r in results if r["result"] == "consistent")
        minor = sum(1 for r in results if r["result"] == "minor_inconsistency")
        major = sum(1 for r in results if r["result"] == "major_conflict")

        if major > 0:
            overall = "fail"
        elif minor > 0:
            overall = "warn"
        else:
            overall = "pass"

        return {
            "phase_id": phase_id,
            "timestamp": datetime.now().isoformat(),
            "pairs_checked": len(results),
            "consistent": consistent,
            "minor": minor,
            "major": major,
            "results": results,
            "overall": overall,
        }

    # ================================================================
    # 内部方法
    # ================================================================

    def _resolve_output(
        self, agent_id: str, source: str,
        outputs: dict, upstream: dict, division: str,
    ) -> Optional[str]:
        """
        根据 source 类型解析 Agent 输出。

        - "current_phase": 从当前 Phase outputs 中查找
        - "upstream": 从 upstream_outputs 中查找
        """
        if source == "current_phase":
            return self._find_output(outputs, agent_id, division)
        elif source == "upstream":
            return self._find_output(upstream, agent_id, division)
        return None

    def _find_output(
        self, outputs: dict, agent_id: str, division: str,
    ) -> Optional[str]:
        """
        在 outputs 中查找指定 Agent 的输出。
        支持三种匹配模式:
        1. 精确匹配: "shared/ml-engineer"
        2. 短名匹配: "ml-engineer" → 匹配任何 "*/ml-engineer"
        3. 事业部匹配: "clinical-researcher" → "geriatrics/clinical-researcher"
        """
        # 精确匹配
        if agent_id in outputs:
            return outputs[agent_id]

        # 模糊匹配
        for key, value in outputs.items():
            if key.endswith(f"/{agent_id}") or key == agent_id:
                return value

        return None

    def _run_check(
        self, pair_def: dict, output_a: str, output_b: str,
    ) -> ConsistencyResult:
        """调用 LLM 执行单次一致性检查"""
        prompt = self._build_check_prompt(
            pair_def["pair_id"],
            pair_def["check_prompt"],
            pair_def["agent_a"], output_a,
            pair_def["agent_b"], output_b,
        )

        response = self.llm.chat(
            system_prompt=CONSISTENCY_CHECKER_SYSTEM_PROMPT,
            user_message=prompt,
        )

        return self._parse_result(pair_def, response.content)

    def _build_check_prompt(
        self, pair_id: str, check_prompt: str,
        agent_a: str, output_a: str,
        agent_b: str, output_b: str,
    ) -> str:
        """构建发送给一致性检查 LLM 的 prompt"""
        # 截断以控制 token 消耗
        max_len = 3000
        return f"""## 一致性检查: {pair_id}

### 检查指令
{check_prompt}

### Agent A: {agent_a}
{output_a[:max_len]}{'...(截断)' if len(output_a) > max_len else ''}

### Agent B: {agent_b}
{output_b[:max_len]}{'...(截断)' if len(output_b) > max_len else ''}

请按以下格式输出:

**检查结果**: [consistent / minor_inconsistency / major_conflict]
**Agent A 的关键主张**: [从A的输出中提取的与本次检查相关的关键信息]
**Agent B 的关键主张**: [从B的输出中提取的与本次检查相关的关键信息]
**详细说明**: [具体的一致/不一致之处]
**修正建议** (仅 minor_inconsistency 时填写): [自动修正建议, 如统一变量名]
**确信度**: [high / medium / low]"""

    def _parse_result(
        self, pair_def: dict, response: str,
    ) -> ConsistencyResult:
        """解析 LLM 返回的一致性检查结果"""
        import re

        result = "major_conflict"  # 默认最坏情况
        detail = ""
        suggested_fix = ""
        a_claim = ""
        b_claim = ""
        confidence = "medium"

        # 解析结果
        result_match = re.search(
            r'检查结果[：:]\s*(consistent|minor_inconsistency|major_conflict)',
            response, re.IGNORECASE
        )
        if result_match:
            result = result_match.group(1).lower()

        # 解析 Agent A 主张
        a_match = re.search(
            r'Agent A.*?主张[：:]\s*(.+?)(?=\n\*\*Agent B|$)', response, re.DOTALL
        )
        if a_match:
            a_claim = a_match.group(1).strip()[:300]

        # 解析 Agent B 主张
        b_match = re.search(
            r'Agent B.*?主张[：:]\s*(.+?)(?=\n\*\*详细说明|$)', response, re.DOTALL
        )
        if b_match:
            b_claim = b_match.group(1).strip()[:300]

        # 解析详细说明
        detail_match = re.search(
            r'详细说明[：:]\s*(.+?)(?=\n\*\*修正建议|$)', response, re.DOTALL
        )
        if detail_match:
            detail = detail_match.group(1).strip()[:500]

        # 解析修正建议
        fix_match = re.search(
            r'修正建议[：:]\s*(.+?)(?=\n\*\*|$)', response, re.DOTALL
        )
        if fix_match:
            suggested_fix = fix_match.group(1).strip()[:500]

        # 解析确信度
        conf_match = re.search(
            r'确信度[：:]\s*(high|medium|low)', response, re.IGNORECASE
        )
        if conf_match:
            confidence = conf_match.group(1).lower()

        return {
            "pair_id": pair_def["pair_id"],
            "agent_a": pair_def["agent_a"],
            "agent_b": pair_def["agent_b"],
            "result": result,
            "detail": detail or response[:200],
            "suggested_fix": suggested_fix,
            "a_claim": a_claim,
            "b_claim": b_claim,
            "confidence": confidence,
        }

    def _skip_result(self, pair_def: dict, a_ok: bool, b_ok: bool) -> ConsistencyResult:
        """某个 Agent 输出缺失时的跳过结果"""
        return {
            "pair_id": pair_def["pair_id"],
            "agent_a": pair_def["agent_a"],
            "agent_b": pair_def["agent_b"],
            "result": "skipped",
            "detail": f"输出缺失: A={a_ok} B={b_ok}",
            "suggested_fix": "",
            "a_claim": "",
            "b_claim": "",
            "confidence": "low",
        }

    def _error_result(self, pair_def: dict, error: str) -> ConsistencyResult:
        """LLM 调用失败时的错误结果"""
        return {
            "pair_id": pair_def["pair_id"],
            "agent_a": pair_def["agent_a"],
            "agent_b": pair_def["agent_b"],
            "result": "skipped",
            "detail": f"LLM调用失败: {error[:100]}",
            "suggested_fix": "",
            "a_claim": "",
            "b_claim": "",
            "confidence": "low",
        }


# ================================================================
# 一致性检查器的 System Prompt
# ================================================================

CONSISTENCY_CHECKER_SYSTEM_PROMPT = """你是一致性交叉验证器 (Consistency Cross-Validator)。
你的唯一职责是: 对比两个 Agent 对同一领域问题的输出, 检查是否存在矛盾。

你不是在审查每个 Agent 的质量——你只检查它们之间的一致性。

## 判定标准

### consistent (一致)
- 两个 Agent 对同一事物的表述没有矛盾
- 允许表述方式不同, 只要核心信息一致
- 允许一个 Agent 提供了另一个没提到的细节 (这是正常的专业分工)

### minor_inconsistency (轻微不一致, 可自动修复)
- 同一概念使用了不同的名称 (如 "frailty_index" vs "frailty_index_v2")
- 数字的小数精度不同 (如 AUC=0.82 vs AUC=0.823)
- 措辞级别的差异, 不影响核心结论
- → 给出自动修正建议, 不阻断流程

### major_conflict (严重矛盾, 需人工)
- 两个 Agent 的核心结论互相矛盾
- 同一数字的值完全不同 (如 AUC=0.82 vs AUC=0.65)
- 一个 Agent 说某个变量存在, 另一个说数据中无此变量
- 临床解读的方向性矛盾 (如一个说风险升高, 另一个说风险降低)
- → 触发 Gate FAIL, 要求返工

## 重要原则
- 不要因为两个 Agent 的写作风格不同而判定矛盾
- 不要因为信息颗粒度不同而判定矛盾
- 宁可将模糊情况判定为 minor_inconsistency
- major_conflict 仅用于实质性的、影响研究结论的矛盾"""
```

---

## 五、编排器集成点

### 5.1 插入位置

```
_run_project_workflow() 中的执行顺序:

Phase 执行
    │
    ▼
_check_gate()          ← 现有: 阈值检查 + 趋势检查 + LLM审查
    │
    ▼
consistency_checker    ← 🆕 在此插入: Agent 间交叉验证
.check_phase()
    │
    ▼
_detect_upstream_issues()  ← 现有: 反馈环B检测
    │
    ▼
Gate 状态判定 (PASS/COND_PASS/FAIL) + 反馈B处理
```

### 5.2 编排器改动

```python
# orchestrator_graph.py: __init__ 中新增
from .consistency_checker import ConsistencyChecker

class ResearchOrchestrator:
    def __init__(self, config=None):
        # ... 现有初始化 ...
        self.consistency_checker = ConsistencyChecker(
            llm_client=self.llm,
            verbose=self.config.verbose,
        )

# orchestrator_graph.py: _run_project_workflow() 中
# 在 _check_gate() 之后, _detect_upstream_issues() 之前插入:

            # 🆕 闸门检查
            gate_result = self._check_gate(phase_id, phase_result, project_id)
            gate_results[phase_id] = gate_result

            # 🆕 一致性交叉验证 (钱学森可靠性工程)
            consistency_report = self.consistency_checker.check_phase(
                phase_id=phase_id,
                outputs=phase_result,
                upstream_outputs=upstream_outputs,
                division=self.active_division,
            )

            # 将一致性检查结果注入 Gate
            if consistency_report["overall"] == "fail":
                # major_conflict → Gate FAIL
                gate_result["status"] = "fail"
                for r in consistency_report["results"]:
                    if r["result"] == "major_conflict":
                        gate_result["checks"].append({
                            "check_id": f"consistency_{r['pair_id']}",
                            "description": f"一致性矛盾: {r['agent_a']} ↔ {r['agent_b']}",
                            "check_type": "llm",
                            "result": "fail",
                            "detail": r["detail"],
                        })
                        print(f"  ❌ consistency:[{r['pair_id']}] {r['detail'][:120]}")

            elif consistency_report["overall"] == "warn":
                # minor_inconsistency → 修正建议注入到下游输入
                fixes = []
                for r in consistency_report["results"]:
                    if r["result"] == "minor_inconsistency" and r["suggested_fix"]:
                        fixes.append(f"- [{r['pair_id']}]: {r['suggested_fix']}")
                if fixes:
                    all_outputs[phase_id]["_consistency_fixes"] = "\n".join(fixes)
                    print(f"  ⚠️ consistency: {consistency_report['minor']} 轻微不一致, "
                          f"修正建议已注入下游")

            # 🆕 反馈环B: 检测下游发现的上游问题
            upstream_issues = self._detect_upstream_issues(
                phase_id, phase_result, project_id
            )
```

### 5.3 上游输出传递

跨 Phase 检查（如 Phase 6 checking against Phase 3/4）需要上游输出。当前 `_run_project_workflow()` 已有 `upstream_outputs` 变量，直接传递即可：

```python
# Phase 6 的一致性检查需要 ml-engineer (P3) 和 biostatistician (P4) 的输出
# upstream_outputs 已经包含了所有上游 Phase 的 Agent 输出
consistency_report = self.consistency_checker.check_phase(
    phase_id=phase_id,
    outputs=phase_result,               # 当前 Phase: scientific-writer
    upstream_outputs=upstream_outputs,   # 上游: ml-engineer + biostatistician + ...
    division=self.active_division,
)
```

---

## 六、分场景判定逻辑

### 6.1 一致性检查结果 → Gate 行为

```
consistency["overall"]
    │
    ├── "pass" (全部一致)
    │   └──→ 不影响 Gate 判定, 原有逻辑继续
    │
    ├── "warn" (有 minor_inconsistency)
    │   └──→ 修正建议注入到 _consistency_fixes
    │       下游 Agent 在 build_agent_input 时可读取修正建议
    │       Gate 不 FAIL, 不阻断
    │
    └── "fail" (有 major_conflict)
        └──→ 注入到 gate_result["checks"] 作为 fail 检查项
            Gate 整体判定为 FAIL
            → 同Phase返工 (反馈环A)
            或 → 跨Phase返工 (反馈环B, 如果矛盾在跨Phase检查)
```

### 6.2 容灾设计

```
一致性检查 LLM 调用失败
    │
    ├── 单次 check 失败
    │   └──→ 该 pair 标记为 "skipped"
    │       confidence="low"
    │       不影响其他 pair 的检查
    │
    ├── 全部 check 失败 (LLM 不可用)
    │   └──→ overall="pass" (不阻断主流程)
    │       detail 中标注 "一致性检查不可用"
    │       记录到运行日志
    │
    └── 降级检查 (无 LLM 时)
        └──→ 简单的关键词/数字对比 (future)
            当前版本: 跳过 + 告警
```

### 6.3 性能约束

| 约束项 | 值 | 说明 |
|--------|-----|------|
| 每次 check 的输入长度 | ≤ 6000 字符 | 两个 Agent 输出各截断到 3000 字符 |
| 每次 check 的 LLM 调用 | 1 次 chat | 无 tool calling |
| 每 Phase 最多 check 次数 | 3 | 最多 3 个检查对 |
| 预期额外耗时 | 10-30 秒/Phase | 取决于 LLM 响应速度 |
| 预期额外 token 消耗 | ~2000-5000/check | 输入截断 + 简短输出 |

---

## 七、测试方案

### 7.1 单元测试

```python
# tests/test_consistency_checker.py

class TestConsistencyChecker:
    
    def test_consistent_outputs(self):
        """两个 Agent 输出一致 → consistent"""
        outputs = {
            "clinical-researcher": "表型定义: frailty_index 基于 36 项缺陷累积",
            "data-engineer": "数据字典: frailty_index 变量存在, 缺失率 5%",
        }
        checker = ConsistencyChecker(mock_llm_with_response(
            "**检查结果**: consistent\n"
            "**详细说明**: 变量 frailty_index 在两者中名称一致"
        ))
        report = checker.check_phase("problem_definition", outputs)
        assert report["overall"] == "pass"
    
    def test_minor_inconsistency(self):
        """变量名细微差异 → minor_inconsistency"""
        outputs = {
            "clinical-researcher": "使用 frailty_index_v2 作为主要暴露",
            "data-engineer": "数据中包含 frailty_index (无 _v2 后缀)",
        }
        checker = ConsistencyChecker(mock_llm_with_response(
            "**检查结果**: minor_inconsistency\n"
            "**修正建议**: 统一使用 frailty_index (数据中实际名称)"
        ))
        report = checker.check_phase("problem_definition", outputs)
        assert report["overall"] == "warn"
        assert report["minor"] == 1
    
    def test_major_conflict(self):
        """效应方向矛盾 → major_conflict"""
        outputs = {
            "clinical-researcher": "frailty_index 升高与死亡率呈正相关",
            "pi": "PI 终审: frailty_index 升高与死亡率呈负相关, 需核实",
        }
        checker = ConsistencyChecker(mock_llm_with_response(
            "**检查结果**: major_conflict\n"
            "**详细说明**: 效应方向完全相反, 存在严重矛盾"
        ))
        report = checker.check_phase("review", outputs)
        assert report["overall"] == "fail"
        assert report["major"] == 1
    
    def test_skipped_when_agent_missing(self):
        """某个 Agent 输出缺失 → 跳过该检查对"""
        outputs = {"clinical-researcher": "表型定义..."}
        # data-engineer 输出缺失
        checker = ConsistencyChecker(mock_llm())
        report = checker.check_phase("problem_definition", outputs)
        # 有一个 pair (phenotype_vs_data_dict) 需要 data-engineer
        skipped = [r for r in report["results"] if r["result"] == "skipped"]
        assert len(skipped) >= 1
    
    def test_no_checks_for_phase_without_pairs(self):
        """无效 Phase → 空报告"""
        checker = ConsistencyChecker(mock_llm())
        report = checker.check_phase("execution", {})  # Phase 3 无检查对
        assert report["pairs_checked"] == 0
        assert report["overall"] == "pass"
    
    def test_cross_phase_check(self):
        """跨Phase检查: Phase 6 paper vs Phase 3 ml-engineer"""
        outputs = {"scientific-writer": "AUC=0.82, ..."}
        upstream = {"ml-engineer": "AUC=0.85, ..."}
        checker = ConsistencyChecker(mock_llm_with_response(
            "**检查结果**: minor_inconsistency\n"
            "**详细说明**: AUC 数值不一致 (0.82 vs 0.85)"
        ))
        report = checker.check_phase(
            "writing", outputs, upstream_outputs=upstream
        )
        assert report["overall"] == "warn"
```

### 7.2 集成测试场景

| 场景 | 输入 | 期望 |
|------|------|------|
| Phase 1 变量名一致 | clinical: "frailty_index" / data: "frailty_index 存在" | overall=pass |
| Phase 1 变量名不一致 | clinical: "frailty_v2" / data: "只有 frailty_index" | overall=warn, 修正建议注入 |
| Phase 2 方法一致 | comp-bio: "XGBoost" / stats: "XGBoost" in SAP | overall=pass |
| Phase 5 结论矛盾 | clinical: "临床价值高" / PI: "临床意义有限" | overall=fail, Gate FAIL |
| Phase 6 数字不一致 | paper: AUC=0.82 / ml-report: AUC=0.85 | overall=warn |
| Phase 6 编造数据 | paper 引用 ml-report 中不存在的数字 | overall=fail |
| LLM 全部调用失败 | network error | overall=pass, 不阻断, 日志标注 |
| 单 pair LLM 失败 | 1/3 checks fail | 该 pair skip, 其余正常 |

---

## 八、文件改动清单

| 文件 | 改动类型 | 改动内容 | 预计行数 |
|------|---------|---------|---------|
| `engine/core/consistency_checker.py` | **新文件** | ConsistencyChecker 类 + CONSISTENCY_PAIRS + System Prompt | ~250 |
| `engine/core/orchestrator_graph.py` | 修改 | `__init__` 初始化 checker + `_run_project_workflow` 插入一致性检查 + 导入 | +30 |
| `tests/test_consistency_checker.py` | **新文件** | 单元测试 (6 cases) + 集成测试 (8 scenarios) | ~200 |
| `company/company-sop.md` | 修改 | QA 章节增加一致性交叉验证说明 | +15 |

---

## 附录：与其他模块的关系

```
┌─────────────────────────────────────────────────────────┐
│                    可靠性工程体系                          │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ LLM 容错      │  │ 一致性交叉    │  │ 知识库备份    │  │
│  │ (P1-2 已完成) │  │ 验证 (本次)   │  │ (P3-3 已完成) │  │
│  │              │  │              │  │               │  │
│  │ • 重试+降级   │  │ • Agent间对比 │  │ • git backup  │  │
│  │ • 指数退避    │  │ • 矛盾检测    │  │ • shell 脚本   │  │
│  │ • checkpoint  │  │ • 修正建议    │  │               │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────────┘  │
│         │                 │                              │
│         └────────┬────────┘                              │
│                  │                                       │
│                  ▼                                       │
│    ┌─────────────────────────────┐                      │
│    │ 钱学森可靠性工程核心原则:      │                      │
│    │ "用不可靠的元件组成可靠系统"    │                      │
│    │                             │                      │
│    │ 单 LLM 可靠性: ~75%          │                      │
│    │ 重试后: ~90%                 │                      │
│    │ 重试 + 交叉验证后: ~95%+      │                      │
│    └─────────────────────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

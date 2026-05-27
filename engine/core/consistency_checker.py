"""
一致性交叉验证引擎 — Consistency Cross-Validator

基于钱学森可靠性工程思想:
"用不可靠的元件, 通过工程协调的方法, 组成可靠的系统。"

两个不可靠的 LLM Agent 输出, 经过交叉验证后,
其一致部分的可靠性远高于单个 Agent 的可靠性。

用法:
    from .consistency_checker import ConsistencyChecker
    from .llm_client import LLMClient

    llm = LLMClient(...)
    checker = ConsistencyChecker(llm, verbose=True)
    report = checker.check_phase(
        phase_id="problem_definition",
        outputs={"clinical-researcher": "...", "data-engineer": "..."},
        upstream_outputs={},
        division="geriatrics",
    )
    # report["overall"] ∈ {"pass", "warn", "fail"}
"""

import re
from datetime import datetime
from typing import Optional, Literal


# ================================================================
# 一致性检查对定义 — 每个 Phase 检查哪些 Agent 对
# ================================================================

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
    # 🆕 Phase 3 跨阶段一致性: 验证模型输出与 SAP 声明一致
    "execution": [
        {
            "pair_id": "cv_results_vs_sap",
            "agent_a": "ml-engineer",
            "agent_b": "biostatistician",
            "source": "cross_phase",
            "verify_phase": "design",
            "severity": "critical",
            "check_prompt": (
                "对比 ml-engineer 的 cv_results.json 中实际训练的模型类型 "
                "(xgboost/logistic_regression/random_forest 等) 与 biostatistician "
                "的 SAP (sap.md) 中声明的分析方法列表。检查: (1) cv_results.json 中 "
                "每个实际训练的模型是否在 SAP 中有对应的统计方法声明, "
                "(2) SAP 中声明的分析是否都已被执行 (未执行的需说明原因), "
                "(3) 模型评估指标 (AUC/Brier/Calibration) 是否与 SAP 规定的指标一致。"
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
            "agent_a_source": "current_phase",
            "agent_b": "ml-engineer",
            "agent_b_source": "upstream",
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
            "agent_a_source": "current_phase",
            "agent_b": "biostatistician",
            "agent_b_source": "upstream",
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


# ================================================================
# System Prompt
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
- major_conflict 仅用于实质性的、影响研究结论的矛盾

## 输出格式
请严格按以下格式输出:

**检查结果**: [consistent / minor_inconsistency / major_conflict]
**Agent A 的关键主张**: [从A的输出中提取的与本次检查相关的关键信息, 1-2句话]
**Agent B 的关键主张**: [从B的输出中提取的与本次检查相关的关键信息, 1-2句话]
**详细说明**: [具体的一致/不一致之处, 2-4句话]
**修正建议**: [仅 minor_inconsistency 时填写, 给出具体的自动修正方案]
**确信度**: [high / medium / low]"""


# ================================================================
# ConsistencyChecker 类
# ================================================================

class ConsistencyChecker:
    """
    Agent 间一致性交叉验证引擎。

    Parameters:
        llm_client: LLMClient 实例 (用于调用 LLM 做交叉验证)
        verbose: 是否打印检查日志
    """

    def __init__(self, llm_client, verbose: bool = True):
        self.llm = llm_client
        self.verbose = verbose

    def check_phase(
        self,
        phase_id: str,
        outputs: dict[str, str],
        upstream_outputs: dict[str, str] = None,
        division: str = "geriatrics",
    ) -> dict:
        """
        对指定 Phase 执行所有定义的一致性检查对。

        Args:
            phase_id: Phase ID
            outputs: 当前 Phase 的 Agent 输出 {agent_id: output_text}
            upstream_outputs: 上游 Phase 的输出 (跨Phase检查时需要)
            division: 事业部 ID

        Returns:
            {
                "phase_id": str,
                "timestamp": str,
                "pairs_checked": int,
                "consistent": int,
                "minor": int,
                "major": int,
                "results": list[dict],
                "overall": "pass" | "warn" | "fail",
            }
        """
        pairs = CONSISTENCY_PAIRS.get(phase_id, [])
        upstream_outputs = upstream_outputs or {}

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
            # 1. 获取两个 Agent 的输出 (支持 per-agent source)
            source_a = pair_def.get("agent_a_source", pair_def.get("source", "current_phase"))
            source_b = pair_def.get("agent_b_source", pair_def.get("source", "current_phase"))
            output_a = self._resolve_output(
                pair_def["agent_a"], source_a,
                outputs, upstream_outputs, division
            )
            output_b = self._resolve_output(
                pair_def["agent_b"], source_b,
                outputs, upstream_outputs, division
            )

            if not output_a or not output_b:
                results.append(self._skip_result(
                    pair_def, bool(output_a), bool(output_b)
                ))
                if self.verbose:
                    print(f"  ⏭️  consistency:[{pair_def['pair_id']}] "
                          f"skipped (A={bool(output_a)} B={bool(output_b)})")
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
                    result.get("result", ""), "❓")
                detail = result.get("detail", "")[:100]
                print(f"  {icon} consistency:[{pair_def['pair_id']}] "
                      f"{result.get('result', '?')}: {detail}")

        # 3. 汇总
        consistent = sum(1 for r in results if r.get("result") == "consistent")
        minor = sum(1 for r in results if r.get("result") == "minor_inconsistency")
        major = sum(1 for r in results if r.get("result") == "major_conflict")

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
        """根据 source 类型从对应池中解析 Agent 输出"""
        pool = outputs if source == "current_phase" else upstream
        return self._find_output(pool, agent_id, division)

    def _find_output(
        self, outputs: dict, agent_id: str, division: str,
    ) -> Optional[str]:
        """
        在 outputs 中查找指定 Agent 的输出。
        支持三种匹配: 精确匹配 → 短名匹配 → 事业部前缀匹配
        """
        if not outputs:
            return None

        # 精确匹配
        if agent_id in outputs:
            return outputs[agent_id]

        # 模糊匹配: */agent_id 或 division/agent_id
        for key, value in outputs.items():
            if key.endswith(f"/{agent_id}") or key == agent_id:
                return value
            # 也匹配不带 shared/ 前缀的短名 (如 "ml-engineer" 匹配 "shared/ml-engineer")
            if key.split("/")[-1] == agent_id.split("/")[-1]:
                return value

        return None

    def _run_check(
        self, pair_def: dict, output_a: str, output_b: str,
    ) -> dict:
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
        max_len = 3000  # 每个 Agent 输出截断到这个长度

        def _truncate(text: str, label: str) -> str:
            if len(text) <= max_len:
                return text
            # 保留开头和结尾 (开头有上下文, 结尾有结论)
            half = max_len // 2
            return text[:half] + f"\n\n...({label} 输出截断, 原文 {len(text)} 字符)...\n\n" + text[-half:]

        return f"""## 一致性检查: {pair_id}

### 检查指令
{check_prompt}

### Agent A: {agent_a}
{_truncate(output_a, agent_a)}

### Agent B: {agent_b}
{_truncate(output_b, agent_b)}

请按格式输出检查结果。"""

    def _parse_result(self, pair_def: dict, response: str) -> dict:
        """解析 LLM 返回的一致性检查结果为结构化 dict"""
        result = "major_conflict"  # 默认最坏情况
        detail = ""
        suggested_fix = ""
        a_claim = ""
        b_claim = ""
        confidence = "medium"

        # 解析检查结果 (处理 markdown bold: **检查结果**: 或 检查结果:)
        result_match = re.search(
            r'\*{0,2}检查结果\*{0,2}[：:]\s*(consistent|minor_inconsistency|major_conflict)',
            response, re.IGNORECASE
        )
        if result_match:
            result = result_match.group(1).lower()

        # 解析 Agent A 主张
        a_match = re.search(
            r'\*{0,2}Agent A[的]?.*?主张\*{0,2}[：:]\s*(.+?)(?=\n\*{0,2}Agent B|\n\*{0,2}详细说明|\Z)',
            response, re.DOTALL | re.IGNORECASE
        )
        if a_match:
            a_claim = a_match.group(1).strip()[:300]

        # 解析 Agent B 主张
        b_match = re.search(
            r'\*{0,2}Agent B[的]?.*?主张\*{0,2}[：:]\s*(.+?)(?=\n\*{0,2}详细说明|\n\*{0,2}修正建议|\Z)',
            response, re.DOTALL | re.IGNORECASE
        )
        if b_match:
            b_claim = b_match.group(1).strip()[:300]

        # 解析详细说明
        detail_match = re.search(
            r'\*{0,2}详细说明\*{0,2}[：:]\s*(.+?)(?=\n\*{0,2}修正建议|\n\*{0,2}确信度|\Z)',
            response, re.DOTALL | re.IGNORECASE
        )
        if detail_match:
            detail = detail_match.group(1).strip()[:500]

        # 解析修正建议
        fix_match = re.search(
            r'\*{0,2}修正建议\*{0,2}[：:]\s*(.+?)(?=\n\*{0,2}确信度|\n\*{0,2}$|\Z)',
            response, re.DOTALL | re.IGNORECASE
        )
        if fix_match:
            suggested_fix = fix_match.group(1).strip()[:500]

        # 解析确信度
        conf_match = re.search(
            r'\*{0,2}确信度\*{0,2}[：:]\s*(high|medium|low)', response, re.IGNORECASE
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

    def _skip_result(self, pair_def: dict, a_ok: bool, b_ok: bool) -> dict:
        """某个 Agent 输出缺失时的跳过结果"""
        missing = []
        if not a_ok:
            missing.append(pair_def["agent_a"])
        if not b_ok:
            missing.append(pair_def["agent_b"])
        return {
            "pair_id": pair_def["pair_id"],
            "agent_a": pair_def["agent_a"],
            "agent_b": pair_def["agent_b"],
            "result": "skipped",
            "detail": f"输出缺失: {', '.join(missing)}",
            "suggested_fix": "",
            "a_claim": "",
            "b_claim": "",
            "confidence": "low",
        }

    def _error_result(self, pair_def: dict, error: str) -> dict:
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

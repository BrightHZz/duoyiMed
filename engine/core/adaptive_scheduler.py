"""
自适应调度器 — 最优控制模块

基于 RunAnalyzer 的统计数据, 对即将执行的 Phase 做自适应调整。
对应钱学森最优控制思想: "基于系统辨识结果, 动态调整控制参数。"

用法:
    from .run_analyzer import RunAnalyzer
    from .adaptive_scheduler import AdaptiveScheduler

    analyzer = RunAnalyzer(...)
    analyzer.load(days=90)
    scheduler = AdaptiveScheduler(analyzer)
    decision = scheduler.decide("execution", division="geriatrics")
    # decision["action"] → "normal" | "add_redundancy" | "split_task" | ...
"""

import statistics
from collections import defaultdict


class AdaptiveScheduler:
    """
    自适应调度器 — 基于运行数据动态调整 Phase 执行策略。

    决策规则按优先级排列:
    1. 历史一次通过率 < 40% → 增加冗余
    2. 平均耗时超过目标 1.5 倍 → 拆分任务
    3. 降级率 > 20% → 建议切换模型
    4. LLM Gate 审查通过率 > 95% → 可跳过 LLM 审查
    """

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.records = analyzer.records

    def decide(self, phase_id: str, division: str = "geriatrics") -> dict:
        """
        基于运行数据, 对即将执行的 Phase 做出调度决策。

        Returns:
            {
                "action": "normal|add_redundancy|split_task|degrade_model|skip_gate_llm",
                "reason": str,
                "params": dict,
            }
        """
        stats = self._get_phase_stats(phase_id, division)

        if not stats or stats.get("sample_size", 0) < 3:
            return {
                "action": "normal",
                "reason": "历史数据不足, 保持默认策略",
                "params": {},
            }

        # 规则1: 通过率低 → 增加冗余
        pass_rate = stats.get("pass_rate", 100)
        if pass_rate < 40:
            return {
                "action": "add_redundancy",
                "reason": (
                    f"Phase {phase_id} 历史一次通过率仅 {pass_rate}%, "
                    f"建议增加交叉验证 Agent 提高可靠性"
                ),
                "params": {"extra_agent": "cross-validator"},
            }

        # 规则2: 耗时超标 → 拆分或增加并行
        avg_h = stats.get("avg_hours", 0)
        target_h = stats.get("target_hours", 1)
        if avg_h > target_h * 1.5:
            new_parallel = min(stats.get("current_parallelism", 1) + 2, 5)
            return {
                "action": "split_task",
                "reason": (
                    f"Phase {phase_id} 平均耗时 {avg_h:.1f}h, "
                    f"超过目标 {target_h}h 的 1.5 倍, "
                    f"建议增加并行度到 {new_parallel}"
                ),
                "params": {"suggested_parallelism": new_parallel},
            }

        # 规则3: 降级率高 → 建议切换模型
        degraded_rate = stats.get("degraded_rate", 0)
        if degraded_rate > 20:
            return {
                "action": "degrade_model",
                "reason": (
                    f"Phase {phase_id} 的 Agent 降级率 {degraded_rate}% 偏高, "
                    f"建议考虑默认使用 Haiku 模型"
                ),
                "params": {"suggested_model": "claude-haiku-4-5-20251001"},
            }

        # 规则4: LLM Gate 审查通过率极高 → 可跳过
        llm_pass = stats.get("llm_gate_pass_rate", 0)
        if llm_pass > 95 and stats.get("sample_size", 0) >= 10:
            return {
                "action": "skip_gate_llm",
                "reason": (
                    f"Phase {phase_id} 的 LLM Gate 审查通过率 {llm_pass}%, "
                    f"可信任 auto checks, 跳过 LLM 审查以节省 token"
                ),
                "params": {},
            }

        return {"action": "normal", "reason": "所有指标正常", "params": {}}

    # ================================================================
    # 统计数据提取
    # ================================================================

    def _get_phase_stats(self, phase_id: str, division: str) -> dict:
        """从 RunLog 记录中提取指定 Phase 的历史统计数据"""
        # 筛选相关记录
        records = [
            r for r in self.records
            if r.get("phase_id") == phase_id
            and not r.get("agent_id", "").startswith("_")
        ]
        div_records = [r for r in records if r.get("division") == division]
        if div_records:
            records = div_records

        if len(records) < 3:
            return {}

        # 计算指标
        times = [float(r.get("wall_time_sec", 0)) for r in records if r.get("success")]
        success_count = sum(1 for r in records if r.get("success"))
        total_count = len(records)
        degraded_count = sum(1 for r in records if r.get("degraded"))

        # 通过率
        pass_rate = round(success_count / total_count * 100, 1) if total_count > 0 else 0

        # 平均耗时
        avg_sec = statistics.mean(times) if times else 0
        avg_hours = round(avg_sec / 3600, 1)

        # 降级率
        degraded_rate = round(degraded_count / total_count * 100, 1) if total_count > 0 else 0

        # 目标耗时 (基于 Phase 定义)
        target_hours = {
            "system_design": 0.5, "problem_definition": 4.0, "design": 2.0,
            "execution": 5.0, "external_validation": 3.0, "review": 2.0,
            "writing": 7.0,
        }.get(phase_id, 4.0)

        return {
            "pass_rate": pass_rate,
            "avg_hours": avg_hours,
            "target_hours": target_hours,
            "sample_size": total_count,
            "degraded_rate": degraded_rate,
            "llm_gate_pass_rate": self._calc_llm_gate_pass_rate(phase_id),
            "current_parallelism": 1,
        }

    def _calc_llm_gate_pass_rate(self, phase_id: str) -> float:
        """计算指定 Phase 的 LLM Gate 审查通过率"""
        gate_records = [
            r for r in self.records
            if r.get("agent_id") == "_gate"
            and r.get("phase_id") == phase_id
        ]
        if len(gate_records) < 5:
            return 100  # 数据不足时默认通过

        passes = sum(1 for r in gate_records if r.get("gate_status") == "pass")
        return round(passes / len(gate_records) * 100, 1)

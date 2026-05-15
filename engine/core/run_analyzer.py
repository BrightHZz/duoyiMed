"""
公司运行数据分析器 — 系统辨识模块

读取运行日志 JSONL 文件, 聚合统计并生成 Markdown 报告。
零外部依赖 (json + statistics 标准库)。

日志目录结构 (v2):
  outputs/projects/{project_id}/run_logs/*.jsonl   — 项目隔离日志
  outputs/_shared/run_logs/*.jsonl                 — 共享日志 (轻量工作流)
  outputs/run_logs/*.jsonl                         — 旧版兼容

用法:
    python -m engine.core.run_analyzer                    # 分析全部数据
    python -m engine.core.run_analyzer --days 30          # 近 30 天
    python -m engine.core.run_analyzer --output report.md # 输出到文件
"""

import json
import statistics
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional


class RunAnalyzer:
    """
    读取 run_logs JSONL 文件, 聚合统计, 生成 Markdown 报告。

    支持新版项目隔离目录 (outputs/projects/{id}/run_logs/) 和
    旧版扁平目录 (outputs/run_logs/)。

    用法:
        analyzer = RunAnalyzer(log_dir="outputs/run_logs")
        analyzer.load(days=90)
        report = analyzer.generate_report()
    """

    def __init__(self, log_dir: str = "outputs/run_logs"):
        self.log_dir = Path(log_dir)
        self.records: list[dict] = []
        self.start_date: Optional[str] = None
        self.end_date: Optional[str] = None

    def _find_log_dirs(self) -> list[Path]:
        """发现所有日志目录。

        检测策略:
        1. 如果 log_dir 指向 projects/ 目录 → 扫描所有 {project_id}/run_logs/ + _shared/run_logs/
        2. 如果 log_dir 是旧版 outputs/run_logs/ → 直接使用
        """
        log_dir = self.log_dir
        if not log_dir.exists():
            return []

        # 检测是否为 projects 根目录 (包含项目子目录或 _shared)
        if (log_dir.name == "projects" or
                (log_dir / "_shared" / "run_logs").exists() or
                any((d / "run_logs").exists() for d in log_dir.iterdir() if d.is_dir() and d.name != "_shared")):
            dirs = []
            # 扫描项目隔离日志
            for project_dir in log_dir.iterdir():
                if project_dir.is_dir() and project_dir.name != "_shared":
                    run_logs = project_dir / "run_logs"
                    if run_logs.exists():
                        dirs.append(run_logs)
            # 共享日志
            shared = log_dir / "_shared" / "run_logs"
            if shared.exists():
                dirs.append(shared)
            return dirs

        # 旧版: log_dir 直接是 run_logs 目录
        return [log_dir]

    def load(self, days: int = 0) -> int:
        """加载日志文件。days=0 表示全部, days=30 表示最近 30 天。"""
        log_dirs = self._find_log_dirs()
        if not log_dirs:
            return 0

        # 收集所有 .jsonl 文件
        all_files = []
        for d in log_dirs:
            all_files.extend(sorted(d.glob("*.jsonl")))

        if days > 0:
            cutoff = datetime.now() - timedelta(days=days)
            all_files = [f for f in all_files if self._file_date(f) >= cutoff.date()]

        self.records = []
        for f in all_files:
            try:
                for line in f.read_text().splitlines():
                    line = line.strip()
                    if line:
                        self.records.append(json.loads(line))
            except Exception:
                continue

        if self.records:
            dates = [r.get("timestamp", "")[:10] for r in self.records if r.get("timestamp")]
            if dates:
                self.start_date = min(dates)
                self.end_date = max(dates)

        return len(self.records)

    @staticmethod
    def _file_date(path: Path) -> datetime.date:
        """从文件名提取日期, e.g. '2026-05-10.jsonl' → date(2026,5,10)"""
        try:
            stem = path.stem
            return datetime.strptime(stem, "%Y-%m-%d").date()
        except ValueError:
            return datetime.min.date()

    # ================================================================
    # 聚合统计
    # ================================================================

    def _phase_stats(self) -> list[dict]:
        """Phase 耗时分布"""
        groups = defaultdict(list)
        for r in self.records:
            pid = r.get("phase_id", "")
            if pid and r.get("success") and not r.get("agent_id", "").startswith("_"):
                groups[pid].append(r["wall_time_sec"])

        def _fmt_sec(s):
            if s < 60:
                return f"{s:.0f}s"
            elif s < 3600:
                return f"{s / 60:.1f}m"
            return f"{s / 3600:.1f}h"

        target_hours = {
            "system_design": 0.5, "problem_definition": 4.0, "design": 2.0,
            "execution": 5.0, "external_validation": 3.0, "review": 2.0,
            "writing": 7.0,
        }

        stats = []
        for phase_id in ["system_design", "problem_definition", "design",
                          "execution", "external_validation", "review", "writing"]:
            times = groups.get(phase_id, [])
            if not times:
                continue
            total_sec = sum(times)
            avg_sec = statistics.mean(times)
            p50_sec = statistics.median(times)
            p95_sec = sorted(times)[int(len(times) * 0.95)] if len(times) >= 20 else avg_sec
            target_h = target_hours.get(phase_id, 4.0)
            pass_rate = sum(1 for t in times if (t / 3600) <= target_h) / len(times) * 100

            bottleneck = ""
            if avg_sec / 3600 > target_h * 1.3:
                bottleneck = "⚠️ 瓶颈"
            elif avg_sec / 3600 > target_h * 1.1:
                bottleneck = "⚡ 偏高"

            stats.append({
                "phase_id": phase_id,
                "count": len(times),
                "total": _fmt_sec(total_sec),
                "avg": _fmt_sec(avg_sec),
                "p50": _fmt_sec(p50_sec),
                "p95": _fmt_sec(p95_sec),
                "target": _fmt_sec(target_h * 3600),
                "pass_rate": round(pass_rate),
                "status": bottleneck or "✓",
            })
        return stats

    def _agent_stats(self) -> list[dict]:
        """Agent 调用统计"""
        groups = defaultdict(lambda: {"total": 0, "success": 0, "degraded": 0,
                                       "errors": defaultdict(int), "gate_fails": 0})
        for r in self.records:
            agent = r.get("agent_id", "")
            if agent.startswith("_"):
                continue
            groups[agent]["total"] += 1
            if r.get("success"):
                groups[agent]["success"] += 1
            if r.get("degraded"):
                groups[agent]["degraded"] += 1
            if r.get("error_type"):
                groups[agent]["errors"][r["error_type"]] += 1
            if r.get("gate_status") == "fail":
                groups[agent]["gate_fails"] += 1

        stats = []
        for agent, data in sorted(groups.items()):
            total = data["total"]
            if total == 0:
                continue
            success_rate = data["success"] / total * 100
            degraded_rate = data["degraded"] / total * 100
            top_errors = sorted(data["errors"].items(), key=lambda x: -x[1])[:2]
            error_summary = ", ".join(f"{e}({c})" for e, c in top_errors) if top_errors else "—"

            status = ""
            if success_rate < 70:
                status = "⚠️ 低"
            elif success_rate < 85:
                status = "⚡ 关注"

            stats.append({
                "agent_id": agent,
                "count": total,
                "success_rate": round(success_rate),
                "degraded_rate": round(degraded_rate),
                "gate_fails": data["gate_fails"],
                "top_errors": error_summary,
                "status": status or "✓",
            })
        return stats

    def _gate_stats(self) -> list[dict]:
        """Gate 状态统计"""
        gate_records = [r for r in self.records if r.get("agent_id") == "_gate"]
        groups = defaultdict(list)
        for r in gate_records:
            groups[r.get("phase_id", "?")].append(r.get("gate_status", "?"))

        stats = []
        for phase_id, statuses in groups.items():
            total = len(statuses)
            passes = sum(1 for s in statuses if s == "pass")
            conds = sum(1 for s in statuses if s == "cond_pass")
            fails = sum(1 for s in statuses if s == "fail")
            stats.append({
                "phase_id": phase_id,
                "total": total,
                "pass_rate": round(passes / total * 100) if total else 0,
                "cond_pass": conds,
                "fail": fails,
                "status": "⚠️" if fails > 0 else "✓",
            })
        return stats

    def _resource_stats(self) -> dict:
        """资源消耗统计"""
        total_in = total_out = total_calls = 0
        for r in self.records:
            if r.get("agent_id", "").startswith("_"):
                continue
            total_calls += 1
            total_in += r.get("input_tokens", 0)
            total_out += r.get("output_tokens", 0)
        return {
            "total_calls": total_calls,
            "total_in_tokens": total_in,
            "total_out_tokens": total_out,
            "est_cost": f"${total_in / 1_000_000 * 3 + total_out / 1_000_000 * 15:.1f}",
        }

    def _improvement_suggestions(self, phase_stats: list, agent_stats: list) -> list:
        """基于数据自动生成改进建议"""
        suggestions = []

        # Phase 耗时超标
        for p in phase_stats:
            if "瓶颈" in p.get("status", ""):
                suggestions.append(
                    f"{p['phase_id']} 平均耗时 {p['avg']} 超过目标 {p['target']} → "
                    f"考虑增加并行 Agent 或拆分任务"
                )

        # Agent 通过率低
        for a in agent_stats:
            if "低" in a.get("status", "") or "关注" in a.get("status", ""):
                suggestions.append(
                    f"{a['agent_id']} 成功率 {a['success_rate']}% → "
                    f"建议审查其 system prompt 和 few-shot 示例"
                )
            if a.get("degraded_rate", 0) > 15:
                suggestions.append(
                    f"{a['agent_id']} 降级率 {a['degraded_rate']}% 偏高 → "
                    f"检查主模型是否不稳定或 prompt 过长"
                )

        if not suggestions:
            suggestions.append("所有指标正常，暂无改进建议。")

        return suggestions

    # ================================================================
    # 报告生成
    # ================================================================

    def generate_report(self) -> str:
        """生成 Markdown 格式的完整运行状态报告"""
        if not self.records:
            return "*无运行数据。运行至少一个项目后自动生成。*\n"

        phase_stats = self._phase_stats()
        agent_stats = self._agent_stats()
        gate_stats = self._gate_stats()
        resources = self._resource_stats()
        suggestions = self._improvement_suggestions(phase_stats, agent_stats)

        date_range = f"{self.start_date or '?'} 至 {self.end_date or '?'}"
        lines = [
            f"# 公司运行状态报告",
            f"",
            f"*数据范围: {date_range} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            f"",
            f"---",
            f"",
            f"## Phase 耗时分布",
            f"",
            f"| Phase | 调用次数 | 总耗时 | 平均 | P50 | P95 | 目标 | 达标率 | 状态 |",
            f"|-------|---------|-------|------|-----|-----|------|-------|------|",
        ]
        for p in phase_stats:
            lines.append(
                f"| {p['phase_id']} | {p['count']} | {p['total']} | {p['avg']} | "
                f"{p['p50']} | {p['p95']} | {p['target']} | {p['pass_rate']}% | {p['status']} |"
            )

        lines += [
            f"",
            f"## Agent 调用统计",
            f"",
            f"| Agent | 调用次数 | 成功率 | 降级率 | Gate 失败 | 主要错误 | 状态 |",
            f"|-------|---------|-------|-------|----------|---------|------|",
        ]
        for a in agent_stats:
            lines.append(
                f"| {a['agent_id']} | {a['count']} | {a['success_rate']}% | "
                f"{a['degraded_rate']}% | {a['gate_fails']} | {a['top_errors']} | {a['status']} |"
            )

        if gate_stats:
            lines += [
                f"",
                f"## Gate 闸门统计",
                f"",
                f"| Phase | 检查次数 | 通过率 | 附条件通过 | 失败 | 状态 |",
                f"|-------|---------|-------|----------|------|------|",
            ]
            for g in gate_stats:
                lines.append(
                    f"| {g['phase_id']} | {g['total']} | {g['pass_rate']}% | "
                    f"{g['cond_pass']} | {g['fail']} | {g['status']} |"
                )

        lines += [
            f"",
            f"## 资源消耗",
            f"",
            f"| 指标 | 值 |",
            f"|------|-----|",
            f"| 总 LLM 调用次数 | {resources['total_calls']} |",
            f"| 总输入 Token | {resources['total_in_tokens']:,} |",
            f"| 总输出 Token | {resources['total_out_tokens']:,} |",
            f"| 估计 API 费用 | {resources['est_cost']} |",
            f"",
            f"## 改进建议",
            f"",
        ]
        for s in suggestions:
            lines.append(f"- {s}")

        lines += [
            f"",
            f"---",
            f"*报告由 RunAnalyzer 自动生成 (P3-1 系统辨识模块)*",
        ]

        return "\n".join(lines)

    def generate_json_summary(self) -> dict:
        """生成 JSON 汇总 (供程序化消费)"""
        return {
            "generated_at": datetime.now().isoformat(),
            "date_range": {"start": self.start_date, "end": self.end_date},
            "total_records": len(self.records),
            "phase_stats": self._phase_stats(),
            "agent_stats": self._agent_stats(),
            "gate_stats": self._gate_stats(),
            "resources": self._resource_stats(),
        }


# ================================================================
# CLI 入口
# ================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="公司运行数据分析器")
    parser.add_argument("--log-dir", default="outputs/projects", help="日志根目录 (projects/ 或旧版 run_logs/)")
    parser.add_argument("--days", type=int, default=0, help="分析天数 (0=全部)")
    parser.add_argument("--output", "-o", default=None, help="输出文件 (默认 stdout)")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    analyzer = RunAnalyzer(log_dir=args.log_dir)
    count = analyzer.load(days=args.days)

    if count == 0:
        print("无运行数据。")
    elif args.json:
        print(json.dumps(analyzer.generate_json_summary(), ensure_ascii=False, indent=2))
    else:
        report = analyzer.generate_report()
        if args.output:
            Path(args.output).write_text(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)

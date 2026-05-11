"""
项目预测器 — 系统辨识模块核心

基于历史 RunLog 数据, 为新项目提供关键指标预测。
对应钱学森系统辨识的"传递函数建模"步骤:

  输入信号(项目特征) → [公司系统] → 输出信号(耗时/成功率)
                              ↑
                    从 I/O 数据反推传递函数
"""

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProjectProfile:
    """新项目的特征画像 — 系统辨识的输入向量"""
    division: str              # "geriatrics" | "urology"
    research_type: str         # "prediction" | "causal_inference" | "systematic_review" | "exploratory"
    data_source: str           # "CHARLS" | "MIMIC-IV" | "NHANES" | "SEER" | ...
    target_journal_tier: int   # 1 (IF>15), 2 (IF 5-15), 3 (IF 2-5)
    estimated_sample_size: str = "medium(1000-10000)"


def infer_profile(user_request: str, division: str) -> ProjectProfile:
    """从用户请求文本中自动推断项目特征"""
    req = user_request.lower()

    # 研究类型推断 (综述优先于预测/因果 — "对预测模型做系统评价" 是综述不是预测)
    if any(w in req for w in ["综述", "review", "系统评价", "meta"]):
        research_type = "systematic_review"
    elif any(w in req for w in ["预测", "predict", "模型", "model", "分类", "classif"]):
        research_type = "prediction"
    elif any(w in req for w in ["因果", "causal", "效应", "effect", "关联", "association"]):
        research_type = "causal_inference"
    else:
        research_type = "exploratory"

    # 数据源推断
    data_sources = {
        "charls": "CHARLS", "clhls": "CLHLS", "hrs": "HRS", "elsa": "ELSA",
        "mimic": "MIMIC-IV", "seer": "SEER", "nhanes": "NHANES",
        "uk biobank": "UK_Biobank",
    }
    data_source = "unknown"
    for keyword, name in data_sources.items():
        if keyword in req:
            data_source = name
            break

    # 期刊 Tier 推断
    if any(w in req for w in ["lancet", "nature", "jama", "bmj", "european urology"]):
        target_tier = 1
    elif any(w in req for w in ["bmc", "plos", "frontiers"]):
        target_tier = 3
    else:
        target_tier = 2

    # 样本量推断
    if any(w in req for w in ["全样本", "大数据", "large", "biobank", ">10000"]):
        sample_size = "large(>10000)"
    elif any(w in req for w in ["小样本", "small", "罕见", "rare"]):
        sample_size = "small(<1000)"
    else:
        sample_size = "medium(1000-10000)"

    return ProjectProfile(
        division=division,
        research_type=research_type,
        data_source=data_source,
        target_journal_tier=target_tier,
        estimated_sample_size=sample_size,
    )


class ProjectPredictor:
    """
    项目预测器 — 基于历史 RunLog 数据预测新项目的关键指标。

    用法:
        from .run_analyzer import RunAnalyzer
        analyzer = RunAnalyzer(log_dir="outputs/run_logs")
        analyzer.load(days=90)

        predictor = ProjectPredictor(analyzer)
        profile = infer_profile("用 CHARLS 数据预测衰弱转换", "geriatrics")
        prediction = predictor.predict(profile)
    """

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.records = analyzer.records

    # ================================================================
    # 主预测接口
    # ================================================================

    def predict(self, profile: ProjectProfile) -> dict:
        """
        基于历史类似项目, 预测新项目的关键指标。

        Returns:
            {
                similar_projects_count, confidence,
                estimated_total_hours, estimated_total_hours_range,
                phase_predictions, estimated_success_rate,
                bottleneck_phase, recommended_journal_tier,
                risk_factors, similar_projects_summary,
            }
        """
        similar = self._find_similar_projects(profile)

        if not similar:
            return self._low_confidence_result(profile)

        n = len(similar)
        confidence = "high" if n >= 5 else ("medium" if n >= 2 else "low")

        estimated_hours = self._estimate_total_hours(similar)
        hours_range = self._hours_range(similar)
        success_rate = self._estimate_success_rate(similar)
        bottleneck = self._identify_bottleneck(similar)
        recommended_tier = self._recommend_tier(similar, profile.target_journal_tier)
        risks = self._extract_risk_factors(similar)
        phase_preds = self._predict_phases(similar)

        return {
            "similar_projects_count": n,
            "confidence": confidence,
            "estimated_total_hours": estimated_hours,
            "estimated_total_hours_range": hours_range,
            "phase_predictions": phase_preds,
            "estimated_success_rate": success_rate,
            "bottleneck_phase": bottleneck,
            "recommended_journal_tier": recommended_tier,
            "risk_factors": risks,
            "similar_projects_summary": self._format_summary(
                n, estimated_hours, hours_range, success_rate, bottleneck,
                recommended_tier, confidence
            ),
        }

    # ================================================================
    # 相似项目搜索
    # ================================================================

    def _find_similar_projects(self, profile: ProjectProfile) -> list[dict]:
        """从 RunLog 中找到与 profile 相似的历史项目, 按相似度排序, 取 top-10"""
        projects = self._group_by_project()

        scored = []
        for proj_id, proj_records in projects.items():
            score = self._similarity_score(profile, proj_records)
            if score > 0:
                scored.append({
                    "project_id": proj_id,
                    "score": score,
                    "metrics": self._compute_project_metrics(proj_records),
                })

        scored.sort(key=lambda x: -x["score"])
        return scored[:10]

    def _similarity_score(self, profile: ProjectProfile, records: list) -> int:
        """
        计算相似度分数:
        事业部匹配 +4, 研究类型匹配 +3, 数据源匹配 +2, 期刊Tier相同±1: +1
        """
        score = 0
        divs = set(r.get("division", "") for r in records)
        if profile.division in divs:
            score += 4

        proj_id = records[0].get("project_id", "").lower()
        if profile.research_type and profile.research_type in proj_id:
            score += 3
        if profile.data_source.lower() in proj_id:
            score += 2

        return score

    def _group_by_project(self) -> dict[str, list[dict]]:
        """将 RunLog records 按 project_id 分组"""
        projects: dict[str, list[dict]] = {}
        for r in self.records:
            pid = r.get("project_id", "unknown")
            if pid not in projects:
                projects[pid] = []
            projects[pid].append(r)
        return projects

    def _compute_project_metrics(self, records: list) -> dict:
        """从单个项目的 RunLog 记录中计算聚合指标"""
        phases: dict[str, dict] = {}
        for r in records:
            pid = r.get("phase_id", "")
            if pid not in phases:
                phases[pid] = {"total_time": 0.0, "count": 0, "success": 0, "fail": 0}
            phases[pid]["total_time"] += float(r.get("wall_time_sec", 0))
            phases[pid]["count"] += 1
            if r.get("success"):
                phases[pid]["success"] += 1
            else:
                phases[pid]["fail"] += 1

        total_time = sum(p["total_time"] for p in phases.values())
        total_calls = sum(p["count"] for p in phases.values())
        success_calls = sum(p["success"] for p in phases.values())

        return {
            "total_hours": round(total_time / 3600, 1),
            "phase_times": {pid: round(p["total_time"] / 3600, 1)
                            for pid, p in phases.items()},
            "phase_success_rates": {
                pid: round(p["success"] / p["count"] * 100) if p["count"] > 0 else 0
                for pid, p in phases.items()
            },
            "overall_success_rate": (
                round(success_calls / total_calls * 100) if total_calls > 0 else 0
            ),
            "total_phases": len(phases),
        }

    # ================================================================
    # 统计推断方法
    # ================================================================

    def _estimate_total_hours(self, similar: list) -> float:
        weights = [s["score"] for s in similar]
        hours = [s["metrics"]["total_hours"] for s in similar]
        total_w = sum(weights)
        return round(sum(w * h for w, h in zip(weights, hours)) / total_w, 1) if total_w > 0 else 0

    def _hours_range(self, similar: list) -> list:
        hours = [s["metrics"]["total_hours"] for s in similar]
        return [min(hours), max(hours)]

    def _predict_phases(self, similar: list) -> list[dict]:
        phase_data: dict[str, list] = defaultdict(list)
        for s in similar:
            for pid, hours in s["metrics"]["phase_times"].items():
                phase_data[pid].append(hours)

        predictions = []
        for pid in sorted(phase_data.keys()):
            hl = phase_data[pid]
            predictions.append({
                "phase_id": pid,
                "avg_hours": round(statistics.mean(hl), 1),
                "min_hours": min(hl),
                "max_hours": max(hl),
            })
        return predictions

    def _estimate_success_rate(self, similar: list) -> float:
        weights = [s["score"] for s in similar]
        rates = [s["metrics"]["overall_success_rate"] for s in similar]
        total_w = sum(weights)
        return round(sum(w * r for w, r in zip(weights, rates)) / total_w, 1) if total_w > 0 else 0

    def _identify_bottleneck(self, similar: list) -> str:
        """识别最常见的瓶颈 Phase: 耗时占比高 + 成功率低"""
        phase_scores: dict[str, list] = defaultdict(list)
        for s in similar:
            for pid, hours in s["metrics"]["phase_times"].items():
                rate = s["metrics"]["phase_success_rates"].get(pid, 100)
                phase_scores[pid].append(hours * (1 - rate / 100))

        if not phase_scores:
            return "unknown"

        avg_scores = {pid: statistics.mean(scores) for pid, scores in phase_scores.items()}
        return max(avg_scores, key=avg_scores.get)

    def _recommend_tier(self, similar: list, target_tier: int) -> int:
        """基于历史类似项目的成功率, 建议期刊 Tier"""
        if target_tier == 1 and len(similar) >= 3:
            tier1_projects = [s for s in similar if s["score"] >= 5]
            if len(tier1_projects) >= 3:
                rates = [s["metrics"]["overall_success_rate"] for s in tier1_projects]
                if statistics.mean(rates) < 30:
                    return 2
        return target_tier

    def _extract_risk_factors(self, similar: list) -> list[str]:
        """从类似项目的失败记录中提取风险因子"""
        risks = set()
        for s in similar:
            m = s["metrics"]
            if m["overall_success_rate"] < 50:
                risks.add(
                    f"类似项目成功率仅 {m['overall_success_rate']}% "
                    f"(耗时 {m['total_hours']}h)"
                )
            for pid, rate in m["phase_success_rates"].items():
                if rate < 50:
                    risks.add(f"Phase {pid}: 历史通过率仅 {rate}%")
        return list(risks)[:5]

    def _format_summary(
        self, n: int, hours: float, hours_range: list,
        success_rate: float, bottleneck: str, tier: int, confidence: str,
    ) -> str:
        return (
            f"基于 {n} 个类似项目的运行数据:\n"
            f"- 预计总耗时: {hours}h (范围 {hours_range[0]}-{hours_range[1]}h)\n"
            f"- 预计成功率: {success_rate}%\n"
            f"- 最常见瓶颈: {bottleneck}\n"
            f"- 建议期刊Tier: Tier {tier}\n"
            f"- 预测可信度: {confidence}"
        )

    def _low_confidence_result(self, profile: ProjectProfile) -> dict:
        return {
            "similar_projects_count": 0,
            "confidence": "low",
            "estimated_total_hours": None,
            "estimated_total_hours_range": [None, None],
            "phase_predictions": [],
            "estimated_success_rate": None,
            "bottleneck_phase": None,
            "recommended_journal_tier": profile.target_journal_tier,
            "risk_factors": ["无历史类似项目, 无法评估风险"],
            "similar_projects_summary": "无足够历史数据。运行至少 3 个项目后自动积累。",
        }

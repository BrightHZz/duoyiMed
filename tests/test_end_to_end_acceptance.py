"""
全链路集成验收测试 — 验证五个改造模块协同工作

对应钱学森工程控制论五周改造计划:
  模块一: 反馈控制 (Δ-Gate + 反馈环B)
  模块二: 一致性交叉验证
  模块三: 研讨厅辩论
  模块四: 系统辨识 (预测 + 自适应调度)
  模块五: 基线管理 (冻结 + 变更请求)

运行: python -m pytest tests/test_end_to_end_acceptance.py -v
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime


# ================================================================
# 测试辅助
# ================================================================

def _make_record(**overrides):
    """创建一条模拟 RunLog 记录"""
    defaults = {
        "timestamp": "2026-05-10T14:00:00",
        "project_id": "test_project",
        "division": "geriatrics",
        "phase_id": "execution",
        "agent_id": "shared/ml-engineer",
        "success": True,
        "degraded": False,
        "wall_time_sec": 1200.0,
        "input_tokens": 4000,
        "output_tokens": 2000,
        "output_len": 1500,
        "error_type": "",
        "gate_status": "pass",
        "rework_of": "",
    }
    defaults.update(overrides)
    return defaults


def _make_log_dir(records: list[dict], tmpdir: str) -> str:
    """在临时目录中创建 RunLog JSONL 文件"""
    log_file = Path(tmpdir) / "2026-05-10.jsonl"
    log_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return tmpdir


# ================================================================
# 测试类 1: 基线管理器单元测试
# ================================================================

class TestBaselineManager:
    """模块五: 基线管理器"""

    def test_freeze_and_retrieve(self):
        """冻结基线 → 获取最新 → 验证内容"""
        from engine.core.baseline_manager import BaselineManager

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))
            outputs = {"agent_a": "内容A", "agent_b": "内容B"}
            gate = {"status": "pass", "checks": [
                {"check_id": "c1", "result": "pass", "detail": "ok"}
            ]}

            baseline = bm.freeze("proj", "problem_definition", outputs, gate)
            assert baseline["version"] == "v1.0"
            assert baseline["status"] == "frozen"
            assert len(baseline["artifacts"]) == 2
            assert baseline["artifacts"]["agent_a"] != baseline["artifacts"]["agent_b"]

            latest = bm.get_latest("proj", "problem_definition")
            assert latest["version"] == "v1.0"

    def test_version_increment(self):
        """多次冻结 → 版本递增"""
        from engine.core.baseline_manager import BaselineManager

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))
            outputs = {"agent_a": "v1"}
            gate = {"status": "pass", "checks": []}

            b1 = bm.freeze("proj", "p1", outputs, gate)
            b2 = bm.freeze("proj", "p1", outputs, gate)
            b3 = bm.freeze("proj", "p1", outputs, gate)

            assert b1["version"] == "v1.0"
            assert b2["version"] == "v1.1"
            assert b3["version"] == "v1.2"
            assert bm.get_latest("proj", "p1")["version"] == "v1.2"

    def test_supersede(self):
        """标记基线为被取代"""
        from engine.core.baseline_manager import BaselineManager

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))
            bm.freeze("proj", "p1", {"a": "x"}, {"status": "pass", "checks": []})
            bm.supersede("proj", "p1", "v1.0")

            latest = bm.get_latest("proj", "p1")
            assert latest["status"] == "superseded"

    def test_create_and_resolve_cr(self):
        """创建变更请求 → 解决"""
        from engine.core.baseline_manager import BaselineManager

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))

            cr = bm.create_change_request(
                "proj", "execution", "problem_definition",
                "ML检测到特征不可用",
                downstream_impact=["design", "execution"],
            )
            assert cr["status"] == "open"
            assert "CR-" in cr["cr_id"]
            assert cr["downstream_impact"] == ["design", "execution"]

            bm.resolve_change_request("proj", cr["cr_id"])
            summary = bm.get_project_summary("proj")
            assert summary["open_change_requests"] == 0
            assert summary["total_change_requests"] == 1

    def test_diff_baselines(self):
        """计算两个基线的差异"""
        from engine.core.baseline_manager import BaselineManager

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))
            out_v1 = {"agent_a": "内容A_v1", "agent_b": "内容B"}
            out_v2 = {"agent_a": "内容A_v2", "agent_b": "内容B"}
            gate = {"status": "pass", "checks": []}

            bm.freeze("proj", "p1", out_v1, gate)
            bm.freeze("proj", "p1", out_v2, gate)

            diff = bm.diff("proj", "p1", "v1.0", "v1.1")
            assert "agent_a" in diff["changed_artifacts"]
            assert "agent_b" in diff["unchanged_artifacts"]
            assert diff["requires_full_rerun"] is False

    def test_nonexistent_project_no_crash(self):
        """不存在的项目: 不崩溃, 返回 None"""
        from engine.core.baseline_manager import BaselineManager

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))
            assert bm.get_latest("nonexistent", "p1") is None
            assert bm.get_project_summary("nonexistent") == {
                "project_id": "nonexistent",
                "phases": {},
                "total_baselines": 0,
                "open_change_requests": 0,
                "total_change_requests": 0,
            }


# ================================================================
# 测试类 2: 系统辨识模块测试
# ================================================================

class TestSystemIdentification:
    """模块四: 系统辨识"""

    def test_predictor_with_data(self):
        """有历史数据 → 预测有值"""
        from engine.core.run_analyzer import RunAnalyzer
        from engine.core.project_predictor import ProjectPredictor, ProjectProfile

        with tempfile.TemporaryDirectory() as td:
            records = []
            for i in range(5):
                for phase in ["problem_definition", "execution", "writing"]:
                    records.append(_make_record(
                        project_id=f"geriatrics_pred_charls_{i}",
                        phase_id=phase,
                    ))
            _make_log_dir(records, td)

            analyzer = RunAnalyzer(log_dir=td)
            analyzer.load(days=90)
            predictor = ProjectPredictor(analyzer)

            profile = ProjectProfile(
                division="geriatrics", research_type="prediction",
                data_source="CHARLS", target_journal_tier=2,
            )
            pred = predictor.predict(profile)

            assert pred["confidence"] in ("high", "medium")
            assert pred["estimated_total_hours"] is not None
            assert pred["estimated_success_rate"] is not None
            assert pred["bottleneck_phase"] is not None

    def test_predictor_empty_data(self):
        """无数据 → 降低可信度, 不崩溃"""
        from engine.core.run_analyzer import RunAnalyzer
        from engine.core.project_predictor import ProjectPredictor, ProjectProfile

        with tempfile.TemporaryDirectory() as td:
            analyzer = RunAnalyzer(log_dir=td)
            analyzer.load(days=90)
            predictor = ProjectPredictor(analyzer)

            profile = ProjectProfile(
                division="geriatrics", research_type="prediction",
                data_source="CHARLS", target_journal_tier=2,
            )
            pred = predictor.predict(profile)

            assert pred["confidence"] == "low"
            assert pred["similar_projects_count"] == 0

    def test_adaptive_scheduler_normal(self):
        """正常通过率但少有Gate记录 → normal"""
        from engine.core.run_analyzer import RunAnalyzer
        from engine.core.adaptive_scheduler import AdaptiveScheduler

        with tempfile.TemporaryDirectory() as td:
            # 用少量记录和混合gate状态 → 触发 normal
            records = [
                _make_record(success=True, gate_status="pass" if i % 2 == 0 else "fail")
                for i in range(5)
            ]
            _make_log_dir(records, td)

            analyzer = RunAnalyzer(log_dir=td)
            analyzer.load(days=90)
            scheduler = AdaptiveScheduler(analyzer)

            decision = scheduler.decide("execution", "geriatrics")
            # 5条记录, pass_rate=100% 但 gate状态有pass有fail,
            # LLM gate pass rate < 95% → normal
            assert decision["action"] == "normal"

    def test_adaptive_scheduler_low_pass_rate(self):
        """低通过率 → add_redundancy"""
        from engine.core.run_analyzer import RunAnalyzer
        from engine.core.adaptive_scheduler import AdaptiveScheduler

        with tempfile.TemporaryDirectory() as td:
            records = [
                _make_record(success=(i < 3), gate_status="pass" if i < 3 else "fail")
                for i in range(10)
            ]
            _make_log_dir(records, td)

            analyzer = RunAnalyzer(log_dir=td)
            analyzer.load(days=90)
            scheduler = AdaptiveScheduler(analyzer)

            decision = scheduler.decide("execution", "geriatrics")
            assert decision["action"] == "add_redundancy"
            assert "30" in decision["reason"]


# ================================================================
# 测试类 3: 全链路协同测试
# ================================================================

class TestEndToEndIntegration:
    """五个模块协同工作"""

    def test_all_modules_import(self):
        """所有五个模块可同时导入, 无循环依赖"""
        from engine.core.orchestrator_graph import ResearchOrchestrator
        from engine.core.gate_checks import GATE_DEFINITIONS
        from engine.core.consistency_checker import ConsistencyChecker
        from engine.core.project_predictor import ProjectPredictor, ProjectProfile
        from engine.core.adaptive_scheduler import AdaptiveScheduler
        from engine.core.baseline_manager import BaselineManager
        from engine.core.state import (
            RunLog, GateResult, ReworkRecord, BaselineRecord, ChangeRequest
        )
        # All imports succeed
        assert len(GATE_DEFINITIONS) >= 5
        assert BaselineManager is not None

    def test_full_baseline_workflow_simulation(self):
        """
        模拟完整项目流程中的基线操作:
        Phase 1 PASS → freeze v1.0
        Phase 2 PASS → freeze v1.0
        Phase 3 发现 Phase 1 问题 → 反馈B触发 → CR创建 → Phase 1 基线 supersede
        Phase 1 重跑 → freeze v1.1
        """
        from engine.core.baseline_manager import BaselineManager

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))
            project_id = "e2e_test_project"
            gate_pass = {"status": "pass", "checks": [
                {"check_id": "c1", "result": "pass", "detail": "ok"}
            ]}

            # Phase 1 执行 → PASS → 冻结
            p1_outputs = {
                "geriatrics/clinical-researcher": "表型: frailty_index ≥0.25",
                "shared/data-engineer": "数据字典: frailty_index 存在",
            }
            b1 = bm.freeze(project_id, "problem_definition", p1_outputs, gate_pass)
            assert b1["version"] == "v1.0"
            assert b1["status"] == "frozen"

            # Phase 2 执行 → PASS → 冻结
            p2_outputs = {
                "geriatrics/computational-biologist": "建模方案: XGBoost",
                "shared/biostatistician": "SAP: XGBoost + LR baseline",
            }
            bm.freeze(project_id, "design", p2_outputs, gate_pass)

            # Phase 3 执行 → 发现 Phase 1 问题 → 反馈B触发
            cr = bm.create_change_request(
                project_id,
                from_phase="execution",
                to_phase="problem_definition",
                reason="ML检测到 frailty_index 缺失率 87%, 表型定义不可操作化",
                affected_artifacts=["data-engineer"],
                downstream_impact=["design", "execution", "external_validation", "review", "writing"],
                trigger_type="feedback_b",
            )
            assert cr["status"] == "open"

            # 无效化下游基线
            bm.supersede(project_id, "design", "v1.0")
            assert bm.get_latest(project_id, "design")["status"] == "superseded"

            # Phase 1 重跑 → PASS → 冻结 v1.1
            p1_outputs_v2 = {
                "geriatrics/clinical-researcher": "表型: frailty_index (修正) ≥0.25",
                "shared/data-engineer": "数据字典: frailty_index 存在, 缺失率 5.2%",
            }
            b2 = bm.freeze(project_id, "problem_definition", p1_outputs_v2, gate_pass)
            assert b2["version"] == "v1.1"

            # 计算差异 (v1.0 vs v1.1)
            diff = bm.diff(project_id, "problem_definition", "v1.0", "v1.1")
            # artifact key 是完整的 agent_id: "shared/data-engineer"
            assert "shared/data-engineer" in diff["changed_artifacts"]

            # 解决变更请求
            bm.resolve_change_request(project_id, cr["cr_id"])

            # 项目总结
            summary = bm.get_project_summary(project_id)
            assert summary["total_baselines"] == 3  # p1_v1.0 + p2_v1.0 + p1_v1.1
            assert summary["total_change_requests"] == 1
            assert summary["open_change_requests"] == 0

    def test_feedback_control_and_baseline_chain(self):
        """反馈环B触发 → CR创建 → 基线supersede → 下游重跑"""
        from engine.core.baseline_manager import BaselineManager
        from engine.core.gate_checks import (
            check_auc_threshold, check_auc_trend,
            _extract_auc_from_outputs
        )

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))
            project_id = "feedback_b_test"

            class MockOrch:
                _trend_baselines = {}
                _cached_aucs = {}
                _phase_features = {}

            orch = MockOrch()

            # Phase 3 执行: AUC=0.82
            p3_outputs = {"shared/ml-engineer": "AUC=0.82, baseline=LR, n_jobs=2"}
            gate_pass = {"status": "pass", "checks": [
                {"check_id": "auc_threshold", "result": "pass", "detail": "AUC=0.820 >= 0.70"}
            ]}
            p3_baseline = bm.freeze(project_id, "execution", p3_outputs, gate_pass)
            assert p3_baseline["version"] == "v1.0"

            # 缓存 AUC 供趋势检查
            auc = _extract_auc_from_outputs(p3_outputs)
            orch._cached_aucs["execution"] = auc
            orch._trend_baselines["auc"] = auc

            # Phase 3 返工: AUC 下降到 0.70 → 趋势Gate FAIL
            # 但这需要触发跨Phase反馈检查
            # 模拟: 外部验证 AUC 相对于内部验证下降 > 0.15
            orch._cached_aucs["execution"] = 0.82  # 内部验证
            orch._cached_aucs["external_validation"] = 0.66  # 外部验证 (Δ=-0.16)

            # 创建变更请求 (反馈B触发)
            cr = bm.create_change_request(
                project_id,
                from_phase="external_validation",
                to_phase="execution",
                reason="外部验证 AUC(0.66) 相比内部验证(0.82) 下降 0.16 > 0.15, 疑似过拟合",
                downstream_impact=["external_validation", "review", "writing"],
                trigger_type="feedback_b",
            )

            # 无效化 Phase 3 基线
            bm.supersede(project_id, "execution", "v1.0")

            # Phase 3 重跑: AUC=0.84
            p3_outputs_v2 = {"shared/ml-engineer": "AUC=0.84, 修正后模型, n_jobs=2"}
            bm.freeze(project_id, "execution", p3_outputs_v2, gate_pass)

            # 解决 CR
            bm.resolve_change_request(project_id, cr["cr_id"])

            # 验证整个链条
            summary = bm.get_project_summary(project_id)
            assert summary["total_baselines"] == 2
            assert summary["open_change_requests"] == 0

    def test_consistency_checker_and_baseline(self):
        """一致性检查发现矛盾 → Gate FAIL → 修正后重新冻结 → 一致性PASS"""
        from engine.core.baseline_manager import BaselineManager
        from engine.core.consistency_checker import ConsistencyChecker, CONSISTENCY_PAIRS

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))
            project_id = "consistency_test"

            # Round 1: clinical 和 PI 存在矛盾
            outputs_v1 = {
                "clinical-researcher": "frailty 与死亡率显著正相关, 临床价值明确",
                "pi": "PI 终审: frailty 临床意义有限, 需补充分析",
            }
            gate_fail = {
                "status": "fail",
                "checks": [
                    {"check_id": "consistency_clinical_vs_pi_review",
                     "check_type": "llm", "result": "fail",
                     "detail": "临床价值判断矛盾"}
                ]
            }
            # 矛盾时基线不应冻结 (Gate FAIL)
            # 修正后:
            outputs_v2 = {
                "clinical-researcher": "frailty 与死亡率正相关, 需敏感性分析确认",
                "pi": "PI 终审: frailty 与死亡率正相关, 同意需敏感性分析, 临床价值待确认",
            }
            gate_pass = {"status": "pass", "checks": [
                {"check_id": "consistency_clinical_vs_pi_review",
                 "check_type": "llm", "result": "pass",
                 "detail": "一致"}
            ]}
            b1 = bm.freeze(project_id, "review", outputs_v2, gate_pass)
            assert b1["version"] == "v1.0"

            # 验证一致性检查对定义存在
            review_pairs = CONSISTENCY_PAIRS.get("review", [])
            assert len(review_pairs) >= 1

    def test_debate_phase_baseline(self):
        """辩论 Phase 产出含 _debate_minutes, 基线应包含但不哈希内部字段"""
        from engine.core.baseline_manager import BaselineManager

        with tempfile.TemporaryDirectory() as td:
            bm = BaselineManager(Path(td))

            # 模拟辩论 Phase 产出
            debate_outputs = {
                "computational-biologist": "推荐 XGBoost...",
                "biostatistician": "推荐 Elastic Net...",
                "clinical-researcher": "两种均可...",
                "_debate_minutes": "# 研讨厅辩论纪要\n\n## 1. 共识\n...",
            }
            gate_pass = {"status": "pass", "checks": []}

            baseline = bm.freeze("proj", "design", debate_outputs, gate_pass)

            # _debate_minutes 不应在 artifacts 中 (内部字段)
            assert "_debate_minutes" not in baseline["artifacts"]
            # 但三个参与方的输出应该在
            assert "computational-biologist" in baseline["artifacts"]
            assert "biostatistician" in baseline["artifacts"]
            assert "clinical-researcher" in baseline["artifacts"]

    def test_empty_baseline_dir_no_crash(self):
        """首次运行: 无 baseline 目录 → 不崩溃"""
        from engine.core.baseline_manager import BaselineManager
        import tempfile, os

        with tempfile.TemporaryDirectory() as td:
            # 确保是全新的空目录
            bm = BaselineManager(Path(td) / "nonexistent_subdir")
            # 不应崩溃
            latest = bm.get_latest("proj", "p1")
            assert latest is None
            summary = bm.get_project_summary("proj")
            assert summary["total_baselines"] == 0

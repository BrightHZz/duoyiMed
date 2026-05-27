"""
技术状态基线管理器 — Baseline Manager

基于钱学森航天系统工程总体设计部思想:
每个 Phase Gate 通过后冻结基线, 变更走正式的变更控制流程。

用法:
    bm = BaselineManager(Path("outputs/baselines"))
    baseline = bm.freeze(project_id, phase_id, outputs, gate_result)
    cr = bm.create_change_request(project_id, from_phase, to_phase, reason)
    bm.supersede(project_id, phase_id, version)
"""

import json
import hashlib
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional


class BaselineManager:
    """
    技术状态基线管理器。

    职责:
    1. Phase Gate 通过后冻结基线
    2. 跨 Phase 反馈触发时创建变更请求
    3. 上游修改后无效化下游基线
    4. 计算基线间差异
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        """项目基线目录: {base_dir}/{project_id}/baselines/"""
        return self.base_dir / project_id / "baselines"

    # ================================================================
    # 基线操作
    # ================================================================

    def freeze(
        self, project_id: str, phase_id: str,
        outputs: dict[str, str], gate_result: dict,
    ) -> dict:
        """
        Phase Gate 通过后冻结基线。

        1. 计算每个 Agent 产出的内容哈希
        2. 确定版本号 (首次=v1.0, 后续递增)
        3. 保存基线快照
        4. 更新基线索引

        Returns:
            BaselineRecord dict
        """
        project_dir = self._project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        # 确定版本号
        existing = self._list_baselines(project_id, phase_id)
        if existing:
            last_ver = existing[-1].get("version", "v1.0").lstrip("v")
            try:
                major, minor = last_ver.split(".")
                new_version = f"v{major}.{int(minor) + 1}"
            except ValueError:
                new_version = "v1.0"
        else:
            new_version = "v1.0"

        baseline_id = f"{project_id}/{phase_id}/{new_version}"

        # 计算内容哈希 (跳过内部字段)
        artifacts = {}
        for agent_id, output in outputs.items():
            if not agent_id.startswith("_"):
                artifacts[agent_id] = hashlib.md5(
                    output.encode("utf-8")
                ).hexdigest()[:12]

        baseline = {
            "baseline_id": baseline_id,
            "project_id": project_id,
            "phase_id": phase_id,
            "version": new_version,
            "status": "frozen",
            "artifacts": artifacts,
            "gate_result": {
                "status": gate_result.get("status"),
                "checks_count": len(gate_result.get("checks", [])),
                "pass_count": sum(
                    1 for c in gate_result.get("checks", [])
                    if c.get("result") == "pass"
                ),
            },
            "timestamp": datetime.now().isoformat(),
            "frozen_by": "orchestrator",
        }

        # 🆕 Phase 3 (execution) 基线额外存储 safety_config
        if phase_id == "execution":
            baseline["safety_config"] = {
                "n_jobs": 2,
                "cross_val_predict_n_jobs": 1,
                "model_n_jobs_override": True,
                "thread_limits": {
                    "OMP_NUM_THREADS": "2",
                    "OPENBLAS_NUM_THREADS": "2",
                    "MKL_NUM_THREADS": "2",
                    "VECLIB_MAXIMUM_THREADS": "2",
                    "NUMEXPR_NUM_THREADS": "2",
                },
                "start_method": "forkserver",
                "platform": platform.system().lower() if hasattr(platform, 'system') else "unknown",
            }
            baseline["downstream_consumers"] = [
                "generate_figures.py",
                "sections/05_results.md",
                "tables/table2_model_performance.md",
                "tables/table3_subgroup.md",
            ]

        # 保存基线文件
        file_name = f"baseline_{phase_id}_{new_version}.json"
        file_path = project_dir / file_name
        file_path.write_text(
            json.dumps(baseline, ensure_ascii=False, indent=2)
        )

        # 更新索引
        self._update_index(project_id, phase_id, new_version, file_name)

        return baseline

    def get_latest(self, project_id: str, phase_id: str) -> Optional[dict]:
        """获取指定 Phase 的最新基线"""
        index = self._read_index(project_id)
        phase_info = index.get(phase_id, {})
        if not phase_info:
            return None

        latest_ver = phase_info.get("latest")
        versions = phase_info.get("versions", {})
        file_name = versions.get(latest_ver) if latest_ver else None
        if not file_name:
            return None

        file_path = self._project_dir(project_id) / file_name
        if not file_path.exists():
            return None

        try:
            return json.loads(file_path.read_text())
        except Exception:
            return None

    def supersede(self, project_id: str, phase_id: str, version: str):
        """将一个基线标记为被取代 (上游修改后, 下游旧基线作废)"""
        file_path = (
            self._project_dir(project_id) /
            f"baseline_{phase_id}_{version}.json"
        )
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text())
                data["status"] = "superseded"
                file_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2)
                )
            except Exception:
                pass  # 基线更新失败不阻塞

    def diff(
        self, project_id: str, phase_id: str,
        version_old: str, version_new: str,
    ) -> dict:
        """
        计算两个基线版本的差异。
        用于下游 Phase 判断是否完全重跑或可增量更新。
        """
        old = self._load_baseline(project_id, phase_id, version_old)
        new = self._load_baseline(project_id, phase_id, version_new)

        if not old or not new:
            return {
                "baseline_old": version_old,
                "baseline_new": version_new,
                "changed_artifacts": [],
                "unchanged_artifacts": [],
                "requires_full_rerun": True,
                "summary": "基线版本不存在, 需要全量重跑",
            }

        old_arts = old.get("artifacts", {})
        new_arts = new.get("artifacts", {})

        all_agents = set(old_arts.keys()) | set(new_arts.keys())
        changed = []
        unchanged = []

        for agent in all_agents:
            if old_arts.get(agent) != new_arts.get(agent):
                changed.append(agent)
            else:
                unchanged.append(agent)

        return {
            "baseline_old": version_old,
            "baseline_new": version_new,
            "changed_artifacts": changed,
            "unchanged_artifacts": unchanged,
            "requires_full_rerun": len(changed) > len(unchanged),
            "summary": (
                f"{len(changed)} 个 Agent 产出变更, "
                f"{len(unchanged)} 个不变"
            ),
        }

    # ================================================================
    # 变更请求操作
    # ================================================================

    def create_change_request(
        self,
        project_id: str,
        from_phase: str,
        to_phase: str,
        reason: str,
        affected_artifacts: list[str] = None,
        downstream_impact: list[str] = None,
        trigger_type: str = "feedback_b",
    ) -> dict:
        """
        创建变更请求 — 跨 Phase 反馈触发的正式变更记录。

        Returns:
            ChangeRequest dict
        """
        cr_id = (
            f"CR-{project_id}-{from_phase}-to-{to_phase}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        cr = {
            "cr_id": cr_id,
            "project_id": project_id,
            "from_phase": from_phase,
            "to_phase": to_phase,
            "reason": reason,
            "affected_artifacts": affected_artifacts or [],
            "downstream_impact": downstream_impact or [],
            "status": "open",
            "trigger_type": trigger_type,
            "created_at": datetime.now().isoformat(),
            "resolved_at": "",
        }

        # 追加到 change_requests.jsonl
        project_dir = self._project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        cr_file = project_dir / "change_requests.jsonl"
        with open(cr_file, "a") as f:
            f.write(json.dumps(cr, ensure_ascii=False) + "\n")

        return cr

    def resolve_change_request(self, project_id: str, cr_id: str):
        """标记变更请求为已解决"""
        project_dir = self._project_dir(project_id)
        if not project_dir.exists():
            return
        cr_file = project_dir / "change_requests.jsonl"
        if not cr_file.exists():
            return

        try:
            lines = cr_file.read_text().splitlines()
            updated = []
            for line in lines:
                if not line.strip():
                    continue
                try:
                    cr = json.loads(line)
                except Exception:
                    updated.append(line)
                    continue
                if cr.get("cr_id") == cr_id:
                    cr["status"] = "implemented"
                    cr["resolved_at"] = datetime.now().isoformat()
                updated.append(json.dumps(cr, ensure_ascii=False))
            cr_file.write_text("\n".join(updated) + "\n")
        except Exception:
            pass  # 变更请求更新失败不阻塞

    def get_project_summary(self, project_id: str) -> dict:
        """获取项目的基线概览"""
        index = self._read_index(project_id)
        phases = {}
        for phase_id, info in index.items():
            phases[phase_id] = {
                "latest_version": info.get("latest"),
                "total_versions": len(info.get("versions", {})),
            }

        crs = self._read_change_requests(project_id)
        open_crs = [cr for cr in crs if cr.get("status") == "open"]

        return {
            "project_id": project_id,
            "phases": phases,
            "total_baselines": sum(p["total_versions"] for p in phases.values()),
            "open_change_requests": len(open_crs),
            "total_change_requests": len(crs),
        }

    # ================================================================
    # 内部辅助
    # ================================================================

    def _list_baselines(self, project_id: str, phase_id: str) -> list[dict]:
        """列出指定 Phase 的所有基线, 按版本排序"""
        project_dir = self._project_dir(project_id)
        if not project_dir.exists():
            return []

        baselines = []
        prefix = f"baseline_{phase_id}_v"
        for f in project_dir.glob(f"{prefix}*.json"):
            try:
                data = json.loads(f.read_text())
                baselines.append(data)
            except Exception:
                continue

        def _ver_key(b):
            v = b.get("version", "v0.0").lstrip("v")
            try:
                parts = v.split(".")
                return tuple(int(p) for p in parts)
            except (ValueError, AttributeError):
                return (0, 0)

        baselines.sort(key=_ver_key)
        return baselines

    def _read_index(self, project_id: str) -> dict:
        """读取基线索引"""
        index_path = self._project_dir(project_id) / "baseline_index.json"
        if not index_path.exists():
            return {}
        try:
            return json.loads(index_path.read_text())
        except Exception:
            return {}

    def _update_index(
        self, project_id: str, phase_id: str,
        version: str, file_name: str,
    ):
        """更新基线索引"""
        index_path = self._project_dir(project_id) / "baseline_index.json"
        index = self._read_index(project_id)

        if phase_id not in index:
            index[phase_id] = {"latest": None, "versions": {}}

        index[phase_id]["latest"] = version
        index[phase_id]["versions"][version] = file_name

        try:
            index_path.write_text(
                json.dumps(index, ensure_ascii=False, indent=2)
            )
        except Exception:
            pass  # 索引写入失败不阻塞

    def _load_baseline(
        self, project_id: str, phase_id: str, version: str,
    ) -> Optional[dict]:
        """加载指定版本的基线"""
        file_path = (
            self._project_dir(project_id) /
            f"baseline_{phase_id}_{version}.json"
        )
        if not file_path.exists():
            return None
        try:
            return json.loads(file_path.read_text())
        except Exception:
            return None

    def supersede_downstream_reviews(
        self, project_id: str, from_phase_id: str
    ):
        """返工后作废下游 Phase 的审查产物。

        当 Phase N 因返工重新执行后, Phase N+1 至 Phase N+2 的审查产物
        (review-*.md, gate_report_phase*.json) 中引用的旧基线数值可能已失效。
        此方法将这些产物标记为 superseded, 强制下游审查重新执行。

        Args:
            project_id: 项目 ID
            from_phase_id: 被返工的 Phase (如 'execution')
        """
        import re

        project_dir = self._project_dir(project_id)
        if not project_dir.exists():
            return

        # Phase 顺序定义
        phase_order = [
            "system_design",    # 0
            "problem_definition",  # 1
            "design",           # 2
            "execution",        # 3
            "external_validation",  # 4
            "review",           # 5
            "writing",          # 6
            "clinical_tool",    # 7
        ]

        if from_phase_id not in phase_order:
            return

        from_idx = phase_order.index(from_phase_id)
        # 作废从下一个 Phase 到当前末尾的所有审查产物
        downstream_phases = phase_order[from_idx + 1:]

        review_files = [
            "review-clinical.md", "review-stats.md", "review-pi.md",
            "review-approval.md", "clinical-review.md",
        ]

        for dp in downstream_phases:
            # 标记 gate_report
            gate_pattern = f"gate_report_phase{dp}.json" if not dp.startswith("phase") else f"gate_report_{dp}.json"
            for f in project_dir.glob(f"gate_report_{dp}*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    data["status"] = "superseded"
                    data["superseded_reason"] = (
                        f"Upstream Phase {from_phase_id} was reworked. "
                        f"Review conclusions based on old baseline may be invalid. "
                        f"Re-run Phase {dp} review before proceeding."
                    )
                    data["superseded_at"] = datetime.now().isoformat()
                    f.write_text(json.dumps(data, ensure_ascii=False, indent=2))
                except Exception:
                    pass  # 不阻塞主流程

        # 标记所有下游 review-*.md 文件
        for rf_name in review_files:
            rf = project_dir / rf_name
            if rf.exists():
                try:
                    content = rf.read_text(encoding="utf-8")
                    if "[SUPERSEDED]" not in content:
                        superseded_notice = (
                            f"\n\n---\n\n**[SUPERSEDED] — Upstream Phase '{from_phase_id}' "
                            f"was reworked on {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
                            f"The conclusions in this review may reference stale baseline data. "
                            f"Re-run review before relying on this content.**\n"
                        )
                        rf.write_text(content + superseded_notice, encoding="utf-8")
                except Exception:
                    pass  # 不阻塞主流程

    def _read_change_requests(self, project_id: str) -> list[dict]:
        """读取项目的所有变更请求"""
        project_dir = self._project_dir(project_id)
        if not project_dir.exists():
            return []
        cr_file = project_dir / "change_requests.jsonl"
        if not cr_file.exists():
            return []
        crs = []
        for line in cr_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                crs.append(json.loads(line))
            except Exception:
                continue
        return crs

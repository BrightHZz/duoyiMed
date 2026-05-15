"""
项目管理器 — Project Manager

负责项目的创建、状态持久化、列表查询和断点续传。
基于钱学森总体设计部思想: 每个项目的技术状态可冻结/恢复/查询。

目录结构:
  outputs/projects/{project_id}/
    project_state.json     — 项目运行状态 (轻量, 可跨进程共享)
    run_logs/              — 运行日志
    baselines/             — 基线存档

用法:
    pm = ProjectManager(config)
    pid = pm.create_project("用 CHARLS 预测衰弱", "geriatrics")
    pm.save_state(pid, state_dict)
    state = pm.load_state(pid)
    projects = pm.list_projects(status_filter="running")
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional


class ProjectManager:
    """项目生命周期管理器。"""

    def __init__(self, config):
        """
        Args:
            config: EngineConfig 实例, 提供 projects_output_dir 等路径
        """
        self.config = config
        self.projects_dir = Path(config.projects_output_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    # ================================================================
    # 项目创建
    # ================================================================

    def create_project(self, user_request: str, division: str) -> str:
        """创建新项目, 返回 project_id。

        生成格式: proj_{timestamp}_{random4}
        """
        ts = int(time.time())
        rand = int.from_bytes(Path(__file__).read_bytes()[:2], "big") % 10000
        project_id = f"proj_{ts}_{rand:04d}"

        # 创建项目输出目录
        proj_dir = self.projects_dir / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "run_logs").mkdir(exist_ok=True)
        (proj_dir / "baselines").mkdir(exist_ok=True)

        # 写入初始状态
        state = {
            "project_id": project_id,
            "division": division,
            "user_request": user_request,
            "status": "running",
            "phases_to_run": [
                "system_design", "problem_definition", "design",
                "execution", "external_validation", "review",
                "writing", "clinical_tool",
            ],
            "current_phase_index": 0,
            "completed_phases": [],
            "phase_outputs": {},
            "gate_results": {},
            "rework_history": [],
            "phase_rework_counts": {},
            "invalidated_phases": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None,
        }
        self._write_state(project_id, state)
        return project_id

    # ================================================================
    # 状态持久化
    # ================================================================

    def _state_path(self, project_id: str) -> Path:
        return self.projects_dir / project_id / "project_state.json"

    def _write_state(self, project_id: str, state: dict):
        """写入项目状态文件。失败不抛异常。"""
        try:
            state["updated_at"] = datetime.now().isoformat()
            path = self._state_path(project_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        except Exception:
            pass  # 状态写入失败不阻塞主流程

    def load_state(self, project_id: str) -> Optional[dict]:
        """加载项目状态。不存在返回 None。"""
        path = self._state_path(project_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception:
            return None

    def save_state(self, project_id: str, **kwargs):
        """
        增量更新项目状态。只更新传入的字段, 保留未传入的现有字段。

        编排器在每个 Phase Gate 通过后调用, 传入:
          - current_phase_index
          - completed_phases
          - phase_outputs (phase_id → {summary, timestamp})
          - gate_results
          - rework_history
          - phase_rework_counts
          - invalidated_phases
          - status
        """
        state = self.load_state(project_id) or {}
        state["project_id"] = project_id

        for key, value in kwargs.items():
            if value is not None:
                state[key] = value

        self._write_state(project_id, state)

    # ================================================================
    # 项目列表
    # ================================================================

    def list_projects(self, status_filter: str = None) -> list[dict]:
        """列出所有项目及其状态摘要。

        Args:
            status_filter: 可选, 过滤状态 ("running" / "completed" / "failed")

        Returns:
            [{project_id, division, status, current_phase, completed_phases,
              created_at, updated_at}]
        """
        result = []
        if not self.projects_dir.exists():
            return result

        for proj_dir in sorted(self.projects_dir.iterdir()):
            if not proj_dir.is_dir() or proj_dir.name.startswith("_"):
                continue
            state_path = proj_dir / "project_state.json"
            if not state_path.exists():
                continue
            try:
                state = json.loads(state_path.read_text())
            except Exception:
                continue

            if status_filter and state.get("status") != status_filter:
                continue

            phases = state.get("phases_to_run", [])
            idx = state.get("current_phase_index", 0)
            current_phase = phases[idx] if 0 <= idx < len(phases) else "done"

            result.append({
                "project_id": state.get("project_id", proj_dir.name),
                "division": state.get("division", ""),
                "status": state.get("status", "unknown"),
                "user_request": state.get("user_request", "")[:100],
                "current_phase": current_phase,
                "completed_count": len(state.get("completed_phases", [])),
                "total_phases": len(phases),
                "created_at": state.get("created_at", ""),
                "updated_at": state.get("updated_at", ""),
            })

        return result

    def get_project_summary(self, project_id: str) -> Optional[str]:
        """生成项目状态的可读摘要 (Markdown)"""
        state = self.load_state(project_id)
        if not state:
            return f"项目 {project_id} 不存在。"

        phases = state.get("phases_to_run", [])
        completed = state.get("completed_phases", [])
        idx = state.get("current_phase_index", 0)

        lines = [
            f"# 项目状态: {project_id}",
            f"",
            f"| 字段 | 值 |",
            f"|------|-----|",
            f"| 事业部 | {state.get('division', '')} |",
            f"| 状态 | {state.get('status', '')} |",
            f"| 创建时间 | {state.get('created_at', '')} |",
            f"| 更新时间 | {state.get('updated_at', '')} |",
            f"| 当前阶段 | {phases[idx] if 0 <= idx < len(phases) else 'done'} ({idx+1}/{len(phases)}) |",
            f"",
            f"## 阶段进度",
            f"",
            f"| Phase | 状态 |",
            f"|-------|------|",
        ]
        for p in phases:
            if p in completed:
                gate = state.get("gate_results", {}).get(p, {})
                gs = gate.get("status", "pass")
                lines.append(f"| {p} | ✅ {gs} |")
            elif p == phases[idx]:
                lines.append(f"| {p} | 🔄 进行中 |")
            else:
                lines.append(f"| {p} | ⏳ 待执行 |")

        # 返工历史
        reworks = state.get("rework_history", [])
        if reworks:
            lines += ["", "## 返工记录", ""]
            for rw in reworks[-5:]:  # 最近 5 条
                lines.append(f"- {rw.get('timestamp', '')[:19]}: {rw.get('from_phase')} → {rw.get('to_phase')}: {rw.get('reason', '')[:80]}")

        return "\n".join(lines)

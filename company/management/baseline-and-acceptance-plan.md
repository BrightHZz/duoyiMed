# 模块五：技术状态基线管理 + 全链路验收 — 详细方案

> 钱学森航天系统工程的核心实践：每个阶段冻结一个**技术状态基线**，变更必须走正式的变更控制流程。
> 
> 这不是额外的流程负担——这是让反馈环 B（跨 Phase 回退）**可追踪、可回滚、可审计**的基础设施。

---

## 目录

1. [基线管理：问题与设计](#一基线管理问题与设计)
2. [数据模型](#二数据模型)
3. [BaselineManager 类设计](#三-baselinemanager-类设计)
4. [编排器集成点](#四编排器集成点)
5. [全链路验收方案](#五全链路验收方案)
6. [文件改动清单](#六文件改动清单)

---

## 一、基线管理：问题与设计

### 1.1 当前差距

```
当前流程:
  Phase 1 Gate PASS → 产出直接传给 Phase 2
  Phase 2 开始执行...
  反馈环B触发: Phase 3 发现 Phase 1 表型定义有问题
  → Phase 1 重新执行 → 新产出覆盖旧产出 → Phase 2 重跑
  
问题:
  ❌ 没有版本概念 — 不知道 Phase 2 第一次用的是 v1.0 还是 v1.1
  ❌ 下游不知道自己依赖的上游被修改了
  ❌ 无法追溯 "这个项目返工了几次, 每次改了什么"
  ❌ 返工后下游被迫全量重跑, 无法增量更新
```

### 1.2 目标

```
目标流程:
  Phase 1 Gate PASS → 冻结基线 v1.0
    ├─ Phase 2 读取 v1.0 → 产出
    └─ Phase 3 发现 v1.0 有问题 → 创建变更请求 CR-001
         → Phase 1 修正 → Gate PASS → 冻结基线 v1.1
         → 通知 Phase 2: "你的上游从 v1.0 变为 v1.1"
         → Phase 2 的基线被标记为 "superseded"
         → Phase 2 重新执行 (可基于 diff 增量更新)
```

### 1.3 设计原则

| 原则 | 说明 |
|------|------|
| **轻量** | 基线存 JSON 文件, 不需要数据库 |
| **非侵入** | 基线管理失败不阻塞主流程 |
| **可追溯** | 每个 Phase 产出有版本号 + 内容哈希 |
| **增量** | 返工时只无效化真正受影响的下游 |

---

## 二、数据模型

### 2.1 state.py 新增类型

```python
# engine/core/state.py 新增

class BaselineRecord(TypedDict):
    """技术状态基线 — Phase 产出的冻结版本"""
    baseline_id: str           # "frailty_ml_2026/phase1/v1.0"
    project_id: str
    phase_id: str
    version: str               # "1.0"
    status: str                # "frozen" | "superseded" | "active"
    artifacts: dict[str, str]  # {agent_id: content_hash}  内容 MD5 哈希
    gate_result: dict          # 冻结时的 Gate 检查结果快照
    timestamp: str
    frozen_by: str             # "orchestrator"


class ChangeRequest(TypedDict):
    """变更请求 — 下游触发上游修改的正式记录"""
    cr_id: str                 # "CR-frailty_ml_2026-001"
    project_id: str
    from_phase: str            # 发现问题的 Phase
    to_phase: str              # 需要修改的 Phase
    reason: str                # 变更原因
    affected_artifacts: list[str]   # 受影响的产出物 (agent_id)
    downstream_impact: list[str]    # 受影响的下游 Phase
    status: str                # "open" | "approved" | "implemented" | "closed"
    trigger_type: str          # "feedback_b" | "gate_fail" | "manual"
    created_at: str
    resolved_at: str           # 空=未解决


class BaselineDiff(TypedDict):
    """两个基线版本的差异"""
    baseline_old: str          # v1.0
    baseline_new: str          # v1.1
    changed_artifacts: list[str]   # 哪些 Agent 的产出变了
    unchanged_artifacts: list[str] # 哪些没变 (下游可复用)
    summary: str               # 人类可读的变更摘要
```

### 2.2 存储方案

```
outputs/baselines/
└── {project_id}/
    ├── baseline_phase1_v1.0.json   # 冻结的基线快照
    ├── baseline_phase1_v1.1.json
    ├── baseline_phase2_v1.0.json
    ├── change_requests.jsonl       # 该项目的所有变更请求
    └── baseline_index.json         # 基线索引 {phase_id: latest_version}
```

---

## 三、BaselineManager 类设计

### 3.1 类结构

```python
# engine/core/baseline_manager.py

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional


class BaselineManager:
    """
    技术状态基线管理器 — 钱学森系统工程总体设计部的核心工具。

    职责:
    1. Phase Gate 通过后冻结基线
    2. 跨 Phase 反馈触发时创建变更请求
    3. 通知下游 Phase 上游变更
    4. 计算基线间差异 (增量更新用)

    用法:
        bm = BaselineManager(project_root / "outputs" / "baselines")
        baseline = bm.freeze("frailty_ml_2026", "problem_definition", 
                             outputs, gate_result)
        cr = bm.create_change_request(
            project_id, from_phase="execution", to_phase="problem_definition",
            reason="ML检测到特征不可用",
            affected_artifacts=["data-engineer"]
        )
        diff = bm.diff("frailty_ml_2026", "problem_definition", "1.0", "1.1")
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

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
        3. 保存基线快照到 JSON 文件
        4. 更新基线索引
        5. 返回 BaselineRecord
        """
        project_dir = self.base_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # 确定版本号
        existing = self._list_baselines(project_id, phase_id)
        if existing:
            # v1.0 → v1.1, v1.9 → v1.10
            last_ver = existing[-1]["version"]
            major, minor = last_ver.lstrip("v").split(".")
            new_version = f"v{major}.{int(minor) + 1}"
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

        # 保存
        file_path = project_dir / f"baseline_{phase_id}_{new_version}.json"
        file_path.write_text(
            json.dumps(baseline, ensure_ascii=False, indent=2)
        )

        # 更新索引
        self._update_index(project_id, phase_id, new_version, file_path.name)

        return baseline

    def get_latest(self, project_id: str, phase_id: str) -> Optional[dict]:
        """获取指定 Phase 的最新基线"""
        index = self._read_index(project_id)
        phase_versions = index.get(phase_id, {})
        if not phase_versions:
            return None

        latest_ver = phase_versions.get("latest")
        if not latest_ver:
            return None

        file_name = phase_versions["versions"].get(latest_ver)
        if not file_name:
            return None

        file_path = self.base_dir / project_id / file_name
        if not file_path.exists():
            return None

        return json.loads(file_path.read_text())

    def supersede(self, project_id: str, phase_id: str, version: str):
        """将一个基线标记为被取代 (上游修改后, 下游旧基线作废)"""
        file_path = self.base_dir / project_id / f"baseline_{phase_id}_{version}.json"
        if file_path.exists():
            data = json.loads(file_path.read_text())
            data["status"] = "superseded"
            file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def diff(
        self, project_id: str, phase_id: str,
        version_old: str, version_new: str,
    ) -> dict:
        """
        计算两个基线版本的差异。
        用于下游 Phase 判断是否需要完全重跑, 还是可以增量更新。
        """
        old = self._load_baseline(project_id, phase_id, version_old)
        new = self._load_baseline(project_id, phase_id, version_new)

        if not old or not new:
            return {"error": "基线版本不存在"}

        old_arts = old.get("artifacts", {})
        new_arts = new.get("artifacts", {})

        all_agents = set(old_arts.keys()) | set(new_arts.keys())
        changed = []
        unchanged = []

        for agent in all_agents:
            old_hash = old_arts.get(agent, "")
            new_hash = new_arts.get(agent, "")
            if old_hash != new_hash:
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
        创建变更请求 — 下游触发上游修改的正式记录。

        Returns: ChangeRequest dict
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

        # 追加到项目的 change_requests.jsonl
        cr_file = self.base_dir / project_id / "change_requests.jsonl"
        with open(cr_file, "a") as f:
            f.write(json.dumps(cr, ensure_ascii=False) + "\n")

        return cr

    def resolve_change_request(self, project_id: str, cr_id: str):
        """标记变更请求为已解决"""
        cr_file = self.base_dir / project_id / "change_requests.jsonl"
        if not cr_file.exists():
            return

        lines = cr_file.read_text().splitlines()
        updated = []
        for line in lines:
            cr = json.loads(line)
            if cr.get("cr_id") == cr_id:
                cr["status"] = "implemented"
                cr["resolved_at"] = datetime.now().isoformat()
            updated.append(json.dumps(cr, ensure_ascii=False))
        cr_file.write_text("\n".join(updated) + "\n")

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
        project_dir = self.base_dir / project_id
        if not project_dir.exists():
            return []

        baselines = []
        for f in project_dir.glob(f"baseline_{phase_id}_v*.json"):
            try:
                data = json.loads(f.read_text())
                baselines.append(data)
            except Exception:
                continue

        # 按版本排序: v1.0, v1.1, v2.0, ...
        def _ver_key(b):
            v = b.get("version", "v0.0").lstrip("v")
            parts = v.split(".")
            return tuple(int(p) for p in parts)

        baselines.sort(key=_ver_key)
        return baselines

    def _read_index(self, project_id: str) -> dict:
        """读取基线索引"""
        index_path = self.base_dir / project_id / "baseline_index.json"
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
        index_path = self.base_dir / project_id / "baseline_index.json"
        index = self._read_index(project_id)

        if phase_id not in index:
            index[phase_id] = {"latest": None, "versions": {}}

        index[phase_id]["latest"] = version
        index[phase_id]["versions"][version] = file_name

        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))

    def _load_baseline(
        self, project_id: str, phase_id: str, version: str,
    ) -> Optional[dict]:
        """加载指定版本的基线"""
        file_path = (
            self.base_dir / project_id /
            f"baseline_{phase_id}_{version}.json"
        )
        if not file_path.exists():
            return None
        try:
            return json.loads(file_path.read_text())
        except Exception:
            return None

    def _read_change_requests(self, project_id: str) -> list[dict]:
        """读取项目的所有变更请求"""
        cr_file = self.base_dir / project_id / "change_requests.jsonl"
        if not cr_file.exists():
            return []
        crs = []
        for line in cr_file.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    crs.append(json.loads(line))
                except Exception:
                    continue
        return crs
```

---

## 四、编排器集成点

### 4.1 __init__ 新增

```python
class ResearchOrchestrator:
    def __init__(self, config=None):
        # ... 现有初始化 ...

        # 🆕 技术状态基线管理器 (钱学森总体设计部)
        baseline_dir = getattr(self.config, 'baseline_dir', None)
        if baseline_dir is None:
            baseline_dir = self.config.project_root / "outputs" / "baselines"
        self.baseline_manager = BaselineManager(baseline_dir)
```

### 4.2 _run_project_workflow 集成 — Gate 通过后冻结基线

```python
# 在 Gate PASS / COND_PASS 时:
if status in ("pass", "conditional_pass"):
    # 🆕 冻结技术状态基线
    try:
        baseline = self.baseline_manager.freeze(
            project_id=project_id,
            phase_id=phase_id,
            outputs=phase_result,
            gate_result=gate_result,
        )
        if self.config.verbose:
            print(f"  📌 基线已冻结: {baseline['baseline_id']}")
    except Exception as e:
        # 基线保存失败不阻塞主流程
        print(f"  ⚠️ 基线冻结失败: {e}")
```

### 4.3 跨 Phase 反馈时 — 创建变更请求 + 无效化下游基线

```python
# 反馈环B触发时:
if cross_phase_rework_triggered:
    # 🆕 创建变更请求
    try:
        cr = self.baseline_manager.create_change_request(
            project_id=project_id,
            from_phase=phase_id,
            to_phase=target_phase,
            reason=issue["reason"],
            affected_artifacts=list(phase_result.keys()),
            downstream_impact=[
                phases_to_run[i]
                for i in range(target_index + 1, len(phases_to_run))
            ],
            trigger_type="feedback_b",
        )
        # 🆕 无效化下游基线
        for i in range(target_index + 1, len(phases_to_run)):
            downstream_phase = phases_to_run[i]
            latest = self.baseline_manager.get_latest(project_id, downstream_phase)
            if latest:
                self.baseline_manager.supersede(
                    project_id, downstream_phase, latest["version"]
                )
        print(f"  📋 变更请求已创建: {cr['cr_id']}")
    except Exception as e:
        print(f"  ⚠️ 变更请求创建失败: {e}")
```

---

## 五、全链路验收方案

### 5.1 验收目标

验证四个改造模块在完整项目流程中**协同工作**，不互相冲突：

```
全链路验收 = 
    模块一 (反馈控制: Δ-Gate + 反馈环B)
  + 模块二 (一致性交叉验证)
  + 模块三 (研讨厅辩论)
  + 模块四 (系统辨识: 预测 + 自适应调度)
  + 模块五 (基线管理: 冻结 + 变更请求)
  → 同时运行在一个完整项目中
```

### 5.2 验收脚本

```python
# tests/test_end_to_end_acceptance.py

class TestEndToEndAcceptance:
    """全链路集成验收 — 模拟完整项目流程中五个模块协同工作"""

    def test_full_project_with_all_modules(self):
        """
        场景: 启动新项目 → 完整走完 7 个 Phase
        
        验证点:
        1. Phase 0 SDS 包含系统辨识预测数据
        2. Phase 1 FRAME 定量化 + 一致性检查 (clinical ↔ data)
        3. Phase 2 研讨厅辩论 → 输出辩论纪要
        4. Phase 3 趋势 Gate 监控 AUC
        5. Phase 4 特征稳定性检查 + 反馈 B (AUC 下降检测)
        6. Phase 5 研讨厅辩论 + 一致性检查
        7. Phase 6 跨 Phase 一致性检查 (paper vs upstream)
        8. 每个 Gate 通过后基线被冻结
        9. 反馈环 B 触发时变更请求被创建
        """
        ...

    def test_feedback_b_triggers_baseline_chain(self):
        """
        场景: Phase 4 检测到 AUC 大幅下降 → 反馈环B 触发 Phase 3 重开
        
        验证点:
        1. Phase 3 基线 v1.0 被冻结
        2. Phase 4 检测到问题 → 变更请求 CR-001 创建
        3. Phase 3 重跑 → 基线 v1.1 被冻结
        4. Phase 3 基线 v1.0 状态变为 inactive
        5. Phase 4 基线被标记为 superseded
        6. Phase 4 自动重跑
        """
        ...

    def test_debate_minutes_baseline_frozen(self):
        """辩论纪要也应作为基线的一部分被冻结"""
        ...

    def test_consistency_check_vs_baseline(self):
        """
        一致性检查发现 major_conflict → Gate FAIL → 
        修正后基线 v1.1 → 一致性重新检查 → PASS
        """
        ...

    def test_empty_baseline_no_crash(self):
        """首次运行无基线目录时, 所有模块正常工作"""
        ...

    def test_all_modules_import_and_init(self):
        """所有五个模块可以同时导入和初始化, 无冲突"""
        from engine.core.orchestrator_graph import ResearchOrchestrator
        from engine.core.gate_checks import GATE_DEFINITIONS
        from engine.core.consistency_checker import ConsistencyChecker
        from engine.core.project_predictor import ProjectPredictor
        from engine.core.adaptive_scheduler import AdaptiveScheduler
        from engine.core.baseline_manager import BaselineManager
        # All imports succeed
```

### 5.3 验收检查清单

| # | 验收项 | 涉及模块 | 通过标准 |
|---|--------|---------|---------|
| 1 | Phase 0 SDS 含系统辨识数据 | 模块四 | SDS 输出包含 "系统辨识参考数据" 表格 |
| 2 | Phase 1 FRAME 两轮 + 一致性 | 模块二 | clinical↔data 一致性结果出现在日志中 |
| 3 | Phase 2 辩论纪要格式 | 模块三 | 输出包含共识/分歧/PI 裁决项 |
| 4 | Phase 3 趋势 Gate 工作 | 模块一 | ΔAUC 检查首次执行 → 保存基准 |
| 5 | Phase 4 特征稳定性检查 | 模块一 | 特征重叠率 < 85% → 预警 |
| 6 | 反馈环 B 自动检测 | 模块一 | ML 输出含 "特征不可用" → 自动触发 Phase 1 重开 |
| 7 | 一致性检查触发 Gate FAIL | 模块二 | clinical↔PI major_conflict → Gate FAIL |
| 8 | Gate PASS 后基线冻结 | 模块五 | outputs/baselines/{project}/ 下有 JSON 文件 |
| 9 | 反馈 B 触发变更请求 | 模块五 | change_requests.jsonl 有新记录 |
| 10 | 下游基线被 supersede | 模块五 | 受影响的 Phase 基线 status = "superseded" |
| 11 | 降级容错: 基线写入失败不阻断 | 模块五 | 模拟磁盘满 → 主流程继续 |
| 12 | 空目录首次运行 | 全部 | 无 crash, 所有懒加载降级到默认行为 |

### 5.4 验收命令

```bash
# 运行全链路集成测试
python -m pytest tests/test_end_to_end_acceptance.py -v

# 验证基线目录结构
tree outputs/baselines/

# 验证运行日志持续记录
cat outputs/run_logs/$(date +%Y-%m-%d).jsonl | jq -s 'length'

# 完整项目模拟 (dry-run)
python -c "
from engine.core.orchestrator_graph import ResearchOrchestrator
orch = ResearchOrchestrator()
# 此处调用真实项目流程 (如果 LLM API 可用)
"
```

---

## 六、文件改动清单

| 文件 | 改动类型 | 改动内容 | 预计行数 |
|------|---------|---------|---------|
| `engine/core/baseline_manager.py` | **新文件** | BaselineManager 类 (freeze/supersede/diff/CR) | ~220 |
| `engine/core/state.py` | 修改 | 新增 BaselineRecord, ChangeRequest, BaselineDiff TypedDict | +30 |
| `engine/core/orchestrator_graph.py` | 修改 | __init__ 初始化 BaselineManager; Gate PASS 时 freeze; 反馈B触发时 create CR + supersede 下游 | +40 |
| `tests/test_end_to_end_acceptance.py` | **新文件** | 全链路验收测试 (6 个场景) | ~200 |

---

## 七、五周改造完成后的全系统架构

```
                        用户请求
                           │
                           ▼
              ┌─────────────────────────┐
              │  Phase 0: SDS 总体设计    │
              │  ← 模块四: 系统辨识预测    │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  Phase 1: 问题定义        │
              │  ← FRAME 定量化           │
              │  ← 模块二: 一致性检查      │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  Phase 2: 方案设计        │
              │  ← 模块三: 研讨厅辩论      │
              │  ← 模块二: 一致性检查      │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  Phase 3-4: 执行+验证     │
              │  ← 模块一: Δ-Gate 趋势    │
              │  ← 模块一: 反馈环B 检测    │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  Phase 5: 审查           │
              │  ← 模块三: 研讨厅辩论      │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  Phase 6: 论文撰写        │
              │  ← 模块二: 跨Phase一致性   │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  产出 + 基线归档          │
              │  ← 模块五: 基线冻结        │
              └─────────────────────────┘

全程:
  模块一 (反馈控制): Δ-Gate + 反馈环A + 反馈环B — 持续监控
  模块二 (可靠性): 一致性交叉验证 — 各 Phase 自动检查
  模块三 (研讨厅): 辩论模式 — Phase 2/5 并行辩论
  模块四 (系统辨识): 预测 + 自适应调度 — Phase 0/执行前
  模块五 (基线管理): 冻结 + 变更请求 — Gate 通过后/反馈触发时
```

---

## 附录：理论对照最终验收

| 钱学森理论 | 实现状态 | 关键代码位置 |
|-----------|---------|------------|
| 闭环反馈控制 | ✅ 双层反馈环 + Δ-Gate | gate_checks.py, orchestrator_graph.py |
| 总体设计部 | ✅ SDS Phase 0 + 接口标准化 | orchestrator_graph.py::_run_system_design |
| 系统辨识 | ✅ RunLog + 季度报告 + 传递函数 | run_analyzer.py, project_predictor.py |
| 最优控制 | ✅ 自适应调度 | adaptive_scheduler.py |
| 可靠性工程 | ✅ LLM容错 + 一致性交叉验证 | llm_client.py, consistency_checker.py |
| 综合集成研讨厅 | ✅ FRAME定量化 + 辩论模式 | orchestrator_graph.py::debate |
| 从定性到定量 | ✅ Gate量化 + 基线版本管理 | gate_checks.py, baseline_manager.py |
| 技术状态管理 | ✅ 基线冻结 + 变更控制 | baseline_manager.py |

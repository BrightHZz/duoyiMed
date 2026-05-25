"""Obsidian 知识库管理器 — Agent 读写知识库的统一接口"""

import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


class KnowledgeBaseManager:
    """管理 Obsidian vault 中的知识库文件的读写 — 支持多事业部多知识库"""

    def __init__(self, vault_path: Path, vaults: dict = None,
                 outputs_dir: Path = None):
        """
        Args:
            vault_path: 默认/主知识库路径
            vaults: 各事业部的知识库路径 dict, e.g. {"geriatrics": Path, "urology": Path}
            outputs_dir: 项目输出根目录 (outputs/projects/), 用于跨项目学习
        """
        self.vault = vault_path
        self.vaults = vaults or {}
        self.outputs_dir = outputs_dir
        self._ensure_dirs()

    def get_vault(self, division: str = None) -> Path:
        """根据事业部获取对应的知识库路径"""
        if division and division in self.vaults:
            return self.vaults[division]
        return self.vault

    def _ensure_dirs(self):
        std_dirs = ["projects", "literature", "methods", "datasets", "concepts", "templates"]
        for vault_path in [self.vault] + list(self.vaults.values()):
            for d in std_dirs:
                (vault_path / d).mkdir(parents=True, exist_ok=True)

    def _get_all_project_dirs(self) -> list[Path]:
        """获取所有项目目录 (vault 项目 + outputs 项目)。"""
        dirs = []
        # 1. Vault 中的项目
        for vault in [self.vault] + list(self.vaults.values()):
            proj_dir = vault / "projects"
            if proj_dir.exists():
                for d in proj_dir.iterdir():
                    if d.is_dir() and not d.name.startswith("_"):
                        dirs.append(d)
        # 2. outputs/projects/ 中的项目运行输出
        if self.outputs_dir and self.outputs_dir.exists():
            for d in self.outputs_dir.iterdir():
                if d.is_dir() and not d.name.startswith("_"):
                    if d not in dirs:
                        dirs.append(d)
        return dirs

    # ================================================================
    # YAML Frontmatter 解析
    # ================================================================

    @staticmethod
    def parse_frontmatter(content: str) -> tuple[dict, str]:
        """解析 Markdown 文件的 YAML frontmatter, 返回 (metadata, body)"""
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return {}, content
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            metadata = {}
        body = content[match.end():]
        return metadata, body

    @staticmethod
    def build_frontmatter(metadata: dict) -> str:
        """构建 YAML frontmatter 字符串"""
        return "---\n" + yaml.dump(metadata, allow_unicode=True, sort_keys=False) + "---\n"

    # ================================================================
    # 读取操作
    # ================================================================

    def read(self, relative_path: str) -> str:
        """读取知识库中的文件内容"""
        filepath = self.vault / relative_path
        if not filepath.exists():
            raise FileNotFoundError(f"知识库文件不存在: {filepath}")
        return filepath.read_text(encoding="utf-8")

    def read_with_metadata(self, relative_path: str) -> tuple[dict, str]:
        """读取文件并解析 frontmatter"""
        content = self.read(relative_path)
        return self.parse_frontmatter(content)

    def get_project_state(self, project_id: str) -> Optional[dict]:
        """获取项目状态 (从 project-brief.md 的 frontmatter)"""
        try:
            metadata, _ = self.read_with_metadata(f"projects/{project_id}/project-brief.md")
            return metadata
        except FileNotFoundError:
            return None

    def get_literature_by_topic(self, topic: str) -> list[dict]:
        """按主题获取文献列表"""
        results = []
        lit_dir = self.vault / "literature"
        for f in lit_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            metadata, _ = self.parse_frontmatter(content)
            if metadata.get("type") == "literature" and topic in metadata.get("topics", []):
                results.append(metadata)
        return results

    def search_knowledge_base(self, query: str) -> list[dict]:
        """在整个知识库中搜索相关内容 (简单关键词匹配)"""
        results = []
        for md_file in self.vault.rglob("*.md"):
            if ".obsidian" in str(md_file):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                if query.lower() in content.lower():
                    metadata, _ = self.parse_frontmatter(content)
                    results.append({
                        "path": str(md_file.relative_to(self.vault)),
                        "type": metadata.get("type", "unknown"),
                        "title": metadata.get("title", metadata.get("name", md_file.stem)),
                        "snippet": self._get_snippet(content, query),
                    })
            except Exception:
                continue
        return results[:20]  # 限制返回数量

    @staticmethod
    def _get_snippet(content: str, query: str, context_chars: int = 120) -> str:
        idx = content.lower().find(query.lower())
        if idx < 0:
            return content[:context_chars]
        start = max(0, idx - context_chars // 2)
        end = min(len(content), idx + len(query) + context_chars // 2)
        snippet = content[start:end]
        return ("..." if start > 0 else "") + snippet + ("..." if end < len(content) else "")

    # ================================================================
    # 写入操作
    # ================================================================

    def write(self, relative_path: str, content: str, metadata: Optional[dict] = None):
        """写入 Markdown 文件到知识库"""
        filepath = self.vault / relative_path
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if metadata:
            full_content = self.build_frontmatter(metadata) + "\n" + content
        else:
            full_content = content

        filepath.write_text(full_content, encoding="utf-8")

    def update_frontmatter(self, relative_path: str, updates: dict):
        """更新文件的 YAML frontmatter (保留 body 不变)"""
        content = self.read(relative_path)
        metadata, body = self.parse_frontmatter(content)
        metadata.update(updates)
        self.write(relative_path, body, metadata)

    def create_literature_note(self, metadata: dict, body: str):
        """创建标准化文献笔记"""
        first_author = metadata.get("first_author", "unknown")
        year = metadata.get("year", datetime.now().year)
        topic = metadata.get("topics", ["general"])[0] if metadata.get("topics") else "general"
        filename = f"literature/{year}-{first_author.lower()}-{topic}.md"
        metadata.setdefault("type", "literature")
        metadata.setdefault("date_read", datetime.now().strftime("%Y-%m-%d"))
        self.write(filename, body, metadata)

    def update_project_status(self, project_id: str, new_status: str, next_actions: Optional[list] = None):
        """更新项目状态"""
        updates = {"status": new_status, "last_updated": datetime.now().strftime("%Y-%m-%d")}
        if next_actions:
            updates["next_actions"] = next_actions
        try:
            self.update_frontmatter(f"projects/{project_id}/project-brief.md", updates)
        except FileNotFoundError:
            pass

    def append_experiment_log(self, project_id: str, experiment_entry: str):
        """向 experiment-log.md 追加实验记录"""
        filepath = self.vault / f"projects/{project_id}/experiment-log.md"
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
        else:
            content = ""
        content += "\n\n---\n\n" + experiment_entry
        filepath.write_text(content, encoding="utf-8")

    # ================================================================
    # 模板加载
    # ================================================================

    def load_template(self, template_name: str) -> str:
        """加载笔记模板, 支持模板变量 {{variable}}"""
        template_path = f"templates/{template_name}.md"
        try:
            return self.read(template_path)
        except FileNotFoundError:
            return ""

    def fill_template(self, template_name: str, variables: dict) -> str:
        """加载模板并填充变量"""
        template = self.load_template(template_name)
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

    # ================================================================
    # 经验规则提取与传播 (知识管理部 — B环 #10 触发器实现)
    # ================================================================

    def scan_lessons_learned(self) -> list[dict]:
        """扫描所有项目目录中的 lessons-learned 文件, 提取可量化规则。

        支持两种格式:
        1. YAML frontmatter Markdown 文件 (lessons-learned*.md):
           frontmatter 含 pattern/file_pattern/severity/fix 字段
        2. 纯文本规则文件 (lessons-learned*.json):
           直接 JSON 数组, 每项含相同的规则字段

        Returns:
            [{"rule_id": str, "pattern": str, "file_pattern": str,
              "severity": str, "fix": str, "source_project": str,
              "source_file": str}, ...]
        """
        rules = []
        # 搜索所有 vault 的 projects 目录
        vaults_to_search = [self.vault] + list(self.vaults.values())

        for vault in vaults_to_search:
            projects_dir = vault / "projects"
            if not projects_dir.exists():
                continue

            # 查找所有 lessons-learned 文件
            for lesson_file in projects_dir.rglob("lessons-learned*"):
                if lesson_file.suffix not in (".md", ".json"):
                    continue

                project_id = lesson_file.parent.name if lesson_file.parent != projects_dir else "_shared"
                try:
                    if lesson_file.suffix == ".json":
                        rules += self._parse_json_lessons(lesson_file, project_id)
                    else:
                        rules += self._parse_md_lessons(lesson_file, project_id)
                except Exception as e:
                    print(f"  ⚠️ [知识管理] 解析 {lesson_file} 失败: {e}")

        return rules

    def _parse_json_lessons(self, filepath: Path, project_id: str) -> list[dict]:
        """解析 JSON 格式的经验规则文件"""
        import json
        data = json.loads(filepath.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = [data]
        for rule in data:
            rule.setdefault("source_project", project_id)
            rule.setdefault("source_file", str(filepath))
            rule.setdefault("file_pattern", "*.py")
            rule.setdefault("severity", "high")
        return data

    def _parse_md_lessons(self, filepath: Path, project_id: str) -> list[dict]:
        """解析 Markdown (YAML frontmatter) 格式的经验规则文件。

        Frontmatter 格式:
        ---
        type: lesson
        rule_id: ML-SAFETY-001
        pattern: "n_jobs\\\\s*=\\\\s*-1"
        file_pattern: "*.py"
        severity: critical
        fix: "Replace n_jobs=-1 with n_jobs=2"
        ---
        """
        content = filepath.read_text(encoding="utf-8")
        metadata, _ = self.parse_frontmatter(content)

        if metadata.get("type") != "lesson" or not metadata.get("pattern"):
            return []

        rule = {
            "rule_id": metadata.get("rule_id", filepath.stem),
            "pattern": metadata["pattern"],
            "file_pattern": metadata.get("file_pattern", "*.py"),
            "severity": metadata.get("severity", "high"),
            "fix": metadata.get("fix", ""),
            "source_project": project_id,
            "source_file": str(filepath),
        }
        return [rule]

    def diff_rules_against_scripts(
        self, rules: list[dict], target_dir: Path
    ) -> list[dict]:
        """将经验规则与目标目录下所有匹配脚本进行 diff。

        对每条规则, 用其 pattern 作为正则表达式搜索目标文件中匹配的脚本。
        命中 → 该脚本违反此规则 → 记录为 violation。

        Args:
            rules: scan_lessons_learned() 的返回结果
            target_dir: 要扫描的项目目录

        Returns:
            [{"rule_id": str, "severity": str, "fix": str,
              "file": str, "line": int, "match": str,
              "source_project": str}, ...]
        """
        violations = []

        for rule in rules:
            pattern = rule.get("pattern", "")
            if not pattern:
                continue

            file_glob = rule.get("file_pattern", "*.py")
            try:
                regex = re.compile(pattern)
            except re.error as e:
                print(f"  ⚠️ [知识管理] 规则 {rule.get('rule_id')} 的 pattern 无效: {e}")
                continue

            # 在目标目录中搜索匹配文件
            for script_file in target_dir.rglob(file_glob):
                # 跳过隐藏目录和虚拟环境
                if any(part.startswith(".") for part in script_file.parts):
                    continue
                if "node_modules" in script_file.parts or "__pycache__" in script_file.parts:
                    continue

                try:
                    content = script_file.read_text(encoding="utf-8")
                except Exception:
                    continue

                for i, line in enumerate(content.splitlines(), 1):
                    match = regex.search(line)
                    if match:
                        violations.append({
                            "rule_id": rule.get("rule_id", ""),
                            "severity": rule.get("severity", "high"),
                            "fix": rule.get("fix", ""),
                            "file": str(script_file.relative_to(target_dir)),
                            "line": i,
                            "match": line.strip(),
                            "source_project": rule.get("source_project", ""),
                            "source_file": rule.get("source_file", ""),
                        })

        # 按 severity 排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        violations.sort(key=lambda x: severity_order.get(x["severity"], 5))

        return violations

    # ================================================================
    # 跨项目学习引擎 (知识管理部 — 系统辨识模块数据源)
    # ================================================================

    def aggregate_run_statistics(self) -> dict:
        """跨所有项目聚合运行统计。

        扫描所有 vault 的 projects/ 目录, 读取 run_logs/*.jsonl 和
        gate_report_phase*.json, 聚合为系统辨识模块所需的数据。

        Returns:
            {"projects": int, "total_calls": int,
             "phase_stats": {phase_id: {"count": int, "avg_sec": float, ...}},
             "agent_stats": {agent_id: {"count": int, "success_rate": float, ...}},
             "gate_stats": {phase_id: {"pass_rate": float, "fail_count": int, ...}},
             "bottlenecks": [...]}
        """
        import json as _json
        from collections import defaultdict

        projects = []
        phase_times = defaultdict(list)
        agent_stats = defaultdict(lambda: {"total": 0, "success": 0, "degraded": 0})
        gate_stats = defaultdict(lambda: {"pass": 0, "cond_pass": 0, "fail": 0, "total": 0})

        for project_path in self._get_all_project_dirs():
            # 读取项目状态
            state_path = project_path / "project_state.json"
            proj_info = {"id": project_path.name, "phases": []}
            if state_path.exists():
                try:
                    state = _json.loads(state_path.read_text(encoding="utf-8"))
                    proj_info["division"] = state.get("division", "")
                    proj_info["request"] = state.get("user_request", "")[:120]
                    proj_info["status"] = state.get("status", "")
                except Exception:
                    pass

            # 读取 gate reports
            for gr_path in sorted(project_path.glob("gate_report_phase*.json")):
                try:
                    gr = _json.loads(gr_path.read_text(encoding="utf-8"))
                    auto_checks = gr.get("auto_checks", [])
                    fail_count = sum(1 for c in auto_checks if c.get("result") == "fail")
                    phase_id = gr.get("phase_id", gr_path.stem.replace("gate_report_", ""))
                    gate_stats[phase_id]["total"] += 1
                    if fail_count == 0:
                        gate_stats[phase_id]["pass"] += 1
                    else:
                        gate_stats[phase_id]["fail"] += 1
                except Exception:
                    pass

            # 读取 run logs
            run_logs_dir = project_path / "run_logs"
            if run_logs_dir.exists():
                for log_file in run_logs_dir.glob("*.jsonl"):
                    try:
                        for line in log_file.read_text(encoding="utf-8").splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            rec = _json.loads(line)
                            agent = rec.get("agent_id", "")
                            if agent.startswith("_"):
                                continue

                            agent_stats[agent]["total"] += 1
                            if rec.get("success"):
                                agent_stats[agent]["success"] += 1
                            if rec.get("degraded"):
                                agent_stats[agent]["degraded"] += 1

                            phase_id = rec.get("phase_id", "")
                            wt = rec.get("wall_time_sec", 0)
                            if phase_id and wt > 0:
                                phase_times[phase_id].append(wt)
                    except Exception:
                        pass

            projects.append(proj_info)

        # 聚合 phase 统计
        phase_summary = {}
        for pid, times in phase_times.items():
            if not times:
                continue
            phase_summary[pid] = {
                "count": len(times),
                "avg_sec": round(sum(times) / len(times), 1),
                "p50_sec": round(sorted(times)[len(times) // 2], 1),
                "total_sec": round(sum(times), 1),
            }

        # 聚合 agent 统计
        agent_summary = {}
        for aid, data in agent_stats.items():
            total = data["total"]
            agent_summary[aid] = {
                "count": total,
                "success_rate": round(data["success"] / total * 100) if total else 0,
                "degraded_rate": round(data["degraded"] / total * 100) if total else 0,
            }

        # 聚合 gate 统计
        gate_summary = {}
        for pid, data in gate_stats.items():
            t = data["total"]
            gate_summary[pid] = {
                "total": t,
                "pass_rate": round(data["pass"] / t * 100) if t else 0,
                "fail_count": data["fail"],
            }

        return {
            "project_count": len(projects),
            "total_agent_calls": sum(a["total"] for a in agent_summary.values()),
            "phase_stats": phase_summary,
            "agent_stats": agent_summary,
            "gate_stats": gate_summary,
            "projects": projects,
        }

    def find_similar_projects(
        self, division: str = None, data_source: str = None,
        method: str = None, n: int = 5
    ) -> list[dict]:
        """为新项目找到历史上最相似的已完成项目。

        基于 division、data_source、method 关键词模糊匹配,
        按相似度评分 (division +4, data_source +2, method +3)。

        Args:
            division: 事业部 (geriatrics/urology/pediatrics)
            data_source: 数据源关键词 (CHARLS/MIMIC/SEER 等)
            method: 方法关键词 (XGBoost/SHAP/logistic 等)
            n: 返回数量

        Returns:
            相似项目列表, 每项含 id/division/request/status/score
        """
        import json as _json

        candidates = []
        vaults_to_search = [self.vault] + list(self.vaults.values())

        for vault in vaults_to_search:
            proj_dir = vault / "projects"
            if not proj_dir.exists():
                continue

            for project_path in proj_dir.iterdir():
                if not project_path.is_dir() or project_path.name.startswith("_"):
                    continue

                state_path = project_path / "project_state.json"
                if not state_path.exists():
                    continue

                try:
                    state = _json.loads(state_path.read_text(encoding="utf-8"))
                except Exception:
                    continue

                score = 0
                proj_div = state.get("division", "")
                proj_req = state.get("user_request", "")

                if division and proj_div == division:
                    score += 4
                if data_source and data_source.lower() in proj_req.lower():
                    score += 2
                if method and method.lower() in proj_req.lower():
                    score += 3

                if score > 0:
                    candidates.append({
                        "id": project_path.name,
                        "division": proj_div,
                        "request": proj_req[:150],
                        "status": state.get("status", ""),
                        "score": score,
                    })

        candidates.sort(key=lambda x: -x["score"])
        return candidates[:n]

    def extract_bottlenecks(self) -> list[dict]:
        """识别系统级瓶颈。

        基于 aggregate_run_statistics() 的数据, 识别:
        - 哪个 Phase 平均耗时最长
        - 哪个 Gate 失败率最高
        - 哪个 Agent 成功率最低

        Returns:
            [{"type": "phase_slow|gate_fail|agent_low", "target": str,
              "value": str, "suggestion": str}, ...]
        """
        stats = self.aggregate_run_statistics()
        bottlenecks = []

        # Phase 耗时瓶颈
        phase_stats = stats.get("phase_stats", {})
        if phase_stats:
            slowest = max(phase_stats.items(), key=lambda x: x[1].get("avg_sec", 0))
            bottlenecks.append({
                "type": "phase_slow",
                "target": slowest[0],
                "value": f"{slowest[1].get('avg_sec', 0):.0f}s avg",
                "suggestion": f"Phase {slowest[0]} 是耗时瓶颈, 考虑增加并行度或拆分任务",
            })

        # Gate 失败瓶颈
        gate_stats = stats.get("gate_stats", {})
        if gate_stats:
            worst_gate = max(gate_stats.items(),
                            key=lambda x: x[1].get("fail_count", 0))
            if worst_gate[1].get("fail_count", 0) > 0:
                bottlenecks.append({
                    "type": "gate_fail",
                    "target": worst_gate[0],
                    "value": f"{worst_gate[1].get('fail_count')} failures",
                    "suggestion": f"Gate {worst_gate[0]} 失败最多, 检查对应 check 函数是否需要校准",
                })

        # Agent 成功率瓶颈
        agent_stats = stats.get("agent_stats", {})
        if agent_stats:
            worst_agent = min(agent_stats.items(),
                             key=lambda x: x[1].get("success_rate", 100))
            if worst_agent[1].get("success_rate", 100) < 70:
                bottlenecks.append({
                    "type": "agent_low",
                    "target": worst_agent[0],
                    "value": f"{worst_agent[1].get('success_rate')}% success rate",
                    "suggestion": f"Agent {worst_agent[0]} 成功率偏低, 审查 system prompt",
                })

        return bottlenecks

    # ================================================================
    # 知识图谱 (知识管理部 — 研讨厅定量化数据支撑)
    # ================================================================

    def find_related_projects(self, project_id: str, n: int = 5) -> list[dict]:
        """找到与指定项目最相关的其他项目。

        基于 division + request 文本相似度 (关键词重叠度),
        返回关联度最高的 n 个项目。

        Returns:
            [{"id": str, "division": str, "request": str, "overlap": int, "status": str}]
        """
        import json as _json

        # 先获取目标项目的特征
        target_div = ""
        target_words = set()
        vaults_to_search = [self.vault] + list(self.vaults.values())

        for vault in vaults_to_search:
            proj_dir = vault / "projects"
            if not proj_dir.exists():
                continue

            target_path = proj_dir / project_id
            if not target_path.exists():
                continue

            state_path = target_path / "project_state.json"
            if state_path.exists():
                try:
                    state = _json.loads(state_path.read_text(encoding="utf-8"))
                    target_div = state.get("division", "")
                    req = state.get("user_request", "")
                    target_words = set(req.lower().split())
                except Exception:
                    pass
            break

        if not target_words:
            return []

        related = []
        for vault in vaults_to_search:
            proj_dir = vault / "projects"
            if not proj_dir.exists():
                continue

            for project_path in proj_dir.iterdir():
                if not project_path.is_dir() or project_path.name.startswith("_"):
                    continue
                if project_path.name == project_id:
                    continue

                state_path = project_path / "project_state.json"
                if not state_path.exists():
                    continue

                try:
                    state = _json.loads(state_path.read_text(encoding="utf-8"))
                except Exception:
                    continue

                div = state.get("division", "")
                req = state.get("user_request", "")

                # 关键词重叠度
                req_words = set(req.lower().split())
                overlap = len(target_words & req_words) if req_words else 0

                # division 匹配加分
                if target_div and div == target_div:
                    overlap += 10

                if overlap > 0:
                    related.append({
                        "id": project_path.name,
                        "division": div,
                        "request": req[:120],
                        "overlap": overlap,
                        "status": state.get("status", ""),
                    })

        related.sort(key=lambda x: -x["overlap"])
        return related[:n]

    def get_method_usage_stats(self) -> dict:
        """统计各方法在不同项目中的使用频率。

        扫描所有项目的 project_state.json 和 gate reports,
        提取方法关键词 (XGBoost/LASSO/SHAP/logistic/SMOTE 等)。

        Returns:
            {method: {"count": int, "projects": [str], "avg_auc": float}}
        """
        import json as _json
        from collections import defaultdict

        method_keywords = [
            "XGBoost", "LightGBM", "CatBoost", "Random Forest",
            "Logistic Regression", "Elastic Net", "LASSO",
            "SHAP", "SMOTE", "Cox PH", "DeepSurv", "LSTM", "Transformer"
        ]

        stats = defaultdict(lambda: {"count": 0, "projects": []})
        vaults_to_search = [self.vault] + list(self.vaults.values())

        for vault in vaults_to_search:
            proj_dir = vault / "projects"
            if not proj_dir.exists():
                continue

            for project_path in proj_dir.iterdir():
                if not project_path.is_dir() or project_path.name.startswith("_"):
                    continue

                state_path = project_path / "project_state.json"
                if not state_path.exists():
                    continue

                try:
                    state = _json.loads(state_path.read_text(encoding="utf-8"))
                except Exception:
                    continue

                req = state.get("user_request", "")
                for method in method_keywords:
                    if method.lower() in req.lower():
                        stats[method]["count"] += 1
                        if project_path.name not in stats[method]["projects"]:
                            stats[method]["projects"].append(project_path.name)

        return dict(stats)

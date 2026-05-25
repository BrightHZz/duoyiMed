"""Obsidian 知识库管理器 — Agent 读写知识库的统一接口"""

import re
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


class KnowledgeBaseManager:
    """管理 Obsidian vault 中的知识库文件的读写 — 支持多事业部多知识库"""

    def __init__(self, vault_path: Path, vaults: dict = None):
        """
        Args:
            vault_path: 默认/主知识库路径
            vaults: 各事业部的知识库路径 dict, e.g. {"geriatrics": Path, "urology": Path}
        """
        self.vault = vault_path
        self.vaults = vaults or {}
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

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
        for d in ["projects", "literature", "methods", "datasets", "concepts", "templates"]:
            (self.vault / d).mkdir(parents=True, exist_ok=True)

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

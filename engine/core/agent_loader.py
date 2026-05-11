"""Agent 系统提示加载器 — 支持公司模式多事业部 (v2.0)

从 company/ 目录加载各 Agent 的 system prompt 和 few-shot 示例。
保留对旧 agents/ 路径的向后兼容。
"""

import re
from pathlib import Path
from typing import Optional


class AgentPromptLoader:
    """从 company/ 目录加载各 Agent 的 system prompt 和 few-shot 示例"""

    # ================================================================
    # Company Mode Agent Registry (v2.0)
    # ================================================================

    AGENT_REGISTRY = {
        # --- 管理层 ---
        "chief-scientist":      "management/chief-scientist.md",
        "company-orchestrator": "management/company-orchestrator.md",
        "pmo":                  "management/pmo.md",

        # --- 老年医学事业部 ---
        "geriatrics/pi":                     "divisions/geriatrics/pi-agent.md",
        "geriatrics/clinical-researcher":     "divisions/geriatrics/clinical-researcher-agent.md",
        "geriatrics/computational-biologist": "divisions/geriatrics/computational-biologist-agent.md",

        # --- 泌尿外科事业部 ---
        "urology/pi":                     "divisions/urology/pi-agent.md",
        "urology/clinical-researcher":     "divisions/urology/clinical-researcher-agent.md",
        "urology/computational-biologist": "divisions/urology/computational-biologist-agent.md",

        # --- 共享服务 ---
        "shared/data-engineer":       "shared-services/data-engineer-agent.md",
        "shared/biostatistician":     "shared-services/biostatistician-agent.md",
        "shared/ml-engineer":         "shared-services/ml-engineer-agent.md",
        "shared/scientific-writer":   "shared-services/scientific-writer-agent.md",
        "shared/research-assistant":  "shared-services/research-assistant-agent.md",
        "shared/humanizer":          "shared-services/humanizer-agent.md",
    }

    FEWSHOT_REGISTRY = {
        # 管理层 (无 few-shot)
        "chief-scientist":      "",
        "company-orchestrator": "",
        "pmo":                  "",

        # 老年医学事业部
        "geriatrics/pi":                     "few-shot/geriatrics/pi.md",
        "geriatrics/clinical-researcher":     "few-shot/geriatrics/clinical-researcher.md",
        "geriatrics/computational-biologist": "few-shot/geriatrics/computational-biologist.md",

        # 泌尿外科事业部
        "urology/pi":                     "few-shot/urology/pi.md",
        "urology/clinical-researcher":     "few-shot/urology/clinical-researcher.md",
        "urology/computational-biologist": "few-shot/urology/computational-biologist.md",

        # 共享服务 (复用 geriatrics few-shot)
        "shared/data-engineer":       "few-shot/geriatrics/data-engineer.md",
        "shared/biostatistician":     "few-shot/geriatrics/biostatistician.md",
        "shared/ml-engineer":         "few-shot/geriatrics/ml-engineer.md",
        "shared/scientific-writer":   "few-shot/geriatrics/scientific-writer.md",
        "shared/research-assistant":  "few-shot/geriatrics/research-assistant.md",
        "shared/humanizer":          "",   # 无需 few-shot, 规则来自 humanizer-rules.md
    }

    # ================================================================
    # Legacy Compatibility Map
    # ================================================================

    LEGACY_MAP = {
        "orchestrator":           "company-orchestrator",
        "pm":                     "pmo",
        "pi":                     "geriatrics/pi",
        "clinical-researcher":    "geriatrics/clinical-researcher",
        "computational-biologist": "geriatrics/computational-biologist",
        "ml-engineer":            "shared/ml-engineer",
        "biostatistician":        "shared/biostatistician",
        "data-engineer":          "shared/data-engineer",
        "scientific-writer":      "shared/scientific-writer",
        "research-assistant":     "shared/research-assistant",
        "humanizer":              "shared/humanizer",
    }

    # Legacy AGENT_FILES for backward compatibility
    AGENT_FILES = {
        "orchestrator": "orchestrator.md",
        "pm": "pm-agent.md",
        "pi": "pi-agent.md",
        "computational-biologist": "computational-biologist-agent.md",
        "clinical-researcher": "clinical-researcher-agent.md",
        "ml-engineer": "ml-engineer-agent.md",
        "biostatistician": "biostatistician-agent.md",
        "data-engineer": "data-engineer-agent.md",
        "scientific-writer": "scientific-writer-agent.md",
        "research-assistant": "research-assistant-agent.md",
        "humanizer": "humanizer-agent.md",
    }

    def __init__(self, agents_dir: Path = None, company_dir: Path = None):
        """
        Args:
            agents_dir: Legacy agents/ directory (backward compat)
            company_dir: New company/ directory (preferred)
        """
        self.agents_dir = agents_dir
        self.company_dir = company_dir
        # Try to auto-detect company_dir
        if self.company_dir is None and agents_dir is not None:
            candidate = agents_dir.parent / "company"
            if candidate.exists():
                self.company_dir = candidate

    def _resolve_agent_id(self, agent_id: str) -> str:
        """Resolve agent_id: legacy → new format. Returns the new-format ID."""
        return self.LEGACY_MAP.get(agent_id, agent_id)

    def _get_agent_path(self, agent_id: str) -> Path:
        """Resolve agent_id to its .md file path. Tries company_dir first, then agents_dir."""
        resolved = self._resolve_agent_id(agent_id)

        # Try company mode first
        if self.company_dir:
            relative = self.AGENT_REGISTRY.get(resolved)
            if relative:
                filepath = self.company_dir / relative
                if filepath.exists():
                    return filepath

        # Fall back to legacy agents_dir
        if self.agents_dir:
            legacy_file = self.AGENT_FILES.get(agent_id)
            if legacy_file:
                filepath = self.agents_dir / legacy_file
                if filepath.exists():
                    return filepath

        raise ValueError(f"Unknown agent: '{agent_id}' (resolved: '{resolved}'). "
                         f"Available: {list(self.AGENT_REGISTRY.keys())}")

    def _get_fewshot_path(self, agent_id: str) -> Optional[Path]:
        """Resolve few-shot file path."""
        resolved = self._resolve_agent_id(agent_id)

        if self.company_dir:
            relative = self.FEWSHOT_REGISTRY.get(resolved)
            if relative:
                filepath = self.company_dir / relative
                if filepath.exists():
                    return filepath

        # Fall back to legacy
        if self.agents_dir:
            legacy_fewshot = {
                "pi": "few-shot/pi.md",
                "computational-biologist": "few-shot/computational-biologist.md",
                "clinical-researcher": "few-shot/clinical-researcher.md",
                "ml-engineer": "few-shot/ml-engineer.md",
                "biostatistician": "few-shot/biostatistician.md",
                "data-engineer": "few-shot/data-engineer.md",
                "scientific-writer": "few-shot/scientific-writer.md",
                "research-assistant": "few-shot/research-assistant.md",
                "orchestrator": "few-shot/orchestrator.md",
            }.get(agent_id, "")
            if legacy_fewshot:
                filepath = self.agents_dir / legacy_fewshot
                if filepath.exists():
                    return filepath

        return None

    def _read_file(self, filepath: Path) -> Optional[str]:
        if not filepath.exists():
            return None
        return filepath.read_text(encoding="utf-8")

    def load_system_prompt(self, agent_id: str) -> str:
        """加载 Agent 的 system prompt"""
        filepath = self._get_agent_path(agent_id)
        content = filepath.read_text(encoding="utf-8")

        # 移除文件开头的 H1 标题
        content = re.sub(r'^# .*\n', '', content, count=1)
        return content.strip()

    def load_fewshot(self, agent_id: str) -> str:
        """加载 Agent 的 few-shot 示例"""
        filepath = self._get_fewshot_path(agent_id)
        if not filepath:
            return ""

        fewshot = filepath.read_text(encoding="utf-8")
        fewshot = re.sub(r'^# .*\n', '', fewshot, count=1)
        return "\n\n## Few-Shot Examples\n\n" + fewshot.strip()

    def load_full_prompt(self, agent_id: str, include_fewshot: bool = True) -> str:
        """加载 Agent 的完整 prompt (system + few-shot)"""
        system = self.load_system_prompt(agent_id)
        if include_fewshot:
            fewshot = self.load_fewshot(agent_id)
            system += fewshot
        return system

    def load_communication_protocol(self) -> str:
        """加载 Agent 间通信协议 (优先 company 版本)"""
        if self.company_dir:
            filepath = self.company_dir / "protocols/communication-protocol.md"
            if filepath.exists():
                return filepath.read_text(encoding="utf-8")
        if self.agents_dir:
            filepath = self.agents_dir / "communication-protocol.md"
            if filepath.exists():
                return filepath.read_text(encoding="utf-8")
        return ""

    def load_kb_protocol(self) -> str:
        """加载知识库交互协议 (优先 company 版本)"""
        if self.company_dir:
            filepath = self.company_dir / "protocols/knowledge-base-protocol.md"
            if filepath.exists():
                return filepath.read_text(encoding="utf-8")
        if self.agents_dir:
            filepath = self.agents_dir / "knowledge-base-protocol.md"
            if filepath.exists():
                return filepath.read_text(encoding="utf-8")
        return ""

    def load_division_interface_protocol(self) -> str:
        """加载事业部接口协议"""
        if self.company_dir:
            filepath = self.company_dir / "protocols/division-interface-protocol.md"
            if filepath.exists():
                return filepath.read_text(encoding="utf-8")
        return ""

    def load_all_division_agents(self, division: str) -> dict:
        """列出某个事业部的所有 Agent"""
        prefix = f"{division}/"
        return {
            agent_id: relative
            for agent_id, relative in self.AGENT_REGISTRY.items()
            if agent_id.startswith(prefix)
        }

    def load_shared_services(self) -> list[str]:
        """列出所有共享服务 Agent ID"""
        return [
            agent_id for agent_id in self.AGENT_REGISTRY
            if agent_id.startswith("shared/")
        ]

    def load_all_agent_summaries(self) -> str:
        """生成所有 Agent 的简要能力摘要 (用于公司编排器路由)"""
        summaries = []
        for agent_id, relative in self.AGENT_REGISTRY.items():
            if agent_id in ("company-orchestrator", "pmo"):
                continue
            if self.company_dir:
                content = self._read_file(self.company_dir / relative)
            elif self.agents_dir:
                # Fallback
                legacy_file = self.AGENT_FILES.get(
                    self.LEGACY_MAP.get(agent_id, agent_id), ""
                )
                if legacy_file:
                    content = self._read_file(self.agents_dir / legacy_file)
                else:
                    continue
            else:
                continue

            if content:
                match = re.search(r'## Role Identity\n\n(.*?)(?=\n## )', content, re.DOTALL)
                if match:
                    summaries.append(f"### {agent_id}\n{match.group(1).strip()}")
        return "# Available Agents (Company Mode)\n\n" + "\n\n".join(summaries)

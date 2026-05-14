"""
Agent 工具集 — 让 Agent 可以真正操作文件和知识库

每个工具有两部分:
1. Anthropic tool definition (name, description, input_schema)
2. Python 执行函数
"""

import json
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


# ================================================================
# Tool 注册表
# ================================================================

class ToolRegistry:
    """工具注册和执行引擎 — 支持多数据源"""

    def __init__(self, data_sources: dict = None, obsidian_vault: Path = None,
                 charls_data_dir: Path = None):
        """
        Args:
            data_sources: {name: DataSourceConfig} 公司级数据源注册表 (新)
            obsidian_vault: Obsidian 知识库路径
            charls_data_dir: 向后兼容旧参数, 等价于 data_sources={"CHARLS": DataSourceConfig(...)}
        """
        # 数据源注册表
        if data_sources:
            self.data_sources = data_sources
        elif charls_data_dir:
            # 向后兼容: 旧调用方式
            self.data_sources = {
                "CHARLS": type('DataSourceConfig', (), {
                    'name': 'CHARLS', 'path': charls_data_dir,
                    'category': 'cohort', 'description': 'CHARLS',
                    'supported_tools': [], 'prefetcher_key': 'cohort',
                })()
            }
        else:
            self.data_sources = {}

        # 向后兼容: charls_dir 快速访问
        charls_ds = self.data_sources.get("CHARLS")
        self.charls_dir = charls_ds.path if charls_ds else Path(".")

        self.vault = obsidian_vault or Path(".")
        self.tools = {}  # name → (definition, handler)

        self._register_all()

    def _get_datasource_path(self, name: str) -> Path:
        """获取数据源路径"""
        ds = self.data_sources.get(name)
        return ds.path if ds else Path(".")

    def _register_all(self):
        # 通用多数据源工具
        self._register(self._list_datasource_files())
        self._register(self._read_datasource_headers())
        self._register(self._read_datasource_sample())
        self._register(self._search_datasource_variable())
        # 向后兼容: CHARLS 专用工具
        self._register(self._list_charles_files())
        self._register(self._read_charles_csv_headers())
        self._register(self._read_charles_csv_sample())
        self._register(self._search_charles_variable())
        self._register(self._get_variable_distribution())
        self._register(self._generate_frailty_variable_report())
        # 知识库工具
        self._register(self._read_kb_file())
        self._register(self._write_kb_file())
        self._register(self._write_literature_note())
        self._register(self._search_knowledge_base())
        self._register(self._update_project_status())
        self._register(self._verify_doi())
        self._register(self._verify_all_dois())
        self._register(self._check_kb_duplicate())

    def _register(self, tool_def: dict):
        handler = tool_def.pop("_handler")
        self.tools[tool_def["name"]] = (tool_def, handler)

    def get_definitions(self) -> list[dict]:
        """获取所有 tool 的 Anthropic 格式定义"""
        return [defn for defn, _ in self.tools.values()]

    def get_definitions_for_agent(self, agent_id: str) -> list[dict]:
        """获取特定 Agent 需要的 tool 定义。

        所有 Agent 均可使用所有数据源的工具 (数据源是公司级资产)。
        agent_id 参数保留用于未来按角色限制敏感操作。
        """
        agent_tools = {
            "data-engineer": [
                # 通用多数据源工具
                "list_datasource_files", "read_datasource_headers",
                "read_datasource_sample", "search_datasource_variable",
                # CHARLS 专用 (向后兼容)
                "list_charles_files", "read_charles_csv_headers",
                "read_charles_csv_sample", "search_charles_variable",
                "get_variable_distribution", "generate_frailty_variable_report",
                # 知识库
                "read_kb_file", "write_kb_file",
            ],
            "research-assistant": [
                "search_knowledge_base", "read_kb_file", "write_kb_file",
                "write_literature_note", "check_kb_duplicate",
                "list_datasource_files", "read_datasource_headers",
                "verify_doi",
            ],
            "ml-engineer": [
                "list_datasource_files", "read_datasource_headers",
                "read_datasource_sample",
                "read_charles_csv_headers", "read_charles_csv_sample",
                "read_kb_file",
            ],
            "computational-biologist": [
                "read_kb_file", "search_knowledge_base",
                "list_datasource_files", "read_datasource_headers",
            ],
            "clinical-researcher": [
                "read_kb_file", "search_knowledge_base",
                "list_datasource_files", "read_datasource_headers",
            ],
            "biostatistician": [
                "read_kb_file", "list_datasource_files",
                "read_datasource_headers", "read_charles_csv_headers",
            ],
            "scientific-writer": [
                "read_kb_file", "write_kb_file",
                "verify_doi", "verify_all_dois",
            ],
            "pi": [
                "read_kb_file", "search_knowledge_base",
            ],
            "pm": [
                "read_kb_file", "search_knowledge_base", "write_kb_file",
                "update_project_status",
            ],
            "orchestrator": [
                "read_kb_file", "search_knowledge_base", "update_project_status",
            ],
        }
        allowed = agent_tools.get(agent_id, ["read_kb_file", "search_knowledge_base"])
        return [defn for name, (defn, _) in self.tools.items() if name in allowed]

    def execute(self, tool_name: str, tool_input: dict) -> str:
        """执行工具调用, 返回结果的字符串表示"""
        if tool_name not in self.tools:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        _, handler = self.tools[tool_name]
        try:
            result = handler(tool_input)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ================================================================
    # 工具定义
    # ================================================================

    # --- 通用多数据源工具 (公司级, 所有事业部可用) ---

    def _list_datasource_files(self):
        """列出指定数据源的数据文件 (通用接口, 支持 CHARLS/MIMIC/SEER 等)"""
        def handler(input: dict) -> dict:
            datasource = input.get("datasource", "CHARLS")
            wave = input.get("wave", "")
            data_type = input.get("data_type", "analysis")
            ds_config = self.data_sources.get(datasource)
            if not ds_config:
                return {"error": f"未知数据源: {datasource}", "available": list(self.data_sources.keys())}

            search_dir = ds_config.path
            category = getattr(ds_config, 'category', 'cohort')

            if category in ("cohort",):
                # 队列数据: wave 子目录结构
                if data_type == "analysis":
                    search_dir = search_dir / "analysis"
                pattern = f"*{wave}*.csv" if wave else "*.csv"
            elif category in ("ehr", "registry"):
                # EHR/registry: 按模块/表组织
                module = input.get("module", "")
                if module:
                    search_dir = search_dir / module
                pattern = f"*{wave}*.csv" if wave else "*.csv"
            else:
                pattern = f"*{wave}*.csv" if wave else "*.csv"

            if not search_dir.exists():
                return {"error": f"数据目录不存在: {search_dir}", "datasource": datasource}

            files = sorted(search_dir.glob(pattern))
            return {
                "datasource": datasource,
                "category": category,
                "wave": wave,
                "data_type": data_type,
                "count": len(files),
                "files": [
                    {
                        "filename": f.name,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2) if f.is_file() else 0,
                        "path": str(f),
                    }
                    for f in files
                ],
            }

        return {
            "name": "list_datasource_files",
            "description": "列出指定数据源的数据文件。datasource 参数可选 CHARLS/MIMIC-IV/SEER 等, wave 用于队列数据的 wave 筛选, module 用于 EHR 数据的模块筛选",
            "input_schema": {
                "type": "object",
                "properties": {
                    "datasource": {"type": "string", "description": "数据源名称, 如 CHARLS、MIMIC-IV、SEER"},
                    "wave": {"type": "string", "description": "Wave/年份 筛选 (队列数据), 如 '2013'"},
                    "data_type": {"type": "string", "description": "'raw' (原始) 或 'analysis' (分析就绪)"},
                    "module": {"type": "string", "description": "模块/子目录 (EHR 数据), 如 'hosp'、'icu'"},
                },
                "required": ["datasource"],
            },
            "_handler": handler,
        }

    def _read_datasource_headers(self):
        """读取数据源文件的表头 (通用接口)"""
        def handler(input: dict) -> dict:
            datasource = input.get("datasource", "CHARLS")
            filepath = input.get("filepath", "")
            n_preview = input.get("n_preview", 5)
            ds_config = self.data_sources.get(datasource)
            if not ds_config:
                return {"error": f"未知数据源: {datasource}"}

            full_path = Path(filepath)
            if not full_path.is_absolute() or not full_path.exists():
                full_path = ds_config.path / "analysis" / filepath
            if not full_path.exists():
                # 模糊匹配
                matches = list(ds_config.path.rglob(f"*{filepath}*"))
                if matches:
                    full_path = matches[0]
                else:
                    return {"error": f"File not found: {filepath}", "tried_path": str(full_path)}

            try:
                with open(full_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= n_preview:
                            break
                        rows.append(row)

                return {
                    "datasource": datasource,
                    "filename": full_path.name,
                    "path": str(full_path),
                    "column_count": len(headers),
                    "columns": headers,
                    "preview_rows": rows[:n_preview],
                    "preview_count": len(rows),
                }
            except Exception as e:
                return {"error": f"Failed to read CSV: {e}"}

        return {
            "name": "read_datasource_headers",
            "description": "读取数据源 CSV 文件的表头(变量名)和前几行预览。支持所有数据源 (CHARLS/MIMIC-IV/SEER 等)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "datasource": {"type": "string", "description": "数据源名称"},
                    "filepath": {"type": "string", "description": "CSV 文件路径或文件名"},
                    "n_preview": {"type": "integer", "description": "预览行数, 默认5"},
                },
                "required": ["datasource", "filepath"],
            },
            "_handler": handler,
        }

    def _read_datasource_sample(self):
        """读取数据源文件样本 (通用接口)"""
        def handler(input: dict) -> dict:
            datasource = input.get("datasource", "CHARLS")
            filepath = input.get("filepath", "")
            n_rows = input.get("n_rows", 10)
            columns = input.get("columns", None)
            ds_config = self.data_sources.get(datasource)
            if not ds_config:
                return {"error": f"未知数据源: {datasource}"}

            full_path = Path(filepath)
            if not full_path.is_absolute() or not full_path.exists():
                full_path = ds_config.path / "analysis" / filepath
            if not full_path.exists():
                matches = list(ds_config.path.rglob(f"*{filepath}*"))
                if matches:
                    full_path = matches[0]
                else:
                    return {"error": f"File not found: {filepath}"}

            try:
                with open(full_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= n_rows:
                            break
                        if columns:
                            rows.append({c: row.get(c, "") for c in columns})
                        else:
                            rows.append(row)

                return {
                    "datasource": datasource,
                    "filename": full_path.name,
                    "rows_returned": len(rows),
                    "columns_returned": list(rows[0].keys()) if rows else [],
                    "data": rows,
                }
            except Exception as e:
                return {"error": f"Failed to read CSV sample: {e}"}

        return {
            "name": "read_datasource_sample",
            "description": "读取数据源 CSV 文件的数据样本。支持按列过滤。支持所有数据源",
            "input_schema": {
                "type": "object",
                "properties": {
                    "datasource": {"type": "string", "description": "数据源名称"},
                    "filepath": {"type": "string", "description": "CSV 文件路径"},
                    "n_rows": {"type": "integer", "description": "读取行数, 默认10"},
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "可选: 只读这些列"},
                },
                "required": ["datasource", "filepath"],
            },
            "_handler": handler,
        }

    def _search_datasource_variable(self):
        """跨数据源搜索变量 (通用接口)"""
        def handler(input: dict) -> dict:
            datasource = input.get("datasource", "CHARLS")
            query = input.get("query", "").lower()
            wave_filter = input.get("wave", "")
            ds_config = self.data_sources.get(datasource)
            if not ds_config:
                return {"error": f"未知数据源: {datasource}"}

            results = []
            csv_dir = ds_config.path / "analysis"
            csv_pattern = f"*{wave_filter}*.csv" if wave_filter else "*.csv"

            if csv_dir.exists():
                for csv_file in csv_dir.glob(csv_pattern):
                    try:
                        with open(csv_file, "r", encoding="utf-8-sig") as f:
                            headers = next(csv.reader(f))
                        matching = [h for h in headers if query in h.lower()]
                        if matching:
                            results.append({
                                "source": "csv",
                                "file": csv_file.name,
                                "matching_columns": matching[:20],
                                "total_columns": len(headers),
                            })
                    except Exception:
                        continue
                    if len(results) >= 15:
                        break

            return {
                "datasource": datasource,
                "query": query,
                "results_count": len(results),
                "results": results,
            }

        return {
            "name": "search_datasource_variable",
            "description": "在指定数据源中搜索变量列名。支持所有数据源。队列数据可选择 wave 筛选",
            "input_schema": {
                "type": "object",
                "properties": {
                    "datasource": {"type": "string", "description": "数据源名称"},
                    "query": {"type": "string", "description": "搜索关键词 (变量编码或名称)"},
                    "wave": {"type": "string", "description": "限定 wave, 如 '2013'"},
                },
                "required": ["datasource", "query"],
            },
            "_handler": handler,
        }

    # --- CHARLS 专用工具 (向后兼容, 内部委托给通用接口) ---

    def _list_charles_files(self):
        def handler(input: dict) -> dict:
            wave = input.get("wave", "")
            data_type = input.get("data_type", "analysis")  # raw (.dta) | analysis (.csv)

            if data_type == "raw":
                pattern = f"{wave}_*.dta"
            elif data_type == "analysis":
                pattern = f"{wave}_*.csv" if wave else "*.csv"
            else:
                pattern = f"*{wave}*.csv" if wave else "*.csv"

            search_dir = self.charls_dir / "analysis" if data_type == "analysis" else self.charls_dir
            files = sorted(search_dir.glob(pattern))

            return {
                "wave": wave,
                "data_type": data_type,
                "count": len(files),
                "files": [
                    {
                        "filename": f.name,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                        "path": str(f),
                    }
                    for f in files
                ],
            }

        return {
            "name": "list_charles_files",
            "description": "列出 CHARLS 指定 wave 的数据文件。wave 参数如 '2013'、'2015'，data_type 可选 'raw'(.dta) 或 'analysis'(.csv)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "wave": {"type": "string", "description": "Wave 年份, 如 '2013'"},
                    "data_type": {"type": "string", "description": "'raw' (原始.dta) 或 'analysis' (CSV)"},
                },
                "required": ["wave"],
            },
            "_handler": handler,
        }

    def _read_charles_csv_headers(self):
        def handler(input: dict) -> dict:
            filepath = input.get("filepath", "")
            n_preview = input.get("n_preview", 5)

            # 支持完整路径或 analysis/ 下的文件名
            full_path = Path(filepath)
            if not full_path.is_absolute() or not full_path.exists():
                full_path = self.charls_dir / "analysis" / filepath

            if not full_path.exists():
                # 尝试模糊匹配
                matches = list(self.charls_dir.glob(f"analysis/*{filepath}*"))
                if matches:
                    full_path = matches[0]
                else:
                    return {"error": f"File not found: {filepath}", "tried_path": str(full_path)}

            try:
                with open(full_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= n_preview:
                            break
                        rows.append(row)

                return {
                    "filename": full_path.name,
                    "path": str(full_path),
                    "column_count": len(headers),
                    "columns": headers,
                    "preview_rows": rows[:n_preview],
                    "preview_count": len(rows),
                }
            except Exception as e:
                return {"error": f"Failed to read CSV: {e}"}

        return {
            "name": "read_charles_csv_headers",
            "description": "读取 CHARLS CSV 文件的表头(变量名)和前几行数据。filepath 可以是完整路径或 analysis/ 下的文件名",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "CSV 文件路径或文件名"},
                    "n_preview": {"type": "integer", "description": "预览行数, 默认5"},
                },
                "required": ["filepath"],
            },
            "_handler": handler,
        }

    def _read_charles_csv_sample(self):
        def handler(input: dict) -> dict:
            filepath = input.get("filepath", "")
            n_rows = input.get("n_rows", 10)
            columns = input.get("columns", None)  # 可选: 只读特定列

            full_path = Path(filepath)
            if not full_path.is_absolute() or not full_path.exists():
                full_path = self.charls_dir / "analysis" / filepath
            if not full_path.exists():
                matches = list(self.charls_dir.glob(f"analysis/*{filepath}*"))
                if matches:
                    full_path = matches[0]
                else:
                    return {"error": f"File not found: {filepath}"}

            try:
                with open(full_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= n_rows:
                            break
                        if columns:
                            rows.append({c: row.get(c, "") for c in columns})
                        else:
                            rows.append(row)

                return {
                    "filename": full_path.name,
                    "rows_returned": len(rows),
                    "columns_returned": list(rows[0].keys()) if rows else [],
                    "data": rows,
                }
            except Exception as e:
                return {"error": f"Failed to read CSV sample: {e}"}

        return {
            "name": "read_charles_csv_sample",
            "description": "读取 CHARLS CSV 文件的数据样本。可以指定列名过滤",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "CSV 文件路径"},
                    "n_rows": {"type": "integer", "description": "读取行数, 默认10"},
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "可选: 只读这些列"},
                },
                "required": ["filepath"],
            },
            "_handler": handler,
        }

    def _search_charles_variable(self):
        def handler(input: dict) -> dict:
            query = input.get("query", "").lower()
            wave_filter = input.get("wave", "")
            search_dta = input.get("search_dta", True)

            results = []

            # 搜索 CSV 文件
            csv_dir = self.charls_dir / "analysis"
            csv_pattern = f"*{wave_filter}*.csv" if wave_filter else "*.csv"
            for csv_file in csv_dir.glob(csv_pattern):
                try:
                    with open(csv_file, "r", encoding="utf-8-sig") as f:
                        headers = next(csv.reader(f))
                    matching = [h for h in headers if query in h.lower()]
                    if matching:
                        results.append({
                            "source": "csv",
                            "file": csv_file.name,
                            "matching_columns": matching[:20],
                            "total_columns": len(headers),
                        })
                except Exception:
                    continue
                if len(results) >= 15:
                    break

            # 搜索 .dta 文件 (保留原始 CHARLS 变量名)
            if search_dta:
                dta_pattern = f"*{wave_filter}*.dta" if wave_filter else "*.dta"
                for dta_file in self.charls_dir.glob(dta_pattern):
                    try:
                        import pandas as pd
                        df = pd.read_stata(dta_file, columns_only=True)
                        cols = list(df) if isinstance(df, list) else df
                        matching = [c for c in cols if query in c.lower()]
                        if matching:
                            results.append({
                                "source": "dta",
                                "file": dta_file.name,
                                "matching_columns": matching[:20],
                                "total_columns": len(cols),
                            })
                    except Exception:
                        pass
                    if len(results) >= 15:
                        break

            return {
                "query": query,
                "results_count": len(results),
                "results": results,
                "tip": "CHARLS 变量名使用编码(如 da049=体重变化, dc011/dc012=CES-D疲乏)。用编码搜索更有效！如需查握力相关变量, 搜索 'da' 前缀并结合 Biomarker 文件。" if not results else "使用 read_charles_csv_headers 查看文件全部变量, get_variable_distribution 查看分布",
            }

        return {
            "name": "search_charles_variable",
            "description": "在 CHARLS 文件中搜索包含指定关键词的变量列名。支持 CSV 和 .dta 文件。CHARLS 变量名是用编码的 (如 da049 体重变化, dc011/dc012 CES-D疲乏, da051 体力活动)。搜索编码比搜索英文词更有效",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词。推荐用 CHARLS 变量编码, 如 'da049'、'dc011'、'da051', 而非英文词"},
                    "wave": {"type": "string", "description": "限定 wave, 如 '2013'"},
                    "search_dta": {"type": "boolean", "description": "是否同时搜索 .dta 文件 (默认 true, 变量名更完整)"},
                },
                "required": ["query"],
            },
            "_handler": handler,
        }

    def _generate_frailty_variable_report(self):
        """一键生成 Fried Phenotype 变量可用性报告"""
        import pandas as pd

        # Fried Phenotype 变量定义 (基于 charls_data_processor.py 验证)
        fried_vars = [
            # 问卷变量 (Health_Status)
            {"standard": "体重下降", "var": "da049", "file_hint": "Health_Status_and_Functioning", "type": "categorical"},
            {"standard": "疲乏(CES-D1)", "var": "dc011", "file_hint": "Health_Status_and_Functioning", "type": "categorical"},
            {"standard": "疲乏(CES-D2)", "var": "dc012", "file_hint": "Health_Status_and_Functioning", "type": "categorical"},
            {"standard": "体力活动(简化)", "var": "da050", "file_hint": "Health_Status_and_Functioning", "type": "categorical"},
            # 握力 (Biomarker) — qc003-qc006, 单位 kg, ≥900=缺失码
            {"standard": "握力-第1次(kg)", "var": "qc003", "file_hint": "Biomarker", "type": "numeric"},
            {"standard": "握力-第2次(kg)", "var": "qc004", "file_hint": "Biomarker", "type": "numeric"},
            {"standard": "握力-第3次(kg)", "var": "qc005", "file_hint": "Biomarker", "type": "numeric"},
            {"standard": "握力-第4次(kg)", "var": "qc006", "file_hint": "Biomarker", "type": "numeric"},
            # 步速 (Biomarker) — qg003, 3m步行时间(秒), ≥900=缺失码
            {"standard": "步速-3m步行(秒)", "var": "qg003", "file_hint": "Biomarker", "type": "numeric"},
            # 人体测量 (Biomarker)
            {"standard": "身高(cm)", "var": "qi002", "file_hint": "Biomarker", "type": "numeric"},
            {"standard": "体重(kg)", "var": "ql002", "file_hint": "Biomarker", "type": "numeric"},
            {"standard": "腰围(cm)", "var": "qm002", "file_hint": "Biomarker", "type": "numeric"},
            {"standard": "椅子站立(秒)", "var": "qh003", "file_hint": "Biomarker", "type": "numeric"},
        ]

        def handler(input: dict) -> dict:
            wave = input.get("wave", "2013")
            analysis_dir = self.charls_dir / "analysis"

            hs_file = analysis_dir / f"{wave}_Health_Status_and_Functioning.csv"
            bio_file = analysis_dir / f"{wave}_Biomarker.csv"

            results = []
            for fv in fried_vars:
                target_file = bio_file if fv["file_hint"] == "Biomarker" else hs_file
                if not target_file.exists():
                    results.append({**fv, "found": False, "error": f"File not found: {target_file.name}"})
                    continue

                try:
                    # 只读该列
                    df = pd.read_csv(target_file, usecols=[fv["var"]])
                    col_data = df[fv["var"]]
                    total = len(col_data)
                    non_null = int(col_data.notna().sum())
                    missing = total - non_null
                    missing_pct = round(missing / total * 100, 1)

                    entry = {
                        "fried_standard": fv["standard"],
                        "variable": fv["var"],
                        "file": target_file.name,
                        "type": fv["type"],
                        "total_rows": total,
                        "non_missing": non_null,
                        "missing": missing,
                        "missing_pct": missing_pct,
                        "status": "good" if missing_pct < 10 else ("warning" if missing_pct < 30 else "critical"),
                    }

                    # 数值变量: 加统计摘要
                    if fv["type"] == "numeric" and non_null > 0:
                        valid = col_data.dropna()
                        entry["stats"] = {
                            "mean": round(float(valid.mean()), 2),
                            "median": round(float(valid.median()), 2),
                            "min": round(float(valid.min()), 2),
                            "max": round(float(valid.max()), 2),
                        }

                    results.append(entry)
                except ValueError:
                    results.append({**fv, "found": False, "error": "Column not found in file"})
                except Exception as e:
                    results.append({**fv, "found": False, "error": str(e)})

            # 汇总
            total_vars = len(results)
            found_vars = sum(1 for r in results if r.get("found") is not False)
            good = sum(1 for r in results if r.get("status") == "good")
            warning = sum(1 for r in results if r.get("status") == "warning")
            critical = sum(1 for r in results if r.get("status") == "critical")

            return {
                "wave": wave,
                "data_source": f"CHARLS {wave} (analysis CSV)",
                "fried_phenotype_variables": results,
                "summary": {
                    "total_variables": total_vars,
                    "found": found_vars,
                    "good_missing_lt_10pct": good,
                    "warning_missing_10_30pct": warning,
                    "critical_missing_gt_30pct": critical,
                    "note": "Biomarker 变量(握力/步速)缺失率高是因为仅 ~50% 受访者同意体检, 但同意者内缺失率较低",
                },
            }

        return {
            "name": "generate_frailty_variable_report",
            "description": "一键生成 CHARLS 指定 wave 的 Fried Phenotype 五项完整变量可用性报告。包含: 变量名、所在文件、总行数、缺失数、缺失率、数值变量的统计摘要。比逐个调用 get_variable_distribution 高效得多",
            "input_schema": {
                "type": "object",
                "properties": {
                    "wave": {"type": "string", "description": "Wave 年份, 如 '2013'"},
                },
                "required": ["wave"],
            },
            "_handler": handler,
        }

    def _get_variable_distribution(self):
        def handler(input: dict) -> dict:
            filepath = input.get("filepath", "")
            column = input.get("column", "")

            full_path = Path(filepath)
            if not full_path.is_absolute() or not full_path.exists():
                full_path = self.charls_dir / "analysis" / filepath

            try:
                with open(full_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    values = []
                    missing = 0
                    for row in reader:
                        val = row.get(column, "")
                        if val == "" or val is None:
                            missing += 1
                        else:
                            values.append(val)

                total = len(values) + missing

                # 尝试数值分析
                numeric_vals = []
                for v in values:
                    try:
                        numeric_vals.append(float(v))
                    except ValueError:
                        pass

                result = {
                    "file": full_path.name,
                    "column": column,
                    "total_rows": total,
                    "non_missing": len(values),
                    "missing": missing,
                    "missing_pct": round(missing / total * 100, 1) if total > 0 else 0,
                }

                if len(numeric_vals) > len(values) * 0.7:  # 大部分是数值
                    import statistics
                    result["type"] = "numeric"
                    result["stats"] = {
                        "mean": round(statistics.mean(numeric_vals), 2),
                        "median": round(statistics.median(numeric_vals), 2),
                        "min": round(min(numeric_vals), 2),
                        "max": round(max(numeric_vals), 2),
                        "std": round(statistics.stdev(numeric_vals), 2) if len(numeric_vals) > 1 else 0,
                    }
                else:
                    # 分类变量
                    from collections import Counter
                    result["type"] = "categorical"
                    value_counts = Counter(values).most_common(15)
                    result["value_counts"] = [
                        {"value": v, "count": c, "pct": round(c / len(values) * 100, 1)}
                        for v, c in value_counts
                    ]

                return result
            except Exception as e:
                return {"error": str(e)}

        return {
            "name": "get_variable_distribution",
            "description": "获取 CHARLS 数据文件中某个变量的分布统计 (数值变量: mean/median/min/max/std; 分类变量: value counts)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "CSV 文件路径"},
                    "column": {"type": "string", "description": "变量列名"},
                },
                "required": ["filepath", "column"],
            },
            "_handler": handler,
        }

    def _read_kb_file(self):
        def handler(input: dict) -> dict:
            relative_path = input.get("path", "")

            # 支持模糊搜索
            filepath = self.vault / relative_path
            if not filepath.exists():
                matches = list(self.vault.glob(f"**/{relative_path}"))
                if matches:
                    filepath = matches[0]
                else:
                    return {"error": f"Knowledge base file not found: {relative_path}"}

            content = filepath.read_text(encoding="utf-8", errors="replace")
            # 解析 frontmatter
            frontmatter, body = {}, content
            fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if fm_match:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(fm_match.group(1)) or {}
                except Exception:
                    pass
                body = content[fm_match.end():]

            return {
                "path": str(filepath.relative_to(self.vault)),
                "frontmatter": frontmatter,
                "body": body[:8000],  # 限制长度
                "total_length": len(content),
                "truncated": len(content) > 8000,
            }

        return {
            "name": "read_kb_file",
            "description": "读取 Obsidian 知识库中的文件。返回 frontmatter 元数据和正文内容。path 支持相对路径或模糊匹配",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "知识库文件路径, 如 'concepts/frailty.md' 或 'datasets/charls.md'"},
                },
                "required": ["path"],
            },
            "_handler": handler,
        }

    def _write_kb_file(self):
        def handler(input: dict) -> dict:
            relative_path = input.get("path", "")
            content = input.get("content", "")
            frontmatter = input.get("frontmatter", None)

            filepath = self.vault / relative_path
            filepath.parent.mkdir(parents=True, exist_ok=True)

            if frontmatter:
                import yaml
                full = "---\n" + yaml.dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n" + content
            else:
                full = content

            filepath.write_text(full, encoding="utf-8")
            return {"success": True, "path": str(filepath.relative_to(self.vault)), "size": len(full)}

        return {
            "name": "write_kb_file",
            "description": "写入文件到 Obsidian 知识库。可以指定 YAML frontmatter",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "知识库中的路径, 如 'literature/2026-zhang-frailty.md'"},
                    "content": {"type": "string", "description": "Markdown 正文内容"},
                    "frontmatter": {"type": "object", "description": "可选的 YAML frontmatter 字典"},
                },
                "required": ["path", "content"],
            },
            "_handler": handler,
        }

    def _write_literature_note(self):
        def handler(input: dict) -> dict:
            title = input.get("title", "Untitled")
            first_author = input.get("first_author", "unknown")
            year = input.get("year", datetime.now().year)
            journal = input.get("journal", "")
            doi = input.get("doi", "")
            topics = input.get("topics", [])
            one_liner = input.get("one_liner", "")
            technical_details = input.get("technical_details", {})
            actionable = input.get("actionable", [])
            gaps = input.get("gaps", [])
            detailed_notes = input.get("detailed_notes", "")

            topic_slug = topics[0] if topics else "general"
            filename = f"literature/{year}-{first_author.lower().replace(' ', '-')}-{topic_slug}.md"

            frontmatter = {
                "type": "literature",
                "title": title,
                "first_author": first_author,
                "year": year,
                "journal": journal,
                "doi": doi,
                "topics": topics,
                "status": "read",
                "relevance_score": input.get("relevance_score", 4),
                "date_read": datetime.now().strftime("%Y-%m-%d"),
                "tags": topics,
            }

            body_parts = [
                f"# {title}",
                f"**{first_author} et al., {journal}, {year}**",
                f"DOI: [{doi}](https://doi.org/{doi})" if doi else "",
                "",
                "## 一句话核心",
                f"> {one_liner}",
                "",
                "## 技术细节",
                f"- **数据**: {technical_details.get('data_source', '')} (N={technical_details.get('sample_size', '')})",
                f"- **方法**: {technical_details.get('method', '')}",
                f"- **结局**: {technical_details.get('outcome', '')}",
                f"- **关键结果**: {technical_details.get('key_result', '')}",
                f"- **验证**: {technical_details.get('validation', '')}",
                "",
                "## 与我们的关系",
            ]
            if actionable:
                body_parts.append("### 可借鉴")
                for a in actionable:
                    body_parts.append(f"- {a}")
            if gaps:
                body_parts.append("### 可改进 (研究缺口)")
                for g in gaps:
                    body_parts.append(f"- {g}")
            if detailed_notes:
                body_parts.append(f"\n## 详细笔记\n{detailed_notes}")

            content = "\n".join(body_parts)

            filepath = self.vault / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            import yaml
            full = "---\n" + yaml.dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n" + content
            filepath.write_text(full, encoding="utf-8")

            return {
                "success": True,
                "path": filename,
                "frontmatter": frontmatter,
                "preview": content[:500],
            }

        return {
            "name": "write_literature_note",
            "description": "将一篇文献的结构化笔记写入 Obsidian 知识库。自动生成标准格式的 YAML frontmatter + Markdown",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "论文标题"},
                    "first_author": {"type": "string", "description": "第一作者姓氏"},
                    "year": {"type": "integer", "description": "发表年份"},
                    "journal": {"type": "string", "description": "期刊名"},
                    "doi": {"type": "string", "description": "DOI"},
                    "topics": {"type": "array", "items": {"type": "string"}, "description": "主题标签, 如 ['frailty_prediction', 'charls']"},
                    "one_liner": {"type": "string", "description": "一句话核心发现"},
                    "technical_details": {"type": "object", "description": "{data_source, sample_size, method, outcome, key_result, validation}"},
                    "actionable": {"type": "array", "items": {"type": "string"}, "description": "可借鉴的点"},
                    "gaps": {"type": "array", "items": {"type": "string"}, "description": "可改进的方向"},
                    "detailed_notes": {"type": "string", "description": "详细笔记"},
                    "relevance_score": {"type": "integer", "description": "相关度评分 1-5"},
                },
                "required": ["title", "first_author", "year", "one_liner"],
            },
            "_handler": handler,
        }

    def _search_knowledge_base(self):
        def handler(input: dict) -> dict:
            query = input.get("query", "").lower()
            topic_filter = input.get("topic", "")
            kb_type = input.get("type", "")

            # 将查询拆分为关键词，匹配任意一个即可
            keywords = query.split() if query else []

            results = []
            for md_file in self.vault.rglob("*.md"):
                if ".obsidian" in str(md_file) or "templates" in str(md_file):
                    continue
                try:
                    content = md_file.read_text(encoding="utf-8", errors="replace")
                    content_lower = content.lower()

                    # 关键词匹配: 至少一个关键词匹配
                    if keywords and not any(kw in content_lower for kw in keywords):
                        continue

                    frontmatter, _ = self._parse_frontmatter(content)
                    ftype = frontmatter.get("type", "unknown")
                    if kb_type and ftype != kb_type:
                        continue
                    if topic_filter and topic_filter not in str(frontmatter.get("topics", [])):
                        continue

                    results.append({
                        "path": str(md_file.relative_to(self.vault)),
                        "type": ftype,
                        "title": frontmatter.get("title", frontmatter.get("name", md_file.stem)),
                        "topics": frontmatter.get("topics", []),
                        "snippet": content_lower[frontmatter_end(content):][:300].strip() if frontmatter.get("type") else content_lower[:300],
                    })
                except Exception:
                    continue

                if len(results) >= 20:
                    break

            return {"query": query, "count": len(results), "results": results}

        return {
            "name": "search_knowledge_base",
            "description": "在 Obsidian 知识库中搜索。可按 query (关键词)、type (literature/project/concept/method/data_source) 过滤",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "type": {"type": "string", "description": "过滤类型: literature, project, concept, method, data_source"},
                    "topic": {"type": "string", "description": "过滤主题标签, 如 'frailty_prediction'"},
                },
                "required": [],
            },
            "_handler": handler,
        }

    def _update_project_status(self):
        def handler(input: dict) -> dict:
            project_id = input.get("project_id", "")
            new_status = input.get("status", "")
            next_actions = input.get("next_actions", [])

            filepath = self.vault / f"projects/{project_id}/project-brief.md"
            if not filepath.exists():
                return {"error": f"Project not found: {project_id}"}

            content = filepath.read_text(encoding="utf-8")
            import yaml

            fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not fm_match:
                return {"error": "No frontmatter found"}

            frontmatter = yaml.safe_load(fm_match.group(1)) or {}
            frontmatter["status"] = new_status
            frontmatter["last_updated"] = datetime.now().strftime("%Y-%m-%d")
            if next_actions:
                frontmatter["next_actions"] = next_actions

            body = content[fm_match.end():]
            new_content = "---\n" + yaml.dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n" + body
            filepath.write_text(new_content, encoding="utf-8")

            return {"success": True, "project_id": project_id, "new_status": new_status}

        return {
            "name": "update_project_status",
            "description": "更新研究项目的状态 (proposed/protocol/execution/writing/submitted/published)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "项目 ID"},
                    "status": {"type": "string", "description": "新状态"},
                    "next_actions": {"type": "array", "items": {"type": "string"}, "description": "下一步行动"},
                },
                "required": ["project_id", "status"],
            },
            "_handler": handler,
        }

    def _verify_doi(self):
        """通过 CrossRef API 验证单个 DOI 是否真实存在"""
        def handler(input: dict) -> dict:
            doi = input.get("doi", "").strip()
            # 标准化 DOI
            doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
            if not doi.startswith("10."):
                return {"doi": doi, "valid": False, "error": "Invalid DOI format", "tip": "DOI must start with 10."}

            import urllib.request, json as _json
            url = f"https://api.crossref.org/works/{doi}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "GeriatricsResearchBot/1.0 (mailto:research@example.com)"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = _json.loads(resp.read().decode())
                msg = data.get("message", {})
                return {
                    "doi": doi,
                    "valid": True,
                    "title": msg.get("title", [""])[0],
                    "container": msg.get("container-title", [""])[0] if msg.get("container-title") else None,
                    "publisher": msg.get("publisher", ""),
                    "year": msg.get("published-print", {}).get("date-parts", [[None]])[0][0] or
                            msg.get("created", {}).get("date-parts", [[None]])[0][0],
                    "type": msg.get("type", ""),
                    "author_count": len(msg.get("author", [])),
                    "is_referenced_by_count": msg.get("is-referenced-by-count", 0),
                }
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return {"doi": doi, "valid": False, "error": "DOI not found in CrossRef", "tip": "This DOI does not exist or the paper is not indexed"}
                return {"doi": doi, "valid": False, "error": f"CrossRef API error: HTTP {e.code}"}
            except Exception as e:
                return {"doi": doi, "valid": None, "error": str(e), "tip": "Network error, retry later"}

        return {
            "name": "verify_doi",
            "description": "通过 CrossRef API 验证单个 DOI 是否对应真实论文。返回论文标题、期刊、年份、被引数。用于检测 AI 编造的虚假引用",
            "input_schema": {
                "type": "object",
                "properties": {
                    "doi": {"type": "string", "description": "DOI, 如 10.1093/gerona/56.3.M146 或 https://doi.org/10.1093/gerona/56.3.M146"},
                },
                "required": ["doi"],
            },
            "_handler": handler,
        }

    def _verify_all_dois(self):
        """批量验证参考文献列表中所有 DOI"""
        def handler(input: dict) -> dict:
            dois = input.get("dois", [])
            if isinstance(dois, str):
                # 从文本中提取 DOI
                import re
                dois = re.findall(r'(10\.\d{4,}/[^\s"\']+)', dois)

            results = []
            valid_count = 0
            fake_count = 0
            error_count = 0

            for doi in dois[:50]:  # 限制 50 条
                r = self.tools["verify_doi"][1]({"doi": doi})
                r = __import__('json').loads(r) if isinstance(r, str) else r
                results.append(r)
                if r.get("valid") is True:
                    valid_count += 1
                elif r.get("valid") is False:
                    fake_count += 1
                else:
                    error_count += 1

            return {
                "total": len(results),
                "valid": valid_count,
                "fake": fake_count,
                "error": error_count,
                "pass": fake_count == 0 and error_count < len(results) * 0.1,
                "details": results,
                "summary": f"{valid_count}/{len(results)} verified real, {fake_count} FAKE ⚠️, {error_count} network errors" if fake_count > 0 else f"All {valid_count} DOIs verified ✓",
            }

        return {
            "name": "verify_all_dois",
            "description": "批量验证参考文献 DOI 列表。输入 DOI 列表或包含 DOI 的文本，返回每条的验证结果和汇总统计。标记虚假引用",
            "input_schema": {
                "type": "object",
                "properties": {
                    "dois": {"type": "array", "items": {"type": "string"}, "description": "DOI 列表, 或包含 DOI 的文本字符串"},
                },
                "required": ["dois"],
            },
            "_handler": handler,
        }

    def _check_kb_duplicate(self):
        """检查一篇论文是否已在知识库中 (按 DOI 精确匹配 + 标题模糊匹配)"""
        def handler(input: dict) -> dict:
            doi = input.get("doi", "").strip()
            title = input.get("title", "").strip().lower()
            lit_dir = self.vault / "literature"

            if not lit_dir.exists():
                return {"duplicate": False, "note": "文献目录不存在, 无法查重"}

            # Step 1: DOI 精确匹配
            if doi:
                doi_clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
                for md_file in lit_dir.glob("*.md"):
                    try:
                        content = md_file.read_text(encoding="utf-8", errors="replace")
                        if doi_clean in content or doi in content:
                            return {
                                "duplicate": True,
                                "matched_by": "doi",
                                "existing_file": str(md_file.relative_to(self.vault)),
                            }
                    except Exception:
                        continue

            # Step 2: 标题模糊匹配 (共享词比例 > 0.7)
            if title:
                tw = set(title.split())
                if not tw:
                    return {"duplicate": False}

                for md_file in lit_dir.glob("*.md"):
                    try:
                        content = md_file.read_text(encoding="utf-8", errors="replace")
                        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                        if fm_match:
                            import yaml as _yaml
                            try:
                                fm = _yaml.safe_load(fm_match.group(1)) or {}
                            except Exception:
                                fm = {}
                            existing_title = str(fm.get("title", "")).lower()
                            if existing_title:
                                ew = set(existing_title.split())
                                if ew:
                                    overlap = len(tw & ew)
                                    similarity = overlap / min(len(tw), len(ew))
                                    if similarity > 0.7:
                                        return {
                                            "duplicate": True,
                                            "matched_by": "title_similarity",
                                            "similarity": round(similarity, 2),
                                            "existing_file": str(md_file.relative_to(self.vault)),
                                        }
                    except Exception:
                        continue

            return {"duplicate": False}

        return {
            "name": "check_kb_duplicate",
            "description": "检查一篇论文是否已在知识库中。按 DOI 精确匹配，再按标题模糊匹配 (共享词比例 > 70%)。用于避免重复入库",
            "input_schema": {
                "type": "object",
                "properties": {
                    "doi": {"type": "string", "description": "论文 DOI (可选)"},
                    "title": {"type": "string", "description": "论文标题 (可选, 用于模糊匹配)"},
                },
                "required": [],
            },
            "_handler": handler,
        }


def frontmatter_end(content: str) -> int:
    """找到 YAML frontmatter 结束位置"""
    match = re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL)
    return match.end() if match else 0


# ================================================================
# 绘图工具 (Phase 6 figure generation)
# ================================================================

def _generate_roc_curve(y_true_path: str, y_prob_path: str, output_path: str) -> str:
    """生成 ROC 曲线图"""
    try:
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from sklearn.metrics import roc_curve, auc

        y_true = np.loadtxt(y_true_path) if Path(y_true_path).exists() else None
        y_prob = np.loadtxt(y_prob_path) if Path(y_prob_path).exists() else None

        if y_true is None or y_prob is None:
            return json.dumps({"error": "输入文件不可读"})

        fpr, tpr, _ = roc_curve(y_true, y_prob)
        roc_auc = auc(fpr, tpr)

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(fpr, tpr, 'b-', lw=2, label=f'AUC = {roc_auc:.4f}')
        ax.plot([0, 1], [0, 1], 'k--', lw=1)
        ax.set_xlabel('1 − Specificity')
        ax.set_ylabel('Sensitivity')
        ax.legend(loc='lower right')
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return json.dumps({"status": "ok", "auc": roc_auc, "output": output_path})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _generate_calibration_plot(y_true_path: str, y_prob_path: str, output_path: str) -> str:
    """生成校准曲线图"""
    try:
        import numpy as np
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from sklearn.calibration import calibration_curve

        y_true = np.loadtxt(y_true_path)
        y_prob = np.loadtxt(y_prob_path)
        frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=10)

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(mean_pred, frac_pos, 'o-', lw=2)
        ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Perfect')
        ax.set_xlabel('Predicted Probability')
        ax.set_ylabel('Observed Proportion')
        ax.legend()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return json.dumps({"status": "ok", "output": output_path})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _generate_shap_plot(features_json: str, output_path: str) -> str:
    """生成 SHAP 特征重要性条形图"""
    try:
        import json as _json
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        data = _json.loads(features_json)  # [{"name": "feature", "importance": 0.15}, ...]
        names = [d["name"] for d in data]
        values = [d["importance"] for d in data]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(range(len(values)), values, color='steelblue', edgecolor='white')
        ax.set_yticks(range(len(values)))
        ax.set_yticklabels(names)
        ax.set_xlabel('Mean |SHAP|')
        fig.tight_layout()
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return json.dumps({"status": "ok", "output": output_path})
    except Exception as e:
        return json.dumps({"error": str(e)})


# Tool definitions for registration
FIGURE_TOOLS = {
    "generate_roc_curve": {
        "name": "generate_roc_curve",
        "description": "生成 ROC 曲线 PNG 图。输入 y_true 和 y_prob 的文本文件路径。",
        "input_schema": {
            "type": "object",
            "properties": {
                "y_true_path": {"type": "string", "description": "真实标签文件路径 (每行一个 0/1)"},
                "y_prob_path": {"type": "string", "description": "预测概率文件路径"},
                "output_path": {"type": "string", "description": "输出 PNG 路径"},
            },
            "required": ["y_true_path", "y_prob_path", "output_path"],
        },
        "_handler": _generate_roc_curve,
    },
    "generate_calibration_plot": {
        "name": "generate_calibration_plot",
        "description": "生成校准曲线 PNG 图。",
        "input_schema": {
            "type": "object",
            "properties": {
                "y_true_path": {"type": "string"},
                "y_prob_path": {"type": "string"},
                "output_path": {"type": "string"},
            },
            "required": ["y_true_path", "y_prob_path", "output_path"],
        },
        "_handler": _generate_calibration_plot,
    },
    "generate_shap_plot": {
        "name": "generate_shap_plot",
        "description": "生成 SHAP 特征重要性条形图。输入 JSON: [{\"name\": \"feature\", \"importance\": 0.15}, ...]",
        "input_schema": {
            "type": "object",
            "properties": {
                "features_json": {"type": "string", "description": "JSON 特征重要性列表"},
                "output_path": {"type": "string"},
            },
            "required": ["features_json", "output_path"],
        },
        "_handler": _generate_shap_plot,
    },
}

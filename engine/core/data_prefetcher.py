"""
数据预取器 (Data Prefetcher) — 在 LLM 调用前自动采集所有需要的数据

设计原则:
  数据采集是确定性操作，应该由代码直接执行，而非让 LLM 通过 tool calling 编排。
  LLM 的角色是推理和报告生成，不是数据管道。

工作流程:
  用户请求 → Prefetcher 分析需求 → 执行工具采集数据 → 注入 Agent 上下文 → LLM 生成报告
"""

import re
import json
from pathlib import Path
from typing import Optional


class DataPrefetcher:
    """
    在 LLM Agent 被调用前，自动检测需要什么数据并预先采集。
    采集结果以结构化上下文的形式注入到 Agent 的输入中。
    """

    def __init__(self, tool_registry):
        self.tools = tool_registry

    def prefetch(self, agent_id: str, user_request: str,
                 data_sources: list[str] = None,
                 previous_outputs: dict = None, current_outputs: dict = None) -> str:
        """
        根据 agent 类型、数据源和用户请求，自动采集所需数据。

        Args:
            data_sources: 活跃数据源名称列表, 如 ["CHARLS", "MIMIC-IV"]
            previous_outputs: 上游阶段的 Agent 输出 {agent_id: output_str}
            current_outputs: 当前阶段已完成的 Agent 输出

        Returns:
            注入到 Agent 输入中的上下文字符串
        """
        if data_sources is None:
            data_sources = ["CHARLS"]

        prefetchers = {
            "data-engineer": self._prefetch_data_engineer,
            "research-assistant": self._prefetch_research_assistant,
            "clinical-researcher": self._prefetch_clinical_researcher,
            "computational-biologist": self._prefetch_computational_biologist,
            "biostatistician": self._prefetch_biostatistician,
            "ml-engineer": self._prefetch_ml_engineer,
            "scientific-writer": self._prefetch_scientific_writer,
            "pi": self._prefetch_pi,
        }

        handler = prefetchers.get(agent_id, self._prefetch_generic)
        return handler(user_request,
                       data_sources=data_sources,
                       previous_outputs=previous_outputs or {},
                       current_outputs=current_outputs or {})

    # ================================================================
    # Agent-specific prefetchers
    # ================================================================

    def _prefetch_data_engineer(self, user_request: str,
                                  data_sources: list[str] = None, **kwargs) -> str:
        """数据工程师: 根据活跃数据源自动采集数据 + 知识库参考"""
        parts = []
        if data_sources is None:
            data_sources = ["CHARLS"]

        for ds_name in data_sources:
            ds_config = self.tools.data_sources.get(ds_name)
            if not ds_config:
                parts.append(f"\n⚠️ 未知数据源: {ds_name}\n")
                continue

            category = getattr(ds_config, 'category', 'cohort')
            if category == "cohort":
                parts.append(self._prefetch_cohort(ds_name, user_request))
            elif category == "ehr":
                parts.append(self._prefetch_ehr(ds_name, user_request))
            elif category == "registry":
                parts.append(self._prefetch_registry(ds_name, user_request))

        parts.append("\n---\n")
        parts.append("## 🚨 你的报告必须:\n")
        parts.append("- 表格中的每个数字都来自上面的预采数据, 不准编造\n")
        parts.append("- 变量名使用数据源中的真实编码, 不准自创\n")
        parts.append('- 数据异常标注为「需确认」而非修改数字\n')
        return "\n".join(parts)

    def _prefetch_cohort(self, ds_name: str, user_request: str) -> str:
        """预取队列数据 (CHARLS/CLHLS/HRS 等)"""
        parts = [f"\n## 📊 {ds_name} 数据预采\n"]

        waves = self._detect_waves(user_request)
        # CHARLS 有专用 Fried Phenotype 报告工具
        if ds_name == "CHARLS":
            for wave in waves:
                try:
                    report = json.loads(self.tools.execute(
                        "generate_frailty_variable_report", {"wave": wave}
                    ))

                    # ⭐ 提取关键数字，用极简格式放到最前面
                    vars_summary = []
                    for v in report.get("fried_phenotype_variables", []):
                        if v.get("found") is not False:
                            vars_summary.append(
                                f"`{v['variable']}` ({v['fried_standard']}): "
                                f"总{v['total_rows']}行, 缺失{v['missing']}行 = **{v['missing_pct']}%**"
                            )

                    parts.append(f"\n## 📊 CHARLS {wave} 实测缺失率数据 (只使用以下数字!)\n")
                    parts.append(f"Health_Status文件: 18,455行 | Biomarker文件: 13,169行\n")
                    for s in vars_summary:
                        parts.append(f"- {s}")

                    # 数值变量统计
                    num_stats = []
                    for v in report.get("fried_phenotype_variables", []):
                        if v.get("stats"):
                            s = v["stats"]
                            num_stats.append(f"`{v['variable']}`: mean={s['mean']}, median={s['median']}, range={s['min']}-{s['max']}")
                    if num_stats:
                        parts.append("\n数值变量统计:\n")
                        for ns in num_stats:
                            parts.append(f"- {ns}")

                    parts.append(f"\n数据来源文件:\n")
                    parts.append(f"- `{wave}_Health_Status_and_Functioning.csv` (18,455行)\n")
                    parts.append(f"- `{wave}_Biomarker.csv` (13,169行, 仅到场体检者)\n")

                except Exception as e:
                    parts.append(f"{ds_name} {wave} 数据采集失败: {e}\n")
        else:
            # 非 CHARLS 队列: 用通用工具列出文件
            try:
                files_result = json.loads(self.tools.execute(
                    "list_datasource_files", {"datasource": ds_name}
                ))
                parts.append(f"数据文件数: {files_result.get('count', 0)}\n")
                for f in files_result.get("files", [])[:10]:
                    parts.append(f"- {f['filename']} ({f.get('size_mb', '?')}MB)\n")
            except Exception as e:
                parts.append(f"{ds_name} 文件列表失败: {e}\n")

        return "\n".join(parts)

    def _prefetch_ehr(self, ds_name: str, user_request: str) -> str:
        """预取 EHR 数据 (MIMIC-IV 等)"""
        parts = [f"\n## 🏥 {ds_name} EHR 数据预采\n"]

        try:
            files_result = json.loads(self.tools.execute(
                "list_datasource_files", {"datasource": ds_name}
            ))
            parts.append(f"数据目录: {ds_name}\n")
            parts.append(f"文件/模块数: {files_result.get('count', 0)}\n\n")

            # 对于 MIMIC-IV，列出关键模块
            if "MIMIC" in ds_name:
                parts.append("MIMIC-IV 关键模块:\n")
                parts.append("- `hosp/` — 住院信息 (admissions, patients, diagnoses_icd, procedures_icd)\n")
                parts.append("- `icu/` — ICU 信息 (chartevents, labevents, inputevents)\n")
                parts.append("- `ed/` — 急诊信息\n")
                parts.append("- `cxr/` — 胸部 X 光 + 报告\n")
                parts.append("\n常用分析表:\n")

            for f in files_result.get("files", [])[:15]:
                parts.append(f"- `{f['filename']}` ({f.get('size_mb', '?')}MB)\n")

            parts.append("\n")
            # 尝试读取关键表头
            key_files = ["patients.csv", "admissions.csv", "diagnoses_icd.csv"]
            for kf in key_files:
                try:
                    header_result = json.loads(self.tools.execute(
                        "read_datasource_headers",
                        {"datasource": ds_name, "filepath": kf, "n_preview": 2}
                    ))
                    if "error" not in header_result:
                        cols = header_result.get("columns", [])[:15]
                        parts.append(f"`{kf}` ({header_result.get('column_count', '?')} 列): "
                                     f"{', '.join(cols)}...\n")
                except Exception:
                    pass

        except Exception as e:
            parts.append(f"{ds_name} EHR 数据预采失败: {e}\n")

        return "\n".join(parts)

    def _prefetch_registry(self, ds_name: str, user_request: str) -> str:
        """预取癌症登记数据 (SEER 等)"""
        parts = [f"\n## 📋 {ds_name} 登记数据预采\n"]

        try:
            files_result = json.loads(self.tools.execute(
                "list_datasource_files", {"datasource": ds_name}
            ))
            parts.append(f"数据文件数: {files_result.get('count', 0)}\n")
            for f in files_result.get("files", [])[:10]:
                parts.append(f"- {f['filename']} ({f.get('size_mb', '?')}MB)\n")

            parts.append(f"\n提示: {ds_name} 是癌症登记数据库, "
                         f"分析前需指定 cancer site + 诊断年份范围\n")
        except Exception as e:
            parts.append(f"{ds_name} 登记数据预采失败: {e}\n")

        return "\n".join(parts)

    def _prefetch_research_assistant(self, user_request: str,
                                       data_sources: list[str] = None,
                                       previous_outputs: dict = None,
                                       **kwargs) -> str:
        """科研助理: 自动搜索知识库 + 注入选题文献预检任务"""
        parts = ["\n## 📚 知识库搜索结果 (Prefetched)\n"]

        # 搜索知识库
        try:
            results = json.loads(self.tools.execute("search_knowledge_base", {
                "query": user_request[:100]
            }))
            parts.append(f"找到 {results.get('count', 0)} 个相关文件:\n")
            for r in results.get("results", [])[:10]:
                parts.append(f"- `{r['path']}` [{r['type']}] {r.get('title', '')}\n")
            parts.append("")
        except Exception:
            parts.append("(知识库搜索未返回结果)\n")

        # 模板参考
        try:
            tmpl = json.loads(self.tools.execute("read_kb_file", {
                "path": "templates/t-literature-note.md"
            }))
            parts.append("### 文献笔记模板\n")
            parts.append(tmpl.get("body", "")[:800] + "\n")
        except Exception:
            pass

        # ⭐ 选题文献预检提示: 如果是新项目提案, 给出 WebSearch 检索式建议
        parts.append("\n## 🔍 选题文献预检 — 检索式建议 (用于 WebSearch)\n")
        parts.append("如果此任务是评估新研究方向的可行性, 请使用以下检索式模板:\n")
        parts.append("1. PubMed: `([P关键词]) AND ([O关键词]) AND ([M关键词]) AND prediction`\n")
        parts.append("2. arXiv/medRxiv: `[O关键词] [M关键词] recent advances 2025 2026`\n")
        parts.append("3. 跨队列: `[O关键词] prediction AND (cohort OR registry) AND machine learning`\n")
        parts.append("4. 高分综述缺口: `[P关键词] AND review AND (future directions OR research gap OR unmet need) 2025 2026`\n")
        parts.append("⚠️ **时效性要求**: 优先近 5 年文献 (当前年份 - 5), 经典方法学文献除外\n")
        parts.append("提取 top 3-5 最相似论文的: 数据源/样本量/方法/AUC/验证策略\n")
        parts.append("输出《选题文献预检报告》交 PI 做 FRAME 评估的 F 维度输入。\n")

        parts.append("---\n")
        parts.append("**你的任务**: 基于以上信息, 完成文献扫描/综述/笔记生成。可调用 `write_literature_note` 写入 Obsidian。")
        return "\n".join(parts)

    def _prefetch_clinical_researcher(self, user_request: str,
                                        data_sources: list[str] = None, **kwargs) -> str:
        """临床研究员: 读取相关的临床概念和数据源信息"""
        parts = ["\n## 🏥 临床知识库上下文 (Prefetched)\n"]

        # 检测需要的概念
        concepts = []
        concept_map = {
            "衰弱": "frailty", "fried": "frailty", "frailty": "frailty",
            "肌少症": "sarcopenia", "sarcopenia": "sarcopenia",
            "表观遗传": "epigenetic-clocks", "衰老时钟": "epigenetic-clocks",
            "epigenetic": "epigenetic-clocks",
        }
        req_lower = user_request.lower()
        for keyword, concept_file in concept_map.items():
            if keyword in req_lower and concept_file not in concepts:
                concepts.append(concept_file)

        for concept in concepts:
            try:
                r = json.loads(self.tools.execute("read_kb_file", {
                    "path": f"concepts/{concept}.md"
                }))
                parts.append(f"### 概念参考: {concept}\n")
                parts.append(r.get("body", "")[:2000] + "\n")
            except Exception:
                pass

        # 活跃数据源的知识库参考 (所有数据源均可使用)
        if data_sources:
            for ds_name in data_sources:
                kb_path = f"datasets/{ds_name.lower().replace(' ', '-')}.md"
                try:
                    r = json.loads(self.tools.execute("read_kb_file", {
                        "path": kb_path
                    }))
                    parts.append(f"### {ds_name} 数据源参考\n")
                    parts.append(r.get("body", "")[:1500] + "\n")
                except Exception:
                    pass

        if not concepts:
            parts.append("(根据请求关键词自动读取相关概念文件)\n")

        parts.append("---\n")
        parts.append("**你的任务**: 基于以上临床知识, 回答用户问题。可以调用 `search_knowledge_base` 补充信息。")
        return "\n".join(parts)

    def _prefetch_computational_biologist(self, user_request: str, **kwargs) -> str:
        """计算生物学家: 读取方法学参考"""
        parts = ["\n## 🔬 方法学参考 (Prefetched)\n"]

        refs = []
        if any(w in user_request.lower() for w in ["模型", "预测", "机器学习", "model", "predict", "ml"]):
            refs.append("methods/model-selection-guide.md")
        if any(w in user_request.lower() for w in ["因果", "causal"]):
            refs.append("methods/causal-inference-choices.md")
        if any(w in user_request.lower() for w in ["omop", "标准化"]):
            refs.append("methods/omop-cdm-mapping.md")

        for ref in refs:
            try:
                r = json.loads(self.tools.execute("read_kb_file", {"path": ref}))
                parts.append(f"### {ref}\n")
                parts.append(r.get("body", "")[:2000] + "\n")
            except Exception:
                pass

        if not refs:
            try:
                r = json.loads(self.tools.execute("read_kb_file", {
                    "path": "methods/model-selection-guide.md"
                }))
                parts.append(r.get("body", "")[:2000] + "\n")
            except Exception:
                pass

        parts.append("---\n")
        parts.append("**你的任务**: 基于方法学参考 + 上游 Agent 输出, 设计方案。可以调用 `read_kb_file` 补充。")
        return "\n".join(parts)

    def _prefetch_biostatistician(self, user_request: str, **kwargs) -> str:
        """统计学家: 读取统计方法参考"""
        parts = ["\n## 📈 统计参考 (Prefetched)\n"]
        try:
            r = json.loads(self.tools.execute("read_kb_file", {
                "path": "methods/causal-inference-choices.md"
            }))
            parts.append(r.get("body", "")[:1500] + "\n")
        except Exception:
            pass
        parts.append("---\n")
        parts.append("**你的任务**: 基于统计方法知识 + 上游输出, 撰写 SAP 或给出统计建议。")
        return "\n".join(parts)

    def _prefetch_ml_engineer(self, user_request: str, **kwargs) -> str:
        """ML工程师: 读取方法学 + 项目实验记录"""
        parts = ["\n## 🛠 ML 工程上下文 (Prefetched)\n"]
        try:
            r = json.loads(self.tools.execute("read_kb_file", {
                "path": "methods/model-selection-guide.md"
            }))
            parts.append(r.get("body", "")[:2000] + "\n")
        except Exception:
            pass
        parts.append("---\n")
        parts.append("**你的任务**: 基于方法学指南 + 建模方案, 实现代码。")
        return "\n".join(parts)

    def _prefetch_scientific_writer(self, user_request: str,
                                     previous_outputs: dict = None,
                                     current_outputs: dict = None) -> str:
        """学术写作: 从上游输出提取关键数字 + 读取模板和作者信息"""
        import re
        parts = ["\n## ✍️ 写作上下文 (Prefetched)\n"]

        # 1. 合并所有上游输出
        all_upstream = {}
        if previous_outputs:
            all_upstream.update(previous_outputs)
        if current_outputs:
            all_upstream.update(current_outputs)

        if all_upstream:
            all_text = "\n".join(all_upstream.values())

            parts.append("### 📊 从上游分析结果中自动提取的关键数字\n")
            parts.append("> 以下数字从上游 Agent 输出中自动提取。"
                         "**撰写论文时必须使用这些数字**，不得修改或估算。\n")

            extracted = []

            # AUC / C-index / AUROC (含可选 CI)
            for m in re.finditer(
                r'(?:AUC|AUROC|C-index|C-statistic)\s*[:=]?\s*(0?\.\d+)'
                r'\s*(?:\(?\s*(?:95%?\s*CI)?[:\s]*([0-9.]+)[-–]([0-9.]+))?',
                all_text, re.IGNORECASE
            ):
                ci_part = f" (95% CI: {m.group(2)}-{m.group(3)})" if m.group(2) else ""
                extracted.append(f"- AUC/C-index: **{m.group(1)}**{ci_part}")

            # 样本量
            for m in re.finditer(r'(?:N|n|sample[_\s]?size)\s*[:=]\s*([\d,]+)', all_text, re.IGNORECASE):
                extracted.append(f"- 样本量: **{m.group(1)}**")

            # 缺失率
            for m in re.finditer(r'(?:缺失率|missing[_\s]?(?:rate|pct))\s*[:=]?\s*([0-9.]+)%', all_text, re.IGNORECASE):
                extracted.append(f"- 缺失率: **{m.group(1)}%**")

            # 常见分类指标
            for metric in ['Accuracy', 'Sensitivity', 'Specificity', 'Precision', 'F1', 'Recall', 'NPV', 'PPV']:
                for m in re.finditer(rf'\b{metric}\s*[:=]\s*(0?\.?\d+)', all_text, re.IGNORECASE):
                    extracted.append(f"- {metric}: **{m.group(1)}**")

            # 去重输出
            seen = set()
            for item in extracted:
                if item not in seen:
                    parts.append(item + "\n")
                    seen.add(item)

            if not extracted:
                parts.append("_(未从上游输出中自动检测到关键数字，请从下方上游输出中手动提取)_\n")

            # 上游数据可用性概览
            parts.append("\n### 📋 上游数据来源\n")
            for src_name, src_output in all_upstream.items():
                parts.append(f"- `{src_name}`: {len(src_output)} 字符\n")
            parts.append("")

        # 2. 读取作者信息 (系统提示中已有，这里作为显式确认)
        try:
            r = json.loads(self.tools.execute("read_kb_file", {
                "path": "reference/author-info.md"
            }))
            parts.append("### 👥 作者信息 (从知识库读取)\n")
            parts.append(r.get("body", "")[:600] + "\n")
        except Exception:
            pass

        # 3. 读取文献笔记模板
        try:
            r = json.loads(self.tools.execute("read_kb_file", {
                "path": "templates/t-literature-note.md"
            }))
            parts.append("### 📝 文献笔记模板参考\n")
            parts.append(r.get("body", "")[:800] + "\n")
        except Exception:
            pass

        parts.append("---\n")
        parts.append("**你的任务**: 基于以上自动提取的分析数据和上游输出，撰写论文。"
                     "所有数字必须来自上游分析结果，不得编造或估算。")
        return "\n".join(parts)

    def _prefetch_pi(self, user_request: str, **kwargs) -> str:
        """PI: 获取项目状态"""
        parts = ["\n## 👔 项目上下文 (Prefetched)\n"]
        parts.append("可以调用 `read_kb_file` 查看项目状态, `search_knowledge_base` 了解领域动态。\n")
        return "\n".join(parts)

    def _prefetch_generic(self, user_request: str, **kwargs) -> str:
        return ""

    # ================================================================
    # Helpers
    # ================================================================

    def _detect_waves(self, user_request: str) -> list[str]:
        """从用户请求中检测需要查询的 CHARLS wave"""
        waves = []
        req = user_request.lower()
        patterns = [
            (r'2011', '2011'), (r'2013', '2013'), (r'2015', '2015'),
            (r'2018', '2018'), (r'2020', '2020'),
        ]
        for pattern, wave in patterns:
            if re.search(pattern, req) and wave not in waves:
                waves.append(wave)

        # 如果用户没有指定 wave，默认 2013+2015
        if not waves:
            waves = ["2013", "2015"]

        return waves

    def build_data_report(self, wave: str = "2013") -> str:
        """生成完整的 Markdown 数据可用性报告 (不通过 LLM)"""
        try:
            report = json.loads(self.tools.execute(
                "generate_frailty_variable_report", {"wave": wave}
            ))
        except Exception as e:
            return f"# 数据报告生成失败\n\n错误: {e}"

        lines = [
            f"# CHARLS {wave} — Fried Phenotype 变量可用性报告",
            f"\n> 报告生成时间: 自动采集 | 数据引擎直接生成 (非 LLM)",
            f"\n## 数据源",
            f"- `{wave}_Health_Status_and_Functioning.csv` — 18,455 行",
            f"- `{wave}_Biomarker.csv` — 13,169 行 (仅到场体检者)",
            f"\n## 缺失率总览\n",
            f"| Fried 标准 | 变量名 | 文件 | 总行数 | 缺失数 | 缺失率 | 状态 |",
            f"|-----------|--------|------|--------|--------|--------|------|",
        ]

        for v in report.get("fried_phenotype_variables", []):
            if v.get("found") is False:
                lines.append(f"| {v.get('fried_standard', '?')} | `{v['var']}` | - | - | - | - | ❌ |")
            else:
                status = {"good": "🟢", "warning": "🟡", "critical": "🔴"}.get(v.get("status", ""), "⚪")
                lines.append(
                    f"| {v['fried_standard']} | `{v['variable']}` | {v['file']} | "
                    f"{v['total_rows']} | {v['missing']} | **{v['missing_pct']}%** | {status} |"
                )

        # 数值统计
        num_vars = [v for v in report.get("fried_phenotype_variables", [])
                     if v.get("stats")]
        if num_vars:
            lines.append(f"\n## 数值变量统计\n")
            lines.append(f"| 变量 | 均值 | 中位数 | 最小值 | 最大值 |")
            lines.append(f"|------|------|--------|--------|--------|")
            for v in num_vars:
                s = v["stats"]
                lines.append(f"| `{v['variable']}` | {s['mean']} | {s['median']} | {s['min']} | {s['max']} |")

        # 汇总
        summary = report.get("summary", {})
        lines.append(f"\n## 汇总\n")
        lines.append(f"- 总变量: {summary.get('total_variables', '?')}")
        lines.append(f"- 良好 (<10%缺失): {summary.get('good_missing_lt_10pct', '?')}")
        lines.append(f"- 警告 (10-30%): {summary.get('warning_missing_10_30pct', '?')}")
        lines.append(f"- 严重 (>30%): {summary.get('critical_missing_gt_30pct', '?')}")
        if summary.get("note"):
            lines.append(f"\n> {summary['note']}")

        lines.append(f"\n## 数据质量警告\n")
        # 自动标注异常
        if any(v.get("missing_pct", 0) > 40 for v in report.get("fried_phenotype_variables", [])):
            lines.append("- 🔴 部分变量缺失率 >40%，需用多重插补或敏感性分析")
        for v in report.get("fried_phenotype_variables", []):
            if v.get("variable") == "qg003" and v.get("missing_pct", 0) > 40:
                lines.append(f"- ⚠️ 步速 `qg003` 缺失率 {v['missing_pct']}% — 仅部分受访者做步行测试，缺失非随机")
            if v.get("variable") == "da050" and v.get("missing_pct", 0) < 10:
                lines.append(f"- ✅ `da050` 缺失率仅 {v['missing_pct']}% — 推荐作为体力活动简化指标")

        lines.append(f"\n## 分析建议\n")
        lines.append(f"1. 握力: 使用 qc003-qc006 最大值, 缺失仅~2.5%, N≈12,600")
        lines.append(f"2. 步速: 使用 qg003, 步速=3.0/qg003 m/s, N≈6,400")
        lines.append(f"3. 体力活动: 使用 da050 二分类 (有/无活动), 缺失<5%")
        lines.append(f"4. 完整 Fried 五项: N≈5,000-6,000 (受步速限制)")
        lines.append(f"5. ⚠️ 清洗规则: qc*/qg*/qi*/ql*/qm* 列中 ≥900 的值替换为 NaN")

        return "\n".join(lines)

    def _format_variable_report(self, report: dict) -> str:
        """将变量报告格式化为 Markdown 表格"""
        lines = []
        summary = report.get("summary", {})
        lines.append(f"**总体**: {summary.get('total_variables', '?')} 个变量, "
                     f"良好(<10%): {summary.get('good_missing_lt_10pct', '?')}, "
                     f"警告(10-30%): {summary.get('warning_missing_10_30pct', '?')}, "
                     f"严重(>30%): {summary.get('critical_missing_gt_30pct', '?')}\n")

        lines.append("| Fried 标准 | 变量名 | 总行数 | 缺失数 | 缺失率 | 状态 |")
        lines.append("|-----------|--------|--------|--------|--------|------|")
        for v in report.get("fried_phenotype_variables", []):
            if v.get("found") is False:
                lines.append(f"| {v.get('fried_standard', '?')} | {v.get('var', '?')} | - | - | - | ❌ 未找到 |")
            else:
                status = {"good": "🟢", "warning": "🟡", "critical": "🔴"}.get(v.get("status", ""), "⚪")
                lines.append(f"| {v.get('fried_standard', '?')} | `{v.get('variable', '?')}` | "
                             f"{v.get('total_rows', '?')} | {v.get('missing', '?')} | "
                             f"**{v.get('missing_pct', '?')}%** | {status} |")

        # 数值变量统计
        num_vars = [v for v in report.get("fried_phenotype_variables", [])
                     if v.get("type") == "numeric" and "stats" in v]
        if num_vars:
            lines.append("\n**数值变量统计摘要**:\n")
            lines.append("| 变量 | 均值 | 中位数 | 范围 |")
            lines.append("|------|------|--------|------|")
            for v in num_vars:
                s = v["stats"]
                lines.append(f"| `{v['variable']}` | {s.get('mean', '?')} | {s.get('median', '?')} | "
                             f"{s.get('min', '?')}-{s.get('max', '?')} |")

        # 备注
        if summary.get("note"):
            lines.append(f"\n> ℹ️ {summary['note']}")

        return "\n".join(lines) + "\n"

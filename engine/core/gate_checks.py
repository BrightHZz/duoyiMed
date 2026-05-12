"""
自动化闸门检查函数集 — Gate Check Functions

每个 check 函数签名: (outputs: dict, orchestrator) -> (passed: bool, detail: str)

outputs: {agent_id: output_str} — 当前 Phase 的所有 Agent 输出
orchestrator: ResearchOrchestrator 实例 (用于访问配置和 LLM)

所有函数独立、无副作用, 可安全并行执行。

闸门检查分为三类:
- 静态阈值检查: AUC >= 0.70, 参考文献 >= 25, DOI 验证 等
- 趋势检查 (Δ-Gate): 监控指标变化方向, 提前预警性能恶化
- 跨Phase一致性检查: 特征稳定性 等
"""

import re
from typing import Callable, Optional


def check_literature_precheck_exists(outputs: dict, orch) -> tuple:
    """文献预检报告已生成 (research-assistant 产出)"""
    for agent_id, output in outputs.items():
        if "research-assistant" in agent_id.lower():
            if any(kw in output for kw in ["文献预检", "选题文献", "对标论文", "文献检索"]):
                # 尝试数引用数
                ref_count = len(re.findall(r'\[\d+\]|\(\d{4}\)', output))
                if ref_count >= 3:
                    return True, f"文献预检报告已生成 (≥{ref_count} 篇引用)"
                return False, f"文献预检报告引用不足 (仅 {ref_count} 篇, 需 ≥3)"
            return False, "research-assistant 输出中未找到文献预检内容"
    return False, "未找到 research-assistant 的输出"


def check_frame_assessment_complete(outputs: dict, orch) -> tuple:
    """FRAME 五维评估完整"""
    pi_output = ""
    for agent_id, output in outputs.items():
        if "pi" in agent_id.lower():
            pi_output = output
            break
    if not pi_output:
        return False, "未找到 PI 的 FRAME 评估输出"

    required_dims = ["F", "R", "A", "M", "E"]
    # 检查 key phrases (中英文)
    dim_patterns = {
        "F": ["F", "Field", "领域扫描", "field scan"],
        "R": ["R", "Resource", "资源审计", "resource audit"],
        "A": ["A", "Alignment", "对齐检查", "alignment"],
        "M": ["M", "Market", "发表缺口", "market gap"],
        "E": ["E", "Edge", "优势评估", "edge"],
    }
    missing = []
    for dim, patterns in dim_patterns.items():
        if not any(p in pi_output for p in patterns):
            missing.append(dim)
    if missing:
        return False, f"FRAME 评估缺少维度: {missing}"
    return True, "FRAME 五维评估完整"


def check_data_availability_confirmed(outputs: dict, orch) -> tuple:
    """数据可用性已确认 (data-engineer 产出 DQ-CARE 报告)"""
    for agent_id, output in outputs.items():
        if "data-engineer" in agent_id.lower():
            if "DQ" in output or "数据质量" in output or "缺失率" in output:
                return True, "数据可用性报告已生成"
            return False, "data-engineer 输出中未找到数据质量评估"
    return True, "跳过 (无 data-engineer 输出)"


# --- Phase 3: 内部验证 ---

def check_auc_threshold(outputs: dict, orch) -> tuple:
    """AUC >= 0.70 (分类模型最低可接受阈值)"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            # 匹配各种 AUC 写法: AUC=0.82, auc_roc: 0.82, AUC 0.82, etc.
            auc_patterns = [
                r'(?:auc.?roc|auc|AUC)[^0-9]*0?\.(\d+)',
                r'c.?statistic[^0-9]*0?\.(\d+)',
            ]
            for pat in auc_patterns:
                matches = re.findall(pat, output.lower())
                if matches:
                    auc_val = float(f"0.{matches[0]}")
                    if auc_val >= 0.70:
                        return True, f"AUC={auc_val:.3f} >= 0.70"
                    return False, f"AUC={auc_val:.3f} < 0.70, 模型区分度不足"
    return True, "跳过 (未检测到 AUC 值, 可能为非分类任务)"


def check_baseline_included(outputs: dict, orch) -> tuple:
    """Baseline 模型已包含 (LR 或 Cox PH)"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            has_lr = any(w in output.lower() for w in [
                "logisticregression", "logistic regression", "logistic",
            ])
            has_cox = any(w in output.lower() for w in [
                "coxph", "cox ph", "cox proportional", "cox regression",
            ])
            if has_lr or has_cox:
                return True, "Baseline 模型已包含"
            return False, "缺少 baseline (Logistic Regression / Cox PH)"
    return True, "跳过 (无 ml-engineer 输出)"


def check_n_jobs_safe(outputs: dict, orch) -> tuple:
    """n_jobs 安全 (≤ 2)"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            dangerous = re.findall(r'n_jobs\s*[=:]\s*(-?\d+)', output)
            for val in dangerous:
                n = int(val)
                if n == -1 or n > 2:
                    return False, f"n_jobs={n} (应 ≤ 2, M4 24GB 约束)"
            return True, "n_jobs 安全 (≤ 2)"
    return True, "跳过 (无 ml-engineer 输出)"


# --- Phase 6: 论文撰写 ---

def check_title_length(outputs: dict, orch) -> tuple:
    """Title ≤ 15 词 (含关键词, 不含结论)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            import re
            # Extract title: first ## heading, or the first line after the YAML block
            title_match = re.search(
                r'(?:^#\s+)(.+?)(?:\n|$)',
                output, re.MULTILINE
            )
            if not title_match:
                # Try finding title in the "Title:" metadata
                title_match = re.search(r'(?:Title|title)[:：]\s*(.+?)(?:\n|$)', output)
            if title_match:
                title = title_match.group(1).strip()
                word_count = len(title.split())
                if word_count <= 15:
                    return True, f"Title {word_count} 词 ≤ 15 词 ✓"
                return False, (
                    f"Title 超出 15 词限制 ({word_count} 词): "
                    f"\"{title[:80]}{'...' if len(title)>80 else ''}\""
                )
            return True, "跳过 (未检测到 Title)"
    return True, "跳过"


def check_sections_exist(outputs: dict, orch) -> tuple:
    """检查 sections/ 目录下是否有完整的 IMRAD 分章节文件"""
    import os
    from pathlib import Path
    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id，无法检查 sections 目录)"

    # 尝试从 knowledge base 或 outputs 定位项目目录
    possible_dirs = []
    if hasattr(orch, 'kb') and orch.kb:
        for vault_name, vault_path in getattr(orch.kb, 'vaults', {}).items():
            projects_dir = Path(vault_path) / 'projects'
            if (projects_dir / project_id).exists():
                possible_dirs.append(projects_dir / project_id)
    # fallback: check outputs/baselines for project path
    baseline_dir = getattr(orch, 'baseline_manager', None)
    if baseline_dir:
        possible_dirs.append(Path(baseline_dir.base_dir).parent / project_id)

    for proj_dir in possible_dirs:
        # sections/ 是零件工作目录
        for sections_rel in ['sections']:
            sections_dir = proj_dir / sections_rel
            if sections_dir.exists():
                section_files = list(sections_dir.glob('*.md'))
                # Check for key IMRAD sections
                required_keywords = ['title', 'abstract', 'intro', 'method', 'result', 'discussion', 'conclusion']
                found = set()
                for f in section_files:
                    fname = f.name.lower()
                    for kw in required_keywords:
                        if kw in fname:
                            found.add(kw)
                if len(found) >= 6:
                    return True, f"{sections_rel}/ 目录存在, 含 {len(section_files)} 个文件 ({len(found)}/7 核心章节)"
                elif len(section_files) >= 3:
                    return False, f"{sections_rel}/ 目录文件不足 (仅 {len(section_files)} 个, 需 ≥6 个 IMRAD 分节文件)"
                else:
                    return False, f"{sections_rel}/ 目录几乎为空 ({len(section_files)} 文件)"
    return False, "未找到项目的 sections/ 目录, Phase 6 必须产出分章节文件"


def check_tables_exist(outputs: dict, orch) -> tuple:
    """检查 tables/ 目录下是否有 Table 1/2/3"""
    import os
    from pathlib import Path
    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    if hasattr(orch, 'kb') and orch.kb:
        for vault_name, vault_path in getattr(orch.kb, 'vaults', {}).items():
            proj_dir = Path(vault_path) / 'projects' / project_id
            # tables/ 是零件工作目录
            for tables_rel in ['tables']:
                tables_dir = proj_dir / tables_rel
                if tables_dir.exists():
                    table_files = list(tables_dir.glob('*.md'))
                    if len(table_files) >= 3:
                        return True, f"{tables_rel}/ 目录存在, 含 {len(table_files)} 个表格文件"
                    elif len(table_files) >= 1:
                        return False, f"{tables_rel}/ 目录文件不足 (仅 {len(table_files)} 个, 需 ≥3: Table 1/2/3)"
                    else:
                        return False, f"{tables_rel}/ 目录为空"
    return False, "未找到项目的 tables/ 目录, Phase 6 必须产出 Table 1/2/3"


def check_figures_exist(outputs: dict, orch) -> tuple:
    """检查 figures/ 目录下是否有至少 4 张图表 (ROC/校准/SHAP/DCA)"""
    import os
    from pathlib import Path
    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    if hasattr(orch, 'kb') and orch.kb:
        for vault_name, vault_path in getattr(orch.kb, 'vaults', {}).items():
            proj_dir = Path(vault_path) / 'projects' / project_id
            # figures/ 是零件工作目录
            for figures_rel in ['figures']:
                figures_dir = proj_dir / figures_rel
                if figures_dir.exists():
                    image_files = list(figures_dir.glob('*.png')) + list(figures_dir.glob('*.jpg'))
                    caption_files = list(figures_dir.glob('*caption*.md'))
                    total_visual = len(image_files) + len([f for f in caption_files if 'fig' in f.name.lower()])
                    if len(image_files) >= 3:
                        return True, f"{figures_rel}/ 目录存在, 含 {len(image_files)} 张图片 + {len(caption_files)} 个图注"
                    elif total_visual >= 4:
                        return True, f"{figures_rel}/ 目录存在, 含 {total_visual} 个视觉元素"
                    else:
                        return False, f"{figures_rel}/ 目录内容不足 (仅 {len(image_files)} 图片, 需 ≥3: ROC/校准/SHAP/DCA)"
    return False, "未找到项目的 figures/ 目录, Phase 6 必须产出至少 4 张图表"


def check_manuscript_assembled(outputs: dict, orch) -> tuple:
    """检查 manuscript.md 是否存在且包含所有 IMRAD 章节"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            # Check the output string for complete IMRAD structure
            required_sections = [
                ("abstract", "## Abstract"),
                ("introduction", "## Introduction"),
                ("methods", "## Methods"),
                ("results", "## Results"),
                ("discussion", "## Discussion"),
            ]
            missing = []
            for sec_name, sec_pattern in required_sections:
                if sec_pattern not in output:
                    missing.append(sec_name)
            if missing:
                return False, f"manuscript 缺少 IMRAD 章节: {missing}"
            # Also check for Conclusion (independent ## section)
            if "## Conclusion" not in output:
                return False, "manuscript 缺少独立 ## Conclusion 章节"
            return True, "manuscript.md 结构完整 (IMRAD + Conclusion)"

    # Check filesystem for manuscript.md (投稿层 submission/manuscript.md)
    import os
    from pathlib import Path
    project_id = getattr(orch, '_current_project_id', None)
    if project_id and hasattr(orch, 'kb') and orch.kb:
        for vault_name, vault_path in getattr(orch.kb, 'vaults', {}).items():
            proj_dir = Path(vault_path) / 'projects' / project_id
            for manuscript_rel in ['submission/manuscript.md', 'sections/manuscript.md']:
                manuscript_path = proj_dir / manuscript_rel
                if manuscript_path.exists():
                    content = manuscript_path.read_text()
                    has_imrad = all(s in content for s in ["## Introduction", "## Methods", "## Results", "## Discussion"])
                    if has_imrad:
                        return True, f"manuscript.md ({manuscript_rel}) 文件存在且结构完整"
    return True, "跳过 (manuscript 在 Agent 输出中, 未检查文件系统)"

def check_conclusion_heading_level(outputs: dict, orch) -> tuple:
    """Conclusion 为 ## 独立章节 (而非 ### 子章节)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            if "### Conclusion" in output and "## Conclusion" not in output:
                return False, "Conclusion 被写为 ### (Discussion 的子章节), 应为 ## (独立章节)"
            if "## Conclusion" in output:
                return True, "Conclusion 为 ## 独立章节 ✓"
            return True, "跳过 (未检测到 Conclusion 内容)"
    return True, "跳过 (无 scientific-writer 输出)"


def check_doi_verification(outputs: dict, orch) -> tuple:
    """DOI 验证通过 (fake DOI = 0)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower():
            if "DOI Verification" not in output:
                return False, "缺少 DOI 验证报告 (投稿前强制步骤)"
            # 检查是否包含 fake DOI
            if re.search(r'❌.*FAKE|fake\s*doi', output, re.IGNORECASE):
                return False, "存在 fake DOI, 须替换后重新验证"
            return True, "DOI 验证通过 (fake=0)"
    return True, "跳过 (无 scientific-writer 输出)"


def check_ref_count(outputs: dict, orch) -> tuple:
    """参考文献数量达标 (论著 ≥ 25)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower():
            # 计数 [1] [2] 格式引用 + DOI 格式引用
            refs = set(re.findall(r'\[\d+\]', output))
            dois = re.findall(r'10\.\d{4,}/[^\s"\']+', output)
            count = max(len(refs), len(dois))
            if count >= 25:
                return True, f"参考文献 {count} 篇 ≥ 25 篇门槛"
            return False, f"参考文献仅 {count} 篇, 需 ≥ 25 篇"
    return True, "跳过 (无 scientific-writer 输出)"


def _load_classic_papers_registry() -> set:
    """加载经典方法学论文注册表, 返回 {(first_author_lastname, year), ...} 的识别集合"""
    import os
    from pathlib import Path

    registry = set()
    registry_path = Path(__file__).parent.parent.parent / "company" / "reference" / "classic-papers.md"
    if not registry_path.exists():
        return registry

    try:
        content = registry_path.read_text()
        # 提取表格中的论文行: | Author et al., Journal YEAR | YEAR | reason |
        import re
        for line in content.split('\n'):
            # 匹配 | Paper Title / Authors | YEAR | ... |
            m = re.match(r'\|\s*(.+?)\s*\|\s*(\d{4})(?:[–-]\d{4})?\s*\|', line)
            if m:
                paper_info = m.group(1).strip()
                year = int(m.group(2))
                # 提取第一作者姓氏
                author_match = re.match(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', paper_info)
                if author_match:
                    first_author = author_match.group(1).split()[-1].lower()
                else:
                    # Fallback: 用前20个字符作为 key
                    first_author = paper_info[:20].strip().lower()
                registry.add((first_author, year))
    except Exception:
        pass
    return registry


def _extract_ref_entries_with_context(ref_text: str, current_year: int) -> list[dict]:
    """从参考文献文本中提取每篇文献的年份、识别信息和上下文"""
    import re
    entries = []
    # Split into individual reference entries
    ref_blocks = re.split(r'\n(?=\d+\.\s)', ref_text)
    for block in ref_blocks:
        years = [int(m) for m in re.findall(r'\b(20\d{2})\b', block) if 2010 <= int(m) <= current_year]
        if not years:
            # Also check for 19xx classic years
            years = [int(m) for m in re.findall(r'\b(19\d{2})\b', block) if 1960 <= int(m) <= current_year]
        pub_year = years[0] if years else None

        # Extract first author surname for classic check
        author_match = re.match(r'\d+\.\s*([A-Z][a-z]+)', block)
        first_author = author_match.group(1).lower() if author_match else ""

        # Check for classic annotation
        has_classic_tag = bool(re.search(
            r'\[Classic\s*[—–-]\s*([^\]]+)\]|\[Foundational\s*[—–-]\s*([^\]]+)\]',
            block, re.IGNORECASE
        ))
        classic_reason = ""
        if has_classic_tag:
            reason_match = re.search(
                r'\[(?:Classic|Foundational)\s*[—–-]\s*([^\]]+)\]',
                block, re.IGNORECASE
            )
            if reason_match:
                classic_reason = reason_match.group(1).strip()

        entries.append({
            "first_author": first_author,
            "year": pub_year,
            "block": block[:200],
            "has_classic_tag": has_classic_tag,
            "classic_reason": classic_reason,
        })
    return entries


def check_ref_recency(outputs: dict, orch) -> tuple:
    """参考文献时效性 — ≥80% 近5年, 经典方法学论文自动豁免

    豁免规则:
    1. 在 classic-papers.md 注册表中的论文 → 自动豁免, 不计入时效分母
    2. 标注了 [Classic — reason] 的论文 → 豁免
    3. 不在注册表且无标注的 >5 年文献 → 计入分母, 可能拉低时效比
    """
    import datetime
    current_year = datetime.datetime.now().year
    recency_window = 5
    cutoff_year = current_year - recency_window

    # Load classic registry
    classic_registry = _load_classic_papers_registry()

    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower():
            ref_section_match = re.search(
                r'(?:##\s*References?|##\s*参考文献|###\s*References?|###\s*参考文献)'
                r'(?:\n|.)+',
                output, re.IGNORECASE
            )
            search_text = ref_section_match.group(0) if ref_section_match else output

            # Extract structured reference entries
            entries = _extract_ref_entries_with_context(search_text, current_year)

            if not entries:
                return False, "未检测到参考文献条目, 无法检查时效性"

            # Classify each entry
            exempted_count = 0
            recent_count = 0
            old_unexplained = []
            total = len(entries)

            for entry in entries:
                year = entry.get("year")
                if year is None:
                    continue

                is_classic_registry = False
                if entry["first_author"] and year:
                    is_classic_registry = (entry["first_author"], year) in classic_registry

                is_classic_annotated = entry["has_classic_tag"]
                # 🆕 检测占位符 "领域" 被当作实际领域名使用
                if is_classic_annotated and entry.get("classic_reason", "").startswith("领域"):
                    old_unexplained.append(entry)
                    continue  # 格式无效, 不计入豁免

                if is_classic_registry or is_classic_annotated:
                    exempted_count += 1
                elif year >= cutoff_year:
                    recent_count += 1
                else:
                    old_unexplained.append(entry)

            # Compute recency ratio: recent / (total - exempted)
            denominator = total - exempted_count
            if denominator == 0:
                return True, f"所有 {total} 篇参考文献均为经典文献 (全部豁免) ✓"

            recency_ratio = recent_count / denominator

            if recency_ratio >= 0.80:
                result = (
                    f"参考文献时效性达标: {recent_count}/{denominator} "
                    f"({recency_ratio:.0%}) 为近{recency_window}年 "
                    f"(豁免 {exempted_count} 篇经典文献)"
                )
                if old_unexplained:
                    old_list = ", ".join(
                        f"{e['first_author']}({e['year']})" for e in old_unexplained[:5]
                    )
                    result += f". ⚠️ {len(old_unexplained)} 篇旧文献缺少豁免标注: {old_list}"
                return True, result

            old_list = ", ".join(
                f"{e['first_author']}({e['year']})" for e in old_unexplained[:5]
            )
            return False, (
                f"参考文献时效性不足: 仅 {recent_count}/{denominator} "
                f"({recency_ratio:.0%}) 为近{recency_window}年, 需 ≥80%. "
                f"豁免 {exempted_count} 篇经典文献. "
                f"{len(old_unexplained)} 篇旧文献缺少豁免标注: {old_list}. "
                f"请添加 [Classic — reason] 标注 或 替换为近5年文献"
            )
    return True, "跳过 (无 scientific-writer 输出)"


def check_all_refs_cited_in_text(outputs: dict, orch) -> tuple:
    """每篇参考文献必须在正文中被引用 — 防止为满足 recency 比例堆砌无关文献

    钱学森闭环控制教训: 单指标优化 (recency ≥80%) 会产生反向激励，Agent 通过堆砌近期
    但无关的文献来提高比例。此检查作为反制措施: 每篇 [n] 必须至少被正文引用一次。

    起因: 2026-05-12 发现为满足 80% 时效性, Agent 添加了十几篇无关近期文献,
    这些文献未被正文引用, 纯粹用于稀释分母。
    """
    import re

    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            # 1. 分离正文和 References
            ref_section_match = re.search(
                r'(?:##\s*References?|##\s*参考文献)',
                output, re.IGNORECASE
            )
            if not ref_section_match:
                return True, "跳过 (无 References 章节)"

            ref_start = ref_section_match.start()
            body_text = output[:ref_start]
            ref_text = output[ref_start:]

            # 2. 从 References 中提取所有引用编号 [n]
            ref_numbers = set()
            for m in re.finditer(r'(?:^|\n)\s*(?:\[(\d+)\]|(\d+)\.)\s', ref_text):
                num = m.group(1) or m.group(2)
                ref_numbers.add(int(num))

            # 也匹配 [1],[2],[3] 紧凑格式
            for m in re.finditer(r'\[(\d+)\]', ref_text):
                ref_numbers.add(int(m.group(1)))

            if not ref_numbers:
                return True, "跳过 (References 中未检测到编号引用)"

            # 3. 从正文中提取所有引用编号 [n]
            cited_numbers = set()
            for m in re.finditer(r'\[(\d+)\]', body_text):
                cited_numbers.add(int(m.group(1)))

            # 4. 找未被引用的文献
            uncited = ref_numbers - cited_numbers
            # 找正文引用了但 References 中不存在的 (孤儿引用)
            orphan = cited_numbers - ref_numbers

            violations = []
            if uncited:
                sorted_uncited = sorted(uncited)
                violations.append(
                    f"{len(uncited)} 篇文献未被正文引用: [{', '.join(str(n) for n in sorted_uncited[:10])}"
                    + (f", ...等{len(uncited)}篇" if len(uncited) > 10 else "]")
                    + " — 可能为满足 recency 比例而堆砌的无关文献"
                )
            if orphan:
                sorted_orphan = sorted(orphan)
                violations.append(
                    f"{len(orphan)} 处正文引用在 References 中无对应条目: "
                    f"[{', '.join(str(n) for n in sorted_orphan[:10])}"
                    + (f", ...等{len(orphan)}处" if len(orphan) > 10 else "]")
                )

            if violations:
                return False, (
                    f"参考文献引用完整性不通过:\n"
                    + "\n".join(f"  • {v}" for v in violations)
                    + f"\n\n总计: References 中 {len(ref_numbers)} 篇, 正文引用 {len(cited_numbers)} 篇, "
                    + f"未引用 {len(uncited)} 篇, 孤儿引用 {len(orphan)} 处"
                )

            return True, (
                f"参考文献引用完整性通过: References {len(ref_numbers)} 篇, "
                f"正文引用 {len(cited_numbers)} 篇, 未引用 0, 孤儿引用 0 ✓"
            )
    return True, "跳过 (无 scientific-writer 输出)"


def check_discussion_four_paragraphs(outputs: dict, orch) -> tuple:
    """Discussion 四段完整 (¶1-¶4 空行分隔)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower():
            if "## Discussion" not in output:
                return True, "跳过 (无 Discussion 章节)"
            # 不强制计数, 检查是否有明确的段落结构
            has_findings = any(kw in output for kw in ["主要发现", "principal finding", "main finding"])
            has_comparison = any(kw in output for kw in ["文献", "compar", "consistent", "previous"])
            has_implications = any(kw in output for kw in ["临床", "clinical", "implication", "public health"])
            has_limitations = any(kw in output for kw in ["局限", "limitation", "优势", "strength"])
            passed = [has_findings, has_comparison, has_implications, has_limitations]
            count = sum(passed)
            if count >= 3:
                return True, f"Discussion 段落完整 ({count}/4 要素检测到)"
            return False, f"Discussion 段落不完整 (仅 {count}/4 要素)"
    return True, "跳过 (无 scientific-writer 输出)"


def check_discussion_p4_no_conclusion(outputs: dict, orch) -> tuple:
    """Discussion ¶4 末尾无结论性收束句"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower():
            if "## Discussion" not in output:
                return True, "跳过"
            # 提取 Discussion 到 Conclusion 之间的内容
            disc_match = re.search(r'## Discussion\n(.*?)(?=## Conclusion|\Z)', output, re.DOTALL)
            if not disc_match:
                return True, "跳过"
            disc_content = disc_match.group(1)

            # 检查 ¶4 区域 (最后一段) 是否有结论性收束
            prohibited = [
                "In conclusion", "Taken together", "Overall", "In summary",
                "我们的研究表明", "综上所述", "总而言之",
                "paving the way", "ushering in", "highlighting the potential",
            ]
            # 取 Discussion 最后 500 字符 (¶4 区域)
            last_part = disc_content[-500:] if len(disc_content) > 500 else disc_content
            for phrase in prohibited:
                if phrase.lower() in last_part.lower():
                    return False, f"Discussion ¶4 末尾含结论性短语: '{phrase}'"
            return True, "Discussion ¶4 无结论性收束句"
    return True, "跳过"


# ============================================================
# Phase 6: 论文内容质量检查 (方案 A — P0 补充)
# ============================================================

def check_discussion_no_subheadings(outputs: dict, orch) -> tuple:
    """Discussion 不含 ### 子标题 — 四段靠逻辑过渡衔接, 不拆分小节"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            if "## Discussion" not in output:
                return True, "跳过 (无 Discussion 章节)"
            # 提取 Discussion 到下一个 ## 之间的内容
            disc_match = re.search(r'## Discussion\n(.*?)(?=##\s|\Z)', output, re.DOTALL)
            if not disc_match:
                return True, "跳过"
            disc_content = disc_match.group(1)
            # 检测 ### 子标题
            sub_headings = re.findall(r'^### (.+)$', disc_content, re.MULTILINE)
            if sub_headings:
                h_list = '", "'.join(sub_headings)
                return False, (
                    f'Discussion 包含 {len(sub_headings)} 个 ### 子标题: '
                    f'"{h_list}". Discussion 应四段靠逻辑过渡衔接, 不使用小标题'
                )
            return True, "Discussion 无 ### 子标题 ✓"
    return True, "跳过"


def check_abstract_word_count(outputs: dict, orch) -> tuple:
    """Abstract ≤ 300 词"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            import re
            abs_match = re.search(
                r'## Abstract\n(.*?)(?=##\s|\Z)', output, re.DOTALL | re.IGNORECASE
            )
            if abs_match:
                text = abs_match.group(1).strip()
                words = len(text.split())
                if words <= 300:
                    return True, f"Abstract {words} 词 ≤ 300 词 ✓"
                return False, f"Abstract 超出 300 词 ({words} 词)"
            return True, "跳过 (未检测到 Abstract)"
    return True, "跳过"


def check_keywords_count(outputs: dict, orch) -> tuple:
    """Keywords ≥ 3 个"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            import re
            kw_match = re.search(
                r'(?:Keywords|关键词)[:：]\s*(.+?)(?:\n|$)', output, re.IGNORECASE
            )
            if kw_match:
                kw_text = kw_match.group(1)
                # Split by comma or semicolon
                keywords = [k.strip() for k in re.split(r'[,;，；]', kw_text) if k.strip()]
                if len(keywords) >= 3:
                    return True, f"Keywords {len(keywords)} 个 ≥ 3 ✓"
                return False, f"Keywords 仅 {len(keywords)} 个, 需 ≥ 3"
            return False, "未检测到 Keywords 行"
    return True, "跳过"


def check_all_refs_have_doi(outputs: dict, orch) -> tuple:
    """每篇期刊参考文献必须有 DOI"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            import re
            ref_section = re.search(
                r'## References?\n(.*?)(?=\n##|\Z)', output, re.DOTALL
            )
            if not ref_section:
                return True, "跳过 (无 References 章节)"
            refs = ref_section.group(1)
            # Count entries (numbered: 1. or [1])
            ref_entries = re.findall(r'(?:^\d+\.\s|\[\d+\])', refs, re.MULTILINE)
            total = len(ref_entries)
            # Count entries with DOI
            dois = re.findall(r'(?:doi|DOI)[: ]*(10\.\d{4,}/[^\s"\']+)', refs)
            no_doi_count = len([e for e in ref_entries if 'doi' not in refs[e.start():e.end()+200].lower()])
            if total == 0:
                return True, "跳过 (无参考文献)"
            if len(dois) >= total * 0.8:
                return True, f"{len(dois)}/{total} 参考文献有 DOI (≥80%) ✓"
            return False, (
                f"仅 {len(dois)}/{total} 参考文献有 DOI, 需 ≥80%. "
                "无 DOI 的文献须标注为预印本/灰色文献/书籍"
            )
    return True, "跳过"


def check_auc_has_ci(outputs: dict, orch) -> tuple:
    """Results 中 AUC 必须带 95% CI"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            import re
            # Find AUC values
            auc_values = re.findall(r'AUC[^0-9]*(\d+\.\d+)', output)
            if not auc_values:
                return True, "跳过 (未检测到 AUC 值)"
            # Check if CI is mentioned nearby (within 200 chars of each AUC)
            auc_with_ci = 0
            for auc_val in auc_values:
                idx = output.find(auc_val)
                context = output[max(0, idx-100):idx+150]
                if re.search(r'(?:95%\s*CI|confidence\s*interval)', context):
                    auc_with_ci += 1
            if auc_with_ci >= len(auc_values) * 0.5:
                return True, f"{auc_with_ci}/{len(auc_values)} AUC 值带 95% CI ✓"
            return False, f"仅 {auc_with_ci}/{len(auc_values)} AUC 值带 95% CI, 所有 AUC 必须报告 CI"
    return True, "跳过"


def check_effect_size_with_ci(outputs: dict, orch) -> tuple:
    """效应量必须与置信区间一起报告"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            import re
            # Check for common effect size patterns
            has_effect = any(kw in output.lower() for kw in [
                "or =", "hr =", "rr =", "β =", "odds ratio", "hazard ratio",
                "risk ratio", "cohen", "hedges",
            ])
            has_ci = re.search(r'(?:95%\s*CI|confidence\s*interval)', output)
            if has_effect and not has_ci:
                return False, "检测到效应量但缺少置信区间, 效应量须与 CI 一起报告"
            return True, "效应量+CI 报告检查通过"
    return True, "跳过"


def check_discrimination_and_calibration_reported(outputs: dict, orch) -> tuple:
    """Results 中必须同时报告区分度和校准度"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            has_auc = bool(re.search(r'AUC|c.index|C.index|c.statistic', output, re.IGNORECASE))
            has_cal = bool(re.search(
                r'calibration|Brier|Hosmer.Lemeshow|校准',
                output, re.IGNORECASE
            ))
            if has_auc and not has_cal:
                return False, "Results 中报告了 AUC (区分度) 但缺少校准度指标 (Calibration/Brier)"
            return True, "区分度+校准度同时报告 ✓" if (has_auc and has_cal) else "跳过"
    return True, "跳过"


def check_normality_test_reported(outputs: dict, orch) -> tuple:
    """Methods 中必须说明连续变量的正态性检验方法"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            methods_section = output
            # Extract Methods section
            m = re.search(r'## Methods?\n(.*?)(?=##\s|\Z)', output, re.DOTALL)
            if m:
                methods_section = m.group(1)
            has_normality = any(kw in methods_section.lower() for kw in [
                "shapiro-wilk", "kolmogorov-smirnov", "normality", "正态",
                "skewness", "d'agostino", "anderson-darling",
            ])
            if has_normality:
                return True, "Methods 含正态性检验说明 ✓"
            return False, "Methods 中未说明连续变量的正态性检验方法"
    return True, "跳过"


def check_missing_data_reported(outputs: dict, orch) -> tuple:
    """Methods 中必须报告缺失率及处理方法"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            methods_section = output
            m = re.search(r'## Methods?\n(.*?)(?=##\s|\Z)', output, re.DOTALL)
            if m:
                methods_section = m.group(1)
            has_missing_rate = any(kw in methods_section.lower() for kw in [
                "missing", "缺失", "complete case", "imputation", "插补",
            ])
            has_method = any(kw in methods_section.lower() for kw in [
                "mice", "multiple imputation", "missforest", "mean imputation",
                "median imputation", "knn", "last observation",
                "complete case analysis", "多重插补", "均值插补",
            ])
            if has_missing_rate and has_method:
                return True, "Methods 含缺失率+处理方法 ✓"
            if not has_missing_rate:
                return False, "Methods 中未报告缺失率"
            return False, "Methods 中报告了缺失率但未说明处理方法 (如 MICE/CCA)"
    return True, "跳过"


def check_software_version_reported(outputs: dict, orch) -> tuple:
    """Methods 中必须报告软件名称及版本号"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            methods_section = output
            m = re.search(r'## Methods?\n(.*?)(?=##\s|\Z)', output, re.DOTALL)
            if m:
                methods_section = m.group(1)
            # Check for common tools + version patterns
            has_software = bool(re.search(
                r'(?:Python|R\b|SPSS|SAS|STATA|Stata|MATLAB|Julia)\s*\d+\.?\d*',
                methods_section
            ))
            has_package = bool(re.search(
                r'(?:scikit-learn|sklearn|pandas|numpy|scipy|survival|rms|'
                r'mice|lme4|mgcv|glmnet|xgboost|lightgbm|catboost)\s*\d+\.?\d*',
                methods_section, re.IGNORECASE
            ))
            if has_software or has_package:
                return True, "Methods 含软件+版本号 ✓"
            return False, "Methods 中未报告软件名称及版本号 (e.g. Python 3.12, scikit-learn 1.5)"
    return True, "跳过"


# ============================================================
# Phase 6: 去 AI 味质量检查 (humanize quality)
# ============================================================

# --- 共享数据: AI 禁用词黑名单 (同步自 company/reference/humanizer-rules.md) ---

_HUMANIZE_FORBIDDEN_WORDS = {
    "high": [
        # (正则, 标签, 替换建议)
        (r'\bpivotal\b', "pivotal", "→ important/key/central"),
        (r'\bcrucial\b', "crucial", "→ essential/vital/important"),
        (r'\blandscape\b', "landscape", "→ field/area/domain"),
        (r'\bdelve\b', "delve", "→ examine/explore/investigate"),
        (r'\bunderscores?\b', "underscore(s)", "→ highlights/emphasizes"),
        (r'evolving\s+landscape', "evolving landscape", "→ changing field"),
        (r'\bgroundbreaking\b', "groundbreaking", "→ innovative/novel"),
        (r'\brenowned\b', "renowned", "→ well-known/prominent"),
        (r'profound\s+impact', "profound impact", "→ substantial effect"),
        (r'\bremarkable\b', "remarkable", "→ notable/striking"),
        (r'\bdramatic(?:ally)?\b', "dramatic(ally)", "→ substantial/large/marked"),
        (r'\bserves?\s+as\b', "serve(s) as", "→ is"),
        (r'\bstands?\s+as\b', "stand(s) as", "→ is"),
        (r'in\s+order\s+to\b', "in order to", "→ to"),
        (r'for\s+the\s+purpose\s+of\b', "for the purpose of", "→ for/to"),
        (r'a\s+total\s+of\b', "a total of", "→ (删除)"),
        (r'\butiliz[ae]s?\b', "utilize(s)", "→ use"),
        (r'\bdemonstrat[es]\b', "demonstrate(s)", "→ show"),
        (r'\bfacilitates?\b', "facilitate(s)", "→ help/enable"),
        (r'\bshowcasing\b', "showcasing", "→ 改为直接陈述"),
        (r'\bhighlighting\s+the\b', "highlighting the", "→ 改为直接陈述"),
    ],
    "transition": [
        (r'^Furthermore[,\s]', "Furthermore", "删除或改为 Also(限1次/段)"),
        (r'^Moreover[,\s]', "Moreover", "删除"),
        (r'^Additionally[,\s]', "Additionally", "删除或改为 Also(限1次/段)"),
        (r'^Notably[,\s]', "Notably", "删除"),
        (r'^Interestingly[,\s]', "Interestingly", "删除"),
        (r'^Importantly[,\s]', "Importantly", "删除"),
    ],
    "coda": [
        (r'paving\s+the\s+way', "paving the way", "终结标语"),
        (r'ushering\s+in', "ushering in", "终结标语"),
        (r'highlighting\s+the\s+potential', "highlighting the potential", "终结标语"),
        (r'opening\s+the\s+door', "opening the door", "终结标语"),
        (r'[Ff]uture\s+(?:research|studies)\s+should\b', "Future research should", "不具体的future research"),
        (r'[Ff]uture\s+looks\s+bright', "future looks bright", "AI标语"),
        (r'\b(?:game[-\s]?changer|revolutionize)\b', "game-changer/revolutionize", "过度推广"),
        (r'[Ii]t\s+is\s+important\s+to\s+note\b', "It is important to note", "删除，直接陈述"),
        (r'[Ss]tudies\s+have\s+shown\b', "Studies have shown", "必须指名具体研究"),
        (r'[Ee]xperts\s+argue\b', "Experts argue", "必须指名具体专家"),
        (r'[Nn]ot\s+only.+but\s+also', "Not only...but also", "学术写作避免此结构"),
    ],
}

# 通用缩写豁免列表
_ACRONYM_EXEMPTIONS = {
    "DNA", "RNA", "BMI", "CI", "AUC", "OR", "HR", "SD", "ROC",
    "SHAP", "DCA", "IQR", "SE", "CI", "MICE", "SMD", "SAP",
    "CHARLS", "CLHLS", "HRS", "ELSA", "NHANES", "MIMIC", "SEER",
    "XGBoost", "LightGBM", "CatBoost", "PRISMA", "STROBE", "TRIPOD",
    "PROBAST", "FRAME", "DQ-CARE", "IMRAD", "PI", "SLA",
}


def check_humanize_quality(outputs: dict, orch) -> tuple:
    """去 AI 味质量检查 — 扫描禁用词、过渡词密度、hedge 密度、终结标语、缩写规范

    检测规则同步自 company/reference/humanizer-rules.md。
    任一高优先级禁用词命中 → FAIL。
    """
    import re

    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            violations = []

            # --- 1. 高优先级禁用词扫描 ---
            for pattern, label, suggestion in _HUMANIZE_FORBIDDEN_WORDS["high"]:
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    count = len(matches)
                    violations.append(
                        f"禁用词 '{label}' 出现 {count} 次 ({suggestion})"
                    )

            # --- 2. 过渡词密度 (按段扫描) ---
            paragraphs = [p for p in output.split('\n\n') if len(p.strip()) > 50]
            transition_over_limit = 0
            total_transitions = 0
            for para in paragraphs:
                count = 0
                for pattern, label, _ in _HUMANIZE_FORBIDDEN_WORDS["transition"]:
                    matches = re.findall(pattern, para, re.MULTILINE | re.IGNORECASE)
                    count += len(matches)
                total_transitions += count
                if count > 1:
                    transition_over_limit += 1
            if total_transitions > 3:
                violations.append(
                    f"过渡词过多: 全文 {total_transitions} 个 (限 ≤ 3), "
                    f"{transition_over_limit} 段超 1 个/段"
                )

            # --- 3. 终结标语扫描 ---
            coda_hits = []
            for pattern, label, suggestion in _HUMANIZE_FORBIDDEN_WORDS["coda"]:
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    coda_hits.append(f"'{label}' ({suggestion})")
            if coda_hits:
                violations.append(f"终结标语/弱写法: {', '.join(coda_hits)}")

            # --- 4. Hedge 密度 (Discussion ¶3 + Conclusion 区域) ---
            # 提取 Discussion ¶3 (临床含义段落) 和 Conclusion
            disc_match = re.search(
                r'## Discussion\n(.*?)(?=## Conclusion|\Z)',
                output, re.DOTALL
            )
            conclusion_match = re.search(
                r'## Conclusion\n(.*?)(?=##\s|\Z)',
                output, re.DOTALL
            )

            hedge_pattern = re.compile(
                r'\b(?:may|might|could|potentially|possibly|suggests?|'
                r'may\s+suggest|have\s+the\s+potential\s+to|appears?\s+to)\b',
                re.IGNORECASE
            )

            if disc_match:
                disc_content = disc_match.group(1)
                # 粗略定位 ¶3 (最后 1/3 的 Discussion 内容，排除 ¶4 局限段)
                disc_paragraphs = [p for p in disc_content.split('\n\n') if len(p.strip()) > 30]
                if len(disc_paragraphs) >= 3:
                    # ¶3 一般位于 Discussion 的后半段，但不是最后一段 (最后是 ¶4)
                    para3_candidates = disc_paragraphs[-3:-1]  # 取倒数第2-3段
                    para3_text = ' '.join(para3_candidates)
                    para3_hedges = len(hedge_pattern.findall(para3_text))
                    if para3_hedges > 3:
                        violations.append(
                            f"Discussion ¶3 hedge 过多: {para3_hedges} 个 (限 ≤ 3)"
                        )

            if conclusion_match:
                conclusion_text = conclusion_match.group(1)
                conclusion_hedges = len(hedge_pattern.findall(conclusion_text))
                if conclusion_hedges > 1:
                    violations.append(
                        f"Conclusion hedge 过多: {conclusion_hedges} 个 (限 ≤ 1)"
                    )

            # --- 5. 缩写规范检查 ---
            # 查找正文中所有大写缩写 (≥ 2 个大写字母)
            body = output
            # 移除代码块和表格行
            body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
            body = re.sub(r'^\|.+\|$', '', body, flags=re.MULTILINE)

            all_acronyms = set()
            for match in re.finditer(r'\b([A-Z]{2,}(?:s)?)\b', body):
                acro = match.group(1)
                if acro not in _ACRONYM_EXEMPTIONS:
                    all_acronyms.add(acro)

            undefined = []
            for acro in all_acronyms:
                # 检查是否在前面定义了: 全称 (ACRONYM) 或 全称 (Acronym)
                idx = body.find(acro)
                if idx > 0:
                    before = body[:idx]
                    # 找最近一次出现: (ACRONYM) 或 (Acronym) 前的全称定义
                    def_match = re.search(
                        rf'(.+?)\s*\({re.escape(acro)}\)',
                        before, re.IGNORECASE
                    )
                    if not def_match:
                        undefined.append(acro)

            if undefined:
                violations.append(
                    f"未定义的缩写: {', '.join(undefined[:10])}"
                    + (f" ...等 {len(undefined)} 个" if len(undefined) > 10 else "")
                )

            # --- 汇总 ---
            if violations:
                return False, (
                    f"去 AI 味检查不通过 — {len(violations)} 类问题:\n"
                    + "\n".join(f"  • {v}" for v in violations)
                )
            return True, "去 AI 味质量检查通过 ✓"

    return True, "跳过 (无 scientific-writer 输出)"


# ============================================================
# Phase 5/6: 流程完整性检查 (方案 B — P1 补充)
# ============================================================

def check_sap_exists(outputs: dict, orch) -> tuple:
    """Pre-flight: 统计分析计划 (SAP) 已存在"""
    import os
    from pathlib import Path
    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            proj_dir = Path(vault_path) / 'projects' / project_id
            sap_files = list(proj_dir.glob('sap.md')) + list(proj_dir.glob('data/sap.md'))
            if sap_files:
                return True, "SAP 文件存在 ✓"
    return False, "缺少 SAP (统计分析计划). 请先完成 SAP 并经 PI 审批"


def check_clinical_review_exists(outputs: dict, orch) -> tuple:
    """Pre-flight: clinical-review.md 已存在 (Discussion 撰写前提)"""
    import os
    from pathlib import Path
    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            proj_dir = Path(vault_path) / 'projects' / project_id
            cr_files = list(proj_dir.glob('clinical-review.md')) + list(proj_dir.glob('data/clinical-review.md'))
            if cr_files:
                return True, "clinical-review.md 存在 ✓"
    return False, "缺少 clinical-researcher 的临床审查产出. 请先完成临床审查再撰写 Discussion"


def check_pi_approval_exists(outputs: dict, orch) -> tuple:
    """Pre-flight: PI 终审签批已存在 (终稿编译前提)"""
    import os
    from pathlib import Path
    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            proj_dir = Path(vault_path) / 'projects' / project_id
            pi_files = (
                list(proj_dir.glob('review-approval.md'))
                + list(proj_dir.glob('data/review-pi-ruling.md'))
            )
            if pi_files:
                return True, "PI 终审签批存在 ✓"
    return False, "缺少 PI 终审签批. 请先完成 PI 审查再编译终稿"


def check_journal_config_locked(outputs: dict, orch) -> tuple:
    """Pre-flight: 目标期刊需求已采集 (字数/格式/引用等)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            has_journal = any(kw in output.lower() for kw in [
                "target journal", "目标期刊", "journal requirements",
                "字数上限", "引用格式", "author guidelines",
            ])
            if has_journal:
                return True, "期刊需求已采集 ✓"
            return False, "目标期刊需求尚未采集. 需确认字数上限/摘要格式/引用格式/图表限制/AI披露"
    return True, "跳过"


def check_sensitivity_analysis_count(outputs: dict, orch) -> tuple:
    """敏感性分析 ≥ 3 项 (biostatistician SAP 要求)"""
    for agent_id, output in outputs.items():
        if "biostatistician" in agent_id.lower() or "sap" in agent_id.lower():
            import re
            # Count sensitivity analysis items (common patterns)
            sa_items = re.findall(
                r'(?:^|\n)\s*(?:-|\d+\.)\s*(?:敏感性|sensitivity|missing|'
                r'imputation|exclu|confound|E.value|extreme)',
                output, re.IGNORECASE | re.MULTILINE
            )
            if len(sa_items) >= 3:
                return True, f"敏感性分析 {len(sa_items)} 项 ≥ 3 ✓"
            return False, f"敏感性分析仅 {len(sa_items)} 项, 需 ≥ 3"
    return True, "跳过"


def check_subgroup_count(outputs: dict, orch) -> tuple:
    """亚组分析 ≤ 5 个 (biostatistician 要求)"""
    for agent_id, output in outputs.items():
        if "biostatistician" in agent_id.lower() or "sap" in agent_id.lower():
            import re
            # Count distinct subgroup definitions
            subgroups = re.findall(
                r'(?:subgroup|亚组|stratif)[:：\s]*(\w+)',
                output, re.IGNORECASE
            )
            unique_subgroups = len(set(s.lower() for s in subgroups))
            if unique_subgroups <= 5:
                return True, f"亚组 {unique_subgroups} 个 ≤ 5 ✓"
            return False, f"亚组 {unique_subgroups} 个超出 5 个上限"
    return True, "跳过"


def check_smd_balance(outputs: dict, orch) -> tuple:
    """SMD < 0.1 组间均衡检查"""
    for agent_id, output in outputs.items():
        if "biostatistician" in agent_id.lower() or "ml-engineer" in agent_id.lower():
            import re
            smd_vals = re.findall(r'(?:SMD|smd|ASMD)[^0-9]*(\d+\.\d+)', output)
            if smd_vals:
                high_smds = [float(v) for v in smd_vals if float(v) >= 0.1]
                if not high_smds:
                    return True, f"所有 SMD < 0.1 (共 {len(smd_vals)} 个) ✓"
                return False, (
                    f"{len(high_smds)}/{len(smd_vals)} 个 SMD ≥ 0.1: "
                    f"{high_smds[:3]}, 组间均衡性不足"
                )
    return True, "跳过 (未检测到 SMD 值)"


def check_num_consistency_validated(outputs: dict, orch) -> tuple:
    """Pre-flight: 数值一致性预检已通过"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            if hasattr(orch, 'consistency_checker') and orch.consistency_checker:
                report = orch.consistency_checker.get_last_report()
                if report and report.get("overall") == "pass":
                    return True, "数值一致性预检已通过 ✓"
            return True, "跳过 (无 consistency_checker 或未执行)"
    return True, "跳过"


# ============================================================
# 趋势检查 (Δ-Gate) — 监控指标变化方向, 提前预警性能恶化
# 钱学森工程控制论: 反馈不仅要检测偏差, 还要监控变化趋势 (微分控制)
# ============================================================

# --- 共享辅助函数 ---

def _extract_auc_from_outputs(outputs: dict) -> Optional[float]:
    """从 ml-engineer 输出中提取 AUC 值"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            patterns = [
                r'(?:auc.?roc|AUC|auc)[^0-9]*0?\.(\d+)',
                r'c.?statistic[^0-9]*0?\.(\d+)',
            ]
            for pat in patterns:
                matches = re.findall(pat, output)
                if matches:
                    return float(f"0.{matches[0]}")
    return None


def _extract_calibration_slope(outputs: dict) -> Optional[float]:
    """从 ml-engineer 输出中提取 calibration slope"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            match = re.search(
                r'calibration.?slope[^0-9]*(\d+\.?\d*)', output, re.IGNORECASE
            )
            if match:
                return float(match.group(1))
    return None


def _extract_features_from_outputs(outputs: dict) -> Optional[list]:
    """从 ml-engineer 输出中提取使用的特征名列表"""
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            features = set()
            for match in re.finditer(
                r'(?:特征|Feature|Variable)[:：]\s*(\w+)', output, re.IGNORECASE
            ):
                features.add(match.group(1))
            if features:
                return list(features)
    return None


# --- 趋势检查函数 ---

def check_auc_trend(outputs: dict, orch) -> tuple:
    """ΔAUC 趋势 — 对比当前 AUC 与历史上次 Gate 通过值, 监控性能恶化趋势"""
    current_auc = _extract_auc_from_outputs(outputs)
    if current_auc is None:
        return True, "跳过 (未检测到 AUC 值, 可能为非分类任务)"

    prev_auc = getattr(orch, '_trend_baselines', {}).get('auc')
    if prev_auc is None:
        # 首次执行: 保存为基准
        if not hasattr(orch, '_trend_baselines'):
            orch._trend_baselines = {}
        orch._trend_baselines['auc'] = current_auc
        return True, f"首次执行, AUC={current_auc:.3f} 已保存为趋势基准"

    delta = current_auc - prev_auc

    if delta < -0.10:
        return False, (
            f"ΔAUC={delta:.3f} (从 {prev_auc:.3f} 降至 {current_auc:.3f}), "
            f"下降超过 0.10, 需审查特征工程/标签定义/过拟合"
        )
    elif delta < -0.05:
        return True, (
            f"⚠️ ΔAUC={delta:.3f} (从 {prev_auc:.3f} 降至 {current_auc:.3f}), "
            f"下降趋势需关注, 建议 PI 审查"
        )
    else:
        direction = "提升" if delta > 0 else "稳定"
        return True, f"ΔAUC={delta:+.3f} ({direction})"


def check_calibration_trend(outputs: dict, orch) -> tuple:
    """校准度趋势 — 监控 calibration slope 是否持续偏离 [0.9, 1.1]"""
    slope = _extract_calibration_slope(outputs)
    if slope is None:
        return True, "跳过 (未检测到 calibration slope)"

    if 0.9 <= slope <= 1.1:
        if hasattr(orch, '_trend_baselines'):
            orch._trend_baselines.pop('calibration', None)
        return True, f"Calibration slope={slope:.3f} 在 [0.9, 1.1] 区间内"

    # 偏离区间 — 检查是否已持续偏离
    if not hasattr(orch, '_trend_baselines'):
        orch._trend_baselines = {}
    prev = orch._trend_baselines.get('calibration')

    if prev and prev.get("state") == "warning":
        return False, (
            f"Calibration slope={slope:.3f} 持续偏离 [0.9, 1.1], "
            f"上次 slope={prev['value']:.3f}, 模型校准度存在问题"
        )

    orch._trend_baselines['calibration'] = {"value": slope, "state": "warning"}
    return True, (
        f"⚠️ Calibration slope={slope:.3f} 首次偏离 [0.9, 1.1], "
        f"建议检查 Platt scaling 或 isotonic regression"
    )


def check_feature_stability(outputs: dict, orch) -> tuple:
    """特征稳定性 — 对比外部验证与内部验证的特征重叠率, 检测特征漂移"""
    internal_features = getattr(orch, '_phase_features', {}).get('execution')
    external_features = _extract_features_from_outputs(outputs)

    if not internal_features or not external_features:
        return True, "跳过 (特征列表不可用 — 可能为首次执行或非ML阶段)"

    internal_set = set(internal_features)
    external_set = set(external_features)

    if not internal_set:
        return True, "跳过 (内部验证特征列表为空)"

    overlap = internal_set & external_set
    overlap_rate = len(overlap) / len(internal_set)
    new_features = external_set - internal_set
    missing_features = internal_set - external_set

    if overlap_rate < 0.70:
        return False, (
            f"特征重叠率仅 {overlap_rate:.0%} ({len(overlap)}/{len(internal_set)}), "
            f"缺失 {len(missing_features)} 个: {list(missing_features)[:5]}, "
            f"新增 {len(new_features)} 个: {list(new_features)[:5]}"
        )
    elif overlap_rate < 0.85:
        return True, (
            f"⚠️ 特征重叠率 {overlap_rate:.0%} 偏低, "
            f"缺失 {len(missing_features)} 个特征, 请确认外部数据可用性"
        )

    return True, f"特征重叠率 {overlap_rate:.0%} ({len(overlap)}/{len(internal_set)})"


# ============================================================
# Phase 5: 方法实现保真度检查
# ============================================================

def check_method_implementation_fidelity(outputs: dict, orch) -> tuple:
    """Methods 声明的分析方法必须与代码实际实现一致

    从 04_methods.md 提取方法声明 → 在 train_model.py / generate_figures.py 中搜索实现
    """
    import os
    import re
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    # 定位项目目录
    proj_dir = None
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            candidate = Path(vault_path) / 'projects' / project_id
            if candidate.exists():
                proj_dir = candidate
                break

    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    # 1. 从 04_methods.md 提取分析方法声明
    methods_files = list(proj_dir.glob('sections/04_methods.md')) + \
                    list(proj_dir.glob('data/*methods*.md'))
    if not methods_files:
        return True, "跳过 (未找到 Methods 文件)"

    methods_text = methods_files[0].read_text()

    # 提取方法声明关键词
    method_patterns = {
        "SHAP": [r'\bshap\b', r'\bshapley\b', r'\bshap_values?\b'],
        "LASSO": [r'\blasso\b', r"LogisticRegressionCV\(penalty='l1'\)"],
        "XGBoost": [r'\bxgboost\b', r'\bXGBClassifier\b', r'\bXGBRegressor\b'],
        "Random Forest": [r'\brandom.?forest\b', r'\bRandomForest\b'],
        "Logistic Regression": [r'\blogistic.?regression\b', r'\bLogisticRegression\b'],
        "Cox PH": [r'\bcox\b', r'\bCoxPH\b', r'\bCox Proportional\b'],
        "Elastic Net": [r'\belastic.?net\b', r"penalty='elasticnet'"],
        "Ridge": [r'\bridge regression\b', r"penalty='l2'"],
        "SVM": [r'\bsvm\b', r'\bsupport vector\b', r'\bSVC\b'],
        "Gradient Boosting": [r'\bgradient.?boosting\b', r'\bGradientBoosting\b'],
    }

    declared_methods = []
    for method_name, patterns in method_patterns.items():
        for pat in patterns:
            if re.search(pat, methods_text, re.IGNORECASE):
                declared_methods.append(method_name)
                break

    if not declared_methods:
        return True, "跳过 (Methods 中未检测到明确的机器学习方法声明)"

    # 2. 在代码中搜索对应实现
    code_files = list(proj_dir.glob('train_model.py')) + \
                 list(proj_dir.glob('tune_model.py')) + \
                 list(proj_dir.glob('generate_figures.py')) + \
                 list(proj_dir.glob('figures/generate_figures.py'))

    if not code_files:
        return True, "跳过 (未找到项目代码文件)"

    code_text = ""
    for cf in code_files:
        if cf.exists():
            code_text += cf.read_text() + "\n"

    # 实现关键词映射
    impl_patterns = {
        "SHAP": [r'import\s+shap\b', r'from\s+shap\b', r'shap\.', r'shap_values?\b'],
        "LASSO": [r"penalty\s*=\s*['\"]l1['\"]", r'Lasso\b', r'lassocv\b',
                   r'LogisticRegressionCV\s*\([^)]*penalty'],
        "XGBoost": [r'import\s+xgboost\b', r'from\s+xgboost\b', r'xgb\.',
                     r'XGBClassifier\b', r'XGBRegressor\b'],
        "Random Forest": [r'RandomForestClassifier\b', r'RandomForestRegressor\b'],
        "Logistic Regression": [r'LogisticRegression\b', r'LogisticRegressionCV\b'],
        "Cox PH": [r'CoxPH\b', r'CoxPHFitter\b', r'CoxRegression\b',
                    r'from\s+lifelines\b'],
        "Elastic Net": [r"penalty\s*=\s*['\"]elasticnet['\"]",
                         r'ElasticNet\b', r'ElasticNetCV\b'],
        "Ridge": [r"penalty\s*=\s*['\"]l2['\"]", r'Ridge\b', r'RidgeCV\b',
                   r'RidgeClassifier\b'],
        "SVM": [r'SVC\b', r'SVR\b', r'LinearSVC\b', r'from\s+sklearn\.svm\b'],
        "Gradient Boosting": [r'GradientBoostingClassifier\b',
                               r'GradientBoostingRegressor\b',
                               r'import\s+lightgbm\b', r'from\s+lightgbm\b',
                               r'import\s+catboost\b', r'from\s+catboost\b'],
    }

    missing_impl = []
    for method in declared_methods:
        patterns = impl_patterns.get(method, [])
        if not patterns:
            continue
        found = any(re.search(pat, code_text, re.IGNORECASE) for pat in patterns)
        if not found:
            missing_impl.append(method)

    if missing_impl:
        return False, (
            f"方法实现保真度不通过: Methods 声明了 {missing_impl} 但代码中未找到对应实现。"
            f"请修正 Methods 文本或补充代码实现。"
        )

    return True, f"方法实现保真度通过: {len(declared_methods)} 个声明的分析方法均在代码中确认 ✓"


# ============================================================
# Phase 6: 数值一致性 + 基线合规 + 投稿层完整性检查
# ============================================================

def check_numerical_traceability(outputs: dict, orch) -> tuple:
    """所有数值可追溯到 cv_results.json (偏差 < 0.1%)

    检查 tables/*.md + manuscript.md + figure*_data.json 中的数值
    是否与 cv_results.json 对应 key 偏差 < 0.1%
    """
    import os
    import re
    import json
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = None
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            candidate = Path(vault_path) / 'projects' / project_id
            if candidate.exists():
                proj_dir = candidate
                break

    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    # 1. 加载真相源 cv_results.json
    cv_paths = list(proj_dir.glob('models/cv_results.json')) + \
               list(proj_dir.glob('data/cv_results.json'))
    if not cv_paths:
        return True, "跳过 (未找到 cv_results.json, 可能尚未完成 Phase 3)"

    try:
        cv_data = json.loads(cv_paths[0].read_text())
    except (json.JSONDecodeError, OSError):
        return True, "跳过 (cv_results.json 无法解析)"

    # 展平 cv_results 为 {key: value} 映射
    def flatten_json(d, prefix=""):
        items = {}
        if isinstance(d, dict):
            for k, v in d.items():
                new_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, (dict, list)):
                    items.update(flatten_json(v, new_key))
                elif isinstance(v, (int, float)):
                    items[new_key] = v
        elif isinstance(d, list):
            for i, v in enumerate(d):
                new_key = f"{prefix}[{i}]"
                if isinstance(v, (dict, list)):
                    items.update(flatten_json(v, new_key))
                elif isinstance(v, (int, float)):
                    items[new_key] = v
        return items

    truth = flatten_json(cv_data)
    if not truth:
        return True, "跳过 (cv_results.json 中无数值)"

    # 2. 从 figure*_data.json 提取数值并对比
    violations = []

    figure_data_files = list(proj_dir.glob('figures/figure*_data.json')) + \
                        list(proj_dir.glob('figures/Figure*_data.json'))
    for fd in figure_data_files:
        try:
            fig_data = json.loads(fd.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        fig_flat = flatten_json(fig_data)
        for fig_key, fig_val in fig_flat.items():
            # 模糊匹配: 在 truth 中找最相似的 key
            matched = None
            for truth_key, truth_val in truth.items():
                # 简单包含匹配 (如 "auc" in truth_key and "auc" in fig_key)
                key_parts = fig_key.lower().replace("_", " ").split()
                if all(part in truth_key.lower() for part in key_parts if len(part) > 2):
                    matched = truth_val
                    break
            if matched and isinstance(matched, (int, float)) and matched != 0:
                deviation = abs(fig_val - matched) / abs(matched)
                if deviation > 0.001:  # 0.1%
                    violations.append(
                        f"{fd.name}:{fig_key}={fig_val} vs cv_results={matched} "
                        f"(偏差 {deviation:.2%})"
                    )

    # 3. 从 tables/*.md 提取数值并对比
    table_files = list(proj_dir.glob('tables/*.md'))
    for tf in table_files:
        try:
            table_text = tf.read_text()
        except OSError:
            continue
        # 提取所有数值: X.XXX 或 XX.X%
        numbers = re.findall(r'(\d+\.\d+)%?', table_text)
        for num_str in numbers:
            num_val = float(num_str)
            if num_val < 0.01:
                continue
            # 在 truth 中找最接近的值
            for truth_val in truth.values():
                if isinstance(truth_val, (int, float)) and truth_val != 0:
                    if abs(num_val - truth_val) / abs(truth_val) < 0.01:
                        break

    if violations:
        return False, (
            f"数值可追溯性不通过 — {len(violations)} 处偏差 > 0.1%:\n"
            + "\n".join(f"  • {v}" for v in violations[:5])
            + (f"\n  ...等 {len(violations)} 处" if len(violations) > 5 else "")
        )

    return True, (
        f"数值可追溯性通过: {len(figure_data_files)} 个 figure data + "
        f"{len(table_files)} 个 table 全部与 cv_results.json 一致 ✓"
    )


def check_baseline_compliance(outputs: dict, orch) -> tuple:
    """Figure 必须从 Phase 3 baseline 读取数据，禁止从模型对象重新提取"""
    import os
    import re
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = None
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            candidate = Path(vault_path) / 'projects' / project_id
            if candidate.exists():
                proj_dir = candidate
                break

    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    # 查找 generate_figures.py
    gen_fig_paths = list(proj_dir.glob('generate_figures.py')) + \
                    list(proj_dir.glob('figures/generate_figures.py')) + \
                    list(proj_dir.glob('regenerate_figures_tables.py'))

    if not gen_fig_paths:
        return True, "跳过 (未找到 generate_figures.py)"

    gen_fig_code = gen_fig_paths[0].read_text()

    violations = []

    # 检查1: 是否 import json (用于读取 cv_results.json)
    if 'import json' not in gen_fig_code and 'from json' not in gen_fig_code:
        violations.append("未 import json (无法读取 cv_results.json)")

    # 检查2: 是否从模型对象直接提取 feature_importances_
    direct_extraction_patterns = [
        r'\.feature_importances_\b',
        r'\.coef_\b',
        r'\.feature_importance\b',
        r'\.get_fscore\b',
        r'\.get_score\b',
    ]
    for pat in direct_extraction_patterns:
        matches = re.findall(pat, gen_fig_code)
        if matches:
            # 检查是否同时读取了 cv_results.json (合规的混合使用)
            if 'cv_results.json' not in gen_fig_code and \
               'cv_results' not in gen_fig_code:
                violations.append(
                    f"从模型对象直接提取数据 ({matches[0]}) 但未读取 cv_results.json，"
                    f"违反基线合规要求"
                )

    # 检查3: 是否 open(cv_results.json) 或读取 baseline
    reads_baseline = (
        'cv_results.json' in gen_fig_code or
        'cv_results' in gen_fig_code or
        'phase3_baseline' in gen_fig_code
    )

    if not reads_baseline:
        violations.append(
            "generate_figures.py 未读取 cv_results.json 或 Phase 3 baseline，"
            "数据源可能来自模型对象而非冻结基线"
        )

    if violations:
        return False, (
            f"基线合规不通过:\n" + "\n".join(f"  • {v}" for v in violations)
        )

    return True, "基线合规通过: figures 数据源来自 cv_results.json ✓"


def check_submission_structure_integrity(outputs: dict, orch) -> tuple:
    """投稿层结构完整性: submission/ 下无 sections/, figures/ 仅 .png/.tiff,
    tables/ 仅 .csv, 无 Classic 标注残留"""
    import os
    import re
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = None
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            candidate = Path(vault_path) / 'projects' / project_id
            if candidate.exists():
                proj_dir = candidate
                break

    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    submission_dir = proj_dir / 'submission'
    if not submission_dir.exists():
        return False, "投稿层不存在: submission/ 目录未创建"

    violations = []

    # 1. submission/ 下不得存在 sections/ 目录
    if (submission_dir / 'sections').exists():
        violations.append(
            "submission/sections/ 目录存在 — "
            "零件层 sections/ 不应出现在投稿层, assembly 误用了 cp -r 而非 cat 拼接"
        )

    # 2. submission/figures/ 下仅允许 .png 和 .tiff
    figures_dir = submission_dir / 'figures'
    if figures_dir.exists():
        for f in figures_dir.iterdir():
            if f.is_file() and f.suffix.lower() not in ('.png', '.tiff', '.tif'):
                violations.append(
                    f"submission/figures/ 含非图片文件: {f.name} — "
                    "caption .md 和 data .json 不应进入投稿层"
                )

        # 检查 .png 是否都有对应 .tiff
        png_files = {f.stem for f in figures_dir.glob('*.png')}
        tiff_files = {f.stem for f in figures_dir.glob('*.tiff')} | \
                     {f.stem for f in figures_dir.glob('*.tif')}
        missing_tiff = png_files - tiff_files
        if missing_tiff:
            violations.append(
                f"submission/figures/ 中 {len(missing_tiff)} 个 .png 缺少对应 .tiff: "
                + ", ".join(sorted(missing_tiff)[:5])
            )

    # 3. submission/tables/ 下仅允许 .csv
    tables_dir = submission_dir / 'tables'
    if tables_dir.exists():
        for f in tables_dir.iterdir():
            if f.is_file() and f.suffix.lower() != '.csv':
                violations.append(
                    f"submission/tables/ 含非 CSV 文件: {f.name} — "
                    "投稿层表格仅需 .csv"
                )

    # 4. submission/manuscript.md 存在
    manuscript = submission_dir / 'manuscript.md'
    if not manuscript.exists():
        violations.append("submission/manuscript.md 不存在 — assembly 未生成合稿")

    # 5. manuscript.md 中不含 Classic 标注
    if manuscript.exists():
        try:
            content = manuscript.read_text()
            if '[Classic' in content or '[classic' in content.lower():
                violations.append(
                    "submission/manuscript.md 中含 [Classic 标注 — "
                    "Classic 标注为零件层内部元数据, assembly 拼接时必须 strip"
                )
        except OSError:
            pass

    if violations:
        return False, (
            f"投稿层结构完整性不通过 — {len(violations)} 项违规:\n"
            + "\n".join(f"  • {v}" for v in violations)
        )

    return True, "投稿层结构完整性通过 ✓"


def check_figure_naming_convention(outputs: dict, orch) -> tuple:
    """Figure 文件名匹配 Figure[N]_[descriptor].[ext] 格式"""
    import re
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = None
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            candidate = Path(vault_path) / 'projects' / project_id
            if candidate.exists():
                proj_dir = candidate
                break

    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    figures_dir = proj_dir / 'figures'
    if not figures_dir.exists():
        return True, "跳过 (figures/ 目录不存在)"

    png_files = list(figures_dir.glob('*.png'))
    if not png_files:
        return True, "跳过 (figures/ 中无 .png 文件)"

    # 期望格式: Figure[N]_[descriptor].png  (N = 数字 或 S数字)
    valid_pattern = re.compile(r'^Figure(S?\d+)_[a-z0-9\-]+\.png$', re.IGNORECASE)

    invalid_names = []
    for f in png_files:
        if not valid_pattern.match(f.name):
            invalid_names.append(f.name)

    if invalid_names:
        return False, (
            f"Figure 命名格式不通过 — {len(invalid_names)} 个文件不符合 "
            f"Figure[N]_[descriptor].[ext] 格式:\n"
            + "\n".join(f"  • {n}" for n in invalid_names[:5])
            + (f"\n  ...等 {len(invalid_names)} 个" if len(invalid_names) > 5 else "")
            + "\n\n期望: Figure1_cohort-flow-diagram.png, Figure2_roc-curve.png, etc."
        )

    return True, f"Figure 命名格式通过: {len(png_files)} 个 .png 文件均符合规范 ✓"


def check_all_figures_have_images(outputs: dict, orch) -> tuple:
    """每张 Figure caption 必须有对应的 .png 图像 — 防止 generate_figures.py 生成 caption 但跳过图像生成

    起因: 2026-05-12 发现 Figure 1 被 generate_figures.py 标记为 "manual diagram" 后仅生成
    Figure1_caption.md, 没有生成实际图像。Gate 6 #6 检查了文件存在性和命名, 但未检查 caption↔image
    对应关系。此检查补齐该缺口。
    """
    import re
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = None
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            candidate = Path(vault_path) / 'projects' / project_id
            if candidate.exists():
                proj_dir = candidate
                break

    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    figures_dir = proj_dir / 'figures'
    if not figures_dir.exists():
        return True, "跳过 (figures/ 目录不存在)"

    # 1. 从 caption 文件提取 Figure 编号
    caption_files = list(figures_dir.glob('*caption*.md'))
    if not caption_files:
        return True, "跳过 (未找到 Figure caption 文件)"

    caption_fig_numbers = {}  # {fig_number: caption_filename}
    for cf in caption_files:
        m = re.match(r'(?:Figure|fig)(S?\d+)', cf.name, re.IGNORECASE)
        if m:
            caption_fig_numbers[m.group(1)] = cf.name

    if not caption_fig_numbers:
        return True, "跳过 (caption 文件名无法解析 Figure 编号)"

    # 2. 从 .png 图像提取 Figure 编号
    png_files = list(figures_dir.glob('*.png'))
    png_fig_numbers = set()
    for pf in png_files:
        m = re.match(r'Figure(S?\d+)', pf.name, re.IGNORECASE)
        if m:
            png_fig_numbers.add(m.group(1))

    # 3. 每个有 caption 的 Figure 必须有对应图像
    missing_images = []
    for num in sorted(caption_fig_numbers.keys(),
                       key=lambda x: (x.startswith('S'), int(x.lstrip('S')))):
        if num not in png_fig_numbers:
            missing_images.append(
                f"Figure {num} — caption {caption_fig_numbers[num]} 存在, "
                f"但无对应图像 (未找到 Figure{num}_*.png)"
            )

    if missing_images:
        return False, (
            f"Figure 图像缺失 — {len(missing_images)} 张图有 caption 但无图像:\n"
            + "\n".join(f"  • {m}" for m in missing_images)
            + "\n\n可能原因: generate_figures.py 将 Figure 标记为 'manual diagram' 后静默跳过。"
            + "\n请手动创建图像或修改 generate_figures.py 生成占位图后重跑。"
        )

    return True, (
        f"Figure caption↔image 对应完整: {len(caption_fig_numbers)} 个 caption "
        f"均有对应 .png ✓"
    )


def check_figure_text_citation(outputs: dict, orch) -> tuple:
    """每张 Figure 必须在正文中被引用 — grep manuscript 确保 Figure[N]_* 文件名有对应 (Figure N) 引用

    起因: 2026-05-12 发现 Figure 1 只有 caption 无图像, Figure 1/2 正文漏引用。
    Gate 6 #6 检查了存在性和命名, 但未检查「正文是否引用了每张图」。
    此检查补齐该缺口。
    """
    import re
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = None
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            candidate = Path(vault_path) / 'projects' / project_id
            if candidate.exists():
                proj_dir = candidate
                break

    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    # 1. 收集所有 Figure 文件，提取 Figure 编号
    figures_dir = proj_dir / 'figures'
    submission_figures_dir = proj_dir / 'submission' / 'figures'

    fig_numbers = set()
    for d in [figures_dir, submission_figures_dir]:
        if not d.exists():
            continue
        for f in d.glob('*.png'):
            m = re.match(r'Figure(S?\d+)', f.name, re.IGNORECASE)
            if m:
                fig_numbers.add(m.group(1))  # e.g. "1", "2", "S1"

    if not fig_numbers:
        return True, "跳过 (未找到 Figure 文件)"

    # 2. 收集正文 — manuscript.md + sections/05_results.md
    text_sources = []
    manuscript = proj_dir / 'submission' / 'manuscript.md'
    if manuscript.exists():
        try:
            text_sources.append(manuscript.read_text())
        except OSError:
            pass

    results_md = proj_dir / 'sections' / '05_results.md'
    if results_md.exists():
        try:
            text_sources.append(results_md.read_text())
        except OSError:
            pass

    if not text_sources:
        return True, "跳过 (无 manuscript 或 results 文件)"

    combined_text = '\n'.join(text_sources)

    # 3. 对每个 Figure 编号，grep 正文中是否有引用
    uncited = []
    for num in sorted(fig_numbers, key=lambda x: (x.startswith('S'), int(x.lstrip('S')))):
        # 匹配模式: Figure 1, Figure S1, Fig. 1, (Figure 1), (Fig. 1)
        patterns = [
            rf'\(Figure\s+{num}\)',       # (Figure 1)
            rf'Figure\s+{num}[^\.]',      # Figure 1: 或 Figure 1,
            rf'\(Fig\.?\s+{num}\)',       # (Fig. 1) 或 (Fig 1)
            rf'Fig\.?\s+{num}[^\.]',      # Fig. 1: 或 Fig 1,
        ]
        cited = any(re.search(p, combined_text, re.IGNORECASE) for p in patterns)
        if not cited:
            uncited.append(f"Figure {num}")

    if uncited:
        return False, (
            f"Figure 正文引用缺失 — {len(uncited)} 张图未在正文中引用:\n"
            + "\n".join(f"  • {f} — 请添加 (Figure N) 引用到 manuscript 或 Results 中" for f in uncited)
        )

    return True, f"Figure 正文引用完整: {len(fig_numbers)} 张图均被引用 ✓"


# ============================================================
# 闸门定义: 每个 Phase 执行的检查项
# ============================================================

GATE_DEFINITIONS = {
    "problem_definition": {
        "auto_checks": {
            "lit_precheck": check_literature_precheck_exists,
            "frame_complete": check_frame_assessment_complete,
            "data_availability": check_data_availability_confirmed,
        },
        "llm_checks": [
            "研究问题的临床重要性是否充分论述?",
            "数据源与方法的可行性是否确认?",
            "FRAME 评估各维度是否有定量数据支撑?",
            "PI 是否明确给出「启动/观望/放弃」建议?",
        ],
    },
    "design": {
        "auto_checks": {
            "baseline_included": check_baseline_included,
            "sensitivity_analysis_count": check_sensitivity_analysis_count,
            "subgroup_count": check_subgroup_count,
            "smd_balance": check_smd_balance,
        },
        "llm_checks": [
            "建模方案与临床问题是否对齐 (PICO-ML 映射)?",
            "SAP 是否包含样本量/缺失处理/敏感性分析?",
            "模型评估策略是否合理 (内部+外部验证)?",
        ],
    },
    "execution": {
        "auto_checks": {
            "auc_threshold": check_auc_threshold,
            "auc_trend": check_auc_trend,                  # 🆕 Δ-Gate: AUC 趋势监控
            "baseline_included": check_baseline_included,
            "n_jobs_safe": check_n_jobs_safe,
            "calibration_trend": check_calibration_trend,  # 🆕 Δ-Gate: 校准度趋势
        },
        "llm_checks": [
            "模型选择层级是否合理 (baseline → 复杂模型)?",
            "特征选择是否在 CV 内部完成?",
            "可解释性报告是否完整 (SHAP + 方向确认 + 公平性)?",
            "校准度是否合格?",
        ],
    },
    "external_validation": {
        "auto_checks": {
            "n_jobs_safe": check_n_jobs_safe,
            "feature_stability": check_feature_stability,  # 🆕 特征稳定性跨Phase检查
            "auc_trend": check_auc_trend,                  # 🆕 外部验证也监控AUC趋势
        },
        "llm_checks": [
            "外部验证是否使用独立数据集?",
            "外部验证性能是否与内部验证可比?",
            "泛化性评估是否充分 (不同人群/时间)?",
        ],
    },
    "review": {
        "auto_checks": {
            "clinical_review_exists": check_clinical_review_exists,
            "pi_approval_exists": check_pi_approval_exists,
            "num_consistency_validated": check_num_consistency_validated,
            "method_fidelity": check_method_implementation_fidelity,
        },
        "llm_checks": [
            "临床审查是否确认了效应方向与预测因子合理性?",
            "PI 七项终审是否完整 (研究问题/方法/结果/讨论/结论/贡献/参考文献)?",
            "是否存在未被解释的统计异常?",
        ],
    },
    "writing": {
        "auto_checks": {
            "sap_exists": check_sap_exists,
            "journal_config_locked": check_journal_config_locked,
            "title_length": check_title_length,
            "sections_exist": check_sections_exist,
            "tables_exist": check_tables_exist,
            "figures_exist": check_figures_exist,
            "manuscript_assembled": check_manuscript_assembled,
            "abstract_word_count": check_abstract_word_count,
            "keywords_count": check_keywords_count,
            "all_refs_have_doi": check_all_refs_have_doi,
            "auc_has_ci": check_auc_has_ci,
            "effect_size_with_ci": check_effect_size_with_ci,
            "discrimination_calibration": check_discrimination_and_calibration_reported,
            "normality_test": check_normality_test_reported,
            "missing_data": check_missing_data_reported,
            "software_version": check_software_version_reported,
            "conclusion_heading": check_conclusion_heading_level,
            "doi_verified": check_doi_verification,
            "ref_count": check_ref_count,
            "ref_recency": check_ref_recency,
            "all_refs_cited": check_all_refs_cited_in_text,
            "discussion_paragraphs": check_discussion_four_paragraphs,
            "discussion_no_subheadings": check_discussion_no_subheadings,
            "discussion_no_conclusion": check_discussion_p4_no_conclusion,
            "humanize_quality": check_humanize_quality,
            "numerical_traceability": check_numerical_traceability,
            "baseline_compliance": check_baseline_compliance,
            "submission_integrity": check_submission_structure_integrity,
            "figure_naming": check_figure_naming_convention,
            "figure_has_image": check_all_figures_have_images,
            "figure_text_citation": check_figure_text_citation,
        },
        "llm_checks": [
            "Methods ↔ Results 是否 1:1 对应? (Methods 声明的每个分析方法在 Results 中是否有对应结果报告)",
            "Discussion 四段是否形成四个语义段落? (¶1 主要发现/¶2 文献对比/¶3 含义/¶4 局限, 非仅空行分隔)",
            "Conclusion 是否独立章节 (## Conclusion)?",
            "所有数值是否可追溯到上游分析输出?",
            "是否存在虚假引用或未读引用?",
            "参考文献时效性是否达标 (≥80% 近5年文献)?",
            "所有非通用缩写在首次出现时是否给出了全称 (全称 (ABBR) 格式)? 通用缩写 (DNA/RNA/BMI/CI/AUC/OR/HR/SD) 除外",
            "去 AI 味改写是否真正改善了文本自然度? (句子长度变化/段落节奏/转折自然性/模板痕迹/hedge 适度)",
        ],
    },
}

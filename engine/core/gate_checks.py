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


def check_data_dictionary_exists(outputs: dict, orch) -> tuple:
    """数据字典已产出: data/data_dictionary.md 存在且包含分类变量编码→标签映射

    防止 generate_tables.py 自行推测/硬编码分类标签导致定义错误传播到全文。
    """
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = _find_project_dir(orch, project_id)
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    dict_file = proj_dir / 'data' / 'data_dictionary.md'
    if not dict_file.exists():
        return False, (
            "data/data_dictionary.md 不存在 — "
            "data-engineer 必须产出中英双语数据字典, 包含所有分类变量的编码→标签映射"
        )

    try:
        content = dict_file.read_text(encoding='utf-8')
    except OSError:
        return False, "data/data_dictionary.md 无法读取"

    # 验证基本结构: 至少有一个分类变量定义了 code_value → label 映射
    # 检测 Markdown 表格格式: | var_name | code | label_en | ...
    has_table = bool(re.search(r'\|.*variable.*\|.*code.*\|.*label', content, re.IGNORECASE))
    has_rows = len(re.findall(r'^\|', content, re.MULTILINE)) >= 3  # header + separator + ≥1 row

    if not has_table or not has_rows:
        return False, (
            "data/data_dictionary.md 格式不正确 — "
            "须包含 Markdown 表格: | variable_name | code_value | label_en | label_zh | source_column |"
        )

    # 检查是否覆盖了项目中的分类变量 (扫描 outputs/ 目录的特征文件)
    var_names = set(re.findall(r'^\|\s*`?(\w+)`?\s*\|', content, re.MULTILINE))
    if len(var_names) < 2:  # 至少 2 个变量 (header 被误匹配的容错)
        return False, "data/data_dictionary.md 表格为空或变量数 < 2"

    return True, f"数据字典存在 ✓ ({len(var_names)} 个变量已定义编码→标签映射)"


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


# 所有分类模型的必备评估指标 — Phase 3 输出标准
_REQUIRED_EVAL_METRICS = {
    "auc": ["auc", "auc_roc", "mean_auc", "auc_mean", "mean"],
    "auc_ci": ["ci_low", "ci_high", "auc_ci"],
    "pr_auc": ["pr_auc", "pr_auc_score", "average_precision"],
    "brier": ["brier", "brier_score"],
    "calibration_slope": ["calibration_slope", "calib_slope"],
    "calibration_intercept": ["calibration_intercept", "calib_intercept"],
    "sensitivity": ["sensitivity", "sens", "tpr", "recall"],
    "specificity": ["specificity", "spec", "tnr"],
    "ppv": ["ppv", "precision", "positive_predictive_value"],
    "npv": ["npv", "negative_predictive_value"],
    "f1": ["f1", "f1_score"],
}

# 数据不平衡时额外要求
_REQUIRED_EVAL_METRICS_IMBALANCED = {
    "pr_auc": ["pr_auc", "pr_auc_score", "average_precision"],
}


def _flatten_model_metrics(cv_data: dict) -> dict[str, dict]:
    """从 cv_results.json 提取每个模型的指标字典 {model_id: {flat_metric_name: value}}

    处理嵌套结构: {auc: {mean: 0.84, ci_low:..., ci_high:...}} → mean_auc, ci_low, ci_high
    """
    models = {}
    candidates = cv_data.get("models", cv_data)

    for model_id, metrics in candidates.items():
        if not isinstance(metrics, dict):
            continue

        flat = {}
        for k, v in metrics.items():
            k_lower = str(k).lower()
            if isinstance(v, dict):
                # 嵌套: auc: {mean: 0.84, ci_low: 0.79, ci_high: 0.89}
                for sub_k, sub_v in v.items():
                    sub_k_lower = str(sub_k).lower()
                    # 保留原始 key 作为前缀: auc_mean, auc_ci_low, auc_ci_high
                    flat[f"{k_lower}_{sub_k_lower}"] = sub_v
                    # 也保留无前缀版本: mean, ci_low, ci_high
                    flat[sub_k_lower] = sub_v
            elif isinstance(v, (int, float)):
                flat[k_lower] = v
            elif isinstance(v, list) and all(isinstance(x, (int, float)) for x in v):
                flat[k_lower] = v  # e.g. cv_fold_aucs: [0.83, 0.85, ...]

        # 判定是否是模型指标 (包含至少一个评估相关 key)
        eval_keys = {"auc", "brier", "f1", "accuracy", "sensitivity", "specificity",
                      "precision", "recall", "calib", "pr_auc", "ci_low", "ci_high"}
        has_eval = any(
            any(ek in str(k).lower() for ek in eval_keys)
            for k in flat.keys()
        )
        if has_eval:
            models[model_id] = flat

    return models


def check_all_models_evaluated_completely(outputs: dict, orch) -> tuple:
    """所有模型的评估指标必须完整 — 主模型和 baseline 必须输出统一的必备指标集

    钱学森总体设计部: 接口格式标准化。任一模型缺 PR-AUC/Brier/Calib Slope → Gate 3 FAIL。

    起因: 2026-05-13 发现 train_model.py 只为主模型算全量指标, baseline 模型仅输出 AUC,
    导致 Table 2 中非主模型缺失关键指标。
    """
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
        # 也尝试从 agent output 中检测
        for agent_id, output in outputs.items():
            if "ml-engineer" in agent_id.lower():
                if "auc" in output.lower() and "brier" not in output.lower():
                    return False, (
                        "ml-engineer 输出中检测到 AUC 但未检测到 Brier/Calibration 指标。"
                        "train_model.py 必须对所有模型输出统一评估指标集: "
                        "AUC + PR-AUC + Brier + Calib Slope + Sens/Spec + F1"
                    )
        return True, "跳过 (无法定位项目目录, 已从 Agent 输出做基本检查)"

    # 读取 cv_results.json
    cv_paths = list(proj_dir.glob('models/cv_results.json')) + \
               list(proj_dir.glob('data/cv_results.json')) + \
               list(proj_dir.glob('outputs/cv_results.json'))
    if not cv_paths:
        return True, "跳过 (未找到 cv_results.json)"

    try:
        cv_data = json.loads(cv_paths[0].read_text())
    except (json.JSONDecodeError, OSError):
        return True, "跳过 (cv_results.json 无法解析)"

    models = _flatten_model_metrics(cv_data)
    if not models:
        return True, "跳过 (cv_results.json 中未检测到模型级别指标)"

    # 检查每个模型的必备指标
    missing_per_model = {}
    for model_id, metrics in models.items():
        flat_keys = {str(k).lower().replace(" ", "_").replace("-", "_") for k in metrics.keys()}
        missing = []
        for metric_name, aliases in _REQUIRED_EVAL_METRICS.items():
            if not any(a in flat_keys for a in aliases):
                missing.append(metric_name)
        if missing:
            missing_per_model[model_id] = missing

    if missing_per_model:
        lines = []
        for model_id, missing in missing_per_model.items():
            lines.append(
                f"  • {model_id}: 缺少 {', '.join(missing)}"
            )
        return False, (
            f"模型评估指标不完整 — {len(missing_per_model)} 个模型缺指标:\n"
            + "\n".join(lines)
            + "\n\ntrain_model.py 必须对所有模型输出统一指标集: "
            + "AUC+CI | PR-AUC | Brier | Calib Slope/Intercept | Sens/Spec | PPV/NPV | F1"
        )

    return True, (
        f"模型评估指标完整: {len(models)} 个模型均包含全部 {len(_REQUIRED_EVAL_METRICS)} 类必备指标 ✓"
    )


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


def check_doi_title_match(outputs: dict, orch) -> tuple:
    """DOI 标题一致性检查 — 验证每个 DOI 解析到的论文标题与引用标题是否匹配。

    调用 CrossRef API 获取 DOI 对应的真实标题，与被引标题做模糊匹配。
    similarity < 0.7 → FAIL (DOI 指向不同论文)
    0.7 ≤ similarity < 0.85 → COND_PASS (待人工确认)
    similarity ≥ 0.85 → PASS
    """
    import difflib
    import html as html_mod
    import urllib.request, urllib.error
    import json as _json
    from pathlib import Path

    # 找到项目目录 (outputs 中可能包含 project_dir)
    project_dir = None
    for _, output in outputs.items():
        if isinstance(output, str) and "project_dir" not in output.lower():
            continue
    # 从 orch 获取 project_dir
    if hasattr(orch, 'project_dir'):
        project_dir = Path(orch.project_dir)
    elif hasattr(orch, 'config') and hasattr(orch.config, 'project_dir'):
        project_dir = Path(orch.config.project_dir)

    if not project_dir:
        return True, "跳过 (无法确定 project_dir)"

    refs_file = project_dir / "sections" / "08_references.md"
    if not refs_file.exists():
        return True, "跳过 (08_references.md 不存在)"

    refs_text = refs_file.read_text()

    # 逐条解析引用: {ref_num, cited_title, doi}
    refs = []
    lines = refs_text.split('\n')
    for line in lines:
        m = re.match(r'^(\d+)\.\s+', line)
        if not m:
            continue
        ref_num = int(m.group(1))
        # 提取 DOI
        doi_m = re.search(r'(10\.\d{4,}/[^\s"\']+)', line)
        if not doi_m:
            continue
        doi = doi_m.group(1).rstrip('.').rstrip(',')
        # 提取被引标题: 位于 "et al. " 或 ". " 之后，到 ". <Journal>" 之前
        # 模式: Authors . Title text . Journal ...
        cited_title = None
        # Strip authors part: everything before and including "et al. " or last author pattern
        title_match = re.match(
            r'^\d+\.\s+'           # ref number
            r'(?:[A-Z][a-z]+\s+[A-Z]\.?,?\s*)+'  # author surnames + initials
            r'(?:et al\.?\s*)?'    # optional et al
            r'[.\s]*'              # separator
            r'(.+?)'               # TITLE (captured)
            r'\.\s+'               # period + space
            r'[A-Z][a-z]+'         # Journal name start (capitalized)
            , line)
        if title_match:
            cited_title = title_match.group(1).strip()
        else:
            # Fallback: try to extract between ". " after et al and ". " before journal
            # Simpler approach: find the title between two significant periods
            parts = re.split(r'\.\s+(?=[A-Z])', line)
            if len(parts) >= 3:
                # parts[0] = ref num + authors, parts[1] = title, parts[2:] = journal etc
                cited_title = parts[1].strip()

        if cited_title:
            # Clean the title
            cited_title = re.sub(r'\[Classic[^]]*\]', '', cited_title).strip()
            cited_title = re.sub(r'\s+', ' ', cited_title)
            refs.append({
                "num": ref_num,
                "cited_title": cited_title,
                "doi": doi,
            })

    if not refs:
        return True, "跳过 (未解析到带 DOI 的引用)"

    # 连通性探针 — CrossRef 不可达时优雅降级
    try:
        probe_url = "https://api.crossref.org/works/10.1001/jama.2017.18391"
        probe_req = urllib.request.Request(probe_url, headers={"User-Agent": "CMRC-GateCheck/1.0"})
        urllib.request.urlopen(probe_req, timeout=5)
        crossref_ok = True
    except Exception:
        crossref_ok = False

    if not crossref_ok:
        return True, f"CrossRef API 不可达 ({len(refs)} DOI 待验证, 仅依赖 check_doi_verification)"

    # 逐 DOI 调用 CrossRef
    mismatches = []
    errors = []
    for ref in refs:
        doi = ref["doi"]
        url = f"https://api.crossref.org/works/{doi}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "CMRC-GateCheck/1.0 (mailto:research@example.com)"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = _json.loads(resp.read().decode())
            msg = data.get("message", {})
            crossref_title = msg.get("title", [""])[0]
            if not crossref_title:
                errors.append(f"[{ref['num']}] DOI {doi}: CrossRef 无标题数据")
                continue
        except urllib.error.HTTPError as e:
            if e.code == 404:
                errors.append(f"[{ref['num']}] DOI {doi}: CrossRef 404 (fake DOI)")
            else:
                errors.append(f"[{ref['num']}] DOI {doi}: HTTP {e.code}")
            continue
        except Exception as e:
            errors.append(f"[{ref['num']}] DOI {doi}: {str(e)[:80]}")
            continue

        # 标题归一化比较
        cited_clean = html_mod.unescape(ref["cited_title"]).lower()
        crossref_clean = html_mod.unescape(crossref_title).lower()
        # 去标点、规范化空格
        for ch in '.,;:()[]{}"\'!?-':
            cited_clean = cited_clean.replace(ch, ' ')
            crossref_clean = crossref_clean.replace(ch, ' ')
        cited_clean = ' '.join(cited_clean.split())
        crossref_clean = ' '.join(crossref_clean.split())

        similarity = difflib.SequenceMatcher(None, cited_clean, crossref_clean).ratio()

        if similarity < 0.7:
            mismatches.append(
                f"[{ref['num']}] cited=\"{ref['cited_title'][:100]}\" "
                f"CrossRef=\"{crossref_title[:100]}\" sim={similarity:.2f}"
            )
        elif similarity < 0.85:
            mismatches.append(
                f"[{ref['num']}] LOW sim={similarity:.2f}: "
                f"cited=\"{ref['cited_title'][:80]}\" vs CrossRef=\"{crossref_title[:80]}\""
            )

    # 判定
    if mismatches:
        fail_count = sum(1 for m in mismatches if "sim=" in m and float(re.search(r'sim=([\d.]+)', m).group(1)) < 0.7)
        if fail_count > 0:
            return False, f"DOI-标题不匹配 ({fail_count} FAIL): {'; '.join(mismatches[:5])}"
        return False, f"DOI-标题低相似 ({len(mismatches)} COND_PASS): {'; '.join(mismatches[:3])}"

    if errors:
        return True, f"标题匹配通过 (DOI 解析: {len(refs)-len(errors)} OK, {len(errors)} 网络/API 错误, 委托 check_doi_verification)"

    return True, f"DOI-标题匹配通过 ({len(refs)}/{len(refs)} similarity ≥ 0.85)"


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


def check_discussion_seven_paragraphs(outputs: dict, orch) -> tuple:
    """Discussion 七段结构检测 — 按空行拆段, ≥6段 + ¶3/¶4含文献引用 + ¶7含局限"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            if "## Discussion" not in output:
                return True, "跳过 (无 Discussion 章节)"

            # 提取 Discussion 内容
            disc_match = re.search(r'## Discussion\n(.*?)(?=##\s|\Z)', output, re.DOTALL)
            if not disc_match:
                return True, "跳过"
            disc = disc_match.group(1)

            # 按空行拆段 (≥2个连续换行)
            paragraphs = re.split(r'\n{2,}', disc.strip())
            paragraphs = [p.strip() for p in paragraphs if p.strip()]

            if len(paragraphs) < 6:
                return False, (
                    f"Discussion 仅 {len(paragraphs)} 段空行分隔, 需 ≥6 段 "
                    f"(七段式: ¶1核心发现/¶2机制解释/¶3文献一致/¶4文献不一致/¶5含义/¶6优势/¶7局限+未来方向)"
                )

            # 检测文献引用是否集中在中段 (¶2-¶5 ≈ literature comparison area)
            # Discussion 必须包含文献引用, 但不在 ¶1 强制检查
            has_citations = bool(re.search(r'\[\d+', disc))
            if not has_citations:
                return False, "Discussion 未检测到任何文献引用 — 文献对比 (¶3/¶4) 必须引用文献"

            # 检测末段是否含局限相关关键词
            last_para = paragraphs[-1]
            has_limitations = bool(
                re.search(r'limitation|局限|limitation|limitations', last_para, re.I)
            )
            if not has_limitations:
                return False, "Discussion 末段 (¶7) 应包含局限性讨论"

            # 检测是否有机制解释区域 (¶2)
            # 在前 1/3 区域内搜索 mechanism/explain/interpret/pathway
            first_third_idx = max(1, len(paragraphs) // 3)
            early_content = '\n'.join(paragraphs[:first_third_idx])
            has_explanation = bool(re.search(
                r'mechanism|pathway|explanation|explain|interpret|'
                r'may reflect|one possible|likely reflects|'
                r'可能机制|可能原因|解释',
                early_content, re.I
            ))
            if not has_explanation:
                return False, (
                    "Discussion 前段 (¶2 区域) 应包含发现解读/机制解释 "
                    "(mechanism/explanation/pathway/may reflect...)"
                )

            return True, f"Discussion 七段结构检测通过 ({len(paragraphs)} 段空行分隔)"
    return True, "跳过"


def check_discussion_last_para_no_conclusion(outputs: dict, orch) -> tuple:
    """Discussion 末段 (¶7) 末尾无结论性收束句 — 以局限缓解说明+未来方向收尾, 不加总结标语"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            if "## Discussion" not in output:
                return True, "跳过"
            # 提取 Discussion 到 Conclusion 之间的内容
            disc_match = re.search(r'## Discussion\n(.*?)(?=## Conclusion|\Z)', output, re.DOTALL)
            if not disc_match:
                return True, "跳过"
            disc_content = disc_match.group(1)

            # 检查 Discussion 末段是否有结论性收束
            prohibited = [
                "In conclusion", "Taken together", "Overall", "In summary",
                "我们的研究表明", "综上所述", "总而言之",
                "paving the way", "ushering in", "highlighting the potential",
            ]
            # 取 Discussion 最后 500 字符 (末段区域)
            last_part = disc_content[-500:] if len(disc_content) > 500 else disc_content
            for phrase in prohibited:
                if phrase.lower() in last_part.lower():
                    return False, f"Discussion 末段 (¶7) 含结论性收束短语: '{phrase}'"
            return True, "Discussion 末段无结论性收束句 ✓"
    return True, "跳过"


def check_discussion_explanation_section(outputs: dict, orch) -> tuple:
    """Discussion ¶2 区域包含发现解读/机制解释 — 对齐 JAMA Editors Guide §2 'Possible explanations'"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            if "## Discussion" not in output:
                return True, "跳过 (无 Discussion 章节)"
            disc_match = re.search(r'## Discussion\n(.*?)(?=##\s|\Z)', output, re.DOTALL)
            if not disc_match:
                return True, "跳过"
            disc = disc_match.group(1)

            # 按空行拆段
            paragraphs = re.split(r'\n{2,}', disc.strip())
            paragraphs = [p.strip() for p in paragraphs if p.strip()]

            if len(paragraphs) < 3:
                return True, "跳过 (段落数不足)"

            # 在前 1/3 区域搜索机制解释关键词
            first_third_idx = max(1, len(paragraphs) // 3)
            early_content = '\n'.join(paragraphs[:first_third_idx])

            explanation_patterns = [
                r'\bmechanism', r'\bpathway', r'\bexplanation', r'\bexplain',
                r'\binterpret', r'may reflect', r'likely reflects',
                r'one possible', r'alternative explanation',
                r'\b可能机制', r'\b可能原因', r'\b解释',
                r'role of', r'mediated by', r'attributable to',
            ]
            has_explanation = any(
                re.search(pat, early_content, re.I) for pat in explanation_patterns
            )
            if has_explanation:
                return True, "Discussion ¶2 区域含机制解释 ✓"
            return False, (
                "Discussion 前段 (¶2 区域) 缺少发现解读/机制解释. "
                "应讨论最可能的解释和替代解释 (JAMA §2 'Possible explanations')"
            )
    return True, "跳过"


# ============================================================
# Phase 6: 论文内容质量检查 (方案 A — P0 补充)
# ============================================================

def check_discussion_no_subheadings(outputs: dict, orch) -> tuple:
    """Discussion 不含任何形式子标题 — 七段靠逻辑过渡衔接 (2026-05-14 强化: 5种模式全覆盖)"""
    for agent_id, output in outputs.items():
        if "scientific-writer" in agent_id.lower() or "writing" in agent_id.lower():
            if "## Discussion" not in output:
                return True, "跳过 (无 Discussion 章节)"
            # 提取 Discussion 到下一个 ## 之间的内容
            disc_match = re.search(r'## Discussion\n(.*?)(?=##\s|\Z)', output, re.DOTALL)
            if not disc_match:
                return True, "跳过"
            disc_content = disc_match.group(1)

            # 模式1: ### 子标题
            h3 = re.findall(r'^### (.+)$', disc_content, re.MULTILINE)
            if h3:
                return False, f"Discussion 含 ### 子标题: {h3}"

            # 模式2: **粗体行** 作为伪子标题 (≤6 词的独立行) — 2026-05-14 新增
            bold_lines = re.findall(r'^\*\*(.+?)\*\*\s*$', disc_content, re.MULTILINE)
            fake_headings = [b.strip() for b in bold_lines if len(b.split()) <= 6]
            if fake_headings:
                return False, (
                    f"Discussion 含粗体伪子标题: {fake_headings}. "
                    f"七段应仅靠空行分隔, 不使用任何标记标示段落名称"
                )

            # 模式3: ___ 下划线分隔符 (≥3 个连续下划线独立成行)
            if re.search(r'^_{3,}\s*$', disc_content, re.MULTILINE):
                return False, "Discussion 含下划线分隔符 (疑似子标题标记)"

            # 模式4: 全大写段名行 (如 "PRINCIPAL FINDINGS" / "LIMITATIONS")
            caps = re.findall(r'^([A-Z][A-Z\s]{4,})$', disc_content, re.MULTILINE)
            # 排除常见的全大写缩写行 (如 "AUC" / "SHAP")
            caps = [c for c in caps if len(c.split()) >= 2]
            if caps:
                return False, f"Discussion 含全大写段名: {caps}"

            # 模式5: 编号段名 (如 "1. Findings" / "2. Literature Comparison")
            numbered = re.findall(r'^(\d+\.\s+\w.{2,})$', disc_content, re.MULTILINE)
            if numbered:
                return False, f"Discussion 含编号段名: {numbered}"

            return True, "Discussion 无任何形式子标题 ✓"
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


def _find_project_dir(orch, project_id: str):
    """在 knowledge base vaults 中定位项目目录"""
    from pathlib import Path
    if hasattr(orch, 'kb') and orch.kb:
        for _, vault_path in getattr(orch.kb, 'vaults', {}).items():
            candidate = Path(vault_path) / 'projects' / project_id
            if candidate.exists():
                return candidate
    return None


def _read_section_from_disk(project_dir, keyword: str) -> tuple:
    """从 sections/ 目录读取指定章节内容。
    返回 (file_path, section_body) 或 (None, None)。
    keyword: 'method' → 匹配 04_methods.md, 'result' → 匹配 05_results.md
    """
    from pathlib import Path
    sections_dir = project_dir / 'sections'
    if not sections_dir.exists():
        return None, None

    # 按文件名关键词匹配
    for f in sorted(sections_dir.glob('*.md')):
        if keyword in f.name.lower():
            try:
                content = f.read_text(encoding='utf-8')
                # 提取 ## Methods / ## Results 章节体
                heading_pattern = {
                    'method': r'^## Methods?\s*\n',
                    'result': r'^## Results?\s*\n',
                }
                pattern = heading_pattern.get(keyword, r'^## .*?\s*\n')
                m = re.search(
                    pattern + r'(.*?)(?=\n## [A-Z]|\Z)',
                    content, re.DOTALL | re.MULTILINE
                )
                if m:
                    return f, m.group(1)
                # fallback: 如果章节标题匹配失败, 返回全文
                return f, content
            except OSError:
                return None, None
    return None, None


def check_methods_excessive_subsections(outputs: dict, orch) -> tuple:
    """Methods 子标题不超过 5 个(五大标准段落), 防止 checklist→header 映射导致章节碎片化

    从 sections/ 磁盘文件读取(源真值), 而非依赖 Agent 输出文本。
    """
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = _find_project_dir(orch, project_id)
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    filepath, methods_body = _read_section_from_disk(proj_dir, 'method')
    if methods_body is None:
        return True, "跳过 (找不到 Methods section 文件)"

    # 提取所有 ### 子标题行
    subs = re.findall(r'^###\s+(.+)$', methods_body, re.MULTILINE)

    # 使用小写子串匹配，容忍单复数/措辞变体
    METHODS_STANDARD = [
        "study design",
        "study population",
        "outcome",           # covers "Outcomes and Predictors", "Outcome Definition"
        "statistical analysis",
        "sensitivity",       # covers "Sensitivity Analysis/Analyses", "Subgroup and Sensitivity Analyses"
    ]

    def _is_standard(sub: str) -> bool:
        return any(kw in sub.lower() for kw in METHODS_STANDARD)

    if len(subs) > 5:
        # 分类: 哪些是标准的, 哪些是多余的
        matched_std = []
        extra = []
        for s in subs:
            s_clean = s.strip()
            if _is_standard(s_clean):
                matched_std.append(s_clean)
            else:
                extra.append(s_clean)

        # 为每个多余子标题给出合并建议
        merge_hints = []
        for e in extra:
            if any(kw in e.lower() for kw in ['population', 'inclusion', 'exclusion', 'cohort', 'dependency']):
                merge_hints.append(f"    - \"{e}\" → 合并到 ### Study Population")
            elif any(kw in e.lower() for kw in ['outcome', 'endpoint', 'frailty index', 'efi', 'definition']):
                merge_hints.append(f"    - \"{e}\" → 合并到 ### Outcomes and Predictors")
            elif any(kw in e.lower() for kw in ['feature', 'model tier', 'model development', 'validation', 'incremental', 'temporal', 'interpretation', 'shap']):
                merge_hints.append(f"    - \"{e}\" → 合并到 ### Statistical Analysis")
            elif any(kw in e.lower() for kw in ['ethic', 'reproducib', 'data availab']):
                merge_hints.append(f"    - \"{e}\" → 移到 Declarations 或单独的 Ethics Statement")
            elif any(kw in e.lower() for kw in ['reference', 'cited']):
                merge_hints.append(f"    - \"{e}\" → 移除 (References 不应出现在 Methods 内)")
            else:
                merge_hints.append(f"    - \"{e}\" → 合并到五大标准段落之一或删除")

        hints_text = "\n".join(merge_hints) if merge_hints else "  请将额外内容整合到五大标准段落中"

        return False, (
            f"Methods 有 {len(subs)} 个 ### 子标题, 超过上限 5。\n"
            f"  当前子标题 ({len(subs)} 个): {subs}\n"
            f"  合并建议:\n{hints_text}"
        )

    if len(subs) < 5:
        covered = {kw for kw in METHODS_STANDARD if any(kw in s.lower() for s in subs)}
        missing = [kw for kw in METHODS_STANDARD if kw not in covered]
        return False, (
            f"Methods 仅有 {len(subs)} 个 ### 子标题, 缺少标准段落: {missing}"
        )

    return True, f"Methods 子标题数 {len(subs)} ✓ (标准五段)"


def check_results_excessive_subsections(outputs: dict, orch) -> tuple:
    """Results 子标题不超过 5 个(五大标准段落), 防止 ad-hoc 碎片化

    从 sections/ 磁盘文件读取(源真值), 而非依赖 Agent 输出文本。
    """
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = _find_project_dir(orch, project_id)
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    filepath, results_body = _read_section_from_disk(proj_dir, 'result')
    if results_body is None:
        return True, "跳过 (找不到 Results section 文件)"

    subs = re.findall(r'^###\s+(.+)$', results_body, re.MULTILINE)

    RESULTS_STANDARD = [
        "study population",
        "model performance",
        "feature importance",
        "secondary and subgroup",
        "sensitivity",
    ]

    def _is_standard(sub: str) -> bool:
        return any(kw in sub.lower() for kw in RESULTS_STANDARD)

    if len(subs) > 5:
        matched_std = []
        extra = []
        for s in subs:
            s_clean = s.strip()
            if _is_standard(s_clean):
                matched_std.append(s_clean)
            else:
                extra.append(s_clean)

        merge_hints = []
        for e in extra:
            if any(kw in e.lower() for kw in ['population', 'baseline', 'flow', 'cohort']):
                merge_hints.append(f"    - \"{e}\" → 合并到 ### Study Population and Baseline Characteristics")
            elif any(kw in e.lower() for kw in ['auc', 'performance', 'roc', 'calibration', 'discrimination', 'brier']):
                merge_hints.append(f"    - \"{e}\" → 合并到 ### Model Performance")
            elif any(kw in e.lower() for kw in ['feature', 'importance', 'shap', 'predictor', 'coefficient']):
                merge_hints.append(f"    - \"{e}\" → 合并到 ### Feature Importance and Model Interpretation")
            elif any(kw in e.lower() for kw in ['subgroup', 'secondary', 'sex', 'age', 'stratif']):
                merge_hints.append(f"    - \"{e}\" → 合并到 ### Secondary and Subgroup Analyses")
            elif any(kw in e.lower() for kw in ['sensitivity', 'robust']):
                merge_hints.append(f"    - \"{e}\" → 合并到 ### Sensitivity Analyses")
            else:
                merge_hints.append(f"    - \"{e}\" → 合并到五大标准段落之一或删除")

        hints_text = "\n".join(merge_hints) if merge_hints else "  请将额外结果按标准五段流程组织"

        return False, (
            f"Results 有 {len(subs)} 个 ### 子标题, 超过上限 5。\n"
            f"  当前子标题 ({len(subs)} 个): {subs}\n"
            f"  合并建议:\n{hints_text}"
        )

    if len(subs) < 5:
        covered = {kw for kw in RESULTS_STANDARD if any(kw in s.lower() for s in subs)}
        missing = [kw for kw in RESULTS_STANDARD if kw not in covered]
        return False, (
            f"Results 仅有 {len(subs)} 个 ### 子标题, 缺少标准段落: {missing}"
        )

    return True, f"Results 子标题数 {len(subs)} ✓ (标准五段)"


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

            # --- 4. Hedge 密度 (Discussion ¶5 临床含义段 + Conclusion) ---
            # 提取 Discussion ¶5 (临床含义段落) 和 Conclusion
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
                # 七段式中 ¶5 临床含义位于后 1/3 区域 (¶6优势/¶7局限在最后)
                disc_paragraphs = [p for p in disc_content.split('\n\n') if len(p.strip()) > 30]
                if len(disc_paragraphs) >= 5:
                    # ¶5 位于倒数第3-4段区域 (七段: .../¶4文献不一致/¶5含义/¶6优势/¶7局限)
                    para5_candidates = disc_paragraphs[-4:-2]  # 取倒数第3-4段
                    para5_text = ' '.join(para5_candidates)
                    para5_hedges = len(hedge_pattern.findall(para5_text))
                    if para5_hedges > 3:
                        violations.append(
                            f"Discussion ¶5 (临床含义) hedge 过多: {para5_hedges} 个 (限 ≤ 3)"
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
               list(proj_dir.glob('data/cv_results.json')) + \
               list(proj_dir.glob('outputs/cv_results.json'))
    if not cv_paths:
        return False, "数值追踪失败: 未找到 cv_results.json (Phase 3 基线文件缺失，无法执行数值追踪。请返回 Phase 3 完成模型训练并产出 cv_results.json)"

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

    # 🆕 强制要求: 有 Figure .png 就必须有对应 data.json (防止数值追踪静默跳过)
    figure_pngs = list(proj_dir.glob('figures/Figure*.png')) + \
                  list(proj_dir.glob('figures/figure*.png'))
    if figure_pngs and not figure_data_files:
        return False, (
            f"数值追踪失败: 发现 {len(figure_pngs)} 个 Figure .png 文件, "
            f"但没有任何 Figure*_data.json 文件。每个 Figure 必须同时产出 data.json, "
            f"缺失 data.json 将导致数值追踪无法执行。"
        )

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


def check_cohort_attrition_consistency(outputs: dict, orch) -> tuple:
    """Figure 1 的队列筛选数字必须与 cohort_attrition.json 一致, 禁止推测。

    检查逻辑:
    1. 定位项目目录
    2. 读取 outputs/cohort_attrition.json (Phase 3 产出, 真相源)
    3. 读取 figures/Figure1_*_data.json (Phase 6 产出)
    4. 对比每个 step 的 excluded/remaining 数字
    """
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

    # 1. 检查 cohort_attrition.json 是否存在
    cohort_paths = list(proj_dir.glob('outputs/cohort_attrition.json'))
    if not cohort_paths:
        return False, (
            "队列筛选一致性检查失败: 未找到 outputs/cohort_attrition.json。"
            "Phase 3 必须产出 cohort_attrition.json (记录每个筛选步骤的排除 N 和剩余 N)。"
            "请返回 Phase 3, 在数据清洗完成后立即输出此文件。"
        )

    try:
        cohort = json.loads(cohort_paths[0].read_text())
    except (json.JSONDecodeError, OSError):
        return False, "队列筛选一致性检查失败: outputs/cohort_attrition.json 无法解析"

    # 2. 检查 Figure 1 data.json
    fig1_data_paths = list(proj_dir.glob('figures/Figure1_*_data.json')) + \
                      list(proj_dir.glob('figures/figure1_*_data.json'))
    if not fig1_data_paths:
        return False, (
            "队列筛选一致性检查失败: 未找到 Figure1_*_data.json。"
            "Figure 1 必须产出对应的 data.json, 其筛选数字从 cohort_attrition.json 读取后写入。"
        )

    try:
        fig1 = json.loads(fig1_data_paths[0].read_text())
    except (json.JSONDecodeError, OSError):
        return False, f"队列筛选一致性检查失败: {fig1_data_paths[0].name} 无法解析"

    # 3. 对比每个 step 的 excluded/remaining
    violations = []
    cohort_steps = cohort.get('steps', [])
    fig1_steps = fig1.get('steps', [])

    if len(cohort_steps) != len(fig1_steps):
        violations.append(
            f"步数不一致: cohort_attrition={len(cohort_steps)}步, "
            f"Figure 1 data={len(fig1_steps)}步"
        )
    else:
        for i, (cs, fs) in enumerate(zip(cohort_steps, fig1_steps)):
            for key in ('excluded', 'remaining'):
                cv = cs.get(key)
                fv = fs.get(key)
                if cv is None or fv is None:
                    violations.append(f"Step {i+1}: {key} 缺失")
                elif isinstance(cv, (int, float)) and isinstance(fv, (int, float)):
                    if cv != fv:
                        violations.append(
                            f"Step {i+1} ({cs.get('criterion','?')}): "
                            f"{key}={fv} (Figure 1) vs {cv} (cohort_attrition)"
                        )

    # 4. 对比 final_n / event_n
    for key in ('final_n', 'event_n'):
        cv = cohort.get(key)
        fv = fig1.get(key)
        if cv is not None and fv is not None and cv != fv:
            violations.append(f"{key}={fv} (Figure 1) vs {cv} (cohort_attrition)")

    if violations:
        return False, (
            f"队列筛选一致性检查失败 — Figure 1 数字与 cohort_attrition.json 不一致 "
            f"(推测或编造嫌疑):\n" + "\n".join(f"  • {v}" for v in violations[:5])
        )

    return True, (
        f"队列筛选一致性通过: Figure 1 的 {len(cohort_steps)} 步筛选数字与 "
        f"cohort_attrition.json 完全一致 ✓"
    )


# ================================================================
# 医学论文数值精度标准 — 钱学森总体设计部: 接口格式标准化
# ================================================================

# 精度规范: 每个指标类型的期望小数位数
NUMERICAL_PRECISION_STANDARDS = {
    "auc": 3,           # AUC / C-statistic / C-index → 0.842
    "p_value": 3,       # p 值 → 0.032 (p < 0.001 除外)
    "or": 2,            # Odds Ratio → 1.34
    "hr": 2,            # Hazard Ratio → 0.78
    "rr": 2,            # Risk Ratio → 1.25
    "percentage": 1,    # 百分比 → 84.2%
    "effect_size": 2,   # Cohen's d / Hedges' g → 0.45
    "sample_size": 0,   # 样本量/计数 → 整数
    "ci": None,         # 95% CI — 精度与点估计一致(不独立检查)
}

# 指标识别正则: (标签, 模式, 数值捕获组位置)
_METRIC_PATTERNS = [
    # AUC
    ("auc", [
        r'(?:AUC|c[-\s]?statistic|c[-\s]?index|AUROC)\s*(?:=|:|=|was|of)\s*(\d+\.\d+)',
        r'area under the (?:ROC\s*)?curve\s*(?:=|:|=|was|of)\s*(\d+\.\d+)',
    ]),
    # p 值
    ("p_value", [
        r'[Pp]\s*[=<]\s*(\d+\.\d+)',
        r'[Pp]\s*value\s*[=<]\s*(\d+\.\d+)',
    ]),
    # OR
    ("or", [
        r'(?:OR|odds\s*ratio)\s*(?:=|:)\s*(\d+\.\d+)',
        r'(?:OR|odds\s*ratio)\s*(?:of|=)\s*(\d+\.\d+)',
    ]),
    # HR
    ("hr", [
        r'(?:HR|hazard\s*ratio)\s*(?:=|:)\s*(\d+\.\d+)',
        r'(?:HR|hazard\s*ratio)\s*(?:of|=)\s*(\d+\.\d+)',
    ]),
    # RR
    ("rr", [
        r'(?:RR|risk\s*ratio|relative\s*risk)\s*(?:=|:)\s*(\d+\.\d+)',
    ]),
    # Percentage
    ("percentage", [
        r'(\d+\.\d+)%',
        r'(\d+\.\d+)\s*percent',
    ]),
    # Effect size
    ("effect_size", [
        r"(?:Cohen'?s?\s*d|Hedges'?\s*g)\s*(?:=|:|=)\s*(\d+\.\d+)",
    ]),
    # Sample size (integer counts)
    ("sample_size", [
        r'(?:[Nn]\s*=\s*)(\d{4,})',
        r'(?:n\s*=\s*)(\d{3,})',
        r'(?:included|enrolled|recruited|analyzed)\s+(\d{3,})',
    ]),
]


def check_numerical_precision_consistency(outputs: dict, orch) -> tuple:
    """跨 manuscript/tables/figures 数值精度一致性检查

    钱学森总体设计部: 接口格式标准化。同一指标在全文中必须使用相同的小数位数。
    例如 AUC 在图注中为 0.8423 (4位), 在正文中为 0.842 (3位) → FAIL。

    起因: 2026-05-13 发现 generate_figures.py 输出 raw float (4位) 写入 figure caption,
    但 scientific-writer 按医学惯例舍入到 3 位。check_numerical_traceability 的 0.1%
    偏差阈值太宽 (4→3位舍入偏差仅 0.036%), 未捕获此不一致。
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

    # 1. 收集所有文本源
    text_sources = {}  # {source_label: text}

    manuscript = proj_dir / 'submission' / 'manuscript.md'
    if manuscript.exists():
        try:
            text_sources['manuscript.md'] = manuscript.read_text()
        except OSError:
            pass

    for tf in proj_dir.glob('tables/*.md'):
        try:
            text_sources[f'tables/{tf.name}'] = tf.read_text()
        except OSError:
            pass

    for cf in proj_dir.glob('figures/*caption*.md'):
        try:
            text_sources[f'figures/{cf.name}'] = cf.read_text()
        except OSError:
            pass

    # 也检查 submission 层
    for tf in proj_dir.glob('submission/tables/*.csv'):
        try:
            text_sources[f'submission/{tf.name}'] = tf.read_text()
        except OSError:
            pass

    if len(text_sources) < 2:
        return True, "跳过 (文本源不足 2 个, 无法交叉比较精度)"

    # 2. 按指标类型提取 (metric_type, value, decimal_places, source) 四元组
    from collections import defaultdict
    metric_values = defaultdict(list)  # {metric_type: [(value_str, decimal_places, source)]}

    for source, text in text_sources.items():
        for metric_type, patterns in _METRIC_PATTERNS:
            for pat in patterns:
                for m in re.finditer(pat, text, re.IGNORECASE):
                    val_str = m.group(1)
                    try:
                        val = float(val_str)
                    except ValueError:
                        continue
                    # 跳过明显不是指标值的数字 (如年份 2023, p < 0.001 字符串)
                    if metric_type == "sample_size" and val < 100:
                        continue
                    if metric_type == "percentage" and (val < 0.1 or val > 100):
                        continue

                    # 计算小数位数
                    if '.' in val_str:
                        decimal_places = len(val_str.split('.')[1])
                    else:
                        decimal_places = 0

                    # 排除已格式化的 p < 0.001 (p value is a threshold statement)
                    if metric_type == "p_value":
                        before = text[max(0, m.start()-10):m.start()]
                        if re.search(r'<\s*$', before):  # "p < 0.001"
                            continue

                    metric_values[metric_type].append((val_str, decimal_places, source))

    if not metric_values:
        return True, "跳过 (未检测到任何数值指标)"

    # 3. 检查精度一致性
    violations = []
    checked_groups = 0

    for metric_type, entries in metric_values.items():
        if len(entries) < 2:
            continue  # 单一出现, 无法比较

        checked_groups += 1

        # 按小数位数分组
        precision_groups = defaultdict(list)  # {decimal_places: [(val_str, source)]}
        for val_str, dp, source in entries:
            precision_groups[dp].append((val_str, source))

        if len(precision_groups) <= 1:
            continue  # 所有同类型值精度一致

        # 检查是否违反期望标准
        expected_dp = NUMERICAL_PRECISION_STANDARDS.get(metric_type)
        nonstandard = []
        for dp, vals in precision_groups.items():
            if expected_dp is not None and dp != expected_dp:
                examples = [f"{v[0]} ({v[1]})" for v in vals[:3]]
                nonstandard.append(
                    f"{dp} 位小数 (期望 {expected_dp} 位): {', '.join(examples)}"
                )

        # 构建违规详情
        precision_summary = []
        for dp in sorted(precision_groups.keys()):
            vals = precision_groups[dp]
            examples = [f"{v[0]} ({v[1]})" for v in vals[:3]]
            marker = " ✓" if (expected_dp is None or dp == expected_dp) else " ✗"
            precision_summary.append(
                f"  {dp} 位小数{marker}: {', '.join(examples)}"
                + (f" ...共{len(vals)}处" if len(vals) > 3 else "")
            )

        metric_label = {
            "auc": "AUC/C-statistic", "p_value": "p值", "or": "OR",
            "hr": "HR", "rr": "RR", "percentage": "百分比",
            "effect_size": "效应量", "sample_size": "样本量",
        }.get(metric_type, metric_type)

        violations.append(
            f"{metric_label} 精度不一致 ({len(precision_groups)} 种精度):\n"
            + "\n".join(precision_summary)
        )

    if violations:
        return False, (
            f"数值精度一致性不通过 — {len(violations)} 类指标精度不统一:\n\n"
            + "\n\n".join(violations)
            + "\n\n原因: generate_figures.py 输出 raw float, 但 manuscript 按医学惯例舍入。"
            + "\n修复: generate_figures.py 中所有数值输出必须按精度标准舍入: "
            + ", ".join(f"{k}={v}位" for k, v in NUMERICAL_PRECISION_STANDARDS.items() if v is not None)
        )

    return True, (
        f"数值精度一致性通过: {checked_groups} 类指标精度统一 ✓"
        + (f" (标准: {', '.join(f'{k}={v}位' for k, v in NUMERICAL_PRECISION_STANDARDS.items() if v is not None)})"
           if checked_groups > 0 else "")
    )


# Table 2 必备列定义
_TABLE2_REQUIRED_COLUMNS = [
    "model",           # 模型名称
    "auc",             # AUC (ROC)
    "auc_ci",          # AUC 95% CI
    "pr_auc",          # PR-AUC
    "brier",           # Brier Score
    "calib_slope",     # Calibration Slope
    "sensitivity",     # Sensitivity
    "specificity",     # Specificity
    "f1",              # F1 Score
]


def check_table2_content_completeness(outputs: dict, orch) -> tuple:
    """Table 2 (模型性能对比) 必须包含所有必备列, 且行数 ≥ cv_results.json 模型数

    钱学森总体设计部: 交付件接口标准化。缺列/缺行 → Gate 6 FAIL。

    起因: 2026-05-13 发现 Table 2 非主模型缺少 PR-AUC | Brier | Calib Slope,
    根因是 Phase 3 train_model.py 未对基线模型计算全量指标, 且 Gate 6 无内容完整性检查。
    """
    import json
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

    # 1. 读取 Table 2
    table2_paths = list(proj_dir.glob('tables/table2*.md')) + \
                   list(proj_dir.glob('tables/*model_performance*.md')) + \
                   list(proj_dir.glob('tables/Table2*.md'))
    if not table2_paths:
        return False, "Table 2 文件不存在 (tables/table2_model_performance.md)"

    try:
        table2_text = table2_paths[0].read_text()
    except OSError:
        return True, "跳过 (无法读取 Table 2)"

    violations = []

    # 2. 检查列完整性 — 表头行
    header_match = re.search(r'^\|(.+)\|', table2_text, re.MULTILINE)
    if not header_match:
        return False, "Table 2 无 Markdown 表头行 (| column1 | column2 | ...)"

    header_text = header_match.group(1).lower()
    table_rows = [r.strip() for r in table2_text.split('\n') if r.strip().startswith('|')]
    data_rows = [r for r in table_rows if not re.match(r'^\|[\s\-:]+\|$', r)]  # 排除分隔行
    data_rows = data_rows[1:]  # 跳过表头

    # 列别名映射
    column_aliases = {
        "model": ["model", "模型"],
        "auc": ["auc", "auroc", "c-statistic", "c-stat"],
        "auc_ci": ["95% ci", "ci", "confidence", "置信区间"],
        "pr_auc": ["pr-auc", "pr auc", "prauc", "precision-recall"],
        "brier": ["brier"],
        "calib_slope": ["calib", "calibration", "slope"],
        "sensitivity": ["sensitivity", "sens", "tpr", "recall"],
        "specificity": ["specificity", "spec", "tnr"],
        "f1": ["f1", "f1-score", "f1 score"],
    }

    missing_cols = []
    for col_key, aliases in column_aliases.items():
        if not any(a in header_text for a in aliases):
            missing_cols.append(col_key)

    if missing_cols:
        violations.append(
            f"Table 2 缺少 {len(missing_cols)} 个必备列: {', '.join(missing_cols)}"
        )

    # 3. 检查行数 — 至少等于 cv_results.json 中模型数
    model_count_from_cv = len(data_rows)  # 默认以 Table 2 行数为准
    cv_paths = list(proj_dir.glob('models/cv_results.json')) + \
               list(proj_dir.glob('data/cv_results.json')) + \
               list(proj_dir.glob('outputs/cv_results.json'))
    if cv_paths:
        try:
            cv_data = json.loads(cv_paths[0].read_text())
            cv_models = _flatten_model_metrics(cv_data)
            if cv_models:
                model_count_from_cv = len(cv_models)
        except (json.JSONDecodeError, OSError):
            pass

    if len(data_rows) < model_count_from_cv or len(data_rows) < 2:
        violations.append(
            f"Table 2 数据行不足: {len(data_rows)} 行 (需 ≥{model_count_from_cv} 行, "
            f"至少包含主模型+baseline)"
        )

    # 4. 检查每行是否有空值 (|| 或 | |)
    empty_cell_rows = []
    for i, row in enumerate(data_rows):
        cells = [c.strip() for c in row.split('|')[1:-1]]  # 去掉首尾 |
        if any(c == '' or c == '-' or c == 'N/A' for c in cells[1:]):  # 跳过模型名列
            empty_cell_rows.append(f"行 {i+2}: {cells[0] if cells else '?'}")

    if empty_cell_rows:
        violations.append(
            f"Table 2 有 {len(empty_cell_rows)} 行含空值: "
            + "; ".join(empty_cell_rows[:5])
            + (f" ...等{len(empty_cell_rows)}行" if len(empty_cell_rows) > 5 else "")
        )

    if violations:
        return False, (
            f"Table 2 内容完整性不通过:\n"
            + "\n".join(f"  • {v}" for v in violations)
            + "\n\nTable 2 必备列: " + " | ".join(_TABLE2_REQUIRED_COLUMNS)
            + "\n所有模型(主模型+baseline)必须填充全部列, 不得留空。"
            + "\n如果 cv_results.json 中对应模型缺少某指标, 请回到 Phase 3 补充 train_model.py 评估。"
        )

    return True, (
        f"Table 2 内容完整: {len(data_rows)} 行 × 所有必备列 ✓"
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
                    list(proj_dir.glob('scripts/generate_figures.py')) + \
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
# KB 富化闸门检查 (kb_enrich)
# ============================================================

def check_doi_verified_for_new_entries(outputs: dict, orch) -> tuple:
    """新入库文献 DOI 全部经 CrossRef 验证, fake DOI 数必须为 0"""
    import json as _json
    combined = " ".join(str(v) for v in outputs.values())

    # 从输出中提取 DOI 验证结果
    fake_count = 0
    error_count = 0
    verified_count = 0

    # 尝试解析 ingest report
    for agent_id, output in outputs.items():
        if "research-assistant" in agent_id.lower():
            # 搜索 fake DOI 标记
            fake_matches = re.findall(r'(?:fake|FAKE|虚假).*?(\d+)', output)
            for m in fake_matches:
                fake_count += int(m)

            # 搜索验证统计
            verify_stats = re.findall(r'(\d+)/(\d+).*?verified', output)
            if verify_stats:
                verified_count = int(verify_stats[0][0])
                total = int(verify_stats[0][1])
                fake_count = total - verified_count

    if fake_count > 0:
        return False, f"DOI 验证失败 — {fake_count} 篇 fake DOI, 要求 fake DOI = 0"
    return True, "DOI 验证通过: 所有入库文献 DOI 真实 ✓"


def check_no_duplicate_in_kb(outputs: dict, orch) -> tuple:
    """新入库文献不与知识库已有文献重复"""
    combined = " ".join(str(v) for v in outputs.values())

    # 从入库报告的「统计概览」或「跳过清单」中提取重复跳过数量
    dup_count = 0
    # 模式: "重复跳过 | 3 篇" 或 "重复跳过: 3"
    dup_stats = re.findall(r'重复跳过\s*[:\|]\s*(\d+)', combined)
    if dup_stats:
        dup_count = sum(int(x) for x in dup_stats)

    # 模式: 统计概览表格中 "重复跳过" 行
    if not dup_count:
        dup_rows = re.findall(r'重复(?:跳过|已存在).*?(\d+)\s*篇', combined)
        if dup_rows:
            dup_count = sum(int(x) for x in dup_rows)

    # 计数跳过清单中的条目数
    skip_list_items = re.findall(r'\|.*?\|\s*重复\s*[—–-]', combined)
    if not dup_count and skip_list_items:
        dup_count = len(skip_list_items)

    # 重复不阻断 (正常现象), 仅报告
    if dup_count > 0:
        return True, f"去重正常: {dup_count} 篇已存在, 已跳过 (不阻断)"
    return True, "无重复文献 ✓"


def check_literature_note_yaml_complete(outputs: dict, orch) -> tuple:
    """新写入的文献笔记 YAML frontmatter 包含所有必填字段"""
    import json as _json
    required_fields = ["title", "first_author", "year", "journal", "doi",
                       "topics", "relevance_score", "date_read"]

    # 从输出中提取入库清单数据
    combined = " ".join(str(v) for v in outputs.values())

    # 检查是否有 "入库成功" 或 write_literature_note 调用
    ingest_success = re.findall(r'入库成功[:\s]*(\d+)', combined)
    if not ingest_success:
        # 可能没有新文献入库, 不阻断
        return True, "无新文献入库, 跳过 YAML 完整性检查"

    # 搜索可能的 frontmatter 缺失告警
    missing_warnings = re.findall(r'(?:missing|缺少|缺失).*?(field|字段|title|doi)', combined, re.IGNORECASE)
    if missing_warnings:
        return False, f"文献笔记 YAML frontmatter 缺少必填字段: {missing_warnings[:3]}"

    return True, "文献笔记 YAML frontmatter 完整 ✓"


def check_recency_of_ingested(outputs: dict, orch) -> tuple:
    """入库论文发表年份满足时效性要求 (近 2 年)"""
    import json as _json
    from datetime import datetime

    combined = " ".join(str(v) for v in outputs.values())
    current_year = datetime.now().year
    threshold_year = current_year - 2

    # 从 JSON 中提取 candidates[].year (精确提取, 避免匹配到数据年份如 CHARLS 2015)
    years = []
    json_blocks = re.findall(r'\{[^{}]*"candidates"\s*:\s*\[.*?\]\s*\}', combined, re.DOTALL)
    for block in json_blocks:
        try:
            data = _json.loads(block)
            for c in data.get("candidates", []):
                y = c.get("year")
                if isinstance(y, int) and 1900 < y < 2100:
                    years.append(y)
        except (_json.JSONDecodeError, TypeError):
            continue

    # 回退: 从 ingest report markdown 表格中提取年份 (| 1 | ... | ... | 2026 | ... |)
    if not years:
        year_cols = re.findall(r'\|\s*\d+\s*\|.*?\|\s*(\d{4})\s*\|', combined)
        for y_str in year_cols:
            y = int(y_str)
            if 1900 < y < 2100:
                years.append(y)

    if not years:
        return True, "无法从输出中提取论文发表年份, 跳过时效性检查 (非阻断)"

    old_papers = [y for y in years if y < threshold_year]
    if old_papers:
        return False, (
            f"入库文献时效性不达标 — {len(old_papers)} 篇超过 2 年:\n"
            + ", ".join(str(y) for y in old_papers[:5])
            + f"\n  要求: 入库文献应为 {threshold_year} 年及以后发表"
        )

    return True, f"入库文献时效性达标: {len(years)} 篇均在 {threshold_year} 年及以后 ✓"


# ============================================================
# Phase 6: 分类变量标签与亚组N计数一致性
# ============================================================


def check_categorical_label_consistency(outputs: dict, orch) -> tuple:
    """分类变量标签一致性: Table 1 的变量标签与 data/data_dictionary.md 一致

    防止 generate_tables.py 硬编码错误标签 (如 is_elective=0 → "Emergency" 应为 "Non-elective")。
    错误标签会传播到 Results/Discussion 导致全文自相矛盾。

    检查逻辑:
    1. 从 data/data_dictionary.md 加载编码→标签映射
    2. 扫描 Table 1 (Table1_baseline.md) 中分类变量的标签行
    3. 比较两者是否一致; 不一致则列出具体差异
    """
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = _find_project_dir(orch, project_id)
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    # 1. 加载数据字典
    dict_file = proj_dir / 'data' / 'data_dictionary.md'
    if not dict_file.exists():
        return True, "跳过 (无数据字典, 无法校验标签)"

    try:
        dict_content = dict_file.read_text(encoding='utf-8')
    except OSError:
        return True, "跳过 (数据字典读取失败)"

    # 解析: | var_name | code_value | label_en | label_zh | ...
    code_to_label = {}  # (var, code) → label_en
    label_set = set()    # 所有合法标签
    for line in dict_content.splitlines():
        cols = [c.strip().strip('`') for c in line.split('|')[1:-1]]
        if len(cols) >= 4 and cols[0] and cols[1] and cols[2]:
            var, code, label = cols[0], cols[1], cols[2]
            if var.lower() not in ('variable_name', 'variable', '---', ':'):
                code_to_label[(var.lower(), code.lower())] = label
                label_set.add(label.lower())

    if not label_set:
        return True, "跳过 (数据字典为空)"

    # 2. 扫描 Table 1
    table1 = proj_dir / 'tables' / 'Table1_baseline.md'
    if not table1.exists():
        return True, "跳过 (无 Table 1)"

    try:
        t1_content = table1.read_text(encoding='utf-8')
    except OSError:
        return True, "跳过 (Table 1 读取失败)"

    violations = []

    # 提取 Table 1 中的分类变量标签: 查找 "xxx, n (%)" 或 "xxx, n(%)" 模式
    # 例如: "Emergency admission, n (%)" → label candidate = "emergency admission"
    label_rows = re.findall(
        r'(?:^\|)?\s*([A-Za-z][A-Za-z\s/()-]+),\s*n\s*\(%\)',
        t1_content, re.MULTILINE | re.IGNORECASE
    )
    for row_label in label_rows:
        row_label_clean = row_label.strip().lower()
        # 跳过连续变量标签 (含 mean/SD/median/IQR/years 等)
        if any(kw in row_label_clean for kw in ['mean', 'sd', 'median', 'iqr', 'year', 'age']):
            continue
        # 检查该标签是否出现在数据字典中
        if row_label_clean not in label_set and row_label_clean not in label_set:
            # 它在字典里吗?
            found = any(
                row_label_clean == label.lower() or label.lower() in row_label_clean
                for label in label_set
            )
            if not found:
                # 尝试模糊匹配
                similar = [l for l in label_set if any(w in l for w in row_label_clean.split())]
                hint = f"  (字典中近似的标签: {similar[:3]})" if similar else "  (该标签未在数据字典中找到对应)"
                violations.append(f"Table 1 标签 \"{row_label.strip()}\" 不在数据字典中{hint}")

    if violations:
        return False, (
            f"分类变量标签不一致: {len(violations)} 处差异\n" +
            "\n".join(f"  - {v}" for v in violations[:5]) +
            ("\n  ..." if len(violations) > 5 else "")
        )

    return True, f"分类标签一致 ✓ (检查了 {len(label_rows)} 个变量标签)"


def check_subgroup_n_consistency(outputs: dict, orch) -> tuple:
    """亚组 N 一致性: Results 中的亚组 N 计数与 Table 1/Table 3 一致

    防止 scientific-writer 独立计算/推测亚组计数, 导致 Results 与 Tables 矛盾
    (如 Results 写 Emergency=11,892 但 Table 1=14,783)。

    检查逻辑:
    1. 从 Table 1 提取分类变量的 N-% 声明
    2. 从 Table 3 提取亚组分层 N
    3. 从 Results (sections/05_results.md) 提取所有 "N=xxx" / "n (%)" 声明
    4. 对同一分类变量, 交叉验证 N 总数和分层计数
    """
    from pathlib import Path

    project_id = getattr(orch, '_current_project_id', None)
    if not project_id:
        return True, "跳过 (无 project_id)"

    proj_dir = _find_project_dir(orch, project_id)
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    # 1. 读 Table 1, 提取分类变量的 N-% 声明
    table1 = proj_dir / 'tables' / 'Table1_baseline.md'
    t1_pairs = {}  # label → (N, pct)
    if table1.exists():
        try:
            t1_text = table1.read_text(encoding='utf-8')
            # 匹配模式: "Emergency admission, n (%) | 14,783 (75.3)" 或 "..., n (%) 14,783 (75.3)"
            for m in re.finditer(
                r'([A-Za-z][A-Za-z\s/()-]+),\s*n\s*\(\s*%\s*\)[^\d]*([\d,]+)\s*\(([\d.]+)%?\)',
                t1_text, re.IGNORECASE
            ):
                label = m.group(1).strip().lower()
                n_val = int(m.group(2).replace(',', ''))
                pct_val = float(m.group(3))
                t1_pairs[label] = (n_val, pct_val)
        except OSError:
            pass

    if not t1_pairs:
        return True, "跳过 (Table 1 无可提取的分类 N 数据)"

    # 2. 读 Results, 提取 N 声明
    results_file = None
    sections_dir = proj_dir / 'sections'
    if sections_dir.exists():
        for f in sections_dir.glob('*.md'):
            if 'result' in f.name.lower():
                results_file = f
                break

    if not results_file:
        return True, "跳过 (无 Results 文件)"

    try:
        results_text = results_file.read_text(encoding='utf-8')
    except OSError:
        return True, "跳过 (Results 读取失败)"

    violations = []

    # 对 Table 1 中每个分类变量, 在 Results 中搜索对应的 N 引用
    for label, (t1_n, t1_pct) in t1_pairs.items():
        # 匹配 Results 中对该变量的 N 引用: "XXX N=xxx" / "XXX (xxx, xx%)" / "xxx patients"
        # 使用 label 中的关键词在 Results 中搜索
        keywords = [w for w in label.split() if len(w) > 2 and w not in ('and', 'the', 'for', 'with')]
        if not keywords:
            continue

        # 在包含关键词的段落中搜索 N/百分比声明
        pattern = re.compile(
            r'(?:n\s*[=:]\s*|\()\s*([\d,]+)\s*(?:\)|patients|subjects)',
            re.IGNORECASE
        )
        # 先找到提及该变量的行
        context_lines = []
        for i, line in enumerate(results_text.splitlines()):
            if any(kw.lower() in line.lower() for kw in keywords[:2]):
                # 收集上下文 (±1 行)
                start = max(0, i - 1)
                end = min(len(results_text.splitlines()), i + 2)
                context_lines.extend(results_text.splitlines()[start:end])

        context = ' '.join(context_lines)
        for m in re.finditer(r'([\d,]+)\s*(?:patients|subjects|\((\d+\.?\d*)%\))', context, re.IGNORECASE):
            results_n = int(m.group(1).replace(',', ''))
            # 容忍 5% 以内的差异 (可能是小数舍入)
            diff_pct = abs(results_n - t1_n) / max(t1_n, 1) * 100
            if diff_pct > 5:
                violations.append(
                    f"\"{label}\": Table 1 N={t1_n} ({t1_pct}%), "
                    f"但 Results 中声明 N≈{results_n} (偏差 {diff_pct:.0f}%)"
                )
            break  # 每个变量只报告第一个矛盾

    if violations:
        return False, (
            f"亚组 N 计数不一致: {len(violations)} 处差异\n" +
            "\n".join(f"  - {v}" for v in violations[:3]) +
            ("\n  ..." if len(violations) > 3 else "")
        )

    return True, f"亚组 N 一致性通过 ✓ (检查了 {len(t1_pairs)} 个分类变量)"


# ============================================================
# Phase 7: 临床工具部署检查
# ============================================================

def check_clinical_model_loadable(outputs: dict, orch) -> tuple:
    """模型文件存在并可加载 — 验证 .pkl 模型存在且有 predict 方法"""
    import os as _os
    proj_dir = _find_project_dir(orch, getattr(orch, '_current_project_id', None) or "")
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    # 检查模型文件是否存在
    model_candidates = []
    for pattern in ["models/*.pkl", "models/*.joblib"]:
        if hasattr(proj_dir, 'glob'):
            model_candidates.extend(proj_dir.glob(pattern))
    if not model_candidates:
        return True, "跳过 (无 .pkl 模型文件)"

    # 尝试加载第一个模型
    model_path = model_candidates[0]
    if not _os.path.exists(str(model_path)):
        return False, f"模型文件不存在: {model_path}"

    try:
        import joblib
        model = joblib.load(str(model_path))
        if not hasattr(model, 'predict'):
            return False, f"模型缺少 predict 方法 (类型: {type(model).__name__})"
        return True, f"模型可加载且含 predict 方法 ✓ (类型: {type(model).__name__})"
    except Exception as e:
        return False, f"模型加载失败: {e}"


def check_model_export_complete(outputs: dict, orch) -> tuple:
    """模型导出文件完整 — model_info.json + feature_config.json 存在且格式正确"""
    import json as _json
    proj_dir = _find_project_dir(orch, getattr(orch, '_current_project_id', None) or "")
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    import os as _os
    model_info = proj_dir / "supplements" / "model_info.json"
    feature_config = proj_dir / "supplements" / "feature_config.json"

    if not model_info.exists():
        return False, "supplements/model_info.json 缺失 — 模型导出步骤未完成"
    if not feature_config.exists():
        return False, "supplements/feature_config.json 缺失 — 特征配置未生成"

    # 验证 JSON 格式
    try:
        mi = _json.loads(model_info.read_text())
        required_keys = ["features", "performance"]
        missing = [k for k in required_keys if k not in mi]
        if missing:
            return False, f"model_info.json 缺少字段: {missing}"
    except _json.JSONDecodeError as e:
        return False, f"model_info.json 格式错误: {e}"

    try:
        fc = _json.loads(feature_config.read_text())
        if not isinstance(fc, dict) or len(fc) == 0:
            return False, "feature_config.json 为空或无特征配置"
    except _json.JSONDecodeError as e:
        return False, f"feature_config.json 格式错误: {e}"

    return True, "模型导出文件完整且格式正确 ✓"


def check_clinical_app_generated(outputs: dict, orch) -> tuple:
    """Web 应用文件存在 — supplements/app.py 存在且包含必要元素"""
    proj_dir = _find_project_dir(orch, getattr(orch, '_current_project_id', None) or "")
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    import os as _os
    app_file = proj_dir / "supplements" / "app.py"
    if not app_file.exists():
        return False, "supplements/app.py 缺失 — Web 应用未生成"

    content = app_file.read_text()
    required_elements = [
        ("streamlit", "import streamlit"),
        ("predict", "def predict"),
        ("st.title", "st.title("),
    ]
    for name, pattern in required_elements:
        if pattern not in content:
            return False, f"app.py 缺少必要元素: {name}"
    return True, "Web 应用文件存在且含必要元素 ✓"


def check_clinical_disclaimer_present(outputs: dict, orch) -> tuple:
    """安全免责声明 — app.py 包含临床安全免责声明"""
    proj_dir = _find_project_dir(orch, getattr(orch, '_current_project_id', None) or "")
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    import os as _os
    app_file = proj_dir / "supplements" / "app.py"
    if not app_file.exists():
        return True, "跳过 (app.py 不存在)"

    content = app_file.read_text().lower()
    checks = [
        ("for research", "for research"),
        ("educational purposes", "educational purposes"),
        ("medical advice", "medical advice"),
    ]
    missing = [name for name, pattern in checks if pattern not in content]
    if missing:
        return False, f"app.py 缺少安全免责声明要素: {missing}"
    return True, "安全免责声明完整 ✓"


def check_deployment_config_complete(outputs: dict, orch) -> tuple:
    """部署配置完整 — run_webapp.py + build_exe.py + requirements.txt + Dockerfile + README.md 存在"""
    proj_dir = _find_project_dir(orch, getattr(orch, '_current_project_id', None) or "")
    if not proj_dir:
        return True, "跳过 (无法定位项目目录)"

    import os as _os
    run_script = proj_dir / "supplements" / "run_webapp.py"
    build_exe = proj_dir / "supplements" / "build_exe.py"
    req_file = proj_dir / "supplements" / "requirements.txt"
    docker_file = proj_dir / "supplements" / "Dockerfile"
    readme = proj_dir / "supplements" / "README.md"

    missing = []
    if not run_script.exists():
        missing.append("run_webapp.py")
    if not build_exe.exists():
        missing.append("build_exe.py")
    if not req_file.exists():
        missing.append("requirements.txt")
    if not docker_file.exists():
        missing.append("Dockerfile")
    if not readme.exists():
        missing.append("README.md")

    if missing:
        return False, f"部署配置文件缺失: {missing}"

    # 检查 requirements.txt 包含核心依赖
    req_content = req_file.read_text().lower()
    core_deps = ["streamlit", "numpy", "pandas"]
    missing_deps = [d for d in core_deps if d not in req_content]
    if missing_deps:
        return False, f"requirements.txt 缺少核心依赖: {missing_deps}"

    # 检查 Dockerfile 包含必要指令
    docker_content = docker_file.read_text()
    if "FROM" not in docker_content or "RUN" not in docker_content:
        return False, "Dockerfile 格式不正确"

    return True, "部署配置完整 ✓"


# ============================================================
# 闸门定义: 每个 Phase 执行的检查项
# ============================================================

GATE_DEFINITIONS = {
    "problem_definition": {
        "auto_checks": {
            "lit_precheck": check_literature_precheck_exists,
            "frame_complete": check_frame_assessment_complete,
            "data_availability": check_data_availability_confirmed,
            "data_dictionary": check_data_dictionary_exists,
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
            "all_models_evaluated": check_all_models_evaluated_completely,  # 🆕 所有模型指标完整
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
            "table2_complete": check_table2_content_completeness,
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
            "discussion_paragraphs": check_discussion_seven_paragraphs,
            "discussion_no_subheadings": check_discussion_no_subheadings,
            "discussion_no_conclusion": check_discussion_last_para_no_conclusion,
            "discussion_explanation": check_discussion_explanation_section,
            "humanize_quality": check_humanize_quality,
            "numerical_traceability": check_numerical_traceability,
            "precision_consistency": check_numerical_precision_consistency,
            "baseline_compliance": check_baseline_compliance,
            "submission_integrity": check_submission_structure_integrity,
            "figure_naming": check_figure_naming_convention,
            "figure_has_image": check_all_figures_have_images,
            "figure_text_citation": check_figure_text_citation,
            "methods_subsections": check_methods_excessive_subsections,
            "results_subsections": check_results_excessive_subsections,
            "cohort_attrition": check_cohort_attrition_consistency,
            "categorical_labels": check_categorical_label_consistency,
            "subgroup_n_consistency": check_subgroup_n_consistency,
            "doi_title_match": check_doi_title_match,
        },
        "llm_checks": [
            "Methods ↔ Results 是否 1:1 对应? (Methods 声明的每个分析方法在 Results 中是否有对应结果报告)",
            (
                "Discussion 七段语义审查 (21b) — 逐段评估:\n"
                "¶1 核心发现是否简洁重申(不重复Results数字/不引用文献)?\n"
                "¶2 是否给出最可能解释+替代解释(不过度推测)?\n"
                "¶3 是否将本研究发现与一致文献逐条对比(每篇说明关系, 非堆砌引用号)?\n"
                "¶4 是否列出不一致发现+可能原因(人群/方法/变量差异, ≥2个差异点)?\n"
                "¶5 每条含义是否有 because(内部数据)+supported by(外部文献)?\n"
                "¶6 优势是否简洁具体(≤4条, 非泛泛)?\n"
                "¶7 局限是否按优先级排列(数据→验证→测量→方法→混杂→泛化)+配缓解+以具体未来方向收尾(非空泛标语)?"
            ),
            "Conclusion 是否独立章节 (## Conclusion)?",
            "所有数值是否可追溯到上游分析输出?",
            "是否存在虚假引用或未读引用?",
            "参考文献时效性是否达标 (≥80% 近5年文献)?",
            "所有非通用缩写在首次出现时是否给出了全称 (全称 (ABBR) 格式)? 通用缩写 (DNA/RNA/BMI/CI/AUC/OR/HR/SD) 除外",
            "去 AI 味改写是否真正改善了文本自然度? (句子长度变化/段落节奏/转折自然性/模板痕迹/hedge 适度)",
        ],
    },
    "clinical_tool": {
        "auto_checks": {
            "model_loadable": check_clinical_model_loadable,
            "model_export_complete": check_model_export_complete,
            "app_generated": check_clinical_app_generated,
            "disclaimer_present": check_clinical_disclaimer_present,
            "deployment_config_complete": check_deployment_config_complete,
        },
        "llm_checks": [
            "临床工具输入表单是否按临床逻辑分组 (人口学/功能测量/实验室/临床)? 每个输入项是否有临床名称+单位?",
            "风险输出是否清晰 (概率+分类+参考AUC)? 对临床医生(<5分钟填写)是否可用?",
            "安全免责声明是否醒目且完整? (必须包含 'for research and educational purposes only' + 'does not constitute medical advice')",
            "输入边界处理和异常值提示是否合理? 是否对不可能值(如年龄>120)给出警告?",
        ],
    },
    "kb_enrich": {
        "auto_checks": {
            "doi_verified": check_doi_verified_for_new_entries,
            "no_duplicate": check_no_duplicate_in_kb,
            "yaml_complete": check_literature_note_yaml_complete,
            "recency": check_recency_of_ingested,
        },
        "llm_checks": [
            "入库文献是否与研究领域 (老年医学/泌尿外科) 高度相关? 是否有堆砌无关文献?",
            "文献笔记的 one_liner 是否准确概括了论文核心发现? (非模糊描述)",
            "每条 actionable 和 gaps 是否具体、可操作? (非泛泛而谈)",
        ],
    },
}

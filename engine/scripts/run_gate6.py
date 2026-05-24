#!/usr/bin/env python3
"""
Gate 6 自动化检查 CLI — Run Gate 6

执行 24 项 Python 确定性 auto check。
Python 管底线 (有没有/对不对), LLM 管上限 (好不好)。
exit 0 = 全部通过, exit 1 = 有 FAIL。

用法:
    python run_gate6.py --project-dir /path/to/project
    或由编排器直接调用 gate_checks 模块中的 check 函数
"""

import sys
import argparse
from pathlib import Path

# 添加 engine 目录到 sys.path
_this_dir = Path(__file__).resolve().parent
_engine_dir = _this_dir.parent
if str(_engine_dir) not in sys.path:
    sys.path.insert(0, str(_engine_dir.parent))

from engine.core.gate_checks import (
    # Phase 6 auto checks (从 GATE_DEFINITIONS["writing"]["auto_checks"] 提取)
    check_sap_exists,
    check_journal_config_locked,
    check_title_length,
    check_sections_exist,
    check_tables_exist,
    check_figures_exist,
    check_manuscript_assembled,
    check_abstract_word_count,
    check_keywords_count,
    check_all_refs_have_doi,
    check_auc_has_ci,
    check_effect_size_with_ci,
    check_discrimination_and_calibration_reported,
    check_normality_test_reported,
    check_missing_data_reported,
    check_software_version_reported,
    check_conclusion_heading_level,
    check_doi_verification,
    check_doi_title_match,
    check_ref_count,
    check_ref_recency,
    check_all_refs_cited_in_text,
    check_discussion_seven_paragraphs,
    check_discussion_no_subheadings,
    check_discussion_last_para_no_conclusion,
    check_humanize_quality,
    check_numerical_traceability,
    check_numerical_precision_consistency,
    check_table_stratification_provenance,
    check_vancouver_reference_order,
)


# Gate 6 全部 30 项 Python auto check 注册表
# (check_id, check_fn, description)
GATE6_PYTHON_CHECKS = [
    # 前置检查
    ("sap_exists", check_sap_exists, "SAP 已签批"),
    ("journal_config_locked", check_journal_config_locked, "期刊需求已锁定"),
    # 格式检查
    ("title_length", check_title_length, "Title ≤ 15 词"),
    ("sections_exist", check_sections_exist, "Sections 分章节存在 (零件层)"),
    ("tables_exist", check_tables_exist, "Tables 存在 (双格式)"),
    ("figures_exist", check_figures_exist, "Figures 存在 + 命名格式 (双格式)"),
    ("manuscript_assembled", check_manuscript_assembled, "Manuscript 合稿"),
    ("abstract_word_count", check_abstract_word_count, "Abstract ≤ 300 词"),
    ("keywords_count", check_keywords_count, "Keywords ≥ 3"),
    ("conclusion_heading", check_conclusion_heading_level, "Conclusion 独立 ## 章节"),
    # 引用检查
    ("all_refs_have_doi", check_all_refs_have_doi, "参考文献 DOI 覆盖 ≥80%"),
    ("doi_verified", check_doi_verification, "DOI 验证通过 (fake=0)"),
    ("doi_title_match", check_doi_title_match, "DOI 标题一致性 — CrossRef 解析验证"),
    ("ref_count", check_ref_count, "参考文献 ≥25/≥45"),
    ("ref_recency", check_ref_recency, "参考文献时效性 ≥80%"),
    ("all_refs_cited", check_all_refs_cited_in_text, "每篇参考文献在正文中被引用"),
    # 内容检查
    ("auc_has_ci", check_auc_has_ci, "AUC 带 95% CI"),
    ("effect_size_with_ci", check_effect_size_with_ci, "效应量+CI 报告"),
    ("discrimination_calibration", check_discrimination_and_calibration_reported, "区分度+校准度"),
    ("normality_test", check_normality_test_reported, "正态性检验"),
    ("missing_data", check_missing_data_reported, "缺失数据处理"),
    ("software_version", check_software_version_reported, "软件+版本号"),
    # 结构检查
    ("discussion_paragraphs", check_discussion_seven_paragraphs, "Discussion 七段式"),
    ("discussion_no_subheadings", check_discussion_no_subheadings, "Discussion 无 ### 子标题"),
    ("discussion_no_conclusion", check_discussion_last_para_no_conclusion, "Discussion 末段无结论收束句"),
    # 质量检查
    ("humanize_quality", check_humanize_quality, "去 AI 味质量检查 (Python 层)"),
    # 🆕 数值一致性 + 基线合规 + 投稿层完整性
    ("numerical_traceability", check_numerical_traceability, "数值可追溯性 (偏差 <0.1%)"),
    ("precision_consistency", check_numerical_precision_consistency, "数值精度跨 manuscript/tables/figures 一致"),
    # 🆕 数据真实性 + 结构规则 (2026-05-24)
    ("stratification_provenance", check_table_stratification_provenance, "Table 1 分层数据来源验证 (非 np.random)"),
    ("vancouver_order", check_vancouver_reference_order, "参考文献 Vancouver 编号顺序"),
]


class DummyOrchestrator:
    """最小编排器桩, 供 check 函数获取 project_id"""

    def __init__(self, project_id: str, project_dir: Path):
        self._current_project_id = project_id

        # 模拟 kb 接口
        # vault_path 应为项目目录的祖父目录 (例如 laoNianYiXue/),
        # 使得 vault_path/projects/project_id = project_dir
        vault_path = project_dir.parent.parent

        class FakeKB:
            class FakeVaults:
                def items(self):
                    return [("main", str(vault_path))]
            vaults = FakeVaults()
        self.kb = FakeKB()


def run_gate6(project_dir: Path) -> dict:
    """
    执行 Gate 6 全部 28 项 Python auto check。

    Returns:
        {"pass": bool, "results": [{"check_id": str, "result": pass/fail/skip, "detail": str}],
         "pass_count": int, "fail_count": int, "skip_count": int}
    """
    project_id = project_dir.name
    orch = DummyOrchestrator(project_id, project_dir)

    # 构建模拟 outputs (空字典, 各 check 函数会从文件系统读取)
    outputs = {
        "scientific-writer": "",  # 让 check 函数能找到 agent_id
    }

    results = []
    pass_count = 0
    fail_count = 0
    skip_count = 0

    for check_id, check_fn, description in GATE6_PYTHON_CHECKS:
        try:
            passed, detail = check_fn(outputs, orch)
            status = "pass" if passed else "fail"
            if detail.startswith("跳过"):
                status = "skip"
                skip_count += 1
            elif passed:
                pass_count += 1
            else:
                fail_count += 1
            results.append({
                "check_id": check_id,
                "description": description,
                "result": status,
                "detail": detail,
            })
        except Exception as e:
            fail_count += 1
            results.append({
                "check_id": check_id,
                "description": description,
                "result": "fail",
                "detail": f"检查异常: {e}",
            })

    return {
        "pass": fail_count == 0,
        "results": results,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Gate 6 自动化检查 — 执行 28 项 Python auto check"
    )
    parser.add_argument(
        "--project-dir", required=True,
        help="项目根目录路径"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="输出 JSON 格式结果"
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"❌ 项目目录不存在: {project_dir}", file=sys.stderr)
        sys.exit(1)

    result = run_gate6(project_dir)

    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Gate 6 — {len(GATE6_PYTHON_CHECKS)} 项 Python auto check")
        print(f"  项目: {project_dir}")
        print(f"  通过: {result['pass_count']}, 失败: {result['fail_count']}, "
              f"跳过: {result['skip_count']}")
        print()

        for r in result["results"]:
            icon = {"pass": "✅", "fail": "❌", "skip": "⏭️ "}.get(r["result"], "❓")
            print(f"  {icon} [{r['check_id']}] {r['description']}")
            if r["result"] != "pass":
                print(f"     {r['detail']}")

        print()
        if result["pass"]:
            print("✅ Gate 6 Python checks PASSED")
        else:
            print(f"❌ Gate 6 BLOCKED — {result['fail_count']} 项 FAIL")
            print()

            # 提醒 LLM 审查
            print("=" * 60)
            print("⚠️  Python auto checks 完成后, 仍需 LLM semantic checks:")
            print("  1. Discussion 四段语义 (¶1 发现/¶2 文献/¶3 含义/¶4 局限)")
            print("  2. 去 AI 味自然度评估 (非仅表面替换)")
            print("  3. 缩写首次引入确认")
            print("  4. Methods ↔ Results 1:1 对应")
            print("=" * 60)

    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()

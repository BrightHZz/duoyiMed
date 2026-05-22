#!/usr/bin/env python3
"""
IMRAD 结构验真脚本 — 独立 CLI 工具 (钱学森模块二: 可靠性工程)

在 Gate 6 之前独立执行，检测 manuscript.md 的 IMRAD 结构合规性。
所有检查均为确定性规则 (regex + 层级分析)，不依赖 LLM。

用法:
    python run_imrad_check.py --project-dir .              # 检查当前项目
    python run_imrad_check.py --project-dir . --blueprint   # 同时验证蓝图存在性
    python run_imrad_check.py --project-dir . --json        # JSON 格式输出

Exit 0 = ALL PASS, Exit 1 = 存在 FAIL
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def find_manuscript(project_dir: str) -> str | None:
    """定位 manuscript.md"""
    candidates = [
        os.path.join(project_dir, 'submission', 'manuscript.md'),
        os.path.join(project_dir, 'manuscript.md'),
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return open(fp, encoding='utf-8').read()
    return None


# ================================================================
# Check 1: IMRAD Heading 层级验真
# ================================================================

def check_heading_hierarchy(content: str) -> dict:
    """
    检查规则:
    1. ## 一级章节必须恰好 5 个: Introduction, Methods, Results, Discussion, Conclusion
    2. Introduction 下禁止任何子标题 (###)
    3. Methods 下必须有且仅有 5 个标准 ### 子标题
    4. Results 下必须有且仅有 5 个标准 ### 子标题, 且顺序正确
    5. Discussion 下禁止任何 ### / ####
    6. Conclusion 必须是 ## 而不是 ###
    """
    errors = []
    warnings = []

    # 1. 一级章节检查
    h2_headers = re.findall(r'^## (.+)$', content, re.MULTILINE)
    h2_names = [h.strip().lower() for h in h2_headers]

    required_h2 = {
        'introduction': 'Introduction',
        'methods': 'Methods',
        'results': 'Results',
        'discussion': 'Discussion',
        'conclusion': 'Conclusion',
    }
    found_h2 = set()
    for h in h2_names:
        for key, label in required_h2.items():
            if key in h:
                found_h2.add(key)
                break

    for key, label in required_h2.items():
        if key not in found_h2:
            errors.append(f"缺少 ## {label} 章节")

    # 2. Introduction 禁止子标题
    intro = _extract_section(content, 'Introduction')
    if intro:
        sub_h3 = re.findall(r'^### (.+)$', intro, re.MULTILINE)
        if sub_h3:
            errors.append(f"Introduction 下禁止 ### 子标题, 发现: {', '.join(sub_h3)}")
    else:
        errors.append("未找到 ## Introduction 章节")

    # 3. Methods 标准子标题
    methods = _extract_section(content, 'Methods')
    if methods:
        m_h3 = re.findall(r'^### (.+)$', methods, re.MULTILINE)
        m_names = [h.lower() for h in m_h3]
        required_methods = [
            'study design', 'study population',
            'outcomes and predictors', 'statistical analysis',
            'sensitivity analysis',
        ]
        for rm in required_methods:
            if not any(rm in n for n in m_names):
                errors.append(f"Methods 缺少 ### (相关标准: {rm})")

        if re.search(r'####\s', methods):
            errors.append("Methods 下禁止 #### 更深层标题")

        # 检查是否有超出标准的额外子标题
        allowed = required_methods
        extra = [h for h in m_h3 if not any(a in h.lower() for a in allowed)]
        if extra:
            warnings.append(f"Methods 存在非标准子标题: {', '.join(extra)}")
    else:
        errors.append("未找到 ## Methods 章节")

    # 4. Results 标准子标题 + 顺序
    results = _extract_section(content, 'Results')
    if results:
        r_h3 = re.findall(r'^### (.+)$', results, re.MULTILINE)
        r_names = [h.lower() for h in r_h3]
        required_results = [
            'study population', 'model performance',
            'feature importance', 'secondary', 'sensitivity',
        ]
        for rr in required_results:
            if not any(rr in n for n in r_names):
                errors.append(f"Results 缺少 ### (相关标准: {rr})")

        # 顺序检查
        if len(r_h3) >= 5:
            if 'population' not in r_h3[0].lower() and 'baseline' not in r_h3[0].lower():
                warnings.append("Results 首个子标题应为 Study Population and Baseline Characteristics")
            if 'sensitivity' not in r_h3[-1].lower():
                warnings.append("Results 末个子标题应为 Sensitivity Analyses")

        if re.search(r'####\s', results):
            errors.append("Results 下禁止 #### 更深层标题")
    else:
        errors.append("未找到 ## Results 章节")

    # 5. Discussion 禁止子标题
    discussion = _extract_section(content, 'Discussion')
    if discussion:
        d_h3 = re.findall(r'^### (.+)$', discussion, re.MULTILINE)
        if d_h3:
            errors.append(f"Discussion 下禁止 ### 子标题, 发现: {', '.join(d_h3)}")
        if re.search(r'####\s', discussion):
            errors.append("Discussion 下禁止 #### 更深层标题")
    else:
        errors.append("未找到 ## Discussion 章节")

    # 6. Conclusion 层级
    if re.search(r'^### Conclusion', content, re.MULTILINE):
        errors.append("Conclusion 必须是 ## (一级), 当前是 ### (二级)")
    if not re.search(r'^## Conclusion', content, re.MULTILINE):
        errors.append("缺少 ## Conclusion 章节")

    return {
        'check': 'heading_hierarchy',
        'passed': len(errors) == 0,
        'h2_found': h2_names,
        'errors': errors,
        'warnings': warnings,
    }


# ================================================================
# Check 2: Methods ↔ Results 1:1 映射
# ================================================================

def check_methods_results_mapping(content: str) -> dict:
    """从 Methods 提取分析方法声明, 验证 Results 中是否存在对应回报"""
    errors = []
    mapped = []

    methods = _extract_section(content, 'Methods')
    results = _extract_section(content, 'Results')

    if not methods or not results:
        return {
            'check': 'methods_results_1to1',
            'passed': False,
            'errors': ['无法提取 Methods 或 Results 章节'],
        }

    # 从 Methods 提取分析关键词
    method_patterns = {
        'LASSO feature selection': r'LASSO|L1.regulariz|elastic.net.*feature.select',
        'cross-validation': r'cross.validation|k-fold|5-fold|10-fold',
        'SHAP': r'SHAP|shapley|shap\.',
        'XGBoost': r'XGBoost|xgboost',
        'Logistic Regression': r'logistic.regression|logistic.model',
        'Random Forest': r'random.forest',
        'DeLong test': r'DeLong|model.comparison|AUC.comparison',
        'calibration': r'calibration|Brier|Hosmer.Lemeshow',
        'sensitivity analysis': r'sensitivity.analys',
        'subgroup analysis': r'subgroup.analys|stratifi',
        'multiple imputation': r'multiple.imputation|MICE|imputation',
        'normality test': r'Shapiro|Kolmogorov|normality',
        'Cox regression': r'Cox.proportional|survival.analys',
        'competing risks': r'Fine.Gray|competing.risk',
        'C-statistic': r'C.statistic|C.index|concordance',
    }

    for method_name, pattern in method_patterns.items():
        if re.search(pattern, methods, re.I):
            # 声明了此方法 → 检查 Results 中是否有对应回报
            if re.search(pattern, results, re.I):
                mapped.append({'method': method_name, 'reported': True})
            else:
                errors.append(
                    f"Methods 声明了 '{method_name}' 但 Results 中未找到对应结果回报"
                )
                mapped.append({'method': method_name, 'reported': False})

    return {
        'check': 'methods_results_1to1',
        'passed': len(errors) == 0,
        'mapped': mapped,
        'errors': errors,
        'total_methods': len(mapped),
        'matched': sum(1 for m in mapped if m['reported']),
    }


# ================================================================
# Check 3: Discussion 结构检查
# ================================================================

def check_discussion_structure(content: str) -> dict:
    """Discussion 七段式 + 无子标题 + 末段无结论收束"""
    errors = []
    warnings = []

    discussion = _extract_section(content, 'Discussion')
    if not discussion:
        return {
            'check': 'discussion_structure',
            'passed': False,
            'errors': ['未找到 ## Discussion 章节'],
        }

    # 按空行拆段
    paragraphs = re.split(r'\n{2,}', discussion.strip())
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if len(paragraphs) < 6:
        errors.append(
            f"Discussion 仅 {len(paragraphs)} 段 (空行分隔), 需 ≥6 (七段式: "
            "¶1核心发现/¶2机制解释/¶3文献一致/¶4文献不一致/¶5含义/¶6优势/¶7局限+未来方向)"
        )

    # 文献引用检查
    if not re.search(r'\[\d+', discussion):
        errors.append("Discussion 未检测到文献引用 — ¶3/¶4 必须引用文献")

    # 末段局限检查
    if paragraphs:
        last = paragraphs[-1]
        if not re.search(r'limitation|局限|limitation', last, re.I):
            warnings.append("Discussion ¶7 (末段) 应包含局限性讨论")
        # 末段不应含结论性收束句
        if re.search(
            r'paving the way|ushering in|highlighting the potential|'
            r'opening the door|revolutionize|game.chang',
            last, re.I
        ):
            errors.append("Discussion ¶7 (末段) 含 AI 标语式收束句, 禁止 (结论是 Conclusion 的事)")

    return {
        'check': 'discussion_structure',
        'passed': len(errors) == 0,
        'paragraphs_count': len(paragraphs),
        'errors': errors,
        'warnings': warnings,
    }


# ================================================================
# Check 4: Conclusion 独立章节
# ================================================================

def check_conclusion_standalone(content: str) -> dict:
    """Conclusion 是 ## 独立章节, 不是 Discussion 的子标题"""
    if '### Conclusion' in content:
        return {
            'check': 'conclusion_standalone',
            'passed': False,
            'errors': ['Conclusion 是 ### (嵌在 Discussion 下), 应该是 ## (独立章节)'],
        }
    if '## Conclusion' not in content:
        return {
            'check': 'conclusion_standalone',
            'passed': False,
            'errors': ['缺少 ## Conclusion 独立章节'],
        }
    return {'check': 'conclusion_standalone', 'passed': True}


# ================================================================
# Helper
# ================================================================

def _extract_section(content: str, section_name: str) -> str | None:
    """Extract ## section content (until next ## heading or end)"""
    pattern = rf'(?:^|\n)## {section_name}\s*\n(.*?)(?=(?:\n##\s)|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1) if match else None


# ================================================================
# Main
# ================================================================

def run_imrad_check(project_dir: str, check_blueprint: bool = False):
    """返回 (results_dict, exit_code)"""
    results = {'project_dir': project_dir, 'checks': [], 'overall': 'PASS'}

    # 蓝图检查 (可选的)
    if check_blueprint:
        bp_path = os.path.join(project_dir, 'imrad_blueprint.md')
        bp_exists = os.path.exists(bp_path)
        bp_approved = False
        if bp_exists:
            bp_content = open(bp_path, encoding='utf-8').read()
            bp_approved = 'APPROVED' in bp_content

        results['checks'].append({
            'check': 'blueprint_exists',
            'passed': bp_exists and bp_approved,
            'detail': (
                'IMRAD 蓝图存在且已签批' if bp_exists and bp_approved
                else 'IMRAD 蓝图存在但未签批' if bp_exists
                else 'IMRAD 蓝图缺失'
            ),
        })

    # 全文检查
    content = find_manuscript(project_dir)
    if content is None:
        results['checks'].append({
            'check': 'manuscript_found',
            'passed': False,
            'detail': 'manuscript.md 未找到 (搜索: submission/manuscript.md, manuscript.md)',
        })
        results['overall'] = 'FAIL'
        return results, 1

    # 执行四项检查
    checks = [
        check_heading_hierarchy(content),
        check_methods_results_mapping(content),
        check_discussion_structure(content),
        check_conclusion_standalone(content),
    ]
    results['checks'].extend(checks)

    # 汇总
    failures = [c for c in checks if not c['passed']]
    if failures:
        results['overall'] = 'FAIL'
        results['summary'] = f"{len(failures)}/{len(checks)} checks FAILED"
    else:
        results['overall'] = 'PASS'
        results['summary'] = f"All {len(checks)} checks PASSED"

    exit_code = 1 if failures else 0
    return results, exit_code


def main():
    parser = argparse.ArgumentParser(description='IMRAD 结构验真脚本')
    parser.add_argument('--project-dir', default='.',
                        help='项目目录 (默认: 当前目录)')
    parser.add_argument('--blueprint', action='store_true',
                        help='同时检查 IMRAD 蓝图存在性')
    parser.add_argument('--json', action='store_true',
                        help='JSON 格式输出')
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    results, exit_code = run_imrad_check(project_dir, check_blueprint=args.blueprint)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        _print_human(results)

    sys.exit(exit_code)


def _print_human(results: dict):
    """人类可读输出"""
    print("=" * 60)
    print("IMRAD 结构验真报告")
    print(f"项目目录: {results['project_dir']}")
    print(f"总体结果: {results['overall']}")
    print("=" * 60)

    for i, check in enumerate(results['checks'], 1):
        status = "✅ PASS" if check.get('passed') else "❌ FAIL"
        check_name = check.get('check', f'Check #{i}')
        print(f"\n  [{i}] {check_name}: {status}")

        if check.get('errors'):
            for e in check['errors']:
                print(f"       ❌ {e}")
        if check.get('warnings'):
            for w in check['warnings']:
                print(f"       ⚠️ {w}")
        if check.get('detail'):
            print(f"       ℹ️  {check['detail']}")
        if check.get('mapped'):
            for m in check['mapped']:
                symbol = "✓" if m['reported'] else "✗"
                print(f"       {symbol}  {m['method']}")

    print()
    if results['overall'] == 'PASS':
        print("All IMRAD structure checks passed.")
    else:
        print("IMRAD structure checks FAILED — fix above issues before proceeding.")


if __name__ == '__main__':
    main()

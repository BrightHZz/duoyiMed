#!/usr/bin/env python3
"""
Gate 6 自动化检查 CLI — Run Gate 6

执行 GATE_DEFINITIONS["writing"]["auto_checks"] 中注册的全部检查。
Python 管底线 (有没有/对不对), LLM 管上限 (好不好)。
exit 0 = 全部通过, exit 1 = 有 FAIL。

用法:
    python run_gate6.py --project-dir /path/to/project
    或由编排器直接调用 gate_checks 模块中的 check 函数

单源真原则:
    本脚本不再维护独立的检查列表。所有检查项从 GATE_DEFINITIONS 读取,
    gate_checks.py 中新增的任何 check 函数一旦注册到 writing gate,
    将自动纳入本脚本的执行范围, 无需手动同步。
"""

import sys
import argparse
from pathlib import Path

# 添加 engine 目录到 sys.path
_this_dir = Path(__file__).resolve().parent
_engine_dir = _this_dir.parent
if str(_engine_dir) not in sys.path:
    sys.path.insert(0, str(_engine_dir.parent))

from engine.core.gate_checks import GATE_DEFINITIONS


def _get_description(check_fn) -> str:
    """从函数 docstring 第一行提取描述, 无 docstring 时回退到函数名"""
    doc = getattr(check_fn, '__doc__', None)
    if doc:
        first_line = doc.strip().split('\n')[0].strip()
        if first_line:
            return first_line
    return check_fn.__name__


def _build_checks_from_definitions():
    """从 GATE_DEFINITIONS["writing"]["auto_checks"] 构建检查列表。

    单源真: 任何时候新增/删除检查, 只需修改 gate_checks.py 的
    GATE_DEFINITIONS, 本脚本自动跟随。
    """
    writing = GATE_DEFINITIONS.get("writing", {})
    auto_checks = writing.get("auto_checks", {})

    checks = []
    for check_id, check_fn in auto_checks.items():
        checks.append((check_id, check_fn, _get_description(check_fn)))
    return checks


class DummyOrchestrator:
    """最小编排器桩, 供 check 函数获取 project_id"""

    def __init__(self, project_id: str, project_dir: Path):
        self._current_project_id = project_id

        # 模拟 kb 接口
        vault_path = project_dir.parent.parent

        class FakeKB:
            class FakeVaults:
                def items(self):
                    return [("main", str(vault_path))]
            vaults = FakeVaults()
        self.kb = FakeKB()


def run_gate6(project_dir: Path) -> dict:
    """
    执行 writing gate 全部 Python auto check。

    检查列表从 GATE_DEFINITIONS["writing"]["auto_checks"] 读取,
    与 gate_checks.py 始终保持一致。

    Returns:
        {"pass": bool, "results": [...], "pass_count": int, "fail_count": int, "skip_count": int}
    """
    project_id = project_dir.name
    orch = DummyOrchestrator(project_id, project_dir)

    outputs = {
        "scientific-writer": "",
    }

    gate6_checks = _build_checks_from_definitions()

    results = []
    pass_count = 0
    fail_count = 0
    skip_count = 0

    for check_id, check_fn, description in gate6_checks:
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
    # 检测：如果此脚本被复制到项目 scripts/ 下运行，发出 deprecated 警告
    _fp = Path(__file__).resolve()
    if _fp.parent.parent.name != "engine":
        import warnings
        warnings.warn(
            f"此脚本的项目本地副本已过时。请删除并使用引擎版本: "
            f"python engine/scripts/{_fp.name} --project-dir .",
            DeprecationWarning, stacklevel=2
        )

    gate6_checks = _build_checks_from_definitions()

    parser = argparse.ArgumentParser(
        description=f"Gate 6 自动化检查 — 执行 {len(gate6_checks)} 项 Python auto check (来自 GATE_DEFINITIONS)"
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
        print(f"Gate 6 — {len(gate6_checks)} 项 Python auto check (GATE_DEFINITIONS)")
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

            print("=" * 60)
            print("⚠️  Python auto checks 完成后, 仍需 LLM semantic checks:")
            print("  1. Discussion 七段语义审查")
            print("  2. 去 AI 味自然度评估 (非仅表面替换)")
            print("  3. 缩写首次引入确认")
            print("  4. Methods ↔ Results 1:1 对应")
            print("=" * 60)

    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()

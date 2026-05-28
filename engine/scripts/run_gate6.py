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

# 基础设施类跳过模式 — 检查"想跑但跑不起来"，非合理不适用
_INFRA_SKIP_PATTERNS = [
    "无 project_dir",
    "无法确定 project_dir",
]


def _is_infrastructure_skip(detail: str) -> bool:
    """判断跳过是否由基础设施问题导致（而非合理不适用）"""
    return any(p in detail for p in _INFRA_SKIP_PATTERNS)


def _run_infrastructure_health_check(orch, outputs) -> list:
    """基础设施自检: 在业务检查之前诊断 CLI 模式的已知限制"""
    warnings = []

    # 检查 orch 关键属性
    for attr, desc in [
        ('_current_project_id', '项目ID'),
        ('_current_project_dir', '项目目录'),
        ('project_dir', '项目路径'),
        ('kb', '知识库'),
    ]:
        if not hasattr(orch, attr):
            warnings.append(f"DummyOrchestrator 缺少 {attr} ({desc})")

    if not hasattr(orch, 'get_project_dir'):
        warnings.append("DummyOrchestrator 缺少 get_project_dir() 方法, IMRAD 检查将回退到 os.getcwd()")

    if not hasattr(orch, 'state'):
        warnings.append("DummyOrchestrator 缺少 state 属性, 综述/论著类型检测将失效")

    # 检查输出内容 (CLI 模式的核心限制)
    writing_output = outputs.get("scientific-writer", "")
    if not writing_output.strip():
        warnings.append(
            "CLI 模式: outputs['scientific-writer'] 为空, "
            "依赖 agent output 文本扫描的检查将全部跳过 (~30 项)")

    return warnings


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
    """最小编排器桩, 供 check 函数获取 project_id 和项目路径"""

    def __init__(self, project_id: str, project_dir: Path):
        self._current_project_id = project_id
        self._current_project_dir = project_dir
        self.project_dir = project_dir

        # 模拟 kb 接口
        vault_path = project_dir.parent.parent

        class FakeKB:
            class FakeVaults:
                def items(self):
                    return [("main", str(vault_path))]
            vaults = FakeVaults()

            @staticmethod
            def scan_lessons_learned():
                return []

        self.kb = FakeKB()

        # 从 sds.md 检测项目类型 (综述 vs 论著)
        self.state = self._detect_project_state(project_dir)

    @staticmethod
    def _detect_project_state(project_dir: Path):
        """从 sds.md 读取项目类型, 构造 mock state 对象"""
        import re

        class MockState:
            user_intent = ""

        state = MockState()
        sds_path = project_dir / "sds.md"
        if not sds_path.exists():
            return state

        try:
            text = sds_path.read_text(encoding="utf-8")
            m = re.search(r'\|\s*项目类型\s*\|\s*([^|]+)\s*\|', text)
            if m:
                type_val = m.group(1).strip()
                if "literature_review" in type_val:
                    state.user_intent = "literature_review"
                elif "new_project" in type_val:
                    state.user_intent = "new_project"
                elif "paper_writing" in type_val:
                    state.user_intent = "paper_writing"
        except OSError:
            pass

        return state

    def get_project_dir(self):
        return self.project_dir


def run_gate6(project_dir: Path) -> dict:
    """
    执行 writing gate 全部 Python auto check。

    检查列表从 GATE_DEFINITIONS["writing"]["auto_checks"] 读取,
    与 gate_checks.py 始终保持一致。

    Returns:
        {"pass": bool, "results": [...], "pass_count": int, "fail_count": int,
         "skip_count": int, "infra_skip_count": int, "infra_warnings": list}
    """
    project_id = project_dir.name
    orch = DummyOrchestrator(project_id, project_dir)

    outputs = {
        "scientific-writer": "",
    }

    gate6_checks = _build_checks_from_definitions()

    # === 基础设施健康自检 ===
    infra_warnings = _run_infrastructure_health_check(orch, outputs)

    results = []
    pass_count = 0
    fail_count = 0
    skip_count = 0
    infra_skip_count = 0

    for check_id, check_fn, description in gate6_checks:
        try:
            passed, detail = check_fn(outputs, orch)
            status = "pass" if passed else "fail"
            if detail.startswith("跳过"):
                status = "skip"
                skip_count += 1
                if _is_infrastructure_skip(detail):
                    infra_skip_count += 1
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
        "infra_skip_count": infra_skip_count,
        "infra_warnings": infra_warnings,
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
        # === 基础设施健康检查报告 ===
        if result.get('infra_warnings'):
            print("🔧 基础设施健康检查:")
            for w in result['infra_warnings']:
                print(f"  ⚠️  {w}")
            print()

        print(f"Gate 6 — {len(gate6_checks)} 项 Python auto check (GATE_DEFINITIONS)")
        print(f"  项目: {project_dir}")
        print(f"  通过: {result['pass_count']}, 失败: {result['fail_count']}, "
              f"跳过: {result['skip_count']}")
        if result.get('infra_skip_count', 0) > 0:
            print(f"  ⚠️  其中 {result['infra_skip_count']} 项跳过可能与基础设施限制有关")
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

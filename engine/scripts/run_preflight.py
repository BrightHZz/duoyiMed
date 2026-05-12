#!/usr/bin/env python3
"""
执行前安全扫描 CLI — Pre-flight Safety Scan Runner

用法:
    python run_preflight.py --project-dir /path/to/project
    python run_preflight.py --project-dir /path/to/project --scripts train_model.py
    python run_preflight.py --project-dir /path/to/project --all

退出码: 0 = SAFE, 1 = BLOCKED (有 FAIL 级别问题)
"""

import sys
import argparse
from pathlib import Path

# 添加 engine 目录到 sys.path (支持从项目根和 engine/scripts/ 运行)
_this_dir = Path(__file__).resolve().parent
_engine_dir = _this_dir.parent
if str(_engine_dir) not in sys.path:
    sys.path.insert(0, str(_engine_dir.parent))

from engine.core.preflight_scanner import preflight_safety_scan


def main():
    parser = argparse.ArgumentParser(
        description="执行前安全扫描 — 检查 ML 脚本的安全配置"
    )
    parser.add_argument(
        "--project-dir", required=True,
        help="项目根目录路径"
    )
    parser.add_argument(
        "--scripts", nargs="*",
        help="要扫描的脚本文件名 (默认: 项目所有 .py)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="扫描项目所有 .py 文件"
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"❌ 项目目录不存在: {project_dir}", file=sys.stderr)
        sys.exit(1)

    # 确定扫描目标
    if args.all:
        target_scripts = ["*.py"]
    elif args.scripts:
        target_scripts = args.scripts
    else:
        # 默认: 扫描常见 ML 脚本
        default_scripts = [
            "train_model.py", "tune_model.py",
            "generate_figures.py", "regenerate_figures_tables.py",
            "external_validation.py",
        ]
        existing = []
        for s in default_scripts:
            if (project_dir / s).exists() or list(project_dir.glob(f'**/{s}')):
                existing.append(s)
        if not existing:
            existing = ["*.py"]  # fallback: all
        target_scripts = existing

    print(f"Preflight Safety Scan")
    print(f"  项目: {project_dir}")
    print(f"  目标: {target_scripts}")
    print()

    result = preflight_safety_scan(str(project_dir), target_scripts)
    print(result["report"])

    if result["pass"]:
        print("\n✅ SAFE — 可以执行")
        sys.exit(0)
    else:
        print(f"\n❌ BLOCKED — {len(result['failures'])} 项 FAIL, "
              f"{len(result['warnings'])} 项 WARN")
        print("\n请修复以上 FAIL 项后重新运行扫描。")
        print("WARN 项不阻断执行，但建议修复。")
        sys.exit(1)


if __name__ == "__main__":
    main()

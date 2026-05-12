#!/usr/bin/env python3
"""
稿件组装 CLI — Run Assembly

将零件层 (sections/, tables/, figures/) 组装为投稿层 (submission/)。
严格遵循 5 条否定约束 + 组装后自检。

用法:
    python run_assembly.py --project-dir /path/to/project

退出码: 0 = 投稿层完整, 1 = FAIL
"""

import sys
import os
import re
import argparse
import shutil
from pathlib import Path


# ================================================================
# 否定约束 (5 条)
# ================================================================
# 1. submission/ 下不得存在 sections/ 目录
# 2. submission/figures/ 下仅允许 .png 和 .tiff 文件
# 3. submission/tables/ 下仅允许 .csv 文件
# 4. 零件层 .md caption、.json 数据文件不进入 submission/
# 5. Classic 标注不得保留在投稿层


def assemble(project_dir: Path) -> dict:
    """
    执行 assembly 组装。

    Returns:
        {"success": bool, "errors": [str], "written": [str]}
    """
    errors = []
    written = []

    root = project_dir
    submission_dir = root / "submission"
    sections_dir = root / "sections"
    tables_dir = root / "tables"
    figures_dir = root / "figures"

    # 检查零件层是否存在
    if not sections_dir.exists():
        errors.append("零件层 sections/ 目录不存在")
        return {"success": False, "errors": errors, "written": written}

    # 清理/创建投稿层
    if submission_dir.exists():
        # 先清理旧的投稿内容（保留目录结构）
        for sub in ['manuscript.md']:
            p = submission_dir / sub
            if p.exists():
                p.unlink()
        for sub in ['tables', 'figures']:
            d = submission_dir / sub
            if d.exists():
                shutil.rmtree(d)

    submission_dir.mkdir(parents=True, exist_ok=True)
    (submission_dir / "tables").mkdir(parents=True, exist_ok=True)
    (submission_dir / "figures").mkdir(parents=True, exist_ok=True)

    # ================================================================
    # Step 1: 拼接 sections/0*.md → submission/manuscript.md
    # ================================================================
    section_files = sorted(sections_dir.glob('0*.md'))
    if not section_files:
        errors.append("sections/ 中无 0*.md 文件 (应至少含 IMRAD 各章节)")
    else:
        manuscript_content = []
        for sf in section_files:
            try:
                text = sf.read_text()
                # ⚠️ 否定约束 #5: strip [Classic ...] 标注
                text = re.sub(r'\[Classic\s*[—–-]\s*[^\]]*\]', '', text)
                text = re.sub(r'\[Foundational\s*[—–-]\s*[^\]]*\]', '', text)
                manuscript_content.append(text)
                manuscript_content.append("\n")
            except OSError as e:
                errors.append(f"无法读取 {sf.name}: {e}")

        if manuscript_content:
            manuscript_path = submission_dir / "manuscript.md"
            manuscript_path.write_text("\n".join(manuscript_content))
            written.append(str(manuscript_path))

    # ================================================================
    # Step 2: 复制 tables/*.csv → submission/tables/
    # ================================================================
    if tables_dir.exists():
        for csv_file in tables_dir.glob('*.csv'):
            dest = submission_dir / "tables" / csv_file.name
            shutil.copy2(csv_file, dest)
            written.append(str(dest))
    else:
        errors.append("零件层 tables/ 目录不存在")

    # ================================================================
    # Step 3: 复制 figures/*.png + figures/*.tiff → submission/figures/
    # ================================================================
    if figures_dir.exists():
        for ext in ['*.png', '*.tiff', '*.tif']:
            for fig_file in figures_dir.glob(ext):
                dest = submission_dir / "figures" / fig_file.name
                shutil.copy2(fig_file, dest)
                written.append(str(dest))
    else:
        errors.append("零件层 figures/ 目录不存在")

    # ================================================================
    # 组装后自检
    # ================================================================
    self_check_errors = check_submission_structure_integrity(submission_dir)
    errors.extend(self_check_errors)

    return {
        "success": len(errors) == 0,
        "errors": errors,
        "written": written,
    }


def check_submission_structure_integrity(submission_dir: Path) -> list[str]:
    """投稿层结构自检 — 与 gate_checks.py 逻辑同步"""
    errors = []

    if not submission_dir.exists():
        return ["submission/ 目录不存在"]

    # 1. submission/ 下不得存在 sections/ 目录
    if (submission_dir / "sections").exists():
        errors.append(
            "submission/sections/ 目录存在 — "
            "零件层 sections/ 不应出现在投稿层, assembly 误用了 cp -r 而非 cat 拼接"
        )

    # 2. submission/figures/ 下仅允许 .png 和 .tiff
    figures_dir = submission_dir / "figures"
    if figures_dir.exists():
        for f in figures_dir.iterdir():
            if f.is_file() and f.suffix.lower() not in ('.png', '.tiff', '.tif'):
                errors.append(
                    f"submission/figures/ 含非图片文件: {f.name} — "
                    "caption .md 和 data .json 不应进入投稿层"
                )

        # 检查 .png 是否都有对应 .tiff
        png_files = {f.stem for f in figures_dir.glob('*.png')}
        tiff_files = {f.stem for f in figures_dir.glob('*.tiff')} | \
                     {f.stem for f in figures_dir.glob('*.tif')}
        missing_tiff = png_files - tiff_files
        if missing_tiff:
            errors.append(
                f"submission/figures/ 中 {len(missing_tiff)} 个 .png 缺少对应 .tiff: "
                + ", ".join(sorted(missing_tiff)[:5])
            )

    # 3. submission/tables/ 下仅允许 .csv
    tables_dir = submission_dir / "tables"
    if tables_dir.exists():
        for f in tables_dir.iterdir():
            if f.is_file() and f.suffix.lower() != '.csv':
                errors.append(
                    f"submission/tables/ 含非 CSV 文件: {f.name} — "
                    "投稿层表格仅需 .csv"
                )

    # 4. submission/manuscript.md 存在
    manuscript = submission_dir / "manuscript.md"
    if not manuscript.exists():
        errors.append("submission/manuscript.md 不存在 — assembly 未生成合稿")

    # 5. manuscript.md 中不含 Classic 标注
    if manuscript.exists():
        try:
            content = manuscript.read_text()
            if '[Classic' in content or '[classic' in content.lower():
                errors.append(
                    "submission/manuscript.md 中含 [Classic 标注 — "
                    "Classic 标注为零件层内部元数据, assembly 拼接时必须 strip"
                )
        except OSError:
            pass

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="稿件组装 — 将零件层组装为投稿层"
    )
    parser.add_argument(
        "--project-dir", required=True,
        help="项目根目录路径 (含 sections/tables/figures 目录)"
    )
    parser.add_argument(
        "--check-only", action="store_true",
        help="仅执行投稿层结构自检, 不做组装"
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"❌ 项目目录不存在: {project_dir}", file=sys.stderr)
        sys.exit(1)

    if args.check_only:
        submission_dir = project_dir / "submission"
        errors = check_submission_structure_integrity(submission_dir)
        if errors:
            print("❌ 投稿层结构完整性不通过:")
            for e in errors:
                print(f"  • {e}")
            sys.exit(1)
        print("✅ 投稿层结构完整性通过")
        sys.exit(0)

    print(f"Assembly")
    print(f"  项目: {project_dir}")
    print(f"  零件层 → 投稿层")
    print()

    result = assemble(project_dir)

    if result["written"]:
        print(f"  已生成 {len(result['written'])} 个文件:")
        for w in result["written"]:
            print(f"    {w}")

    if result["errors"]:
        print(f"\n❌ ASSEMBLY FAILED — {len(result['errors'])} 项错误:")
        for e in result["errors"]:
            print(f"  • {e}")
        sys.exit(1)

    print("\n✅ Assembly 完成 — 投稿层结构完整")
    sys.exit(0)


if __name__ == "__main__":
    main()

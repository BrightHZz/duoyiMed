#!/usr/bin/env python3
"""Vancouver Reference Reordering — 按首次引用顺序自动重编号

读取项目 sections/*.md，按正文阅读顺序提取 [N] 引用的首次出现顺序，
重建 old→new 映射，重写所有 section 文件中的引用编号和参考文献列表。

适用所有事业部和所有项目。纯确定性操作，无需 LLM。

用法:
    python run_reference_order.py --project-dir /path/to/project
    python run_reference_order.py --project-dir /path/to/project --check-only
"""

import os
import re
import sys
import argparse
from pathlib import Path

# Reading order: body sections first, references last
BODY_SECTIONS = [
    "02_introduction.md",
    "03_methods.md",
    "04_results.md",
    "05_discussion.md",
    "06_conclusion.md",
    "01_title_abstract.md",
]
REF_SECTION = "07_references.md"


def extract_first_appearance_order(sections_dir: Path):
    """Scan body sections in reading order, return list of ref numbers by first appearance."""
    seen = {}
    order = []
    for fname in BODY_SECTIONS:
        path = sections_dir / fname
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\[(\d+(?:,\d+)*)\]", text):
            nums = [int(x) for x in match.group(1).split(",")]
            for n in nums:
                if n not in seen:
                    seen[n] = len(order) + 1
                    order.append(n)
    return order, {old: new for new, old in enumerate(order, 1)}


def renumber_citations(mapping: dict, sections_dir: Path):
    """Rewrite all body section files with renumbered citations."""
    for fname in BODY_SECTIONS:
        path = sections_dir / fname
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")

        def replace_ref(match):
            nums = [int(x) for x in match.group(1).split(",")]
            new_nums = sorted(mapping.get(n, n) for n in nums)
            return "[" + ",".join(str(x) for x in new_nums) + "]"

        new_text = re.sub(r"\[(\d+(?:,\d+)*)\]", replace_ref, text)
        path.write_text(new_text, encoding="utf-8")


def reorder_reference_list(mapping: dict, sections_dir: Path):
    """Reorder references section to match new numbering."""
    ref_path = sections_dir / REF_SECTION
    if not ref_path.exists():
        return False

    text = ref_path.read_text(encoding="utf-8")
    entries = re.split(r"\n(?=\d+\.\s)", text.strip())

    header_lines = []
    ref_entries = {}
    for entry in entries:
        m = re.match(r"(\d+)\.\s(.+)", entry, re.DOTALL)
        if m:
            ref_entries[int(m.group(1))] = m.group(2)
        else:
            header_lines.append(entry)

    new_lines = header_lines[:]
    for new_num in sorted(mapping.values()):
        old_num = None
        for o, n in mapping.items():
            if n == new_num:
                old_num = o
                break
        if old_num and old_num in ref_entries:
            new_lines.append(f"{new_num}. {ref_entries[old_num]}")

    ref_path.write_text("\n".join(new_lines), encoding="utf-8")
    return True


def check_order_correct(order: list) -> bool:
    """Check if current numbering follows Vancouver rules."""
    for i, ref_num in enumerate(order, 1):
        if ref_num != i:
            return False
    return True


def run_reference_order(project_dir: Path, check_only: bool = False) -> dict:
    """
    Execute Vancouver reference reordering.

    Returns:
        {"ok": bool, "ref_count": int, "was_correct": bool, "message": str}
    """
    sd = project_dir / "sections"
    if not sd.is_dir():
        return {"ok": False, "ref_count": 0, "was_correct": False,
                "message": f"Sections directory not found: {sd}"}

    order, mapping = extract_first_appearance_order(sd)

    if not order:
        return {"ok": True, "ref_count": 0, "was_correct": True,
                "message": "No references found in body sections."}

    is_correct = check_order_correct(order)

    if is_correct:
        return {"ok": True, "ref_count": len(order), "was_correct": True,
                "message": f"References already in Vancouver order ({len(order)} refs)."}

    if check_only:
        violations = sum(1 for i, o in enumerate(order, 1) if i != o)
        return {"ok": False, "ref_count": len(order), "was_correct": False,
                "message": f"{violations} references out of Vancouver order. Run without --check-only to auto-fix."}

    # Auto-fix
    renumber_citations(mapping, sd)
    reorder_reference_list(mapping, sd)

    # Verify
    order2, _ = extract_first_appearance_order(sd)
    if check_order_correct(order2):
        return {"ok": True, "ref_count": len(order2), "was_correct": False,
                "message": f"Renumbered {len(order2)} references to Vancouver order."}
    else:
        return {"ok": False, "ref_count": len(order2), "was_correct": False,
                "message": "ERROR: Renumbering failed — order still incorrect."}


def main():
    parser = argparse.ArgumentParser(description="Vancouver reference reordering")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check, exit 1 if order is wrong")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Vancouver Reference Order Check")
    print(f"Project: {project_dir}")
    print("=" * 60)

    result = run_reference_order(project_dir, args.check_only)
    print(f"\n{result['message']}")

    if not result["ok"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

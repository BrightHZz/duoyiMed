#!/usr/bin/env python3
"""Pre-flight Data Authenticity Scan — 数据真实性扫描（Preflight 第7步）

在 Phase 6 脚本执行前调用，扫描源码中是否存在数据注入/模拟的风险模式。
Scan FAIL → 拒绝执行，输出修复清单。

通用规则 — 仅触发当 np.random 用于生成分层/标签/分数等影响 Table 1 的变量。
适用所有事业部（老年/泌尿/儿科）和所有数据源（CHARLS/MIMIC/NHANES）。

用法:
    python run_preflight_data.py --project-dir /path/to/project
"""

import os
import re
import sys
import argparse
from pathlib import Path

# Phase 6 脚本扫描目标
PHASE6_SCRIPTS = [
    "generate_figures.py",
    "generate_tables.py",
    "run_humanize.py",
    "run_assembly.py",
]


def scan_file(filepath: Path) -> list:
    """Scan a single file for data authenticity violations."""
    basename = filepath.name
    try:
        source = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return [{"file": basename, "line": 0, "severity": "WARN", "detail": str(e)}]

    lines = source.split("\n")
    violations = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        # CRITICAL: np.random assigned to variable with data-infusion keywords
        m_assign = re.match(
            r'(\w+)\s*=\s*np\.random\.(?!seed\b|RandomState\b)(\w+)\(', stripped
        )
        if m_assign:
            var_name = m_assign.group(1).lower()
            func_name = m_assign.group(2)
            data_kw = r'(efi|frail|strata|stratum|group_label|risk_score|grade|stage|label|class|cluster|synthetic)'
            if re.search(data_kw, var_name):
                ctx = "\n".join(lines[max(0, i - 3):min(len(lines), i + 8)])
                if re.search(r'(Table|table|stratif|group.*by|\.iloc|\.loc|patients?|cohort)', ctx):
                    violations.append({
                        "file": basename, "line": i,
                        "severity": "CRITICAL",
                        "detail": f"np.random.{func_name}() -> '{var_name}' used in stratification context"
                    })

        # CRITICAL: explicit simulate/synthetic keyword near data creation
        if re.search(r'(simulate|synthetic).*?(data|score|strata|cohort|patient)',
                     stripped, re.IGNORECASE):
            violations.append({
                "file": basename, "line": i,
                "severity": "CRITICAL",
                "detail": f"simulated/synthetic keyword: {stripped[:100]}"
            })

    # HIGH: check data source declarations
    if basename == "generate_tables.py":
        has_pkl = bool(re.search(r'(features_cache\.pkl|cache\[.?X.?\])', source))
        has_efi_col = bool(re.search(r'df\[.efi_score.\]|efi_score.*=.*df\[', source))
        if not has_pkl and not has_efi_col:
            violations.append({
                "file": basename, "line": 0,
                "severity": "HIGH",
                "detail": "No reference to features_cache.pkl or efi_score column. "
                          "Stratification data source must be declared."
            })

    if basename == "generate_figures.py":
        has_cv = bool(re.search(r'(cv_results\.json|CV_RESULTS)', source))
        if not has_cv:
            violations.append({
                "file": basename, "line": 0,
                "severity": "HIGH",
                "detail": "No reference to cv_results.json. Figures must read from baseline."
            })

    return violations


def run_preflight_data(project_dir: Path) -> dict:
    """
    Execute data authenticity preflight scan.

    Returns:
        {"ok": bool, "violations": list, "scanned": int}
    """
    violations = []
    scanned = 0

    # Try scripts/ subdirectory first, then project root
    for loc in [project_dir / "scripts", project_dir]:
        if not loc.is_dir():
            continue
        for fname in PHASE6_SCRIPTS:
            fpath = loc / fname
            if fpath.exists():
                scanned += 1
                v = scan_file(fpath)
                violations.extend(v)

    critical = [v for v in violations if v["severity"] == "CRITICAL"]
    high = [v for v in violations if v["severity"] == "HIGH"]

    return {
        "ok": len(critical) + len(high) == 0,
        "violations": violations,
        "scanned": scanned,
        "critical_count": len(critical),
        "high_count": len(high),
    }


def main():
    parser = argparse.ArgumentParser(description="Pre-flight Data Authenticity Scan")
    parser.add_argument("--project-dir", required=True, help="Project root directory")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("Pre-flight Data Authenticity Scan (Step 7)")
    print(f"Project: {project_dir}")
    print("=" * 60)

    result = run_preflight_data(project_dir)

    print(f"\nScanned: {result['scanned']} file(s)")
    print(f"Results: {result['critical_count']} CRITICAL, {result['high_count']} HIGH")

    for v in result["violations"]:
        icon = "BLOCK" if v["severity"] == "CRITICAL" else "WARN " if v["severity"] == "HIGH" else "INFO "
        print(f"  [{icon}] [{v['severity']}] {v['file']}:{v['line']} — {v['detail']}")

    if not result["ok"]:
        print(f"\nBLOCKED: {result['critical_count']} CRITICAL + {result['high_count']} HIGH violation(s).")
        print("  Fix: replace np.random with real data from features_cache.pkl or baseline CSV.")
        sys.exit(1)
    else:
        print("\nPre-flight data scan PASSED — safe to execute.")
        sys.exit(0)


if __name__ == "__main__":
    main()

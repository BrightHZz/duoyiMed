#!/usr/bin/env python3
"""Phase 6 Humanize Check CLI — Reusable engine script.

Scans sections/*.md for AI-writing markers:
  - Banned words/phrases (36 patterns from humanizer-rules)
  - Transition word overuse (>3 per section file)
  - Hedge word overuse per section
  - Concluding slogans (Discussion + Conclusion)
  - Abbreviation convention violations

Exit 0 = CLEAN, exit 1 = FAIL (must fix before proceeding).
LLM semantic review for naturalness is a separate step performed by the orchestrator.

Usage:
    python run_humanize.py --project-dir /path/to/project
    python run_humanize.py --project-dir /path/to/project --json
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path


# ================================================================
# Banned AI words/phrases (36 items, synced with humanizer-rules.md)
# ================================================================
BANNED_PATTERNS = [
    # High priority
    r"\bpivotal\b",
    r"\bcrucial\b",
    r"\blandscape\b",  # metaphorical
    r"\bdelve[s]?\b", r"\bdelve\s+into\b",
    r"\bunderscores?\b", r"\bunderscoring\b",
    r"\bevolving\s+landscape\b",
    r"\bgroundbreaking\b",
    r"\brenowned\b",
    r"\bprofound\s+impact\b",
    r"\bremarkable\b",
    r"\bdramatic(?:ally)?\b",
    r"\b(?:showcasing|highlighting|underscoring)\s+the\s+",
    r"\bmoreover\b", r"\bfurthermore\b",
    r"\bnotably\b", r"\bnoteworthy\b",
    r"\bserves?\s+as\b", r"\bstands?\s+as\b",
    r"\bin\s+order\s+to\b",
    r"\bfor\s+the\s+purpose\s+of\b",
    r"\ba\s+total\s+of\b",
    r"\butiliz[ae]s?\b",
    r"\bdemonstrat[es]\b",  # non-experimental context
    r"\bfacilitates?\b",
    # Medium priority
    r"[Nn]ot\s+only.+but\s+also",
    r"[Ss]tudies\s+have\s+shown\b",
    r"[Ee]xperts\s+argue\b",
    r"[Ii]t\s+is\s+important\s+to\s+note\b",
    # Concluding slogans
    r"\bpaving\s+the\s+way\b",
    r"\bushering\s+in\b",
    r"\bhighlighting\s+the\s+potential\b",
    r"\bopening\s+the\s+door\b",
    r"\b(?:game.changer|revolutionize)\b",
    # Added from comprehensive rules
    r"\bnevertheless\b", r"\bnonetheless\b",
    r"\bconsequently\b", r"\baccordingly\b",
    r"\bin\s+light\s+of\b", r"\bin\s+this\s+regard\b",
    r"\bit\s+is\s+worth\s+noting\b",
    r"\bparamount\b",
    r"\bleveraging\b", r"\bleveraged\b",
    r"\bsheds?\s+light\b",
    r"\bdemonstrates?\s+the\s+(?:power|potential|efficacy|utility)\b",
    r"\bcomprehensive\s+(?:analysis|review|evaluation|assessment)\b",
    r"\brobust\b.*?\b(?:methodology|framework|analysis|approach)\b",
]

# ================================================================
# Transition words (allow ≤3 per full document)
# ================================================================
TRANSITION_WORDS = [
    r"\bhowever\b", r"\btherefore\b", r"\bthus\b", r"\bhence\b",
    r"\bmoreover\b", r"\bfurthermore\b", r"\bnevertheless\b", r"\bnonetheless\b",
    r"\bconsequently\b", r"\baccordingly\b", r"\bin\s+addition\b",
    r"\bmeanwhile\b", r"\bwhereas\b", r"\bnotably\b", r"\bindeed\b",
    r"\bspecifically\b", r"\bimportantly\b", r"\binterestingly\b",
    r"\btaken\s+together\b", r"\boverall\b", r"\bin\s+summary\b",
    r"\bin\s+conclusion\b",
]
TRANSITION_MAX_PER_FILE = 3

# ================================================================
# Hedge words
# ================================================================
HEDGE_WORDS = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bpotentially\b",
    r"\bpossibly\b", r"\blikely\b", r"\bsuggest(?:s|ed|ing)?\b",
    r"\bappears?\b", r"\btend(?:s|ed)?\b",
]
HEDGE_MAX_DISCUSSION_P3 = 3
HEDGE_MAX_CONCLUSION = 1

# ================================================================
# Concluding slogans (banned in Discussion ¶4 and Conclusion)
# ================================================================
CONCLUDING_SLOGANS = [
    r"(?i)\bfuture\s+(?:research|studies|work|investigations?)\s+(?:should|must|will|are?\s+needed)\b",
    r"(?i)\bfurther\s+(?:research|studies|investigations?)\s+(?:is|are)\s+(?:needed|warranted|required)\b",
    r"(?i)\bmore\s+(?:research|studies)\s+(?:is|are)\s+needed\b",
    r"(?i)\bin\s+conclusion\b", r"(?i)\bto\s+sum\s+up\b",
    r"(?i)\btaken\s+together\b",
    r"(?i)\bthese\s+findings\s+(?:collectively|together)\b",
    r"(?i)\bour\s+results\s+(?:demonstrate|show|indicate|suggest)\s+that\b",
]

# ================================================================
# Common abbreviations that need definition
# ================================================================
COMMON_ABBR_DEFINITIONS = {
    "eFI": "electronic Frailty Index",
    "HDU": "high dependency unit",
    "SOFA": "Sequential Organ Failure Assessment",
    "SHAP": "SHapley Additive exPlanations",
    "MICE": "Multivariate Imputation by Chained Equations",
    "NRI": "Net Reclassification Improvement",
    "IDI": "Integrated Discrimination Improvement",
    "DCA": "decision curve analysis",
    "EHR": "electronic health record",
    "ICU": "intensive care unit",
    "PR-AUC": "precision-recall AUC",
    "PPV": "positive predictive value",
    "NPV": "negative predictive value",
    "LR": "logistic regression",
    "XGB": "extreme gradient boosting",
    "RF": "random forest",
    "LGBM": "light gradient boosting machine",
}

# Universal abbreviations exempted from full-form requirement
UNIVERSAL_ABBR = {
    "DNA", "RNA", "BMI", "CI", "AUC", "OR", "HR", "SD", "SE",
    "ROC", "IQR", "SD", "p", "N", "n", "vs", "et al",
}


def scan_file(filepath: Path) -> list[dict]:
    """Scan a single markdown file and return violations."""
    text = filepath.read_text(encoding='utf-8')
    violations = []
    short_name = filepath.name

    # 1. Banned words
    for pattern in BANNED_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            violations.append({
                "file": short_name,
                "type": "BANNED",
                "pattern": pattern,
                "match": m.group(),
                "context": text[max(0, m.start() - 40):m.end() + 40].replace("\n", " "),
            })

    # 2. Transition word overuse (per file, not per occurrence)
    trans_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in TRANSITION_WORDS)
    if trans_count > TRANSITION_MAX_PER_FILE:
        violations.append({
            "file": short_name,
            "type": "TRANSITION_OVERUSE",
            "count": trans_count,
            "limit": TRANSITION_MAX_PER_FILE,
        })

    # 3. Hedge word count
    hedge_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in HEDGE_WORDS)
    # Only flag if excessive (>80 across entire document)
    if hedge_count > 80:
        violations.append({
            "file": short_name,
            "type": "HEDGE_EXCESSIVE",
            "count": hedge_count,
            "limit": 80,
        })

    # 4. Concluding slogans (only in discussion/conclusion)
    if "discussion" in short_name.lower() or "conclusion" in short_name.lower():
        for pattern in CONCLUDING_SLOGANS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                violations.append({
                    "file": short_name,
                    "type": "CONCLUDING_SLOGAN",
                    "match": m.group(),
                    "context": text[max(0, m.start() - 40):m.end() + 40].replace("\n", " "),
                })

    # 5. Check Discussion specifically for ¶4 slogans + hedge in ¶3
    if "discussion" in short_name.lower():
        # Extract paragraphs (split by blank line)
        paragraphs = re.split(r'\n\n+', text)
        # Find Discussion body (after the ## Discussion heading)
        disc_start = 0
        for i, p in enumerate(paragraphs):
            if re.match(r'^## Discussion', p):
                disc_start = i + 1
                break

        disc_paragraphs = paragraphs[disc_start:]

        # Check ¶3 (index 2) hedge density
        if len(disc_paragraphs) >= 3 and disc_paragraphs[2]:
            p3_hedge = sum(len(re.findall(p, disc_paragraphs[2], re.IGNORECASE)) for p in HEDGE_WORDS)
            if p3_hedge > HEDGE_MAX_DISCUSSION_P3:
                violations.append({
                    "file": short_name,
                    "type": "HEDGE_P3_OVERUSE",
                    "count": p3_hedge,
                    "limit": HEDGE_MAX_DISCUSSION_P3,
                    "context": "Discussion ¶3 hedge density exceeds limit",
                })

        # Check ¶4 (index 3) for concluding slogans
        if len(disc_paragraphs) >= 4 and disc_paragraphs[3]:
            for pattern in CONCLUDING_SLOGANS:
                for m in re.finditer(pattern, disc_paragraphs[3], re.IGNORECASE):
                    violations.append({
                        "file": short_name,
                        "type": "DISCUSSION_P4_SLOGAN",
                        "match": m.group(),
                        "context": disc_paragraphs[3][max(0, m.start()-30):m.end()+30].replace("\n", " "),
                    })

    return violations


def scan_abbreviations(text: str) -> list[dict]:
    """Check that each abbreviation has full form on first use."""
    issues = []

    # Find all potential abbreviations (2+ uppercase letters)
    all_caps = set()
    for m in re.finditer(r'\b([A-Z]{2,}(?:/[A-Z]{2,})*)\b', text):
        abbr = m.group(1)
        if abbr not in UNIVERSAL_ABBR and not abbr.isdigit():
            all_caps.add(abbr)

    # Check each abbreviation
    for abbr in sorted(all_caps):
        # Count occurrences
        occurrences = list(re.finditer(rf'\b{re.escape(abbr)}\b', text))
        standalone_count = len(occurrences)

        if standalone_count == 0:
            continue

        # Check for "Full Name (ABBR)" definition pattern before first occurrence
        first_pos = occurrences[0].start()
        text_before_first = text[:first_pos]

        # Look for definition: either "Full Name (ABBR)" or "ABBR (Full Name)"
        has_definition = False
        if abbr in COMMON_ABBR_DEFINITIONS:
            full_form = COMMON_ABBR_DEFINITIONS[abbr]
            if re.search(rf'{re.escape(full_form)}\s*\({re.escape(abbr)}\)', text_before_first, re.IGNORECASE):
                has_definition = True

        # Generic check: any "Words (ABBR)" pattern
        if not has_definition:
            # Look for any word preceding the abbreviation definition
            if re.search(rf'\(.*?\)\s*\({re.escape(abbr)}\)', text_before_first):
                has_definition = True
            # Or if the abbreviation appears as a definition itself
            if re.search(rf'{re.escape(abbr)}\s*\(', text_before_first):
                has_definition = True

        if not has_definition and standalone_count >= 2:
            issues.append({
                "abbreviation": abbr,
                "occurrences": standalone_count,
                "first_position": first_pos,
                "suggested_definition": COMMON_ABBR_DEFINITIONS.get(abbr, "?"),
            })

    return issues


def run_humanize(project_dir: Path) -> dict:
    """Execute humanize check and return structured results.

    Returns:
        {"pass": bool, "violations": [...], "abbr_issues": [...],
         "banned_count": int, "trans_overuse_count": int, "slogan_count": int}
    """
    sections_dir = project_dir / "sections"
    if not sections_dir.is_dir():
        return {
            "pass": False,
            "violations": [{"file": "N/A", "type": "ERROR",
                            "match": "sections/ directory not found"}],
            "abbr_issues": [],
            "banned_count": 0, "trans_overuse_count": 0, "slogan_count": 0,
        }

    md_files = sorted([f for f in sections_dir.iterdir() if f.suffix == ".md"])
    if not md_files:
        return {
            "pass": False,
            "violations": [{"file": "N/A", "type": "ERROR",
                            "match": "No .md files in sections/"}],
            "abbr_issues": [],
            "banned_count": 0, "trans_overuse_count": 0, "slogan_count": 0,
        }

    all_violations = []
    total_banned = 0
    total_trans = 0
    total_slogans = 0

    for fpath in md_files:
        violations = scan_file(fpath)
        banned_c = sum(1 for v in violations if v["type"] == "BANNED")
        trans_c = sum(1 for v in violations if v["type"] == "TRANSITION_OVERUSE")
        slogan_c = sum(1 for v in violations if v["type"] in ("CONCLUDING_SLOGAN", "DISCUSSION_P4_SLOGAN"))

        total_banned += banned_c
        total_trans += trans_c
        total_slogans += slogan_c
        all_violations.extend(violations)

    # Scan abbreviations across full text (excluding references/acknowledgments)
    full_text = ""
    for fpath in md_files:
        name_lower = fpath.name.lower()
        if "reference" not in name_lower and "acknowledgment" not in name_lower:
            full_text += fpath.read_text(encoding='utf-8') + "\n"

    abbr_issues = scan_abbreviations(full_text)

    passed = (total_banned == 0 and total_trans == 0 and total_slogans == 0)

    return {
        "pass": passed,
        "violations": all_violations,
        "abbr_issues": abbr_issues,
        "banned_count": total_banned,
        "trans_overuse_count": total_trans,
        "slogan_count": total_slogans,
    }


def main():
    _fp = Path(__file__).resolve()
    if _fp.parent.parent.name != "engine":
        import warnings
        warnings.warn(
            f"此脚本的项目本地副本已过时。请删除并使用引擎版本: "
            f"python engine/scripts/{_fp.name} --project-dir .",
            DeprecationWarning, stacklevel=2
        )

    parser = argparse.ArgumentParser(
        description="Phase 6 Humanize Check — Python regex layer (de-AI scan)"
    )
    parser.add_argument(
        "--project-dir", required=True,
        help="Project root directory (must contain sections/ subdirectory)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON"
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    result = run_humanize(project_dir)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print("=" * 60)
        print("Phase 6: Humanize Quality Check (Python Layer)")
        print(f"Project: {project_dir}")
        print("=" * 60)

        # Banned words
        banned_violations = [v for v in result["violations"] if v["type"] == "BANNED"]
        if banned_violations:
            print(f"\n--- Banned AI Words ({len(banned_violations)} hits) ---")
            for v in banned_violations:
                print(f"  [{v['file']}] '{v['match']}'")
                print(f"    Context: ...{v['context']}...")

        # Transition overuse
        trans_violations = [v for v in result["violations"] if v["type"] == "TRANSITION_OVERUSE"]
        if trans_violations:
            print(f"\n--- Transition Overuse ({len(trans_violations)} files) ---")
            for v in trans_violations:
                print(f"  [{v['file']}] {v['count']} transition words (limit: {v['limit']})")

        # Concluding slogans
        slogan_violations = [v for v in result["violations"]
                            if v["type"] in ("CONCLUDING_SLOGAN", "DISCUSSION_P4_SLOGAN")]
        if slogan_violations:
            print(f"\n--- Concluding Slogans ({len(slogan_violations)} hits) ---")
            for v in slogan_violations:
                print(f"  [{v['file']}] '{v['match']}'")

        # Hedge issues
        hedge_violations = [v for v in result["violations"]
                           if v["type"] in ("HEDGE_EXCESSIVE", "HEDGE_P3_OVERUSE")]
        if hedge_violations:
            print(f"\n--- Hedge Overuse ({len(hedge_violations)} issues) ---")
            for v in hedge_violations:
                print(f"  [{v['file']}] {v['count']} hedge words (limit: {v['limit']})")

        # Abbreviation issues
        if result["abbr_issues"]:
            print(f"\n--- Abbreviation Issues ({len(result['abbr_issues'])} items) ---")
            for issue in result["abbr_issues"]:
                print(f"  {issue['abbreviation']}: used {issue['occurrences']} times, "
                      f"no definition found before first use "
                      f"(suggested: {issue['suggested_definition']})")

        # Summary
        print(f"\n--- Summary ---")
        print(f"  Banned: {result['banned_count']} (must be 0)")
        print(f"  Transition overuse: {result['trans_overuse_count']} files (must be 0)")
        print(f"  Concluding slogans: {result['slogan_count']} (must be 0)")
        print(f"  Abbreviation issues: {len(result['abbr_issues'])}")

    if not result["pass"]:
        print("\nFAIL: Humanize check not clean. Fix violations above before proceeding.")
        print("NOTE: LLM semantic review for naturalness is still required (Gate 6 #22 LLM layer).")
        sys.exit(1)
    else:
        print("\nPASS: Humanize check clean (Python layer).")
        print("NOTE: LLM semantic review for naturalness is still required (Gate 6 #22 LLM layer).")
        sys.exit(0)


if __name__ == "__main__":
    main()

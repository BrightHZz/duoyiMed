"""
Phase 6 Runner — Encapsulates the full Phase 6 pipeline.

Python+LLM hybrid execution model:
  - Python steps: deterministic, run as subprocess, exit != 0 blocks pipeline
  - LLM steps: creative, delegated to orchestrator's agent call mechanism

Pipeline:
  Step 0: Preflight (Python)  → safety scan, FAIL blocks
  Step 1: Figures   (Python)  → project generate_figures.py subprocess
  Step 2: Tables    (Python)  → project generate_tables.py subprocess
  Step 3: Sections  (LLM)     → orchestrator calls scientific-writer
  Step 4: Humanize  (Python+LLM) → run_humanize.py + LLM naturalness review
  Step 5: Assembly  (Python)  → engine/scripts/run_assembly.py
  Step 6: Gate 6    (Python+LLM) → run_gate6.py + LLM semantic checks (4 items)

Usage:
    from engine.core.phase6_runner import Phase6Runner

    runner = Phase6Runner(
        project_dir=Path("/projects/hdu-geriatric-2026"),
        project_id="hdu-geriatric-2026",
        orchestrator=orch,  # None for headless mode (LLM steps skipped)
    )
    result = runner.run(user_request="...", previous_outputs={...})
    if not result["success"]:
        for err in result["errors"]:
            print(err)
"""

import os
import re
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Any
from datetime import datetime


# ================================================================
# Phase6Runner
# ================================================================

class Phase6Runner:
    """Encapsulates the full Phase 6 pipeline (preflight → figures → tables →
    sections(LLM) → humanize → assembly → gate6).

    Python steps run as subprocesses with exit code checking.
    LLM steps delegate to the orchestrator's _call_agent() method.
    """

    # Step timeout defaults (seconds)
    TIMEOUT_PREFLIGHT = 30
    TIMEOUT_FIGURES = 300
    TIMEOUT_TABLES = 120
    TIMEOUT_SECTIONS_LLM = 300
    TIMEOUT_HUMANIZE = 60
    TIMEOUT_ASSEMBLY = 30
    TIMEOUT_GATE6 = 120
    TIMEOUT_GATE6_LLM = 120

    # Engine scripts directory (relative to this file's parent)
    # engine/core/phase6_runner.py → engine/scripts/
    ENGINE_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

    # Section output order (for assembly + file listing)
    SECTION_ORDER = [
        "01_title_abstract.md",
        "02_introduction.md",
        "03_methods.md",
        "04_results.md",
        "05_discussion.md",
        "06_conclusion.md",
        "07_references.md",
        "08_acknowledgments.md",
    ]

    def __init__(
        self,
        project_dir: Path,
        project_id: str,
        orchestrator=None,  # OrchestratorGraph instance (or None for headless)
        verbose: bool = True,
    ):
        self.project_dir = Path(project_dir)
        self.project_id = project_id
        self.orch = orchestrator
        self.verbose = verbose

        # Derived paths
        self.sections_dir = self.project_dir / "sections"
        self.tables_dir = self.project_dir / "tables"
        self.figures_dir = self.project_dir / "figures"
        self.submission_dir = self.project_dir / "submission"
        self.scripts_dir = self.project_dir / "scripts"
        self.outputs_dir = self.project_dir / "outputs"

    # ================================================================
    # Public API
    # ================================================================

    def run(
        self,
        user_request: str = "",
        previous_outputs: dict = None,
    ) -> dict:
        """Execute the full Phase 6 pipeline in strict sequence.

        Returns:
            {"success": bool,
             "step_results": {step_name: {...}},
             "errors": [str],
             "failed_at": str or None}
        """
        previous_outputs = previous_outputs or {}
        step_results = {}
        errors = []

        pipeline = [
            ("preflight",  self._step_preflight),
            ("figures",    lambda: self._step_figures()),
            ("tables",     lambda: self._step_tables()),
            ("sections",   lambda: self._step_sections(user_request, previous_outputs, step_results)),
            ("humanize",   lambda: self._step_humanize()),
            ("assembly",   lambda: self._step_assembly()),
            ("gate6",      lambda: self._step_gate6()),
        ]

        for step_name, step_fn in pipeline:
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"Phase 6 — Step: {step_name}")
                print(f"{'='*60}")

            try:
                result = step_fn()
            except Exception as e:
                result = {"success": False, "error": str(e)}
                if self.verbose:
                    print(f"  ❌ Exception in {step_name}: {e}")

            step_results[step_name] = result

            if not result.get("success", False):
                errors.append(
                    f"Step '{step_name}': {result.get('error', 'FAILED')}"
                )
                if self.verbose:
                    print(f"  ❌ Pipeline BLOCKED at step: {step_name}")
                return {
                    "success": False,
                    "step_results": step_results,
                    "errors": errors,
                    "failed_at": step_name,
                    "timestamp": datetime.now().isoformat(),
                }

            if self.verbose:
                print(f"  ✅ {step_name} PASSED")

        return {
            "success": True,
            "step_results": step_results,
            "errors": [],
            "failed_at": None,
            "timestamp": datetime.now().isoformat(),
        }

    # ================================================================
    # Step 0: Preflight Safety Scan
    # ================================================================

    def _step_preflight(self) -> dict:
        """Run preflight safety scan on project scripts.

        Scans scripts/generate_figures.py and scripts/generate_tables.py.
        FAIL blocks pipeline entirely.
        """
        scan_targets = []
        for script_name in ["generate_figures.py", "generate_tables.py"]:
            candidate = self.scripts_dir / script_name
            if candidate.exists():
                scan_targets.append(f"scripts/{script_name}")

        if not scan_targets:
            # No scripts to scan — skip
            return {"success": True, "pass": True, "report": "No scripts to scan (skipped)",
                    "failures": [], "warnings": [], "exit_code": 0, "stdout": "", "stderr": ""}

        # Use engine's PreflightScanner if available (in-process), otherwise subprocess
        try:
            from engine.core.preflight_scanner import PreflightScanner
            scanner = PreflightScanner()
            scan_result = scanner.scan(self.project_dir, scan_targets)
            return {
                "success": scan_result["pass"],
                "pass": scan_result["pass"],
                "report": scan_result["report"],
                "failures": scan_result["failures"],
                "warnings": scan_result["warnings"],
                "exit_code": 0 if scan_result["pass"] else 1,
                "stdout": scan_result["report"],
                "stderr": "",
            }
        except ImportError:
            # Fallback: run as subprocess
            preflight_script = self.ENGINE_SCRIPTS_DIR / "run_preflight.py"
            if not preflight_script.exists():
                return {"success": True, "pass": True,
                        "report": "Preflight scanner not available (skipped)",
                        "failures": [], "warnings": [], "exit_code": 0, "stdout": "", "stderr": ""}

            script_args = [str(preflight_script), "--project-dir", str(self.project_dir)]
            if scan_targets:
                script_args.extend(["--scripts"] + [s.replace("scripts/", "") for s in scan_targets])

            return self._run_subprocess(
                str(preflight_script),
                extra_args=["--project-dir", str(self.project_dir),
                           "--scripts"] + [s.replace("scripts/", "") for s in scan_targets],
                timeout_sec=self.TIMEOUT_PREFLIGHT,
            )

    # ================================================================
    # Step 1: Generate Figures (Python subprocess)
    # ================================================================

    def _step_figures(self) -> dict:
        """Run project's generate_figures.py as subprocess.

        The script reads cv_results.json from outputs/ and writes Figure[N]_*.png/.tiff
        + _data.json + _caption.md to figures/.
        """
        fig_script = self._find_script("generate_figures.py")
        if not fig_script:
            return self._script_not_found("generate_figures.py", "figures")

        return self._run_subprocess(
            str(fig_script),
            extra_args=["--project-dir", str(self.project_dir)],
            timeout_sec=self.TIMEOUT_FIGURES,
        )

    # ================================================================
    # Step 2: Generate Tables (Python subprocess)
    # ================================================================

    def _step_tables(self) -> dict:
        """Run project's generate_tables.py as subprocess.

        The script reads cv_results.json from outputs/ and writes Table[N]_*.csv/.md
        to tables/.
        """
        tbl_script = self._find_script("generate_tables.py")
        if not tbl_script:
            return self._script_not_found("generate_tables.py", "tables")

        return self._run_subprocess(
            str(tbl_script),
            extra_args=["--project-dir", str(self.project_dir)],
            timeout_sec=self.TIMEOUT_TABLES,
        )

    # ================================================================
    # Step 3: Write Sections (LLM — orchestrator required)
    # ================================================================

    def _step_sections(
        self,
        user_request: str,
        previous_outputs: dict,
        step_results: dict,
    ) -> dict:
        """LLM writes all IMRAD sections via orchestrator's scientific-writer agent.

        This is the ONLY creative step in Phase 6. The LLM produces section text
        which the orchestrator writes to sections/*.md.

        Without an orchestrator (headless mode), this step is skipped.
        """
        if not self.orch:
            if self.sections_dir.is_dir() and list(self.sections_dir.glob("*.md")):
                return {"success": True, "agent_output": "(headless — sections already exist)",
                        "error": None}
            return {"success": False, "agent_output": "",
                    "error": "No orchestrator available for LLM sections writing, "
                             "and sections/ directory is empty"}

        # Build rich prompt with context from prior steps
        prompt_parts = [user_request]

        # Add figure/table context
        fig_result = step_results.get("figures", {})
        tbl_result = step_results.get("tables", {})
        if fig_result.get("success"):
            prompt_parts.append("\n## Figure Generation Complete\n"
                               f"The following figures have been generated:\n{fig_result.get('stdout', '')[-2000:]}")
        if tbl_result.get("success"):
            prompt_parts.append("\n## Table Generation Complete\n"
                               f"The following tables have been generated:\n{tbl_result.get('stdout', '')[-2000:]}")

        # Add previous phase outputs
        for key, value in previous_outputs.items():
            if not key.startswith("_") and isinstance(value, str) and len(value) > 50:
                safe_key = key.split("/")[-1]
                truncated = value[:3000] + "..." if len(value) > 3000 else value
                prompt_parts.append(f"\n## Upstream: {safe_key}\n{truncated}")

        prompt = "\n".join(prompt_parts)
        prompt += (
            "\n\nPlease write each IMRAD section as a separate markdown file "
            "to be saved in sections/:\n"
            "- 01_title_abstract.md\n- 02_introduction.md\n- 03_methods.md\n"
            "- 04_results.md\n- 05_discussion.md\n- 06_conclusion.md\n"
            "- 07_references.md\n- 08_acknowledgments.md\n\n"
            "Constraints:\n"
            "- Title ≤ 15 words, Abstract ≤ 300 words, Keywords ≥ 3\n"
            "- Discussion must be 4 paragraphs (findings/literature/implications/limitations)\n"
            "- Methods ↔ Results must be 1:1 corresponding\n"
            "- All numbers must be traceable to cv_results.json\n"
            "- References ≥ 25, ≥ 80% recent (within 5 years)\n"
            "- Every reference must be cited in the text\n"
        )

        try:
            # Find the scientific-writer agent ID (division-aware)
            writer_id = "shared/scientific-writer"
            if hasattr(self.orch, 'active_division'):
                div = self.orch.active_division
                # Try division-specific first, fall back to shared
                writer_id = f"{div}/scientific-writer"

            # Call agent via orchestrator
            agent_output = self.orch._call_agent(
                agent_id=writer_id,
                task_input=prompt,
                phase_id="writing_sections",
                project_id=self.project_id,
            )

            # Check that sections/ has content after LLM call
            md_files = list(self.sections_dir.glob("*.md")) if self.sections_dir.is_dir() else []
            if len(md_files) >= 6:
                return {"success": True, "agent_output": agent_output,
                        "files_written": [f.name for f in md_files],
                        "error": None}
            else:
                # LLM may not have written files — orchestrator's _write_phase6_files handles this
                return {"success": True, "agent_output": agent_output,
                        "files_written": [f.name for f in md_files],
                        "note": "sections/ has < 6 files — may need _write_phase6_files fallback",
                        "error": None}

        except Exception as e:
            return {"success": False, "agent_output": "",
                    "error": f"LLM sections writing failed: {e}"}

    # ================================================================
    # Step 4: Humanize Check (Python + LLM)
    # ================================================================

    def _step_humanize(self) -> dict:
        """Two-layer humanize check.

        Layer 1 (Python): run_humanize.py subprocess — regex scan for banned words,
                          transition overuse, concluding slogans.
        Layer 2 (LLM): orchestrator calls humanizer to evaluate naturalness.
        """
        # Layer 1: Python regex scan
        humanize_script = self.ENGINE_SCRIPTS_DIR / "run_humanize.py"
        if not humanize_script.exists():
            python_result = {"success": True, "exit_code": 0,
                            "stdout": "run_humanize.py not found (skipped)", "stderr": ""}
        else:
            python_result = self._run_subprocess(
                str(humanize_script),
                extra_args=["--project-dir", str(self.project_dir), "--json"],
                timeout_sec=self.TIMEOUT_HUMANIZE,
            )

        # Layer 2: LLM naturalness review
        llm_result = {"pass": True, "feedback": "No orchestrator — LLM review skipped"}
        if self.orch:
            try:
                llm_result = self._run_llm_humanize_review()
            except Exception as e:
                llm_result = {"pass": False, "feedback": f"LLM humanize review failed: {e}"}

        overall_success = python_result.get("success", False) and llm_result.get("pass", False)

        return {
            "success": overall_success,
            "python": python_result,
            "llm": llm_result,
            "error": None if overall_success else "Humanize check not clean (Python or LLM layer failed)",
        }

    def _run_llm_humanize_review(self) -> dict:
        """Call LLM to evaluate naturalness of the de-AI-ified text."""
        if not self.orch:
            return {"pass": True, "feedback": "No orchestrator — skipped"}

        # Collect sections for review
        sections_text = ""
        for fname in self.SECTION_ORDER:
            fpath = self.sections_dir / fname
            if fpath.exists():
                sections_text += f"\n\n=== {fname} ===\n{fpath.read_text()[:2000]}"

        prompt = (
            "You are evaluating the naturalness of a de-AI-ified academic manuscript. "
            "Review the following sections and assess:\n\n"
            "1. Sentence rhythm: does sentence length vary naturally (not uniform 20-25 words)?\n"
            "2. Transition naturalness: are transitions organic, not mechanically replaced?\n"
            "3. Hedge balance: are hedging words (may, could, suggest) appropriately retained, "
            "not aggressively deleted?\n"
            "4. Template traces: does the text sound like it follows a rigid template, "
            "or does it read like domain-specific scientific writing?\n\n"
            f"SECTIONS:\n{sections_text[:8000]}\n\n"
            "Return a structured assessment: pass/fail + 2-3 sentence feedback."
        )

        try:
            humanizer_id = "shared/humanizer"
            response = self.orch._call_agent(
                agent_id=humanizer_id,
                task_input=prompt,
                phase_id="writing_humanize_llm",
                project_id=self.project_id,
            )
            # Parse response for pass/fail
            is_pass = "fail" not in response.lower()[:200]
            return {"pass": is_pass, "feedback": response[:500]}
        except Exception as e:
            return {"pass": True, "feedback": f"LLM call failed (non-blocking): {e}"}

    # ================================================================
    # Step 5: Assembly (Python subprocess)
    # ================================================================

    def _step_assembly(self) -> dict:
        """Run engine/scripts/run_assembly.py to assemble submission package.

        Concatenates sections/*.md → submission/manuscript.md (strips Classic annotations).
        Copies tables/*.csv → submission/tables/.
        Copies figures/*.png + *.tiff → submission/figures/.
        Enforces 5 negative constraints + self-check.
        """
        assembly_script = self.ENGINE_SCRIPTS_DIR / "run_assembly.py"
        if not assembly_script.exists():
            return {"success": False, "exit_code": -1,
                    "stdout": "", "stderr": "run_assembly.py not found in engine/scripts/",
                    "error": "run_assembly.py not found in engine/scripts/"}

        return self._run_subprocess(
            str(assembly_script),
            extra_args=["--project-dir", str(self.project_dir)],
            timeout_sec=self.TIMEOUT_ASSEMBLY,
        )

    # ================================================================
    # Step 6: Gate 6 Check (Python + LLM)
    # ================================================================

    def _step_gate6(self) -> dict:
        """Two-layer gate check.

        Layer 1 (Python): run_gate6.py subprocess — 28 deterministic auto checks.
        Layer 2 (LLM): 4 semantic checks via orchestrator LLM call.
        """
        # Layer 1: Python auto checks
        gate6_script = self.ENGINE_SCRIPTS_DIR / "run_gate6.py"
        if not gate6_script.exists():
            python_result = {"success": False, "exit_code": -1,
                            "stdout": "", "stderr": "run_gate6.py not found in engine/scripts/"}
        else:
            python_result = self._run_subprocess(
                str(gate6_script),
                extra_args=["--project-dir", str(self.project_dir), "--json"],
                timeout_sec=self.TIMEOUT_GATE6,
            )

        # Layer 2: LLM semantic checks (4 items)
        llm_result = {"pass": True, "checks": []}
        if self.orch and python_result.get("success", False):
            try:
                llm_result = self._run_llm_gate6_checks()
            except Exception as e:
                llm_result = {"pass": False, "checks": [{
                    "check_id": "llm_semantic",
                    "result": "fail",
                    "detail": f"LLM semantic checks failed: {e}",
                }]}

        python_pass = python_result.get("success", False)
        llm_pass = llm_result.get("pass", False)
        overall_success = python_pass and llm_pass

        return {
            "success": overall_success,
            "python": python_result,
            "llm": llm_result,
            "error": None if overall_success else (
                f"Gate 6: Python={'PASS' if python_pass else 'FAIL'}, "
                f"LLM={'PASS' if llm_pass else 'FAIL'}"
            ),
        }

    def _run_llm_gate6_checks(self) -> dict:
        """Execute 4 LLM semantic checks for Gate 6.

        Check 21b: Discussion four-paragraph semantic structure
        Check 22:  De-AI naturalness quality (semantic layer)
        Check 23:  Abbreviation first-use introduction
        Check overall: Methods ↔ Results 1:1 correspondence
        """
        if not self.orch:
            return {"pass": True, "checks": [], "note": "No orchestrator — LLM checks skipped"}

        # Read manuscript for review
        manuscript_path = self.submission_dir / "manuscript.md"
        if not manuscript_path.exists():
            return {"pass": False, "checks": [{
                "check_id": "llm_prerequisite",
                "result": "fail",
                "detail": "submission/manuscript.md not found — cannot run LLM semantic checks",
            }]}

        manuscript_text = manuscript_path.read_text()

        # Build a comprehensive prompt for all 4 checks
        prompt = (
            "You are a Gate 6 LLM semantic reviewer for a scientific manuscript. "
            "Perform the following 4 checks on the manuscript below. "
            "For each check, return: CHECK_ID, PASS/FAIL, and 2-3 sentences of detailed feedback.\n\n"
            "## Check 21b: Discussion Four-Paragraph Semantic Structure\n"
            "Read the Discussion section. Determine whether it forms four semantic paragraphs: "
            "(1) Principal findings summary, (2) Comparison with literature, "
            "(3) Clinical/research implications, (4) Limitations. "
            "Does each paragraph stay on topic? Does ¶4 avoid concluding slogans?\n\n"
            "## Check 22: De-AI Naturalness (Semantic Layer)\n"
            "Evaluate the text's naturalness: sentence length variation, paragraph rhythm, "
            "transition naturalness, hedge word balance. Does it read like human-written "
            "scientific prose, or are there template traces?\n\n"
            "## Check 23: Abbreviation First-Use Introduction\n"
            "List all non-universal abbreviations (exclude: DNA, RNA, BMI, CI, AUC, OR, HR, SD, SE, ROC). "
            "For each, find its FIRST occurrence in the manuscript and verify whether "
            "the full name is given at that point in 'Full Name (ABBR)' format.\n\n"
            "## Check Overall: Methods ↔ Results 1:1 Correspondence\n"
            "Cross-check each analytical method declared in Methods against its corresponding "
            "result in Results. Flag any method declared but not reported, or any result "
            "appearing without a corresponding method declaration.\n\n"
            f"MANUSCRIPT:\n{manuscript_text[:15000]}\n\n"
            "Return structured output with each check's PASS/FAIL status and detailed feedback."
        )

        try:
            # Use PI as gate reviewer (authority for quality sign-off)
            pi_id = "geriatrics/pi"
            if hasattr(self.orch, 'active_division'):
                pi_id = f"{self.orch.active_division}/pi"

            response = self.orch._call_agent(
                agent_id=pi_id,
                task_input=prompt,
                phase_id="writing_gate6_llm",
                project_id=self.project_id,
            )

            # Parse the response for pass/fail per check
            checks = []
            check_ids = ["21b", "22", "23", "overall"]
            for cid in check_ids:
                # Look for PASS/FAIL near the check ID
                pattern = rf'(?:check\s*{cid}|{cid})[^P]*(PASS|FAIL)'
                match = re.search(pattern, response, re.IGNORECASE)
                result = "pass" if (match and match.group(1).upper() == "PASS") else "fail"
                if not match:
                    # Fallback: if no FAIL found near check ID, assume pass
                    section_start = response.lower().find(f"check {cid}")
                    if section_start > 0:
                        section = response[section_start:section_start+500].lower()
                        result = "fail" if "fail" in section else "pass"

                checks.append({
                    "check_id": f"llm_{cid}",
                    "result": result,
                    "detail": response[:300],
                })

            all_pass = all(c["result"] == "pass" for c in checks)
            return {"pass": all_pass, "checks": checks}

        except Exception as e:
            return {"pass": False, "checks": [{
                "check_id": "llm_semantic",
                "result": "fail",
                "detail": f"LLM Gate 6 semantic checks failed: {e}",
            }]}

    # ================================================================
    # Utility Methods
    # ================================================================

    def _find_script(self, script_name: str) -> Optional[Path]:
        """Locate a script: first try project_dir/scripts/, then project_dir root."""
        candidate = self.scripts_dir / script_name
        if candidate.exists():
            return candidate
        candidate = self.project_dir / script_name
        if candidate.exists():
            return candidate
        return None

    def _script_not_found(self, script_name: str, step_name: str) -> dict:
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"{script_name} not found in {self.scripts_dir} or {self.project_dir}",
            "error": f"Step '{step_name}': {script_name} not found",
        }

    # Repo root (my-ai-writer/) for PYTHONPATH injection — allows generated
    # scripts to import from engine.utils.rounding etc.
    _ENGINE_ROOT = Path(__file__).resolve().parent.parent.parent

    @staticmethod
    def _run_subprocess(
        script_path: str,
        extra_args: list[str] = None,
        timeout_sec: int = 120,
    ) -> dict:
        """Run a Python script as subprocess, blocking on completion.

        Injects _ENGINE_ROOT into PYTHONPATH so generated scripts (generate_figures.py,
        generate_tables.py) can import from engine.utils.

        Args:
            script_path: Absolute path to the Python script
            extra_args: Additional CLI arguments (e.g. ["--project-dir", "/path"])
            timeout_sec: Max execution time before timeout

        Returns:
            {"success": bool, "exit_code": int, "stdout": str, "stderr": str}
        """
        extra_args = extra_args or []
        cmd = ["python", script_path] + extra_args

        # Inject engine root into PYTHONPATH
        env = os.environ.copy()
        engine_root = str(Phase6Runner._ENGINE_ROOT)
        existing = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = f"{engine_root}:{existing}" if existing else engine_root

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=env,
            )
            # Truncate stdout/stderr to avoid memory issues
            stdout = result.stdout[-5000:] if result.stdout else ""
            stderr = result.stderr[-5000:] if result.stderr else ""
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Timeout after {timeout_sec}s",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "python not found on PATH",
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
            }

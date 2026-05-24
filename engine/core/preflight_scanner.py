"""
执行前安全扫描器 — Pre-flight Safety Scanner

基于钱学森可靠性工程思想:
在 Phase 3/4/6 执行任何 Python 脚本前，强制执行安全配置扫描。
扫描 FAIL 时禁止执行，输出具体修复项清单。

背景: 2026-05-09/10/11 三次 kernel panic/memory exhaustion，
根因均为 ML 内存安全规范被违反但系统未阻断。

用法:
    from .preflight_scanner import PreflightScanner
    scanner = PreflightScanner()
    result = scanner.scan(Path("/project"), ["train_model.py", "generate_figures.py"])
    if not result["pass"]:
        print(result["report"])
"""

import re
import os
import platform
from pathlib import Path
from typing import Optional


class PreflightScanner:
    """执行前安全扫描器，检查 n_jobs、线程限制、pickle 覆盖、内存预估等"""

    # 必需的线程限制环境变量
    REQUIRED_THREAD_VARS = [
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ]

    # 安全样板必须包含的模式 (支持 os.environ["VAR"] = "val" 和 VAR = "val" 两种格式)
    SAFETY_BOILERPLATE_PATTERNS = [
        (r'OMP_NUM_THREADS', r'OMP_NUM_THREADS\s*=\s*["\']\d+["\']|os\.environ\[["\']\s*OMP_NUM_THREADS\s*["\']\s*\]\s*=\s*["\']\d+["\']'),
        (r'OPENBLAS_NUM_THREADS', r'OPENBLAS_NUM_THREADS\s*=\s*["\']\d+["\']|os\.environ\[["\']\s*OPENBLAS_NUM_THREADS\s*["\']\s*\]\s*=\s*["\']\d+["\']'),
        (r'MKL_NUM_THREADS', r'MKL_NUM_THREADS\s*=\s*["\']\d+["\']|os\.environ\[["\']\s*MKL_NUM_THREADS\s*["\']\s*\]\s*=\s*["\']\d+["\']'),
        (r'VECLIB_MAXIMUM_THREADS', r'VECLIB_MAXIMUM_THREADS\s*=\s*["\']\d+["\']|os\.environ\[["\']\s*VECLIB_MAXIMUM_THREADS\s*["\']\s*\]\s*=\s*["\']\d+["\']'),
        (r'NUMEXPR_NUM_THREADS', r'NUMEXPR_NUM_THREADS\s*=\s*["\']\d+["\']|os\.environ\[["\']\s*NUMEXPR_NUM_THREADS\s*["\']\s*\]\s*=\s*["\']\d+["\']'),
    ]

    def scan(self, project_dir: Path, target_scripts: list[str]) -> dict:
        """
        扫描指定项目的目标脚本。

        Args:
            project_dir: 项目根目录
            target_scripts: 要扫描的脚本文件名列表 (相对于 project_dir)

        Returns:
            {"pass": bool, "failures": [str], "warnings": [str], "report": str}
        """
        failures = []
        warnings = []
        all_scripts_data = {}

        # 解析目标脚本的绝对路径
        scripts_to_scan = []
        for script_name in target_scripts:
            # 支持 glob 模式: "*.py" 扫描所有
            if '*' in script_name:
                scripts_to_scan.extend(project_dir.glob(script_name))
            else:
                candidate = project_dir / script_name
                if candidate.exists():
                    scripts_to_scan.append(candidate)
                # 也搜索子目录
                else:
                    found = list(project_dir.glob(f'**/{script_name}'))
                    scripts_to_scan.extend(found)

        if not scripts_to_scan:
            return {
                "pass": True,
                "failures": [],
                "warnings": [f"未找到目标脚本: {target_scripts}"],
                "report": "无脚本可扫描 (脚本文件不存在)",
            }

        # 对每个脚本执行检查
        for script_path in scripts_to_scan:
            try:
                code = script_path.read_text(encoding='utf-8')
            except OSError as e:
                failures.append(f"无法读取 {script_path.name}: {e}")
                continue

            script_data = {
                "path": script_path,
                "code": code,
                "n_jobs_values": [],
                "nthread_values": [],
                "has_pickle_load": False,
                "has_joblib_load": False,
                "has_gc_collect": "gc.collect()" in code or "gc.collect" not in code,
                "has_smote": False,
                "thread_limits": {},
            }

            # 1. n_jobs / nthread 审计
            self._audit_n_jobs(code, script_path, script_data, failures)

            # 2. pickle.load 后 n_jobs 覆盖检查
            self._check_pickle_override(code, script_path, script_data, failures, warnings)

            # 3. 线程限制环境变量检查
            self._check_thread_limits(code, script_path, script_data, failures, warnings)

            # 4. 启动方式检查
            self._check_start_method(code, script_path, failures, warnings)

            # 5. SMOTE 检测
            if re.search(r'\bSMOTE\b', code):
                script_data["has_smote"] = True

            # 安全样板检查
            self._check_safety_boilerplate(code, script_path, failures)

            # GC 检查
            has_pickle = script_data.get("has_pickle_load") or script_data.get("has_joblib_load")
            if has_pickle or len(re.findall(r'(?:pickle|joblib)\.load', code)) >= 2:
                if 'gc.collect()' not in code and 'gc.collect' not in code:
                    warnings.append(
                        f"{script_path.name}: 检测到 pickle/joblib 加载但缺少 gc.collect() — "
                        f"多模型串行加载可能内存累积"
                    )

            all_scripts_data[script_path.name] = script_data

        # 5. 跨脚本安全配置一致性
        self._check_cross_script_consistency(all_scripts_data, failures, warnings)

        # 6. 内存峰值预估
        self._estimate_peak_memory(all_scripts_data, project_dir, failures, warnings)

        # 7. 数据真实性扫描 (2026-05-24)
        self._check_data_authenticity(all_scripts_data, failures, warnings)

        # 构建报告
        report_lines = [f"Preflight Safety Scan — {len(scripts_to_scan)} 脚本"]
        report_lines.append("=" * 60)

        if failures:
            report_lines.append(f"\n❌ FAILURES ({len(failures)}):")
            for f in failures:
                report_lines.append(f"  • {f}")

        if warnings:
            report_lines.append(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for w in warnings:
                report_lines.append(f"  • {w}")

        if not failures and not warnings:
            report_lines.append("\n✅ 所有检查通过 — SAFE to execute")

        return {
            "pass": len(failures) == 0,
            "failures": failures,
            "warnings": warnings,
            "report": "\n".join(report_lines),
        }

    # ================================================================
    # 1. n_jobs / nthread 审计
    # ================================================================

    def _audit_n_jobs(self, code: str, script_path: Path, script_data: dict,
                      failures: list):
        """扫描所有 n_jobs / nthread 赋值"""
        # n_jobs 赋值
        n_jobs_assignments = re.findall(
            r'(?:^|\s)n_jobs\s*[=:]\s*(\d+|None|-1)',
            code, re.MULTILINE
        )
        # nthread 赋值 (XGBoost/LightGBM)
        nthread_assignments = re.findall(
            r'(?:nthread|n_threads?|num_threads?)\s*[=:]\s*(\d+|None|-1)',
            code, re.MULTILINE
        )

        script_data["n_jobs_values"] = [int(v) if v.lstrip('-').isdigit() else v
                                         for v in n_jobs_assignments]
        script_data["nthread_values"] = [int(v) if v.lstrip('-').isdigit() else v
                                          for v in nthread_assignments]

        for val_str in n_jobs_assignments + nthread_assignments:
            if val_str == '-1':
                failures.append(
                    f"{script_path.name}: n_jobs=-1 (使用所有核心) — 绝对禁止"
                )
            elif val_str.isdigit() and int(val_str) > 4:
                failures.append(
                    f"{script_path.name}: n_jobs={val_str} > 4 上限"
                )

        # cross_val_score / cross_val_predict / cross_validate 未显式传 n_jobs
        cv_calls_no_njobs = []
        for call in re.finditer(
            r'(cross_val_score|cross_val_predict|cross_validate)\s*\((?:(?!n_jobs\s*=).)*?\)',
            code, re.DOTALL
        ):
            call_text = call.group(0)
            if 'n_jobs' not in call_text:
                cv_calls_no_njobs.append(call.group(1))

        if cv_calls_no_njobs:
            failures.append(
                f"{script_path.name}: {', '.join(cv_calls_no_njobs)} 调用未显式传 n_jobs — "
                f"默认值行为不确定, 可能导致并行爆炸"
            )

        # RandomizedSearchCV / GridSearchCV 未显式传 n_jobs
        search_calls = re.findall(
            r'(RandomizedSearchCV|GridSearchCV)\s*\((?:(?!n_jobs\s*=).)*?\)',
            code, re.DOTALL
        )
        for call_text in search_calls:
            if 'n_jobs' not in call_text:
                failures.append(
                    f"{script_path.name}: {call_text[:40]}... 未显式传 n_jobs"
                )

    # ================================================================
    # 2. pickle.load 后 n_jobs 覆盖检查
    # ================================================================

    def _check_pickle_override(self, code: str, script_path: Path,
                                script_data: dict, failures: list, warnings: list):
        """grep pickle.load/joblib.load 后续 8 行，检查是否覆盖 n_jobs"""
        load_pattern = r'(?:pickle|joblib)\.load\s*\([^)]+\)'
        load_matches = list(re.finditer(load_pattern, code))

        if not load_matches:
            return

        script_data["has_pickle_load"] = True

        for match in load_matches:
            # 取后续 8 行的内容
            post_load_start = match.end()
            post_load = code[post_load_start:post_load_start + 2000]
            lines_after = post_load.split('\n')[:8]
            post_block = '\n'.join(lines_after)

            # 检查是否覆盖了 n_jobs
            has_n_jobs_override = bool(re.search(
                r'(?:\.n_jobs\s*=|\.set_params\s*\(.*n_jobs)',
                post_block
            ))
            has_nthread_override = bool(re.search(
                r'(?:\.nthread\s*=|\.set_params\s*\(.*nthread|n_threads)',
                post_block
            ))

            if not has_n_jobs_override and not has_nthread_override:
                # 检查加载的是否是 sklearn/XGBoost/LightGBM 模型
                # (无法在静态扫描中100%确定，但如果有 pickle.load 且无覆盖即告警)
                failures.append(
                    f"{script_path.name}: pickle.load 后未覆盖 model.n_jobs=1 — "
                    f"训练时的 n_jobs 逃逸到推理时, 可能 CoW 内存爆炸"
                )
                break

    # ================================================================
    # 3. 线程限制环境变量检查
    # ================================================================

    def _check_thread_limits(self, code: str, script_path: Path,
                              script_data: dict, failures: list, warnings: list):
        """检查是否设置了线程限制环境变量 (支持 os.environ['VAR'] 和 VAR = 两种格式)"""
        for var in self.REQUIRED_THREAD_VARS:
            # 匹配格式: os.environ["VAR"] = "2" 或 os.environ['VAR'] = '2'
            environ_pattern = rf'os\.environ\[["\']\s*{var}\s*["\']\s*\]\s*=\s*["\'](\d+)["\']'
            # 匹配格式: VAR = "2" 或 VAR = '2'
            direct_pattern = rf'(?:^|\n)\s*{var}\s*=\s*["\'](\d+)["\']'

            environ_match = re.search(environ_pattern, code)
            direct_match = re.search(direct_pattern, code)

            match = environ_match or direct_match
            if match:
                val = int(match.group(1))
                script_data["thread_limits"][var] = val
                if val > 2:
                    warnings.append(
                        f"{script_path.name}: {var}={match.group(1)} > 2 — "
                        f"建议降为 2 避免 worker × threads 乘积效应"
                    )
            else:
                failures.append(
                    f"{script_path.name}: 缺少 {var} 线程限制 — "
                    f"未设此值 → worker × threads 爆炸风险 (n_jobs=N + OMP=M = N×M 线程)"
                )

    # ================================================================
    # 4. 启动方式检查
    # ================================================================

    def _check_start_method(self, code: str, script_path: Path,
                             failures: list, warnings: list):
        """Unix 平台缺少 JOBLIB_START_METHOD=forkserver → FAIL"""
        if platform.system() == "Windows":
            return  # Windows 默认 spawn 本身就是干净进程

        has_forkserver = bool(
            re.search(r'JOBLIB_START_METHOD\s*=\s*["\']forkserver["\']', code) or
            re.search(r'os\.environ\[["\']\s*JOBLIB_START_METHOD\s*["\']\s*\]\s*=\s*["\']forkserver["\']', code)
        )

        if not has_forkserver:
            failures.append(
                f"{script_path.name}: Unix 平台缺少 JOBLIB_START_METHOD=forkserver — "
                f"fork 会继承父进程内存, CoW 爆炸风险"
            )
        else:
            # 检查设置位置是否在 import numpy/pandas 之前
            forkserver_line = None
            first_import_line = None
            for i, line in enumerate(code.split('\n'), 1):
                if 'JOBLIB_START_METHOD' in line and 'forkserver' in line:
                    forkserver_line = i
                if first_import_line is None and re.match(
                    r'^\s*(?:import|from)\s+(?:numpy|pandas|sklearn|xgboost|lightgbm)',
                    line
                ):
                    first_import_line = i
                    break

            if forkserver_line and first_import_line and forkserver_line > first_import_line:
                warnings.append(
                    f"{script_path.name}: JOBLIB_START_METHOD 设置在 import numpy/pandas 之后 "
                    f"(line {forkserver_line} > line {first_import_line}) — "
                    f"应在所有 import 之前设置"
                )

    # ================================================================
    # 安全样板检查
    # ================================================================

    def _check_safety_boilerplate(self, code: str, script_path: Path,
                                   failures: list):
        """检查脚本是否包含必需的安全样板 (线程限制 + forkserver)"""
        missing = []
        for var_name, pat in self.SAFETY_BOILERPLATE_PATTERNS:
            if not re.search(pat, code):
                missing.append(var_name)
        if missing:
            failures.append(
                f"{script_path.name}: 缺少安全样板 — 未设置: {', '.join(missing[:3])}"
                + ("..." if len(missing) > 3 else "")
                + " (所有 ML 脚本必须在 import 前设置线程限制)"
            )

    # ================================================================
    # 5. 跨脚本安全配置一致性
    # ================================================================

    def _check_cross_script_consistency(self, all_data: dict,
                                         failures: list, warnings: list):
        """检查同项目脚本间的 N_JOBS 和 thread_limits 是否一致"""
        if len(all_data) < 2:
            return

        n_jobs_all = {}
        thread_limits_all = {}

        for name, data in all_data.items():
            vals = [v for v in data.get("n_jobs_values", []) if isinstance(v, int)]
            if vals:
                n_jobs_all[name] = max(vals)
            if data.get("thread_limits"):
                thread_limits_all[name] = data["thread_limits"]

        # N_JOBS 一致性
        if len(n_jobs_all) >= 2:
            unique_vals = set(n_jobs_all.values())
            if len(unique_vals) > 1:
                warnings.append(
                    f"跨脚本 N_JOBS 不一致: "
                    + ", ".join(f"{n}={v}" for n, v in n_jobs_all.items())
                )

        # thread_limits 一致性
        if len(thread_limits_all) >= 2:
            # 比较每个变量的值
            for var in self.REQUIRED_THREAD_VARS:
                var_vals = {}
                for name, limits in thread_limits_all.items():
                    if var in limits:
                        var_vals[name] = limits[var]
                if len(set(var_vals.values())) > 1:
                    warnings.append(
                        f"跨脚本 {var} 不一致: "
                        + ", ".join(f"{n}={v}" for n, v in var_vals.items())
                    )

        # 检查是否有脚本完全缺少安全样板
        for name, data in all_data.items():
            code = data.get("code", "")
            missing_patterns = []
            for var_name, pat_str in self.SAFETY_BOILERPLATE_PATTERNS:
                if not re.search(pat_str, code):
                    missing_patterns.append(var_name)
            if missing_patterns:
                failures.append(
                    f"{name}: 缺少安全样板 — 未设置: {', '.join(missing_patterns[:3])}"
                    + ("..." if len(missing_patterns) > 3 else "")
                )

    # ================================================================
    # 6. 内存峰值预估
    # ================================================================

    def _estimate_peak_memory(self, all_data: dict, project_dir: Path,
                               failures: list, warnings: list):
        """预估内存峰值并检查是否超过可用内存的 70%"""
        try:
            import psutil
            available_gb = psutil.virtual_memory().available / (1024 ** 3)
        except ImportError:
            warnings.append("无法获取可用内存 (psutil 未安装), 跳过内存预估")
            return
        except Exception as e:
            warnings.append(f"无法获取可用内存: {e}, 跳过内存预估")
            return

        # 估算数据大小
        data_size_mb = self._estimate_data_size(project_dir)

        # 取所有脚本中最大的 n_jobs 值
        n_jobs_max = 2  # 默认
        for data in all_data.values():
            for v in data.get("n_jobs_values", []):
                if isinstance(v, int) and v > n_jobs_max:
                    n_jobs_max = v
            for v in data.get("nthread_values", []):
                if isinstance(v, int) and v > n_jobs_max:
                    n_jobs_max = v

        # SMOTE 系数
        has_smote = any(d.get("has_smote") for d in all_data.values())
        smote_factor = 1.5 if has_smote else 1.0

        # 峰值预估 = 数据内存 × n_jobs × SMOTE系数 × 20(模型展开) + 4GB(基础)
        peak_est_gb = data_size_mb / 1024 * n_jobs_max * smote_factor * 20 + 4

        if peak_est_gb > available_gb * 0.7:
            failures.append(
                f"内存峰值预估 {peak_est_gb:.1f} GB > 可用 {available_gb:.1f} GB × 70% = {available_gb*0.7:.1f} GB — "
                f"建议: 降 n_jobs (当前最大={n_jobs_max}) 或关闭其他应用"
            )

    def _estimate_data_size(self, project_dir: Path) -> float:
        """估算项目数据目录的 Parquet/CSV 文件总大小 (MB)"""
        total_size = 0.0
        data_dir = project_dir / "data"
        if not data_dir.exists():
            data_dir = project_dir

        for pattern in ['*.parquet', '*.csv', '*.dta', '*.sas7bdat', '*.pkl']:
            for f in data_dir.glob(pattern):
                try:
                    total_size += f.stat().st_size / (1024 ** 2)
                except OSError:
                    pass
            # 也搜索子目录
            for f in data_dir.glob(f'**/{pattern}'):
                try:
                    total_size += f.stat().st_size / (1024 ** 2)
                except OSError:
                    pass

        return max(total_size, 10.0)  # 最少假设 10MB

    # ================================================================
    # 7. 数据真实性扫描 (2026-05-24)
    # ================================================================
    DATA_AUTHENTICITY_TARGETS = [
        "generate_tables.py",
        "generate_figures.py",
    ]

    def _check_data_authenticity(self, all_data: dict, failures: list, warnings: list):
        """扫描 Phase 6 脚本是否存在 np.random 数据注入风险。

        跨事业部通用: 检测 np.random 赋值给分层相关变量名
        (efi/frail/strata/risk_score/grade/stage 等)。
        """
        import re

        for script_name, script_data in all_data.items():
            if script_name not in self.DATA_AUTHENTICITY_TARGETS:
                continue

            code = script_data["code"]
            lines = code.split("\n")

            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue

                # np.random assigned to variable with stratification keywords
                m = re.match(
                    r'(\w+)\s*=\s*np\.random\.(?!seed\b|RandomState\b)(\w+)\(',
                    stripped
                )
                if m:
                    var_name = m.group(1).lower()
                    func = m.group(2)
                    data_kw = r'(efi|frail|strata|stratum|group_label|risk_score|grade|stage|label|class|cluster|synthetic)'
                    if re.search(data_kw, var_name):
                        ctx = "\n".join(lines[max(0, i - 3):min(len(lines), i + 8)])
                        if re.search(r'(Table|table|stratif|group.*by|patients?|cohort)', ctx):
                            failures.append(
                                f"{script_name}:L{i} np.random.{func}() -> '{var_name}' "
                                f"used in stratification context — replace with real data from baseline"
                            )

                # simulate/synthetic keyword
                if re.search(r'(simulate|synthetic).*?(data|score|strata|cohort|patient)',
                             stripped, re.IGNORECASE):
                    failures.append(
                        f"{script_name}:L{i} simulated/synthetic data keyword: {stripped[:100]}"
                    )

            # Check data source declaration
            if script_name == "generate_tables.py":
                has_pkl = bool(re.search(r'(features_cache\.pkl|cache\[.?X.?\])', code))
                if not has_pkl:
                    warnings.append(
                        f"{script_name}: no reference to features_cache.pkl — "
                        f"stratification data source must be declared"
                    )

            if script_name == "generate_figures.py":
                has_cv = bool(re.search(r'(cv_results\.json|CV_RESULTS)', code))
                if not has_cv:
                    warnings.append(
                        f"{script_name}: no reference to cv_results.json — "
                        f"figures must read from baseline"
                    )


# ================================================================
# 便捷函数: 供 run_preflight.py 使用
# ================================================================

def preflight_safety_scan(project_dir: str, target_scripts: list[str] = None) -> dict:
    """
    便捷函数，与 SKILL.md 中的伪代码签名对齐。

    Args:
        project_dir: 项目目录路径
        target_scripts: 要扫描的脚本列表，默认扫描所有 .py 文件

    Returns:
        {"pass": bool, "failures": [str], "warnings": [str], "report": str}
    """
    scanner = PreflightScanner()
    if target_scripts is None:
        target_scripts = ["*.py"]
    return scanner.scan(Path(project_dir), target_scripts)

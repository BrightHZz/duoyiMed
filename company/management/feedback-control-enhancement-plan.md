# 模块一：闭环反馈控制系统 — 详细改造方案

> 对应钱学森《工程控制论》"闭环反馈控制"理论
>
> 核心命题：没有反馈的系统是不稳定的。反馈不是「出了问题才修」，而是让系统在持续扰动下保持预定品质。

---

## 目录

1. [现状分析与差距识别](#一现状分析与差距识别)
2. [子模块A：趋势Gate (Δ-Gate)](#二子模块a趋势gate)
3. [子模块B：跨Phase反馈环B自动触发](#三子模块b跨phase反馈环b自动触发)
4. [子模块C：工作流循环改造](#四子模块c工作流循环改造)
5. [子模块D：状态模型扩展](#五子模块d状态模型扩展)
6. [集成测试方案](#六集成测试方案)
7. [需要修改的文件清单](#七需要修改的文件清单)

---

## 一、现状分析与差距识别

### 1.1 当前反馈机制

```
Phase N 执行 → Gate N 检查 → [PASS/COND_PASS] → Phase N+1
                            → [FAIL]          → Phase N 返工 (最多3次)

反馈类型:
✅ A环 (阶段内): Gate FAIL → 同Phase返工            — 已实现
🟡 B环 (阶段间): 下游发现上游问题 → 手动触发返工     — 部分实现 (有 rework_history 记录,
                                                              但缺少自动检测和触发)
❌ C环 (趋势):    性能指标持续下滑 → 预警            — 未实现
```

### 1.2 核心差距

| 差距 | 当前行为 | 目标行为 |
|------|---------|---------|
| **趋势盲区** | AUC=0.72 通过，AUC=0.71 也通过，直到 AUC=0.69 才告警 | AUC 连续下降趋势被监控，ΔAUC < -0.05 时提前预警 |
| **下游被动** | ML 发现特征不可用 → 只能写在输出里 → 编排器不会自动回退 | ML 输出中的"数据质量问题"被自动检测 → 触发 Phase 1 重开 |
| **跨Phase单向** | 反馈环B只记录了 rework_history，未真正回退 phase_index | 检测到上游问题 → 暂停当前Phase → phase_index 回退 → 上游重跑 |
| **Gate无记忆** | 每次 Gate 检查是独立的，不对比历史 | 趋势Gate对比当前值与上次Gate值，检测恶化趋势 |

### 1.3 涉及文件

| 文件 | 当前状态 | 改造内容 |
|------|---------|---------|
| `engine/core/gate_checks.py` | 已有6个auto check函数 + GATE_DEFINITIONS | 新增趋势检查函数 + 更新Gate定义 |
| `engine/core/orchestrator_graph.py` | 已有 `_check_gate()` + `_run_project_workflow()` | 新增 `_detect_upstream_issues()` + 修改workflow循环 |
| `engine/core/state.py` | 已有 `GateResult`, `ReworkRecord`, `RunLog` | 新增 `TrendBaseline` + `ReworkRecord` 字段扩展 |

---

## 二、子模块A：趋势Gate（Δ-Gate）

### 2.1 理论依据

钱学森指出控制论的关键在于应对**不确定性**。在系统运行中，性能指标的**变化方向**比**绝对值**更早暴露问题。这是一个典型的微分控制（D-control）：PID 控制器中的 D 项，对变化率做出响应。

### 2.2 新增趋势检查函数

在 `engine/core/gate_checks.py` 中新增以下函数。

#### 2.2.1 AUC 趋势检查

```python
def check_auc_trend(outputs: dict, orch) -> tuple:
    """ΔAUC 趋势检查 — 监控模型性能的恶化趋势。
    
    对比当前 AUC 与本项目历史上最后一次 Gate 通过的 AUC 值。
    - 下降 < 0.05: 正常波动
    - 下降 0.05-0.10: 预警 (通过但告警)
    - 下降 > 0.10: 触发审查
    
    首次执行时跳过 (无历史基准)。
    """
    current_auc = _extract_auc_value(outputs)
    if current_auc is None:
        return True, "跳过 (未检测到 AUC 值, 可能为非分类任务)"

    # 从编排器获取历史 Gate 结果中的 AUC
    prev_auc = _get_previous_gate_auc(orch)
    if prev_auc is None:
        # 保存当前 AUC 作为后续趋势检查的基准
        _save_auc_baseline(orch, current_auc)
        return True, f"首次执行, AUC={current_auc:.3f} 已保存为趋势基准"

    delta = current_auc - prev_auc

    if delta < -0.10:
        return False, (
            f"ΔAUC={delta:.3f} (从 {prev_auc:.3f} 降至 {current_auc:.3f}), "
            f"下降超过 0.10, 需审查特征工程、标签定义或过拟合"
        )
    elif delta < -0.05:
        # 通过但附带预警 — 让 PI 知晓性能在下降
        return True, (
            f"⚠️ ΔAUC={delta:.3f} (从 {prev_auc:.3f} 降至 {current_auc:.3f}), "
            f"下降趋势需关注, 建议 PI 审查"
        )
    else:
        direction = "提升" if delta > 0 else "稳定"
        return True, f"ΔAUC={delta:+.3f} ({direction})"


def _extract_auc_value(outputs: dict) -> Optional[float]:
    """从 ml-engineer 输出中提取 AUC 值"""
    import re
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            patterns = [
                r'(?:auc.?roc|AUC|auc)[^0-9]*0?\.(\d+)',
                r'c.?statistic[^0-9]*0?\.(\d+)',
            ]
            for pat in patterns:
                matches = re.findall(pat, output)
                if matches:
                    return float(f"0.{matches[0]}")
    return None


def _get_previous_gate_auc(orch) -> Optional[float]:
    """从编排器的项目状态中获取上次 Gate 通过的 AUC 值"""
    # 从项目的 gate_results 中查找 execution 阶段的 pass 记录
    if hasattr(orch, '_trend_baselines') and 'auc' in orch._trend_baselines:
        return orch._trend_baselines['auc']
    return None


def _save_auc_baseline(orch, auc_value: float):
    """保存 AUC 基准值供后续趋势检查"""
    if not hasattr(orch, '_trend_baselines'):
        orch._trend_baselines = {}
    orch._trend_baselines['auc'] = auc_value
```

#### 2.2.2 校准度趋势检查

```python
def check_calibration_trend(outputs: dict, orch) -> tuple:
    """校准度趋势检查 — 监控模型校准度的恶化。
    
    检测 calibration slope 是否偏离 [0.9, 1.1] 区间。
    首次偏离时预警，持续偏离时 FAIL。
    """
    slope = _extract_calibration_slope(outputs)
    if slope is None:
        return True, "跳过 (未检测到 calibration slope)"

    if 0.9 <= slope <= 1.1:
        _save_calibration_baseline(orch, slope, "ok")
        return True, f"Calibration slope={slope:.3f} 在 [0.9, 1.1] 区间内"

    # 偏离区间 — 检查是否持续
    prev_state = _get_calibration_state(orch)
    if prev_state and prev_state.get("state") == "warning":
        return False, (
            f"Calibration slope={slope:.3f} 持续偏离 [0.9, 1.1], "
            f"上次 slope={prev_state['value']:.3f}, 模型校准度存在问题"
        )

    _save_calibration_baseline(orch, slope, "warning")
    return True, (
        f"⚠️ Calibration slope={slope:.3f} 首次偏离 [0.9, 1.1], "
        f"建议检查 Platt scaling 或 isotonic regression 校准"
    )


def _extract_calibration_slope(outputs: dict) -> Optional[float]:
    """从 ml-engineer 输出中提取 calibration slope"""
    import re
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            match = re.search(
                r'calibration.?slope[^0-9]*(\d+\.?\d*)', output, re.IGNORECASE
            )
            if match:
                return float(match.group(1))
    return None


def _save_calibration_baseline(orch, slope: float, state: str):
    if not hasattr(orch, '_trend_baselines'):
        orch._trend_baselines = {}
    orch._trend_baselines['calibration'] = {"value": slope, "state": state}


def _get_calibration_state(orch) -> Optional[dict]:
    if hasattr(orch, '_trend_baselines'):
        return orch._trend_baselines.get('calibration')
    return None
```

#### 2.2.3 特征稳定性检查 (跨Phase)

```python
def check_feature_stability(outputs: dict, orch) -> tuple:
    """特征稳定性检查 — 监控跨Phase的特征使用一致性。
    
    对比 Phase 3 (内部验证) 与 Phase 4 (外部验证) 使用的特征集。
    如果外部验证使用的特征与内部验证差异过大 (>30% 不同),
    可能说明特征选择过拟合或外部数据特征不可用。
    """
    # 仅在 external_validation Phase 执行
    internal_features = _get_features_from_phase(orch, "execution")
    external_features = _extract_features_from_output(outputs)

    if not internal_features or not external_features:
        return True, "跳过 (特征列表不可用)"

    internal_set = set(internal_features)
    external_set = set(external_features)

    if not internal_set:
        return True, "跳过 (内部验证特征列表为空)"

    # 计算特征重叠率
    overlap = internal_set & external_set
    overlap_rate = len(overlap) / len(internal_set)

    # 新特征 (外部有但内部没有)
    new_features = external_set - internal_set
    # 缺失特征 (内部有但外部没有)
    missing_features = internal_set - external_set

    if overlap_rate < 0.70:
        return False, (
            f"特征重叠率仅 {overlap_rate:.0%} ({len(overlap)}/{len(internal_set)}), "
            f"缺失 {len(missing_features)} 个: {list(missing_features)[:5]}, "
            f"新增 {len(new_features)} 个: {list(new_features)[:5]}"
        )
    elif overlap_rate < 0.85:
        return True, (
            f"⚠️ 特征重叠率 {overlap_rate:.0%} 偏低, "
            f"缺失 {len(missing_features)} 个特征, 请确认外部数据可用性"
        )

    return True, f"特征重叠率 {overlap_rate:.0%} ({len(overlap)}/{len(internal_set)})"


def _get_features_from_phase(orch, phase_id: str) -> Optional[list]:
    """从编排器获取某个Phase产出的特征列表"""
    if hasattr(orch, '_phase_features'):
        return orch._phase_features.get(phase_id)
    return None


def _extract_features_from_output(outputs: dict) -> Optional[list]:
    """从 ml-engineer 输出中提取使用的特征名列表"""
    import re
    for agent_id, output in outputs.items():
        if "ml-engineer" in agent_id.lower():
            # 匹配常见的特征列表格式: "Feature: xxx", "特征: xxx", "- xxx", 表格
            features = set()
            for match in re.finditer(
                r'(?:特征|Feature|Variable)[:：]\s*(\w+)', output, re.IGNORECASE
            ):
                features.add(match.group(1))
            if features:
                return list(features)
    return None
```

### 2.3 更新 GATE_DEFINITIONS

在 `gate_checks.py` 的 `GATE_DEFINITIONS` 中，为 `execution` 和 `external_validation` 增加趋势检查：

```python
GATE_DEFINITIONS = {
    # ... problem_definition 不变 ...
    # ... design 不变 ...

    "execution": {
        "auto_checks": {
            "auc_threshold": check_auc_threshold,      # 已有: AUC >= 0.70
            "auc_trend": check_auc_trend,              # 🆕: ΔAUC 趋势监控
            "baseline_included": check_baseline_included,
            "n_jobs_safe": check_n_jobs_safe,
            "calibration_trend": check_calibration_trend,  # 🆕: 校准度趋势
        },
        "llm_checks": [
            # ... 不变 ...
        ],
    },
    "external_validation": {
        "auto_checks": {
            "n_jobs_safe": check_n_jobs_safe,
            "feature_stability": check_feature_stability,  # 🆕: 特征稳定性
            "auc_trend": check_auc_trend,                  # 🆕: 外部验证也监控AUC趋势
        },
        "llm_checks": [
            # ... 不变 ...
        ],
    },

    # ... review 和 writing 不变 ...
}
```

---

## 三、子模块B：跨Phase反馈环B自动触发

### 3.1 设计原理

当前问题是：下游 Agent 发现上游问题后，只能将问题写在输出文本中，编排器不会自动解析并触发回退。反馈环B需要实现**自动检测→自动触发→自动回退**。

### 3.2 新增方法：`_detect_upstream_issues()`

在 `orchestrator_graph.py` 的 `ResearchOrchestrator` 类中新增：

```python
# ================================================================
# 跨 Phase 反馈环 B — 自动检测下游发现的上游问题
# ================================================================

# 反馈触发规则: 当下游输出中包含这些信号时, 自动触发上游 Phase 重开
FEEDBACK_B_TRIGGERS = {
    "execution": {
        # ML 阶段可能发现 Phase 1 的问题
        "problem_definition": {
            "signals": [
                "特征不可用", "feature not available", "变量不存在",
                "数据质量不足", "data quality insufficient", "缺失率过高",
                "样本量不足", "insufficient sample", "标签泄露",
                "label leakage", "表型定义模糊", "phenotype unclear",
                "变量编码错误", "encoding error",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "ML 阶段检测到数据/表型问题, 需返回 Phase 1 修正",
        },
        "design": {
            "signals": [
                "模型不适用", "model not suitable", "方法选择错误",
                "SAP 与建模方案不一致", "统计方法不匹配",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "ML 阶段检测到方案设计问题, 需返回 Phase 2 修正",
        },
    },
    "external_validation": {
        "execution": {
            "signals": [],  # 不依赖文本信号, 改为数值规则 (见下方)
            "severity": "critical",
            "action": "reopen_gate",
            "message": "外部验证 AUC 相比内部验证下降 > 0.15, 疑似过拟合, 需返回 Phase 3 审查",
            "numeric_rule": {
                "metric": "auc",
                "compare_phase": "execution",
                "threshold": -0.15,  # 下降超过 0.15 触发
            },
        },
        "problem_definition": {
            "signals": [
                "外部数据不可用", "external data unavailable",
                "外部人群不匹配", "population mismatch",
            ],
            "severity": "high",
            "action": "notify_pi",  # 不自动回退, 通知PI决策
            "message": "外部验证阶段发现数据源问题, 建议 PI 评估",
        },
    },
    "review": {
        "problem_definition": {
            "signals": [
                "表型定义不可操作化", "临床定义有问题",
                "effect direction mismatch", "效应方向矛盾",
                "预测因子不合理的临床解释",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "审查阶段发现临床定义问题, 需返回 Phase 1 修正表型定义",
        },
        "execution": {
            "signals": [
                "SHAP 方向与临床知识矛盾", "特征重要性异常",
                "模型行为不合理", "校准度不可接受",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "审查阶段发现模型问题, 需返回 Phase 3 重新建模",
        },
    },
    "writing": {
        "execution": {
            "signals": [
                "[数据待确认]", "[数据矛盾]", "[数值不一致]",
                "[结果缺失]", "data missing",
            ],
            "severity": "critical",
            "action": "reopen_gate",
            "message": "写作阶段发现数据缺失或矛盾, 需返回上游确认",
        },
        "problem_definition": {
            "signals": [
                "缺少关键的临床背景", "研究意义不明确",
            ],
            "severity": "high",
            "action": "notify_pi",
            "message": "写作阶段发现研究定义不够清晰, 建议 PI 补充",
        },
    },
}


def _detect_upstream_issues(
    self, phase_id: str, outputs: dict, project_id: str
) -> list[dict]:
    """
    检测当前 Phase 输出中暗示的上游问题, 生成反馈触发列表。

    扫描逻辑:
    1. 文本信号: 检查 Agent 输出中是否包含上游问题的关键词
    2. 数值规则: 检查跨 Phase 的数值指标是否触发阈值 (如 AUC 下降)
    3. 汇总所有触发项, 按 severity 排序

    Returns:
        [{from_phase, to_phase, reason, severity, action, detected_by}]
    """
    triggers = FEEDBACK_B_TRIGGERS.get(phase_id, {})
    if not triggers:
        return []

    issues = []

    for target_phase, rule in triggers.items():
        detected = False
        detection_detail = ""

        # 方式1: 文本信号检测
        signals = rule.get("signals", [])
        if signals:
            for agent_id, output in outputs.items():
                output_lower = output.lower()
                for signal in signals:
                    if signal.lower() in output_lower:
                        detected = True
                        detection_detail = (
                            f"{agent_id} 输出中包含信号: '{signal}'"
                        )
                        break
                if detected:
                    break

        # 方式2: 数值规则检测
        numeric_rule = rule.get("numeric_rule")
        if not detected and numeric_rule:
            detected, detection_detail = self._check_numeric_trigger(
                phase_id, target_phase, numeric_rule
            )

        if detected:
            issues.append({
                "from_phase": phase_id,
                "to_phase": target_phase,
                "reason": f"{rule['message']} — {detection_detail}",
                "severity": rule["severity"],
                "action": rule["action"],
                "timestamp": datetime.now().isoformat(),
                "detected_by": "auto",  # 标记为自动检测
                "rework_count": 0,       # 将在 workflow 循环中更新
            })

    # 按 severity 排序: critical > high > normal
    severity_order = {"critical": 0, "high": 1, "normal": 2}
    issues.sort(key=lambda x: severity_order.get(x["severity"], 3))

    if issues:
        print(f"  🔄 反馈环B: 检测到 {len(issues)} 个上游问题")
        for issue in issues:
            icon = "🚨" if issue["severity"] == "critical" else "⚠️"
            print(f"    {icon} {issue['to_phase']}: {issue['reason'][:120]}")

    return issues


def _check_numeric_trigger(
    self, from_phase: str, target_phase: str, rule: dict
) -> tuple:
    """
    检查跨 Phase 的数值指标是否触发阈值。

    当前支持的规则:
    - AUC 下降: 外部验证 AUC 相比内部验证下降超过 threshold
    """
    metric = rule.get("metric")
    compare_phase = rule.get("compare_phase")
    threshold = rule.get("threshold", 0)

    if metric == "auc":
        current_auc = self._get_auc_from_outputs(from_phase)
        compare_auc = self._get_auc_from_outputs(compare_phase)

        if current_auc is None or compare_auc is None:
            return False, "无法获取 AUC 值进行对比"

        delta = current_auc - compare_auc
        if delta < threshold:
            return True, (
                f"AUC 从 {compare_phase}({compare_auc:.3f}) "
                f"降至 {from_phase}({current_auc:.3f}), "
                f"Δ={delta:.3f} < 阈值 {threshold:.3f}"
            )

    return False, ""


def _get_auc_from_outputs(self, phase_id: str) -> Optional[float]:
    """从已缓存的 Phase 输出中提取 AUC 值"""
    # 从 all_outputs 或 gate_results 中获取
    if hasattr(self, '_cached_aucs') and phase_id in self._cached_aucs:
        return self._cached_aucs[phase_id]
    return None
```

### 3.3 缓存 AUC 值

在 `_check_gate()` 方法执行完成后, 自动缓存AUC值供后续Phase的趋势检查使用:

```python
def _check_gate(self, phase_id: str, outputs: dict, project_id: str) -> dict:
    # ... 现有检查逻辑 ...

    # 🆕 缓存关键指标供趋势检查和跨Phase对比
    auc_value = _extract_auc_value(outputs)
    if auc_value is not None:
        if not hasattr(self, '_cached_aucs'):
            self._cached_aucs = {}
        self._cached_aucs[phase_id] = auc_value

    # 🆕 缓存特征列表
    features = _extract_features_from_output(outputs)
    if features:
        if not hasattr(self, '_phase_features'):
            self._phase_features = {}
        self._phase_features[phase_id] = features

    return result  # 现有返回值
```

---

## 四、子模块C：工作流循环改造

### 4.1 当前循环逻辑

```python
# 当前: _run_project_workflow() 中的主循环
phase_index = 0
while phase_index < len(phases_to_run):
    phase_id = phases_to_run[phase_index]
    # ... 执行 Phase ...
    # Gate 检查
    if status == "pass":
        phase_index += 1    # 前进
    elif status == "fail":
        # phase_index 不变 → 返工同一 Phase
```

### 4.2 改造后循环逻辑

```python
# 改造后: 主循环中增加反馈环B的检测和处理

phase_index = 0
# 🆕 追踪每个 Phase 的返工次数 (跨Phase反馈也计入)
phase_rework_counts = {p: 0 for p in phases_to_run}
# 🆕 标记被跨Phase反馈无效化的下游 Phase
invalidated_phases = set()

while phase_index < len(phases_to_run):
    phase_id = phases_to_run[phase_index]
    phase_def = PROJECT_PHASES.get(phase_id, {})
    deps = phase_def.get("depends_on", [])

    # 🆕 检查当前 Phase 是否被上游反馈无效化
    if phase_id in invalidated_phases:
        print(f"  🔄 Phase {phase_id} 已被上游反馈无效化, 重新执行")
        invalidated_phases.discard(phase_id)
        # 清除该 Phase 之前的输出, 强制重新执行
        if phase_id in all_outputs:
            del all_outputs[phase_id]

    # 检查依赖是否满足
    deps_met = all(dep in all_outputs for dep in deps)
    if not deps_met:
        missing = [d for d in deps if d not in all_outputs]
        print(f"[Orchestrator] 阶段 {phase_id} 依赖未满足: {missing}")
        # 🆕 依赖不满足时, 回退到第一个缺失依赖
        first_missing_idx = min(
            phases_to_run.index(d) for d in missing if d in phases_to_run
        )
        phase_index = first_missing_idx
        continue

    # ... Phase 0 特殊处理 (不变) ...

    # ... 执行 Phase (不变) ...

    # Gate 检查
    gate_result = self._check_gate(phase_id, phase_result, project_id)
    gate_results[phase_id] = gate_result

    # 🆕 反馈环B: 检测上游问题
    upstream_issues = self._detect_upstream_issues(
        phase_id, phase_result, project_id
    )

    # 🆕 处理跨Phase反馈
    cross_phase_rework_triggered = False
    for issue in upstream_issues:
        target_phase = issue["to_phase"]

        if issue["action"] == "reopen_gate":
            # Critical: 暂停当前, 回退到目标 Phase
            print(f"  🔄 反馈环B触发: {issue['reason']}")

            # 记录返工
            rework_record = {
                "from_phase": phase_id,
                "to_phase": target_phase,
                "reason": issue["reason"],
                "timestamp": datetime.now().isoformat(),
                "rework_count": phase_rework_counts[target_phase] + 1,
                "auto_detected": True,
                "severity": issue["severity"],
            }
            rework_history.append(rework_record)

            # 回退 phase_index 到目标 Phase
            target_index = phases_to_run.index(target_phase)
            phase_index = target_index

            # 无效化目标 Phase 之后的所有下游 Phase
            for i in range(target_index + 1, len(phases_to_run)):
                invalidated_phases.add(phases_to_run[i])

            # 清除目标 Phase 的 Gate 结果 (强制重新 Gate)
            if target_phase in gate_results:
                del gate_results[target_phase]
            if target_phase in all_outputs:
                del all_outputs[target_phase]

            cross_phase_rework_triggered = True
            phase_rework_counts[target_phase] += 1

            # 检查是否超过最大返工次数
            if phase_rework_counts[target_phase] >= 3:
                print(f"  🚨 Phase {target_phase} 返工 {phase_rework_counts[target_phase]} 次, "
                      f"升级到首席科学家")
                self._escalate_to_chief_scientist(
                    phase_id=target_phase,
                    reason=f"跨Phase反馈触发 {phase_rework_counts[target_phase]} 次返工",
                    issues=upstream_issues,
                )

            break  # 一次只处理一个最严重的跨Phase反馈

        elif issue["action"] == "notify_pi":
            # High: 通知PI但不自动回退, 记录到 rework_history 中
            print(f"  ⚠️ 反馈环B通知PI: {issue['reason']}")
            rework_history.append({
                "from_phase": phase_id,
                "to_phase": target_phase,
                "reason": issue["reason"],
                "timestamp": datetime.now().isoformat(),
                "rework_count": 0,
                "auto_detected": True,
                "severity": issue["severity"],
            })

    if cross_phase_rework_triggered:
        continue  # 跳过正常的 Gate 判断, 直接开始回退 Phase 的执行

    # 正常的 Gate 判断 (同Phase返工)
    status = gate_result.get("status", "fail")
    rework_cnt = gate_result.get("rework_count", 0)
    max_rework = gate_result.get("max_rework", 3)

    if status == "pass":
        # 🆕 Gate通过时, 对跨Phase反馈检测到的同Phase信号做静默告警
        print(f"  ✅ Gate {phase_id}: PASS → 进入下一阶段")
        phase_index += 1

    elif status == "conditional_pass":
        conditions = gate_result.get("conditions", [])
        print(f"  ⚠️  Gate {phase_id}: COND_PASS (附 {len(conditions)} 条件) → 进入下一阶段")
        all_outputs[phase_id]["_gate_conditions"] = conditions
        phase_index += 1

    elif status == "fail":
        if rework_cnt >= max_rework:
            print(f"  ❌ Gate {phase_id}: FAIL × {rework_cnt} (超过最大返工 {max_rework} 次)")
            print(f"  🚨 升级到首席科学家进行裁决")
            rework_history.append({
                "from_phase": phase_id, "to_phase": phase_id,
                "reason": f"Gate检查连续失败 {rework_cnt+1} 次",
                "timestamp": datetime.now().isoformat(),
                "rework_count": rework_cnt,
                "auto_detected": False,
                "severity": "critical",
            })
            self._escalate_to_chief_scientist(
                phase_id=phase_id,
                reason=f"Gate 连续失败 {rework_cnt+1} 次",
                gate_result=gate_result,
            )
            break
        else:
            fail_items = [c for c in gate_result.get("checks", [])
                          if c.get("result") == "fail"]
            reasons = [f"{c['check_id']}: {c['detail']}" for c in fail_items]
            print(f"  ❌ Gate {phase_id}: FAIL (返工 {rework_cnt+1}/{max_rework})")
            print(f"     原因: {reasons}")
            rework_history.append({
                "from_phase": phase_id, "to_phase": phase_id,
                "reason": str(reasons),
                "timestamp": datetime.now().isoformat(),
                "rework_count": rework_cnt + 1,
                "auto_detected": False,
                "severity": "normal",
            })
            # phase_index 不变 → 重新执行本 Phase
```

### 4.3 新增：首席科学家升级方法

```python
def _escalate_to_chief_scientist(
    self, phase_id: str, reason: str,
    gate_result: dict = None, issues: list = None,
):
    """
    当 Gate 连续失败或跨Phase返工超过上限时,
    调用首席科学家 Agent 做最终裁决。

    首席科学家的裁决可以是:
    - 强制通过 (overrule gate): 认为当前产出可接受
    - 更换策略 (change strategy): 改变建模方法或数据源
    - 放弃项目 (abandon): 认为在当前约束下不可行
    """
    print(f"\n{'='*60}")
    print(f"[首席科学家] 介入裁决 — Phase {phase_id}")
    print(f"{'='*60}")

    prompt_parts = [
        f"## 首席科学家紧急裁决",
        f"",
        f"**触发原因**: {reason}",
        f"**Phase**: {phase_id}",
        f"**事业部**: {self.active_division}",
        f"",
    ]

    if gate_result:
        prompt_parts.append("### Gate 检查结果")
        for c in gate_result.get("checks", []):
            if c.get("result") == "fail":
                prompt_parts.append(f"- ❌ {c['check_id']}: {c['detail']}")

    if issues:
        prompt_parts.append("### 跨Phase反馈问题")
        for issue in issues:
            prompt_parts.append(
                f"- [{issue['severity']}] {issue['from_phase']} → "
                f"{issue['to_phase']}: {issue['reason']}"
            )

    prompt_parts.append("")
    prompt_parts.append("请作出裁决:")
    prompt_parts.append("1. [强制通过] — 当前产出可接受, 允许继续")
    prompt_parts.append("2. [更换策略] — 改变方法或数据源, 提供具体建议")
    prompt_parts.append("3. [放弃项目] — 当前约束下不可行, 说明原因")

    chief_prompt = "\n".join(prompt_parts)
    chief_result = self._call_agent(
        agent_id="chief-scientist",
        task_input=chief_prompt,
        phase_id=f"{phase_id}_escalation",
        project_id=getattr(self, '_current_project_id', ''),
    )
    print(f"[首席科学家] 裁决: {chief_result[:200]}...")
    return chief_result
```

---

## 五、子模块D：状态模型扩展

### 5.1 state.py 改动

```python
# engine/core/state.py 新增

class TrendBaseline(TypedDict):
    """趋势监控的基准值 — 用于 Δ-Gate"""
    metric: str              # "auc" | "calibration_slope" | "feature_overlap"
    phase_id: str            # 采集自哪个 Phase
    value: float             # 基准值
    state: str               # "ok" | "warning" (预警状态)
    timestamp: str           # 采集时间


class CrossPhaseTrigger(TypedDict):
    """跨Phase反馈触发记录"""
    from_phase: str          # 发现问题的 Phase
    to_phase: str            # 需要回退到的 Phase
    reason: str              # 触发原因
    severity: str            # "critical" | "high" | "normal"
    action: str              # "reopen_gate" | "notify_pi"
    detected_by: str         # "auto" | "manual"
    timestamp: str


# ReworkRecord 扩展 (在现有基础上新增字段)
# 现有 ReworkRecord 字段:
#   from_phase: str
#   to_phase: str
#   reason: str
#   timestamp: str
#   rework_count: int
# 新增字段:
#   auto_detected: bool      # 🆕 是否由反馈环B自动检测
#   severity: str            # 🆕 critical / high / normal
```

### 5.2 orchestrator_graph.py 中 ResearchOrchestrator 新增属性

```python
class ResearchOrchestrator:
    def __init__(self, config=None):
        # ... 现有初始化 ...

        # 🆕 趋势监控缓存 (跨 Gate 调用的状态)
        self._trend_baselines: dict = {}    # {metric: value/state}
        self._cached_aucs: dict = {}        # {phase_id: auc_value}
        self._phase_features: dict = {}     # {phase_id: [feature_names]}
        self._current_project_id: str = ""  # 当前项目ID (用于升级)
```

---

## 六、集成测试方案

### 6.1 测试用例

#### TC-1: 趋势Gate — AUC正常波动

```
前置: 无历史 AUC 基准
操作: Phase 3 输出 AUC=0.82
期望: gate_checks.check_auc_trend → (True, "首次执行, AUC=0.820 已保存为趋势基准")
      _cached_aucs["execution"] = 0.82
```

#### TC-2: 趋势Gate — AUC轻微下降 (预警)

```
前置: _cached_aucs["execution"] = 0.82 (来自上次Gate)
操作: Phase 3 返工后输出 AUC=0.77 (Δ = -0.05)
期望: gate_checks.check_auc_trend → (True, "⚠️ ΔAUC=-0.050 ... 下降趋势需关注")
      Gate 整体 PASS 但 check 的 detail 包含预警信息
```

#### TC-3: 趋势Gate — AUC严重下降 (FAIL)

```
前置: _cached_aucs["execution"] = 0.82
操作: Phase 3 返工后输出 AUC=0.70 (Δ = -0.12)
期望: gate_checks.check_auc_trend → (False, "ΔAUC=-0.120 ... 下降超过 0.10")
      Gate 整体 FAIL → 触发返工
```

#### TC-4: 跨Phase反馈B — 文本信号检测

```
前置: Phase 3 执行中
操作: ML-engineer 输出包含 "特征不可用: frailty_index 在 CHARLS 2013 wave 中缺失率 87%"
期望: _detect_upstream_issues("execution", outputs, project_id)
      → [{from_phase: "execution", to_phase: "problem_definition",
          reason: "ML 阶段检测到数据/表型问题...",
          severity: "critical", action: "reopen_gate"}]
      → phase_index 回退到 problem_definition
      → invalidated_phases = {"design", "execution", "external_validation", "review", "writing"}
```

#### TC-5: 跨Phase反馈B — 数值规则检测

```
前置: _cached_aucs["execution"] = 0.85 (内部验证)
操作: Phase 4 外部验证输出 AUC=0.69
期望: _detect_upstream_issues("external_validation", outputs, project_id)
      → 检测到 ΔAUC = -0.16 < -0.15
      → 触发 execution Phase 重开
```

#### TC-6: 跨Phase反馈B — 写作阶段检测

```
前置: Phase 6 执行中
操作: scientific-writer 输出 "[数据待确认] 外部验证的 AUC (0.69) 与内部验证 (0.85) 差异较大,
       请 ML-engineer 确认是否存在过拟合"
期望: _detect_upstream_issues("writing", outputs, project_id)
      → 检测到 "[数据待确认]" 信号
      → 触发 execution Phase 重开
```

#### TC-7: 首席科学家升级

```
前置: Phase 3 返工 3 次后仍然 FAIL
操作: Gate FAIL 第4次
期望: _escalate_to_chief_scientist() 被调用
      首席科学家 Agent 被调用并输出裁决
```

### 6.2 单元测试脚本

```python
# tests/test_feedback_control.py

import pytest
from engine.core.gate_checks import (
    check_auc_trend, check_calibration_trend, check_feature_stability,
    _extract_auc_value, _extract_calibration_slope,
)
from engine.core.orchestrator_graph import ResearchOrchestrator


class TestTrendGates:
    """趋势Gate单元测试"""

    def test_auc_trend_first_run(self, orchestrator):
        """首次执行: 无历史基准"""
        outputs = {"shared/ml-engineer": "AUC=0.82, ..."}
        passed, detail = check_auc_trend(outputs, orchestrator)
        assert passed is True
        assert "首次执行" in detail
        assert orchestrator._trend_baselines["auc"] == 0.82

    def test_auc_trend_stable(self, orchestrator):
        """AUC稳定: 无预警"""
        orchestrator._trend_baselines["auc"] = 0.82
        outputs = {"shared/ml-engineer": "AUC=0.83, ..."}
        passed, detail = check_auc_trend(outputs, orchestrator)
        assert passed is True
        assert "提升" in detail or "稳定" in detail

    def test_auc_trend_warning(self, orchestrator):
        """AUC轻微下降: 预警但通过"""
        orchestrator._trend_baselines["auc"] = 0.82
        outputs = {"shared/ml-engineer": "AUC=0.76, ..."}
        passed, detail = check_auc_trend(outputs, orchestrator)
        assert passed is True
        assert "⚠️" in detail

    def test_auc_trend_fail(self, orchestrator):
        """AUC严重下降: FAIL"""
        orchestrator._trend_baselines["auc"] = 0.82
        outputs = {"shared/ml-engineer": "AUC=0.70, ..."}
        passed, detail = check_auc_trend(outputs, orchestrator)
        assert passed is False
        assert "下降超过" in detail

    def test_calibration_first_warning(self, orchestrator):
        """校准度首次偏离"""
        outputs = {"shared/ml-engineer": "calibration_slope=0.85, ..."}
        passed, detail = check_calibration_trend(outputs, orchestrator)
        assert passed is True
        assert "首次偏离" in detail

    def test_calibration_persistent_fail(self, orchestrator):
        """校准度持续偏离"""
        orchestrator._trend_baselines["calibration"] = {"value": 0.85, "state": "warning"}
        outputs = {"shared/ml-engineer": "calibration_slope=0.82, ..."}
        passed, detail = check_calibration_trend(outputs, orchestrator)
        assert passed is False
        assert "持续偏离" in detail


class TestCrossPhaseFeedback:
    """跨Phase反馈环B测试"""

    def test_detect_data_quality_issue(self, orchestrator):
        """ML阶段检测到数据质量问题"""
        outputs = {
            "shared/ml-engineer": "训练过程中发现 frailty_index 特征不可用, "
                                  "缺失率过高 (87%), 建议 data-engineer 重新处理"
        }
        issues = orchestrator._detect_upstream_issues(
            "execution", outputs, "test_project"
        )
        assert len(issues) >= 1
        data_issue = [i for i in issues if i["to_phase"] == "problem_definition"]
        assert len(data_issue) >= 1
        assert data_issue[0]["severity"] == "critical"
        assert data_issue[0]["action"] == "reopen_gate"

    def test_detect_writing_data_gap(self, orchestrator):
        """写作阶段检测到数据缺失"""
        outputs = {
            "shared/scientific-writer": "... 外部验证 AUC 为 [数据待确认], "
                                         "需 ML-engineer 提供具体数值 ..."
        }
        issues = orchestrator._detect_upstream_issues(
            "writing", outputs, "test_project"
        )
        assert len(issues) >= 1
        exec_issue = [i for i in issues if i["to_phase"] == "execution"]
        assert len(exec_issue) >= 1

    def test_no_issue_when_clean_output(self, orchestrator):
        """正常输出不触发反馈"""
        outputs = {
            "shared/ml-engineer": "AUC=0.85, 模型训练成功, 特征重要性正常..."
        }
        issues = orchestrator._detect_upstream_issues(
            "execution", outputs, "test_project"
        )
        assert len(issues) == 0
```

---

## 七、需要修改的文件清单

| 文件 | 改动类型 | 改动内容 | 预计行数 |
|------|---------|---------|---------|
| `engine/core/gate_checks.py` | 修改 + 新增 | 新增 `check_auc_trend()`, `check_calibration_trend()`, `check_feature_stability()` + 辅助函数 + 更新 GATE_DEFINITIONS | +120 |
| `engine/core/orchestrator_graph.py` | 修改 + 新增 | 新增 `FEEDBACK_B_TRIGGERS` 常量 + `_detect_upstream_issues()` + `_check_numeric_trigger()` + 新增 `_escalate_to_chief_scientist()` + 修改 `_run_project_workflow()` 主循环 + `__init__` 新增趋势缓存属性 + `_check_gate()` 增补指标缓存 | +180 / -20 |
| `engine/core/state.py` | 修改 | `ReworkRecord` 新增 `auto_detected` + `severity` 字段 + 新增 `TrendBaseline` + `CrossPhaseTrigger` TypedDict | +20 |
| `tests/test_feedback_control.py` | **新文件** | 趋势Gate + 跨Phase反馈B 的单元测试和集成测试 | +150 |

---

## 八、实施步骤

### Day 1-2: 趋势Gate
1. 在 `gate_checks.py` 中新增 `check_auc_trend()` 及辅助函数
2. 新增 `check_calibration_trend()` 及辅助函数
3. 新增 `check_feature_stability()` 及辅助函数
4. 更新 `GATE_DEFINITIONS`
5. 在 `orchestrator_graph.py` 的 `__init__` 中初始化 `_trend_baselines`, `_cached_aucs`, `_phase_features`
6. 在 `_check_gate()` 末尾增加指标缓存逻辑

### Day 3: 跨Phase反馈检测
1. 新增 `FEEDBACK_B_TRIGGERS` 常量
2. 新增 `_detect_upstream_issues()` 方法
3. 新增 `_check_numeric_trigger()` 方法
4. 在 `state.py` 扩展 `ReworkRecord`

### Day 4: 工作流循环改造
1. 修改 `_run_project_workflow()` 主循环
2. 新增 `_escalate_to_chief_scientist()` 方法
3. 新增 `invalidated_phases` + `phase_rework_counts` 追踪

### Day 5: 测试与验收
1. 编写 `tests/test_feedback_control.py`
2. 按集成测试方案逐项验收
3. 边界条件测试：空输出、中文英文混合、并发Phase的反馈B检测

---

## 附录：反馈控制系统的三种反馈模式总结

```
模式        触发方式        检测点       响应        对应理论
══════════════════════════════════════════════════════════════════
A环         同Phase内       Gate检查     同Phase返工  比例控制 (P)
(阶段内)    Gate FAIL

B环         下游Agent输出   文本信号+     回退到上游   积分控制 (I)
(阶段间)    自动检测        数值规则      Phase重开    (累计偏差修正)

C环         Gate间对比      趋势函数     预警+预防    微分控制 (D)
(趋势)      历史vs当前      ΔAUC等       性返工       (变化率响应)
```

三者共同构成类似 PID 控制器的完整反馈体系，确保系统在不确定性中保持预定品质——这正是钱学森工程控制论的核心目标。

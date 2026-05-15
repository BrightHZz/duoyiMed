# 钱学森工程控制论 — 公司全面改造方案

> 基于钱学森《工程控制论》五大核心理论，对DuoyiMed的组织架构、工作流程、质量体系和技术系统进行系统性改造。

---

## 目录

1. [改造总览与理论框架](#一改造总览与理论框架)
2. [模块一：闭环反馈控制系统](#二模块一闭环反馈控制系统)
3. [模块二：总体设计部与 SDS](#三模块二总体设计部与-sds)
4. [模块三：系统辨识与最优控制](#四模块三系统辨识与最优控制)
5. [模块四：可靠性工程](#五模块四可靠性工程)
6. [模块五：综合集成研讨厅](#六模块五综合集成研讨厅)
7. [模块六：研讨厅辩论模式](#七模块六研讨厅辩论模式)
8. [模块七：技术状态基线管理](#八模块七技术状态基线管理)
9. [实施路线图与验收标准](#九实施路线图与验收标准)

---

## 一、改造总览与理论框架

### 1.1 钱学森五大理论 → 七大改造模块

```
钱学森工程控制论                    公司改造模块
═══════════════                    ════════════

① 闭环反馈控制 ──────────────→ 模块一: 双层反馈环 + 趋势Gate + 跨Phase反馈B
② 总体设计部 ────────────────→ 模块二: SDS 系统设计 + 接口标准化
③ 系统辨识 ──────────────────→ 模块三: 运行数据采集 + 季度报告 + 传递函数建模
④ 可靠性工程 ────────────────→ 模块四: LLM容错 + 冗余交叉验证 + 一致性检查
⑤ 综合集成研讨厅 ────────────→ 模块五: FRAME定量化 + 人机分歧处理
                              模块六: 研讨厅辩论模式 (并行辩论替代流水线)
⑤+② 从定性到定量 ───────────→ 模块七: 技术状态基线管理 (版本冻结+变更控制)
```

### 1.2 当前实现状态

| 模块 | 状态 | 已完成 | 待完成 |
|------|------|--------|--------|
| 模块一 (反馈控制) | 🟡 部分完成 | Gate检查 + COND_PASS/FAIL + 返工循环 | 趋势Gate、跨Phase B环自动触发、Δ监控 |
| 模块二 (SDS) | 🟢 已完成 | Phase 0 + SDS生成 + 接口矩阵 | SDS与Gate一致性校验 |
| 模块三 (系统辨识) | 🟢 已完成 | RunLog采集 + JSONL存储 + 季度报告 | 传递函数建模 (预测模型)、自适应调度 |
| 模块四 (可靠性) | 🟡 部分完成 | LLM容错重试+降级+指数退避 | Agent间一致性检查、冗余交叉验证 |
| 模块五 (FRAME) | 🟢 已完成 | 两轮执行 + 定量化prompt | 人机分歧处理升级流程 |
| 模块六 (研讨厅) | 🔴 未开始 | - | Phase 2/5 并行辩论模式 |
| 模块七 (基线管理) | 🔴 未开始 | - | 版本冻结 + 变更通知 + 依赖追踪 |

---

## 二、模块一：闭环反馈控制系统

### 2.1 理论依据

钱学森《工程控制论》核心命题：
> 反馈系统远比开环系统优越。没有反馈的系统是不稳定的。

当前六阶段流程已实现基础反馈（Gate检查 → 返工），但缺少两个关键机制：

1. **趋势监控**：只在Gate点检查绝对值，不监控变化趋势
2. **跨Phase自动触发**：下游发现问题后需手动触发上游返工

### 2.2 详细设计

#### 2.2.1 趋势Gate (Δ-Gate)

在现有阈值Gate基础上，增加变化率监控：

```
当前 Gate 模式 (静态):
  AUC >= 0.70 → PASS
  AUC < 0.70  → FAIL

新增 Δ-Gate 模式 (动态):
  ΔAUC < -0.05 (compared to previous Gate) → ⚠️ 预警
  ΔAUC < -0.10                               → ❌ 触发返工审查
```

**实现位置**: `engine/core/gate_checks.py` 新增函数：

```python
def check_auc_trend(outputs: dict, orch) -> tuple:
    """ΔAUC 趋势检查 — 相对于上一版本的 AUC 变化"""
    current_auc = _extract_auc(outputs)
    if current_auc is None:
        return True, "跳过 (无 AUC 值)"

    # 从项目状态中获取上一次 Gate 的 AUC
    prev_auc = _get_previous_auc(orch, project_id)
    if prev_auc is None:
        return True, "首次执行，无趋势基准"

    delta = current_auc - prev_auc
    if delta < -0.10:
        return False, f"ΔAUC={delta:.3f} (从 {prev_auc:.3f} 降至 {current_auc:.3f})"
    elif delta < -0.05:
        return True, f"⚠️ ΔAUC={delta:.3f} (从 {prev_auc:.3f} 降至 {current_auc:.3f}) — 注意下滑趋势"
    return True, f"ΔAUC={delta:+.3f} 稳定"
```

**Gate定义更新**: 在 `GATE_DEFINITIONS["execution"]` 中增加：
```python
"auc_trend": check_auc_trend,
```

#### 2.2.2 跨Phase反馈环 B (自动触发)

当前代码已有 `rework_history` 记录，但缺少**自动检测下游问题并触发上游Gate重开**的逻辑。

**新增方法**: `_detect_upstream_issues()`

```python
def _detect_upstream_issues(self, phase_id: str, outputs: dict, 
                            project_id: str) -> list[dict]:
    """
    检测当前Phase中发现的、属于上游Phase的问题。
    
    返回: [{from_phase, to_phase, reason, severity}]
    
    触发条件 (自动检测):
    1. ML工程师报告 "特征不可用" 或 "数据质量问题" → 触发 Phase 1 重开
    2. 统计审查发现 "表型定义不可操作化" → 触发 Phase 1 重开
    3. 学术写作发现 "结果数字矛盾" 或 "统计方法与结果不匹配" → 触发 Phase 2/3 重开
    4. 外部验证AUC相比内部验证下降 > 0.15 → 触发 Phase 3 重开 (过拟合)
    """
    triggers = []
    
    # 规则1: ML阶段检测数据问题
    if phase_id == "execution":
        ml_output = ""
        for agent_id, output in outputs.items():
            if "ml-engineer" in agent_id:
                ml_output = output.lower()
                break
        data_quality_signals = [
            "特征不可用", "feature not available", "数据质量问题",
            "data quality", "缺失值过多", "missing rate", "样本量不足"
        ]
        for signal in data_quality_signals:
            if signal in ml_output:
                triggers.append({
                    "from_phase": phase_id,
                    "to_phase": "problem_definition",
                    "reason": f"ML检测到数据问题: {signal}",
                    "severity": "critical",
                })
                break
    
    # 规则2: 外部验证AUC大幅下降
    if phase_id == "external_validation":
        ext_auc = _extract_auc(outputs)
        int_auc = _get_previous_auc_from_gate("execution")
        if ext_auc and int_auc and (int_auc - ext_auc) > 0.15:
            triggers.append({
                "from_phase": phase_id,
                "to_phase": "execution",
                "reason": f"外部验证AUC({ext_auc:.3f})相比内部验证({int_auc:.3f})下降>0.15，疑似过拟合",
                "severity": "critical",
            })
    
    # 规则3: 写作阶段发现数据矛盾
    if phase_id == "writing":
        writer_output = ""
        for agent_id, output in outputs.items():
            if "scientific-writer" in agent_id:
                writer_output = output
                break
        if "[数据待确认]" in writer_output or "[数据矛盾]" in writer_output:
            triggers.append({
                "from_phase": phase_id,
                "to_phase": "execution",
                "reason": "学术写作发现数据矛盾或待确认数值",
                "severity": "high",
            })
    
    return triggers
```

**编排器集成**: 在 `_check_gate()` 之后调用：

```python
# 在 _run_project_workflow() 中, Gate检查之后:
upstream_issues = self._detect_upstream_issues(phase_id, phase_result, project_id)
for issue in upstream_issues:
    if issue["severity"] == "critical":
        # 暂停当前Phase, 强制重开上游Gate
        rework_history.append({...})
        phase_index = phases_to_run.index(issue["to_phase"])  # 回退
        print(f"  🔄 反馈环B触发: {issue['reason']} → 回退到 {issue['to_phase']}")
```

#### 2.2.3 需要修改的文件

| 文件 | 改动内容 | 新增行数 |
|------|---------|---------|
| `engine/core/gate_checks.py` | 新增 `check_auc_trend()` + `check_calibration_trend()` + `check_feature_stability()` | ~60 |
| `engine/core/orchestrator_graph.py` | 新增 `_detect_upstream_issues()` + 修改workflow循环处理跨Phase回退 | ~80 |
| `engine/core/state.py` | `ReworkRecord` 新增 `severity` 和 `auto_detected` 字段 | ~5 |

---

## 三、模块二：总体设计部与 SDS

### 3.1 状态：已完成但需补强

Phase 0 的 SDS 生成和两轮FRAME已完整实现。需补强：

### 3.2 SDS 与 Gate 一致性校验

SDS 中定义的 quality_gate 标准必须与 `GATE_DEFINITIONS` 中的实际检查项一致。新增校验方法：

```python
def _validate_sds_gate_alignment(self, sds_text: str, phase_id: str) -> dict:
    """
    校验 SDS 中定义的 Gate 标准是否与代码中的 GATE_DEFINITIONS 一致。
    
    不一致时发出警告但不阻断，记录到运行日志。
    """
    gate_def = GATE_DEFINITIONS.get(phase_id, {})
    actual_checks = set(gate_def.get("auto_checks", {}).keys())
    actual_checks.update(f"llm_{i}" for i in range(len(gate_def.get("llm_checks", []))))
    
    # 从SDS提取声明的检查项
    sds_checks = _extract_gate_checks_from_sds(sds_text, phase_id)
    
    missing_in_sds = actual_checks - sds_checks
    extra_in_sds = sds_checks - actual_checks
    
    return {
        "aligned": len(missing_in_sds) == 0 and len(extra_in_sds) == 0,
        "missing_in_sds": list(missing_in_sds),
        "extra_in_sds": list(extra_in_sds),
    }
```

### 3.3 需要修改的文件

| 文件 | 改动内容 | 新增行数 |
|------|---------|---------|
| `engine/core/orchestrator_graph.py` | 新增 `_validate_sds_gate_alignment()` + 在Phase 0完成后调用 | ~40 |

---

## 四、模块三：系统辨识与最优控制

### 4.1 状态：数据采集和报告已完成，缺少预测模型

RunLog采集 (`_call_agent` 埋点 + JSONL存储) 和 `run_analyzer.py` (季度报告生成) 均已完整实现。

### 4.2 传递函数建模 (新增)

钱学森系统辨识的完整流程：

```
输入信号            →  [公司系统]  →  输出信号
(项目类型+数据源+  →   (黑箱)     →  (耗时+成功率+
 目标期刊+团队)                               返工次数+接受率)
                     ↑
               系统辨识: 从 I/O 数据反推传递函数
```

**新增模块**: `engine/core/project_predictor.py`

```python
"""
项目预测器 — 基于历史运行数据预测新项目的关键指标。

钱学森系统辨识思想: 从 I/O 数据建立系统自身行为的数学模型。
"""

class ProjectPredictor:
    """
    读取 RunLog 数据, 为新建项目提供预测:
    - 预计总耗时
    - 预计各Phase一次通过率
    - 历史类似项目的成功率
    - 建议的目标期刊Tier
    """
    
    def __init__(self, analyzer: RunAnalyzer):
        self.analyzer = analyzer
        self.records = analyzer.records
    
    def predict(self, project_type: str, data_source: str, 
                target_journal_tier: str) -> dict:
        """
        基于历史类似项目, 预测新项目的关键指标。
        
        相似度匹配维度:
        1. 事业部 (geriatrics/urology)
        2. 研究类型 (prediction/causal/systematic_review)
        3. 数据源 (CHARLS/MIMIC/NHANES)
        4. 目标期刊Tier (1/2/3)
        """
        similar = self._find_similar_projects(
            project_type, data_source, target_journal_tier
        )
        
        if not similar:
            return {"confidence": "low", "message": "无足够历史数据"}
        
        return {
            "similar_projects_count": len(similar),
            "estimated_total_hours": statistics.mean(p["total_hours"] for p in similar),
            "estimated_success_rate": statistics.mean(p["success_rate"] for p in similar),
            "bottleneck_phase": self._identify_bottleneck(similar),
            "recommended_journal_tier": self._recommend_tier(similar, target_journal_tier),
            "risk_factors": self._extract_risk_factors(similar),
            "confidence": "high" if len(similar) >= 5 else "medium",
        }
    
    def _find_similar_projects(self, project_type, data_source, tier) -> list:
        """从 RunLog 中找到相似项目"""
        # 按 project_id 分组, 计算相似度
        ...
    
    def _identify_bottleneck(self, projects: list) -> str:
        """识别历史上类似项目的最常见瓶颈Phase"""
        ...
    
    def _recommend_tier(self, similar: list, target: str) -> str:
        """
        基于历史数据建议期刊Tier。
        如果历史类似项目投Tier1成功率<30%, 建议降级到Tier2。
        """
        ...
```

**集成到 Phase 0 SDS 生成**: 在 `_run_system_design()` 中注入预测结果：

```python
def _run_system_design(self, user_request: str, project_id: str) -> str:
    # 新增: 加载历史数据做预测
    predictor = ProjectPredictor(self.analyzer)
    prediction = predictor.predict(...)
    
    # 将预测结果注入SDS prompt
    if prediction["confidence"] != "low":
        prompt += f"""
        ## 历史参考数据 (系统辨识)
        类似项目数量: {prediction['similar_projects_count']}
        历史平均耗时: {prediction['estimated_total_hours']:.1f}h
        历史成功率: {prediction['estimated_success_rate']:.0%}
        常见瓶颈: {prediction['bottleneck_phase']}
        建议期刊Tier: {prediction['recommended_journal_tier']}
        """
```

### 4.3 自适应调度 (最优控制)

基于运行数据自动调整资源分配：

```python
def _adaptive_schedule(self, phase_id: str):
    """
    基于系统辨识结果自适应调整Phase执行策略。
    
    规则示例:
    - 如果某个Phase的历史一次通过率 < 60% → 增加该Phase的Agent并行度
    - 如果某个Agent的降级率 > 20% → 自动切换其默认模型
    - 如果当前资源负载 > 80% → 自动降低新项目的优先级
    """
    stats = self.analyzer.get_phase_stats(phase_id)
    
    if stats["pass_rate"] < 60:
        # 增加冗余: 让同Phase的另一个Agent做交叉验证
        return {"action": "add_redundancy", "extra_agent": "cross-validator"}
    
    if stats["avg_time"] > stats["target"] * 1.5:
        # 拆分任务或增加并行度
        return {"action": "split_or_parallelize"}
    
    return {"action": "normal"}
```

### 4.4 需要修改/新增的文件

| 文件 | 改动内容 | 新增行数 |
|------|---------|---------|
| `engine/core/project_predictor.py` | **新文件** — 传递函数建模 + 项目预测 | ~150 |
| `engine/core/orchestrator_graph.py` | SDS生成注入预测数据; `_adaptive_schedule()` | ~40 |
| `engine/core/run_analyzer.py` | 新增 `get_phase_stats()` 和 `get_similar_projects()` | ~50 |

---

## 五、模块四：可靠性工程

### 5.1 状态：LLM容错已完成，缺少Agent间冗余

LLM容错（重试+降级+指数退避+checkpoint）已在 `llm_client.py` 中完整实现。

### 5.2 新增：Agent间一致性检查 (冗余交叉验证)

钱学森核心思想：**"用不可靠的元件，通过工程协调的方法，组成可靠的系统。"**

LLM 是天然不可靠的元件。不能指望单个 Agent 一次输出就正确。需要在关键节点引入交叉验证。

```python
CONSISTENCY_CHECKER_PROMPT = """你是一致性检查器 (Consistency Checker)。
你的唯一职责是：对比两个 Agent 对同一概念/数据的表述，检查是否存在矛盾。

检查维度:
1. 术语一致性: 同一概念是否使用了不同名称？
2. 数值一致性: 同一数字在不同Agent的输出中是否一致？
3. 逻辑一致性: 两个Agent的结论是否存在逻辑矛盾？
4. 范围一致性: 表型定义/纳入排除标准是否一致？

输出格式:
- ✅ 一致: [说明]
- ⚠️ 轻微不一致 (可自动修复): [说明 + 建议统一表述]
- ❌ 严重矛盾 (需人工裁决): [说明 + 两个Agent的各自表述]
"""
```

**触发时机**: 在以下Phase完成后自动触发一致性检查：

| Phase | 对比对象 | 检查内容 |
|-------|---------|---------|
| Phase 1 (问题定义) | clinical-researcher ↔ data-engineer | 表型定义中变量名是否在数据字典中存在 |
| Phase 2 (方案设计) | computational-biologist ↔ biostatistician | 建模方案中的方法是否与SAP一致 |
| Phase 5 (审查) | clinical-researcher ↔ pi | 临床解读与终审结论是否一致 |
| Phase 6 (论文撰写) | scientific-writer ↔ 所有上游Agent | 论文中的数字是否与上游输出一致 |

**实现**: 新增 `engine/core/consistency_checker.py`

```python
"""
一致性检查器 — 基于钱学森可靠性工程思想,
通过 Agent 间冗余交叉验证, 用不可靠的 LLM 构建可靠的系统产出。
"""

CONSISTENCY_PAIRS = {
    "problem_definition": [
        {
            "agents": ["clinical-researcher", "data-engineer"],
            "check": "表型定义中的变量是否在数据字典中存在且名称一致",
            "severity": "critical",
        },
    ],
    "design": [
        {
            "agents": ["computational-biologist", "biostatistician"],
            "check": "建模方案中的模型是否与SAP中的分析方法一致",
            "severity": "critical",
        },
    ],
    "review": [
        {
            "agents": ["clinical-researcher", "pi"],
            "check": "临床审查结论与PI终审是否存在矛盾",
            "severity": "critical",
        },
    ],
    "writing": [
        {
            "agents": ["scientific-writer", "ml-engineer"],
            "check": "论文中的AUC/C-index/OR等数字是否与ML报告一致",
            "severity": "critical",
        },
        {
            "agents": ["scientific-writer", "biostatistician"],
            "check": "论文中的p值/置信区间/效应量是否与统计报告一致",
            "severity": "critical",
        },
    ],
}

class ConsistencyChecker:
    """Agent 间一致性交叉验证"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def check(self, phase_id: str, outputs: dict, division: str) -> list[dict]:
        """
        对指定Phase执行所有一致性检查对。
        
        返回: [{pair, result: pass/warn/fail, detail}]
        """
        pairs = CONSISTENCY_PAIRS.get(phase_id, [])
        results = []
        
        for pair in pairs:
            agent_a_output = self._find_output(outputs, pair["agents"][0], division)
            agent_b_output = self._find_output(outputs, pair["agents"][1], division)
            
            if not agent_a_output or not agent_b_output:
                continue
            
            prompt = f"""请对比以下两个Agent的输出, 检查{pair['check']}:

## Agent A: {pair['agents'][0]}
{agent_a_output[:3000]}

## Agent B: {pair['agents'][1]}
{agent_b_output[:3000]}

请输出:
- 一致性判定: [一致 / 轻微不一致 / 严重矛盾]
- 具体说明: ...
- 建议: ..."""
            
            response = self.llm.chat(
                system_prompt=CONSISTENCY_CHECKER_PROMPT,
                user_message=prompt,
            )
            
            result = self._parse_consistency_result(response.content)
            result["pair"] = f"{pair['agents'][0]} ↔ {pair['agents'][1]}"
            result["severity"] = pair["severity"]
            results.append(result)
        
        return results
```

**编排器集成**: 在 `_check_gate()` 之后调用一致性检查：

```python
# 在 _run_project_workflow() 中:
consistency_results = self.consistency_checker.check(
    phase_id, phase_result, self.active_division
)
for cr in consistency_results:
    if cr["result"] == "fail" and cr["severity"] == "critical":
        # 严重矛盾 → 触发返工
        gate_result["status"] = "fail"
        gate_result["checks"].append({
            "check_id": f"consistency_{cr['pair']}",
            "result": "fail",
            "detail": cr["detail"],
        })
```

### 5.3 需要修改/新增的文件

| 文件 | 改动内容 | 新增行数 |
|------|---------|---------|
| `engine/core/consistency_checker.py` | **新文件** — Agent间一致性交叉验证 | ~180 |
| `engine/core/orchestrator_graph.py` | 集成一致性检查到 `_check_gate()` 之后 | ~30 |
| `engine/core/llm_client.py` | 无需修改 (已有容错能力) | 0 |

---

## 六、模块五：综合集成研讨厅 (FRAME 定量化)

### 6.1 状态：已完成

两轮Phase执行 + FRAME定量化prompt已在 `_execute_phase_two_round()` 和 `_build_frame_quantitative_prompt()` 中完整实现。

### 6.2 待补强：人机分歧处理升级流程

当 PI 的 FRAME 结论与机器预检数据存在明显矛盾时的处理：

```python
def _handle_frame_disagreement(self, pi_output: str, round1_outputs: dict) -> str:
    """
    检测 PI FRAME 评估与机器预检报告的矛盾, 按严重程度分级处理。
    
    Level 1 — 轻微分歧: PI给出"启动"但F维度文献数据建议"观望"
               → 自动提醒PI复核F维度, 不阻断
    Level 2 — 中度分歧: PI给出"放弃"但R/E/M三个维度数据均支持
               → 升级到首席科学家二次评估
    Level 3 — 严重分歧: PI的结论与Round1报告数据完全矛盾
               → 首席科学家裁决 + 记录到知识库
    """
    disagreements = self._detect_disagreements(pi_output, round1_outputs)
    
    if not disagreements:
        return "aligned"
    
    level = max(d["level"] for d in disagreements)
    
    if level == 1:
        return f"⚠️ 提醒PI复核: {[d['dimension'] for d in disagreements]}"
    elif level == 2:
        return self._escalate_to_chief_scientist(disagreements)
    else:
        return self._escalate_to_chief_scientist(
            disagreements, 
            note="PI结论与定量数据严重矛盾, 需首席科学家裁决"
        )
```

---

## 七、模块六：研讨厅辩论模式

### 7.1 理论基础

钱学森的综合集成研讨厅不是流水线，而是**并行辩论**：

```
当前流水线模式:              研讨厅辩论模式:
  A → B → C → D → 产出       A ─┐
                              B ─┼→ 观点碰撞 → 共识/分歧列表 → PI裁决 → 产出
                              C ─┘
```

辩论模式的核心优势：
- **暴露分歧**: 不同Agent从各自视角看同一问题，分歧点才是需要人工判断的关键
- **防止群体思维**: 串行执行中后执行的Agent容易受前面Agent的影响
- **效率更高**: 并行输出后只审分歧点，而不是逐个审每个Agent的完整输出

### 7.2 适用Phase

辩论模式适用于**需要多视角判断的决策节点**：

| Phase | 参与者 | 辩论议题 |
|-------|--------|---------|
| Phase 2 (方案设计) | computational-biologist + biostatistician + clinical-researcher | 研究设计选择: 建模方法、统计策略、协变量选择 |
| Phase 5 (审查) | clinical-researcher + biostatistician + pi | 结果解读: 临床意义、统计显著性、效应方向 |

### 7.3 详细设计

**新增方法**: `_execute_phase_debate()`

```python
DEBATE_MODERATOR_PROMPT = """你是研讨厅主持人 (Debate Moderator)。
你的职责是主持多Agent并行辩论, 汇总各方观点, 识别共识与分歧, 给出裁决建议。

流程:
1. 接收多个Agent对同一问题的并行输出
2. 识别各方一致同意的点 (共识)
3. 识别各方观点不同的点 (分歧), 按重要性排序
4. 对每个分歧点, 给出: 各方论据、证据强度、建议方向
5. 最终输出《研讨厅辩论纪要》提交PI裁决
"""

def _execute_phase_debate(
    self, phase_id: str, user_request: str,
    previous_outputs: dict, project_id: str,
    debate_topic: str, participants: list[str],
) -> dict:
    """
    研讨厅辩论模式: 并行执行所有参与者, 然后由主持人汇总共识与分歧。
    
    Args:
        debate_topic: 辩论主题 (如 "研究设计选择")
        participants: 参与辩论的Agent列表
    """
    outputs = {}
    
    # Round 1: 所有参与者并行输出自己的观点
    print(f"  [研讨厅] {debate_topic} — 并行辩论开始 ({len(participants)} 参与)")
    
    debate_prompt_template = """## 研讨厅辩论: {debate_topic}

请从你的专业视角, 对以下议题给出你的独立分析和建议:

{debate_topic}

用户原始需求: {user_request}

上游阶段输出:
{upstream_summary}

请注意:
1. 独立分析, 不要试图猜测其他Agent的结论
2. 每个主张必须有证据或推理支撑
3. 明确标注你确信的程度: [高/中/低]
4. 格式: 观点 → 证据 → 确信度 → 建议"""
    
    for agent_id in participants:
        task_input = debate_prompt_template.format(
            debate_topic=debate_topic,
            user_request=user_request,
            upstream_summary=self._summarize_outputs(previous_outputs, max_len=2000),
        )
        result = self._call_agent(agent_id, task_input,
                                  phase_id=f"{phase_id}_debate", project_id=project_id)
        outputs[agent_id] = result
    
    # Round 2: 主持人汇总共识与分歧
    moderator_prompt = f"""## 研讨厅辩论纪要

辩论主题: {debate_topic}

### 各方观点:
"""
    for agent_id, output in outputs.items():
        moderator_prompt += f"\n#### {agent_id}\n{output[:2000]}\n---\n"
    
    moderator_prompt += """
请输出《研讨厅辩论纪要》:

## 研讨厅辩论纪要

### 1. 共识 (所有参与方一致同意)
- [共识1]: ...
- [共识2]: ...

### 2. 分歧 (按重要性排序)
#### 分歧1: [议题]
- 观点A (Agent X, 确信度: 高): ...
- 观点B (Agent Y, 确信度: 中): ...
- 主持人建议: [倾向哪个观点 / 需补充什么证据]

#### 分歧2: ...

### 3. PI裁决项 (需PI明确决策)
- [ ] 决策项1: ...
- [ ] 决策项2: ...

### 4. 综合建议
- ...
"""
    
    moderator_output = self._call_agent(
        "debate-moderator", moderator_prompt,
        phase_id=f"{phase_id}_moderator", project_id=project_id,
    )
    outputs["_debate_minutes"] = moderator_output
    
    return outputs
```

**集成到 PROJECT_PHASES**:

```python
PROJECT_PHASES = {
    # ... 现有定义 ...
    "design": {
        "agents": ["computational-biologist", "biostatistician"],
        "parallel": True,
        "debate_mode": True,  # 🆕 启用研讨厅辩论模式
        "debate_topic": "研究设计选择: 建模方法 + 统计策略 + 协变量选择",
        "debate_participants": ["shared/computational-biologist", 
                                "shared/biostatistician",
                                "{division}/clinical-researcher"],
        "description": "方案设计 (研讨厅辩论模式)",
        "depends_on": ["problem_definition"],
        "next": "execution",
    },
}
```

### 7.4 需要修改/新增的文件

| 文件 | 改动内容 | 新增行数 |
|------|---------|---------|
| `engine/core/orchestrator_graph.py` | 新增 `_execute_phase_debate()` + 修改 `_run_project_workflow()` 支持 debate_mode | ~120 |
| `company/management/debate-moderator.md` | **新文件** — 研讨厅主持人 Agent 定义 | ~60 |

---

## 八、模块七：技术状态基线管理

### 8.1 理论基础

钱学森在航天系统工程中的核心实践：每个阶段冻结一个**技术状态基线 (baseline)**，变更必须走正式的变更控制流程。

当前公司流程中，Phase产出没有版本概念——Agent输出后直接传递给下游。如果下游发现问题需要回退修改，之前的下游工作全部作废且无法追踪。

### 8.2 详细设计

```
Phase N 完成 → Gate N PASS → 冻结基线 v1.0
                                  │
                    下游 Phase N+1 发现上游问题
                                  │
                         创建变更请求 (CR)
                                  │
                    上游修正 → 新基线 v1.1
                                  │
                    通知所有依赖方 → 下游重跑
```

**数据模型新增**:

```python
class BaselineRecord(TypedDict):
    """技术状态基线 — Phase产出的冻结版本"""
    baseline_id: str           # "frailty_ml_2026/phase1/v1.0"
    project_id: str
    phase_id: str
    version: str               # "1.0", "1.1", "2.0"
    status: str                # "frozen" | "superseded" | "active"
    artifacts: dict            # {artifact_name: content_hash}
    gate_result: dict          # 冻结时的Gate检查结果
    timestamp: str
    frozen_by: str             # "orchestrator"

class ChangeRequest(TypedDict):
    """变更请求 — 下游触发上游修改的正式记录"""
    cr_id: str
    project_id: str
    from_phase: str            # 发现问题的Phase
    to_phase: str              # 需要修改的Phase
    reason: str
    affected_artifacts: list[str]  # 受影响的产出物
    downstream_impact: list[str]   # 受影响的下游Phase
    status: str                # "open" | "approved" | "implemented" | "closed"
```

**编排器集成**:

在 `_run_project_workflow()` 中，每个 Phase Gate通过后：

```python
# Gate PASS 后冻结基线
baseline = BaselineRecord(
    baseline_id=f"{project_id}/{phase_id}/v{version}",
    project_id=project_id,
    phase_id=phase_id,
    version=f"{major}.{minor}",
    status="frozen",
    artifacts={k: hashlib.md5(v.encode()).hexdigest()[:8] 
               for k, v in phase_result.items()},
    gate_result=gate_result,
    timestamp=datetime.now().isoformat(),
    frozen_by="orchestrator",
)
self._save_baseline(baseline)
project_state["baselines"].append(baseline)
```

当反馈环B触发回退修改时：

```python
# 上游修改完成后创建变更记录
cr = ChangeRequest(
    cr_id=f"CR-{project_id}-{phase_id}-{datetime.now().strftime('%Y%m%d%H%M')}",
    from_phase=triggering_phase,
    to_phase=target_phase,
    reason=reason,
    affected_artifacts=[...],
    downstream_impact=[...],
    status="open",
)
# 通知所有依赖方
self._notify_downstream(cr)
# 将下游Phase标记为"待重新验证"
self._invalidate_downstream(project_id, target_phase)
```

### 8.3 需要修改/新增的文件

| 文件 | 改动内容 | 新增行数 |
|------|---------|---------|
| `engine/core/state.py` | 新增 `BaselineRecord` + `ChangeRequest` + `ProjectState` 新增 `baselines` 字段 | ~30 |
| `engine/core/orchestrator_graph.py` | 新增 `_freeze_baseline()` + `_create_change_request()` + `_invalidate_downstream()` | ~80 |
| `engine/core/baseline_manager.py` | **新文件** — 基线存储与变更追踪 | ~100 |

---

## 九、实施路线图与验收标准

### 9.1 总体优先级矩阵

```
影响力 / 实施成本 矩阵:

高影响 │  模块六         │  模块一         │
       │  (研讨厅辩论)   │  (反馈环B+      │
       │                 │   趋势Gate)     │
       │                 │                 │
       │  模块七         │  模块四         │
       │  (基线管理)     │  (一致性检查)    │
       │                 │                 │
低影响 │                 │  模块三         │
       │                 │  (传递函数)     │
       └─────────────────┴─────────────────┘
         高成本              低成本

优先顺序: 模块一 → 模块四 → 模块六 → 模块三 → 模块七
```

### 9.2 五周实施计划

#### 第一周：反馈控制增强 (模块一)

| 日期 | 任务 | 产出 |
|------|------|------|
| Day 1-2 | 实现 `_detect_upstream_issues()` 跨Phase自动检测 | orchestrator_graph.py +80行 |
| Day 3 | 实现趋势Gate: `check_auc_trend()` + `check_calibration_trend()` | gate_checks.py +60行 |
| Day 4 | 修改workflow循环支持跨Phase回退 + 断点续传 | orchestrator_graph.py +40行 |
| Day 5 | 集成测试: 模拟各种反馈触发场景 | 测试用例 |

**验收标准**:
- [ ] ML阶段发现"特征不可用" → 自动触发Phase 1重开
- [ ] 外部AUC相比内部下降>0.15 → 自动触发Phase 3重开
- [ ] 趋势Gate检测到ΔAUC<-0.05 → 预警信息出现在日志中
- [ ] 跨Phase回退后, 下游Phase自动标记"待重新验证"

#### 第二周：可靠性增强 (模块四)

| 日期 | 任务 | 产出 |
|------|------|------|
| Day 1-2 | 实现 `ConsistencyChecker` 类 | consistency_checker.py (新) 180行 |
| Day 3 | 实现各Phase的一致性检查对 | consistency_checker.py |
| Day 4 | 集成到 `_check_gate()` 之后 | orchestrator_graph.py +30行 |
| Day 5 | 集成测试: 故意制造Agent间矛盾 | 测试用例 |

**验收标准**:
- [ ] Phase 1 完成后自动检查 clinical-researcher ↔ data-engineer 变量名一致性
- [ ] Phase 6 完成后自动检查 scientific-writer 数字与上游一致
- [ ] 严重矛盾 → Gate FAIL → 触发返工
- [ ] 轻微不一致 → 自动注入修正建议到下游

#### 第三周：研讨厅辩论模式 (模块六)

| 日期 | 任务 | 产出 |
|------|------|------|
| Day 1-2 | 实现 `_execute_phase_debate()` | orchestrator_graph.py +120行 |
| Day 3 | 创建 debate-moderator Agent 定义 | debate-moderator.md (新) 60行 |
| Day 4 | 修改 Phase 2 和 Phase 5 为辩论模式 | orchestrator_graph.py |
| Day 5 | 集成测试: 启动辩论 → 检查辩论纪要质量 | 测试用例 |

**验收标准**:
- [ ] Phase 2 执行时, 3个Agent并行输出各自方案 → 主持人输出共识/分歧纪要
- [ ] 辩论纪要包含: 共识列表、分歧列表(按重要性排)、PI裁决项
- [ ] PI基于辩论纪要(而非逐个审Agent输出)做决策

#### 第四周：系统辨识增强 (模块三)

| 日期 | 任务 | 产出 |
|------|------|------|
| Day 1-2 | 实现 `ProjectPredictor` 类 | project_predictor.py (新) 150行 |
| Day 3 | 实现 `_adaptive_schedule()` | orchestrator_graph.py +40行 |
| Day 4 | 集成预测结果到Phase 0 SDS生成 | orchestrator_graph.py |
| Day 5 | 验证: 用历史数据回测预测准确度 | 测试用例 |

**验收标准**:
- [ ] 新建项目时SDS包含"历史类似项目参考数据"
- [ ] 预测耗时与实际耗时偏差 < 30% (历史≥5个类似项目时)
- [ ] 项目预测器能正确识别瓶颈Phase

#### 第五周：基线管理 + 整体验收 (模块七)

| 日期 | 任务 | 产出 |
|------|------|------|
| Day 1-2 | 实现 `BaselineRecord` + `ChangeRequest` + 存储逻辑 | state.py + baseline_manager.py |
| Day 3 | 实现 `_freeze_baseline()` + `_invalidate_downstream()` | orchestrator_graph.py +80行 |
| Day 4 | 全链路集成测试: 完整项目走一遍 | 端到端测试 |
| Day 5 | 文档更新 + company-sop.md 同步 | 文档 |

**验收标准**:
- [ ] 每个Phase Gate通过后自动冻结基线版本
- [ ] 下游触发上游修改 → 自动创建变更请求 → 通知依赖方
- [ ] 所有下游Phase自动标记"待重新验证"

### 9.3 全系统集成验收

端到端测试场景：

```
1. 启动新项目 "CHARLS 衰弱预测"
2. Phase 0: SDS 生成 (含历史参考数据)
3. Phase 1: FRAME定量化 (两轮) + 一致性检查 (clinical ↔ data-engineer)
4. Phase 2: 研讨厅辩论 (computational-bio + biostat + clinical 并行辩论)
5. Phase 3: 执行 + 趋势Gate (ΔAUC监控) + 一致性检查
6. 模拟故障: ΔAUC < -0.10 → 趋势Gate FAIL → 返工
7. 模拟跨Phase反馈: ML发现数据问题 → 自动回退 Phase 1
8. Phase 6: 论文撰写 + 数字一致性交叉验证
9. 季度报告: 自动生成运行状态 + 改进建议
```

### 9.4 理论-实现对照表 (最终状态)

| 钱学森理论 | 实现模块 | 核心机制 | 验收指标 |
|-----------|---------|---------|---------|
| 闭环反馈控制 | 模块一 | Gate检查 + 趋势Gate + 跨Phase B环自动触发 | 3类反馈全部自动生效 |
| 总体设计部 | 模块二 | Phase 0 SDS + 接口矩阵 + Gate一致性校验 | 每个新项目有SDS蓝图 |
| 系统辨识 | 模块三 | RunLog采集 + 季度报告 + 传递函数建模 | 新项目预测准确度>70% |
| 最优控制 | 模块三 | 自适应调度: 瓶颈检测→并行/拆分 | Phase耗时达标率>80% |
| 可靠性工程 | 模块四 | LLM容错 + Agent间一致性交叉验证 | 系统可用率>99%, 严重矛盾检出率100% |
| 综合集成研讨厅 | 模块五+六 | FRAME定量化 + 研讨厅辩论模式 | PI决策有定量数据支撑 |
| 从定性到定量 | 全部 | 每个Gate有量化阈值 + 基线版本管理 | 无口头通过, 无未经审查的产出 |
| 开放复杂巨系统 | 全部 | 反馈环 + 运行数据 + 辩论 + 基线 | 系统具备自观察、自修正、自进化能力 |

---

> 钱学森说："系统工程不是一堆方法的堆砌，而是一种思考方式。"
>
> 本改造方案的目标不是增加流程步骤，而是建立一个**能观察自身、能自我修正、能持续进化的研究系统** — 这正是钱学森工程控制论的核心追求。

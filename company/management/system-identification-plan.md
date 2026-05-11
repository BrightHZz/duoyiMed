# 模块四：系统辨识与最优控制 — 详细设计方案

> 钱学森系统辨识的核心流程：**从 I/O 数据反推系统的数学模型，然后基于模型做最优控制。**
>
> 当前已有 RunLog 数据采集 + 季度报告（系统辨识的 Step 1-2），缺的是 Step 3：用历史数据**预测新项目**，以及 Step 4：基于预测**自适应调度**资源。

---

## 目录

1. [现状与差距](#一现状与差距)
2. [核心概念：传递函数建模](#二核心概念传递函数建模)
3. [ProjectPredictor 类设计](#三-projectpredictor-类设计)
4. [自适应调度器设计](#四自适应调度器设计)
5. [Phase 0 SDS 集成](#五phase-0-sds-集成)
6. [编排器集成点](#六编排器集成点)
7. [测试方案](#七测试方案)
8. [文件改动清单](#八文件改动清单)

---

## 一、现状与差距

### 1.1 已有能力

```
✅ RunLog 数据采集 — _call_agent() 每次调用自动记录 JSONL
   字段: timestamp, project_id, division, phase_id, agent_id,
         success, degraded, wall_time_sec, tokens, error_type, gate_status

✅ RunAnalyzer — 读取 JSONL, 聚合统计, 生成 Markdown/JSON 报告
   维度: Phase耗时分布, Agent一次通过率, Gate统计, 资源消耗, 改进建议

✅ 季度报告 CLI — python run_research.py --analyze
```

### 1.2 核心差距

```
钱学森系统辨识的完整流程:

  输入信号    →    [公司系统]    →    输出信号
  (项目类型,       (黑箱)          (总耗时, 成功率,
   数据源,                          返工次数, 各Phase通过率)
   目标期刊)
       ↑                               ↑
       └──── 系统辨识: 从I/O反推数学模型 ────┘
                     ↓
              传递函数 f(输入) → 输出
                     ↓
              最优控制: 基于模型调整资源

当前差距:
  ❌ 步骤3 — 传递函数建模: 无法回答 "这个新项目大概要多久？成功率多高？"
  ❌ 步骤4 — 自适应调度: 不会根据历史数据自动调整执行策略
  ❌ Phase 0 未集成预测: SDS 生成时没有历史参考数据
```

### 1.3 两个新增模块

| 模块 | 对应理论 | 功能 |
|------|---------|------|
| **ProjectPredictor** | 系统辨识 — 传递函数 | 输入新项目特征 → 预测耗时/成功率/瓶颈/建议期刊Tier |
| **AdaptiveScheduler** | 最优控制 | 基于运行数据自动调整Phase执行策略 |

---

## 二、核心概念：传递函数建模

### 2.1 钱学森理论映射

钱学森在《工程控制论》中定义系统辨识为：

> 通过测量系统在正常运行时的输入和输出数据，建立系统动态特性的数学模型。

对公司而言：
- **输入向量 X** = (事业部, 研究类型, 数据源, 目标期刊Tier, 样本量级)
- **输出向量 Y** = (总耗时, 一次通过率, 返工次数, 瓶颈Phase, API费用)
- **传递函数** = Y ≈ f(X)，从历史 RunLog 中学习 f

### 2.2 相似度定义

不是做 ML 模型训练，而是基于**项目特征相似度**找历史类似项目，做统计推断：

```
新项目的特征向量:  (geriatrics, prediction, CHARLS, tier_2)
                          ↓
历史项目库中搜索:  相似事业部 + 相同研究类型 + 相同数据源 + 相似期刊
                          ↓
找到 N 个类似项目 → 计算各指标的均值和置信区间
                          ↓
输出: "类似项目 5 个, 平均耗时 12.5h, 成功率 60%, 瓶颈为 execution Phase"
```

### 2.3 项目特征定义

```python
@dataclass
class ProjectProfile:
    """新项目的特征画像 — 系统辨识的输入向量"""
    division: str              # "geriatrics" | "urology"
    research_type: str         # "prediction" | "causal_inference" | "systematic_review" | "exploratory"
    data_source: str           # "CHARLS" | "MIMIC-IV" | "NHANES" | "SEER" | "CLHLS" | ...
    target_journal_tier: int   # 1 (IF>15), 2 (IF 5-15), 3 (IF 2-5)
    estimated_sample_size: str # "small(<1000)" | "medium(1000-10000)" | "large(>10000)"
    
    @classmethod
    def from_user_request(cls, user_request: str, division: str) -> 'ProjectProfile':
        """从用户请求中自动推断项目特征"""
        ...
```

---

## 三、ProjectPredictor 类设计

### 3.1 类结构

```python
# engine/core/project_predictor.py

class ProjectPredictor:
    """
    项目预测器 — 系统辨识模块核心。
    
    基于历史 RunLog 数据, 为新项目提供关键指标预测。
    对应钱学森系统辨识的"传递函数建模"步骤。
    
    用法:
        analyzer = RunAnalyzer(log_dir="outputs/run_logs")
        analyzer.load(days=90)
        
        predictor = ProjectPredictor(analyzer)
        profile = ProjectProfile(
            division="geriatrics",
            research_type="prediction",
            data_source="CHARLS",
            target_journal_tier=2,
        )
        prediction = predictor.predict(profile)
        # prediction["estimated_total_hours"] → 14.2
        # prediction["bottleneck_phase"] → "execution"
    """
    
    def __init__(self, analyzer: 'RunAnalyzer'):
        self.analyzer = analyzer
        self.records = analyzer.records
    
    # ================================================================
    # 主预测接口
    # ================================================================
    
    def predict(self, profile: 'ProjectProfile') -> dict:
        """
        基于历史类似项目, 预测新项目的关键指标。
        
        Returns:
            {
                "similar_projects_count": int,       # 找到的类似项目数
                "confidence": "high|medium|low",      # 预测可信度
                "estimated_total_hours": float,       # 预计总耗时 (h)
                "estimated_total_hours_range": [min, max],
                "phase_predictions": [...],            # 各Phase预测
                "estimated_success_rate": float,      # 估计一次通过率
                "bottleneck_phase": str,              # 最可能的瓶颈Phase
                "recommended_journal_tier": int,       # 建议目标期刊Tier
                "risk_factors": [...],                 # 历史类似项目的风险因子
                "similar_projects_summary": str,       # 人类可读的摘要
            }
        """
        similar = self._find_similar_projects(profile)
        
        if not similar:
            return self._low_confidence_result(profile)
        
        confidence = "high" if len(similar) >= 5 else ("medium" if len(similar) >= 2 else "low")
        
        return {
            "similar_projects_count": len(similar),
            "confidence": confidence,
            "estimated_total_hours": self._estimate_total_hours(similar),
            "estimated_total_hours_range": self._hours_range(similar),
            "phase_predictions": self._predict_phases(similar),
            "estimated_success_rate": self._estimate_success_rate(similar),
            "bottleneck_phase": self._identify_bottleneck(similar),
            "recommended_journal_tier": self._recommend_tier(similar, profile.target_journal_tier),
            "risk_factors": self._extract_risk_factors(similar),
            "similar_projects_summary": self._format_summary(similar, profile),
        }
    
    # ================================================================
    # 核心算法
    # ================================================================
    
    def _find_similar_projects(self, profile: 'ProjectProfile') -> list[dict]:
        """
        从 RunLog 中找到与 profile 相似的历史项目。
        
        相似度维度 (不是精确匹配, 而是按优先级逐级放宽):
        1. 同事业部 + 同研究类型 + 同数据源 → 权重最高
        2. 同事业部 + 同研究类型 → 次之
        3. 同事业部 → 兜底
        
        每个项目按 project_id 分组, 计算聚合指标。
        """
        # 按 project_id 分组
        projects = self._group_by_project()
        
        similar = []
        for proj_id, proj_records in projects.items():
            score = self._similarity_score(profile, proj_records)
            if score > 0:
                similar.append({
                    "project_id": proj_id,
                    "score": score,
                    "metrics": self._compute_project_metrics(proj_records),
                })
        
        # 按相似度排序, 取 top-10
        similar.sort(key=lambda x: -x["score"])
        return similar[:10]
    
    def _similarity_score(self, profile, records: list) -> int:
        """
        计算相似度分数。
        
        事业部匹配: +4
        研究类型匹配: +3  (从 SDS/用户请求推断)
        数据源匹配: +2
        期刊Tier相同或±1: +1
        """
        score = 0
        div = set(r.get("division", "") for r in records)
        if profile.division in div:
            score += 4
        
        # 研究类型和数据源从 records 的上下文中推断
        # (简化: 先基于 project_id 中的关键词, 后续可从 SDS 中提取)
        proj_id = records[0].get("project_id", "").lower()
        if profile.research_type in proj_id:
            score += 3
        if profile.data_source.lower() in proj_id:
            score += 2
        
        return score
    
    def _group_by_project(self) -> dict:
        """将 RunLog records 按 project_id 分组"""
        projects = {}
        for r in self.records:
            pid = r.get("project_id", "unknown")
            if pid not in projects:
                projects[pid] = []
            projects[pid].append(r)
        return projects
    
    def _compute_project_metrics(self, records: list) -> dict:
        """从单个项目的 RunLog 记录中计算聚合指标"""
        phases = {}
        for r in records:
            pid = r.get("phase_id", "")
            if pid not in phases:
                phases[pid] = {"total_time": 0, "count": 0, "success": 0, "fail": 0}
            phases[pid]["total_time"] += r.get("wall_time_sec", 0)
            phases[pid]["count"] += 1
            if r.get("success"):
                phases[pid]["success"] += 1
            else:
                phases[pid]["fail"] += 1
        
        total_time = sum(p["total_time"] for p in phases.values())
        total_calls = sum(p["count"] for p in phases.values())
        success_calls = sum(p["success"] for p in phases.values())
        
        return {
            "total_hours": round(total_time / 3600, 1),
            "phase_times": {pid: round(p["total_time"] / 3600, 1) for pid, p in phases.items()},
            "phase_success_rates": {
                pid: round(p["success"] / p["count"] * 100) if p["count"] > 0 else 0
                for pid, p in phases.items()
            },
            "overall_success_rate": round(success_calls / total_calls * 100) if total_calls > 0 else 0,
            "total_phases": len(phases),
        }
    
    # ================================================================
    # 统计推断方法
    # ================================================================
    
    def _estimate_total_hours(self, similar: list) -> float:
        """加权平均预测总耗时"""
        if not similar:
            return 0
        weights = [s["score"] for s in similar]
        hours = [s["metrics"]["total_hours"] for s in similar]
        return round(sum(w * h for w, h in zip(weights, hours)) / sum(weights), 1)
    
    def _hours_range(self, similar: list) -> list:
        """耗时预测区间 [min, max]"""
        hours = [s["metrics"]["total_hours"] for s in similar]
        return [min(hours), max(hours)]
    
    def _predict_phases(self, similar: list) -> list[dict]:
        """预测每个 Phase 的耗时和通过率"""
        # 取所有类似项目的 Phase 聚合
        phase_data = defaultdict(list)
        for s in similar:
            for pid, hours in s["metrics"]["phase_times"].items():
                phase_data[pid].append(hours)
        
        predictions = []
        for pid, hour_list in sorted(phase_data.items()):
            predictions.append({
                "phase_id": pid,
                "avg_hours": round(statistics.mean(hour_list), 1),
                "min_hours": min(hour_list),
                "max_hours": max(hour_list),
            })
        return predictions
    
    def _estimate_success_rate(self, similar: list) -> float:
        """加权平均预测一次通过率"""
        weights = [s["score"] for s in similar]
        rates = [s["metrics"]["overall_success_rate"] for s in similar]
        return round(sum(w * r for w, r in zip(weights, rates)) / sum(weights), 1)
    
    def _identify_bottleneck(self, similar: list) -> str:
        """识别最常见的瓶颈 Phase"""
        # 瓶颈定义: 耗时占比最高 且 成功率最低 的 Phase
        phase_scores = defaultdict(list)
        for s in similar:
            for pid, hours in s["metrics"]["phase_times"].items():
                rate = s["metrics"]["phase_success_rates"].get(pid, 100)
                # 瓶颈得分 = 耗时(归一化) * (1 - 成功率)
                phase_scores[pid].append(hours * (1 - rate / 100))
        
        if not phase_scores:
            return "unknown"
        
        avg_scores = {pid: statistics.mean(scores) for pid, scores in phase_scores.items()}
        return max(avg_scores, key=avg_scores.get)
    
    def _recommend_tier(self, similar: list, target_tier: int) -> int:
        """
        基于历史数据建议期刊Tier。
        如果历史类似项目投 Tier 1 成功率 < 30%，建议降级到 Tier 2。
        """
        tier1_projects = [s for s in similar if s["score"] >= 5]
        if target_tier == 1 and len(tier1_projects) >= 3:
            success_rates = [s["metrics"]["overall_success_rate"] for s in tier1_projects]
            avg_rate = statistics.mean(success_rates)
            if avg_rate < 30:
                return 2  # 建议降级
        return target_tier
    
    def _extract_risk_factors(self, similar: list) -> list[str]:
        """从类似项目的失败记录中提取风险因子"""
        risks = []
        for s in similar:
            metrics = s["metrics"]
            # 成功率低于 50% → 高风险
            if metrics["overall_success_rate"] < 50:
                risks.append(
                    f"类似项目 {s['project_id']}: 成功率仅 {metrics['overall_success_rate']}%, "
                    f"耗时 {metrics['total_hours']}h"
                )
            # 某个 Phase 成功率特别低
            for pid, rate in metrics["phase_success_rates"].items():
                if rate < 50:
                    risks.append(
                        f"Phase {pid}: 历史通过率仅 {rate}% (项目 {s['project_id']})"
                    )
        return list(set(risks))[:5]  # 去重, 最多 5 条
    
    def _format_summary(self, similar: list, profile: 'ProjectProfile') -> str:
        """生成人类可读的项目预测摘要"""
        pred = self.predict(profile) if not similar else {}
        return (
            f"基于 {len(similar)} 个类似项目的运行数据:\n"
            f"- 预计总耗时: {pred.get('estimated_total_hours', '?')}h "
            f"(范围 {pred.get('estimated_total_hours_range', ['?', '?'])})\n"
            f"- 预计成功率: {pred.get('estimated_success_rate', '?')}%\n"
            f"- 最常见瓶颈: {pred.get('bottleneck_phase', '?')}\n"
            f"- 建议期刊Tier: {pred.get('recommended_journal_tier', '?')}\n"
            f"- 预测可信度: {pred.get('confidence', '?')}"
        )
    
    def _low_confidence_result(self, profile) -> dict:
        """无足够历史数据时的低可信度结果"""
        return {
            "similar_projects_count": 0,
            "confidence": "low",
            "estimated_total_hours": None,
            "estimated_total_hours_range": [None, None],
            "phase_predictions": [],
            "estimated_success_rate": None,
            "bottleneck_phase": None,
            "recommended_journal_tier": profile.target_journal_tier,
            "risk_factors": ["无历史类似项目, 无法评估风险"],
            "similar_projects_summary": "无足够历史数据。运行至少 3 个项目后自动积累。",
        }
```

### 3.2 ProjectProfile 推断

从用户请求中自动推断项目特征，不需要人工填写：

```python
def infer_profile(user_request: str, division: str) -> ProjectProfile:
    """从用户请求文本中推断项目特征"""
    req = user_request.lower()
    
    # 研究类型推断
    if any(w in req for w in ["预测", "predict", "模型", "model", "分类", "classif"]):
        research_type = "prediction"
    elif any(w in req for w in ["因果", "causal", "效应", "effect", "关联", "association"]):
        research_type = "causal_inference"
    elif any(w in req for w in ["综述", "review", "系统评价", "meta"]):
        research_type = "systematic_review"
    else:
        research_type = "exploratory"
    
    # 数据源推断
    data_sources = {
        "charls": "CHARLS", "clhls": "CLHLS", "hrs": "HRS", "elsa": "ELSA",
        "mimic": "MIMIC-IV", "seer": "SEER", "nhanes": "NHANES",
        "uk biobank": "UK_Biobank",
    }
    data_source = "unknown"
    for keyword, name in data_sources.items():
        if keyword in req:
            data_source = name
            break
    
    # 期刊Tier推断
    if any(w in req for w in ["lancet", "nature", "jama", "bmj", "european urology"]):
        target_tier = 1
    elif any(w in req for w in ["bmc", "plos", "frontiers"]):
        target_tier = 3
    else:
        target_tier = 2  # 默认Tier 2
    
    return ProjectProfile(
        division=division,
        research_type=research_type,
        data_source=data_source,
        target_journal_tier=target_tier,
        estimated_sample_size="medium(1000-10000)",  # 默认, 后续可从数据评估中更新
    )
```

---

## 四、自适应调度器设计

### 4.1 设计原理

钱学森最优控制：**基于系统模型，在约束条件下找到使性能指标最优的控制策略。**

```python
# engine/core/adaptive_scheduler.py

class AdaptiveScheduler:
    """
    自适应调度器 — 最优控制模块。
    
    基于 RunAnalyzer 的统计数据, 对新 Phase 的执行策略做自适应调整。
    对应钱学森最优控制思想: "基于系统辨识结果, 动态调整控制参数。"
    
    用法:
        analyzer = RunAnalyzer(...)
        analyzer.load(days=90)
        scheduler = AdaptiveScheduler(analyzer)
        decision = scheduler.decide("execution", division="geriatrics")
        # decision["action"] → "add_redundancy" | "split_task" | "normal"
    """
    
    def __init__(self, analyzer: 'RunAnalyzer'):
        self.analyzer = analyzer
    
    def decide(self, phase_id: str, division: str = "geriatrics") -> dict:
        """
        基于运行数据, 对即将执行的 Phase 做出调度决策。
        
        Returns:
            {
                "action": "normal|add_redundancy|split_task|degrade_model|skip_gate_llm",
                "reason": str,
                "params": dict,  # 动作参数
            }
        """
        stats = self._get_phase_stats(phase_id, division)
        
        # 决策规则 (优先级从高到低)
        
        # 规则1: 如果该 Phase 历史一次通过率 < 40% → 增加冗余
        if stats.get("pass_rate", 100) < 40:
            return {
                "action": "add_redundancy",
                "reason": f"Phase {phase_id} 历史通过率仅 {stats['pass_rate']}%, "
                          f"建议增加一个交叉验证 Agent",
                "params": {"extra_agent": "cross-validator"},
            }
        
        # 规则2: 如果该 Phase 平均耗时超过目标 1.5 倍 → 拆分任务或增加并行
        if stats.get("avg_hours", 0) > stats.get("target_hours", 1) * 1.5:
            return {
                "action": "split_task",
                "reason": f"Phase {phase_id} 平均耗时 {stats['avg_hours']:.1f}h, "
                          f"超过目标 {stats['target_hours']}h 的 1.5 倍",
                "params": {"suggested_parallelism": min(stats.get("current_parallelism", 1) + 2, 5)},
            }
        
        # 规则3: 如果该 Agent 降级率 > 20% → 考虑切换默认模型
        if stats.get("degraded_rate", 0) > 20:
            return {
                "action": "degrade_model",
                "reason": f"Phase {phase_id} 的 Agent 降级率 {stats['degraded_rate']}% 偏高",
                "params": {"suggested_model": "claude-haiku-4-5-20251001"},
            }
        
        # 规则4: 如果该 Phase 的历史 Gate LLM 审查通过率 > 95% → 可跳过 LLM 审查
        if stats.get("llm_gate_pass_rate", 0) > 95 and stats.get("sample_size", 0) >= 10:
            return {
                "action": "skip_gate_llm",
                "reason": f"Phase {phase_id} 的 LLM Gate 审查通过率 {stats['llm_gate_pass_rate']}%, "
                          f"可信任 auto check 结果, 跳过 LLM 审查以节省 token",
                "params": {},
            }
        
        return {"action": "normal", "reason": "无需调整", "params": {}}
    
    def _get_phase_stats(self, phase_id: str, division: str) -> dict:
        """从 RunAnalyzer 获取指定 Phase 的历史统计数据"""
        # 利用 RunAnalyzer 已有的聚合能力
        phase_stats_list = self.analyzer._phase_stats()
        
        for ps in phase_stats_list:
            if ps["phase_id"] == phase_id:
                return {
                    "pass_rate": ps.get("pass_rate", 100),
                    "avg_hours": self._parse_hours(ps.get("avg", "0h")),
                    "target_hours": self._parse_hours(ps.get("target", "4h")),
                    "sample_size": ps.get("count", 0),
                    "degraded_rate": self._get_degraded_rate(phase_id, division),
                    "llm_gate_pass_rate": self._get_llm_gate_pass_rate(phase_id),
                    "current_parallelism": self._get_current_parallelism(phase_id),
                }
        return {}
```

### 4.2 调度决策 → 编排器行为

调度器的输出被编排器消费，在 Phase 执行前做出调整：

```
_execute_phase() 前:
    │
    ├─ AdaptiveScheduler.decide(phase_id) → action
    │
    ├─ action="normal"         → 标准流程
    ├─ action="add_redundancy" → 为该 Phase 增加一个 cross-validator Agent
    ├─ action="split_task"     → 将大任务拆分为子任务并行执行
    ├─ action="degrade_model"  → 从下一轮开始使用 Haiku
    └─ action="skip_gate_llm"  → Gate 检查时跳过 LLM 审查, 仅做 auto checks
```

---

## 五、Phase 0 SDS 集成

在 `_run_system_design()` 中注入预测结果，使 SDS 包含历史参考数据：

```python
def _run_system_design(self, user_request: str, project_id: str) -> str:
    """Phase 0: SDS 生成 — 现在包含系统辨识参考数据"""
    
    # 🆕 加载运行数据
    from .run_analyzer import RunAnalyzer
    from .project_predictor import ProjectPredictor, ProjectProfile, infer_profile
    
    analyzer = RunAnalyzer(log_dir=self.config.run_log_dir)
    n_records = analyzer.load(days=90)
    
    historical_context = ""
    if n_records > 0:
        profile = infer_profile(user_request, self.active_division)
        predictor = ProjectPredictor(analyzer)
        prediction = predictor.predict(profile)
        
        if prediction["confidence"] != "low":
            historical_context = f"""

## 📊 系统辨识参考数据 (基于 {prediction['similar_projects_count']} 个类似项目)

| 指标 | 预测值 | 范围 |
|------|--------|------|
| 预计总耗时 | {prediction['estimated_total_hours']}h | {prediction['estimated_total_hours_range']} |
| 预计成功率 | {prediction['estimated_success_rate']}% | — |
| 历史瓶颈Phase | {prediction['bottleneck_phase']} | — |
| 建议期刊Tier | Tier {prediction['recommended_journal_tier']} | 原始目标 Tier {profile.target_journal_tier} |
| 预测可信度 | {prediction['confidence']} | — |

### 风险因子
{chr(10).join('- ' + r for r in prediction['risk_factors'])}

---
"""
    
    prompt = f"""... (existing SDS prompt) ...
{historical_context}
..."""
    
    return self._call_agent(...)
```

---

## 六、编排器集成点

### 6.1 __init__ 新增

```python
class ResearchOrchestrator:
    def __init__(self, config=None):
        # ... 现有初始化 ...

        # 🆕 系统辨识模块
        self.run_analyzer = None    # 懒加载, 首次使用时初始化
        self.project_predictor = None
        self.adaptive_scheduler = None
    
    def _ensure_analyzer_loaded(self):
        """懒加载 RunAnalyzer, 首次调用时从 JSONL 加载数据"""
        if self.run_analyzer is not None:
            return
        from .run_analyzer import RunAnalyzer
        self.run_analyzer = RunAnalyzer(
            log_dir=getattr(self.config, 'run_log_dir', None) or 
                     self.config.project_root / "outputs" / "run_logs"
        )
        self.run_analyzer.load(days=90)
```

### 6.2 _run_project_workflow 集成自适应调度

```python
# 在 _execute_phase 调用前:
if phase_def.get("debate_mode") or phase_def.get("two_round"):
    # 复杂模式不过度干预
    pass
else:
    self._ensure_analyzer_loaded()
    if self.run_analyzer and len(self.run_analyzer.records) >= 10:
        if self.adaptive_scheduler is None:
            from .adaptive_scheduler import AdaptiveScheduler
            self.adaptive_scheduler = AdaptiveScheduler(self.run_analyzer)
        
        decision = self.adaptive_scheduler.decide(phase_id, self.active_division)
        if decision["action"] != "normal":
            print(f"  🎯 自适应调度: {decision['action']} — {decision['reason']}")
            if decision["action"] == "add_redundancy":
                # 增加一个 cross-validation Agent
                ...
```

---

## 七、测试方案

### 7.1 单元测试

| 测试 | 输入 | 期望 |
|------|------|------|
| 相似度评分 — 完全相同 | profile=(geriatrics, prediction, CHARLS, 2); record 完全匹配 | score >= 9 |
| 相似度评分 — 事业部匹配 | profile=(geriatrics, ...); record 是 urology | score=0 (事业部不匹配) |
| 预测 — 足够数据 | ≥5 个类似项目 | confidence=high, 所有字段有值 |
| 预测 — 不足数据 | 1-2 个类似项目 | confidence=medium |
| 预测 — 无数据 | 0 记录 | confidence=low, hours=None |
| 瓶颈识别 | 3个项目, execution 平均耗时最高 + 通过率最低 | bottleneck=execution |
| 期刊建议 | Tier1 目标, 历史类似项目成功率 20% | recommended_tier=2 |
| ProjectProfile 推断 | "用 CHARLS 数据预测衰弱转换" | research_type=prediction, data_source=CHARLS |

### 7.2 集成测试

| 场景 | 期望 |
|------|------|
| SDS 生成 — 有历史数据 | SDS 包含"系统辨识参考数据"表格 |
| SDS 生成 — 无历史数据 | SDS 不崩溃, 无历史数据部分 |
| 自适应调度 — 通过率低 | decision.action = "add_redundancy" |
| 自适应调度 — 正常 | decision.action = "normal" |

---

## 八、文件改动清单

| 文件 | 改动类型 | 改动内容 | 预计行数 |
|------|---------|---------|---------|
| `engine/core/project_predictor.py` | **新文件** | ProjectPredictor 类 + ProjectProfile + infer_profile() | ~200 |
| `engine/core/adaptive_scheduler.py` | **新文件** | AdaptiveScheduler 类 + 决策规则 | ~120 |
| `engine/core/orchestrator_graph.py` | 修改 | __init__ 初始化系统辨识模块; SDS 生成注入预测; Phase 执行前调用自适应调度 | +50 |
| `engine/core/run_analyzer.py` | 修改 | 新增 `_parse_hours()` 辅助方法; 暴露更多聚合接口 | +20 |
| `tests/test_system_identification.py` | **新文件** | ProjectPredictor + AdaptiveScheduler 测试 | ~180 |

---

## 九、与其他模块的关系

```
┌──────────────────────────────────────────────────┐
│                 系统辨识与最优控制                   │
│                                                  │
│  RunLog 采集 (已有)                               │
│      │                                           │
│      ▼                                           │
│  RunAnalyzer (已有) — 读取/聚合/报告              │
│      │                                           │
│      ├──→ ProjectPredictor (🆕) — 传递函数建模    │
│      │       │                                   │
│      │       └──→ Phase 0 SDS 注入预测数据         │
│      │                                           │
│      └──→ AdaptiveScheduler (🆕) — 最优控制       │
│              │                                   │
│              └──→ Phase 执行前自适应调整            │
│                                                  │
│  反馈闭环:                                        │
│  调整后的执行结果 → 新 RunLog → 更新统计            │
│  → 下次预测更准确 (系统持续自进化)                  │
└──────────────────────────────────────────────────┘

模块间交互:
- 模块一 (反馈控制): 自适应调度的决策被 Gate 结果验证
- 模块三 (辩论): 辩论 Phase 不参与自适应调度 (保持完整性)
- 模块五 (基线管理): 预测结果可存入项目基线供后续对比
```

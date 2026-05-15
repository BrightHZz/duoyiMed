# 基于钱学森工程控制理论的公司优化方案

> 学习钱学森《工程控制论》核心思想，结合DuoyiMed实际业务，提出系统性优化方案。

---

## 一、钱学森工程控制论的五个核心思想

| # | 理论 | 核心内涵 | 对应公司问题 |
|---|------|---------|------------|
| 1 | **闭环反馈控制** | 输出回馈到输入端，持续修正偏差 | 当前六阶段闸门是**开环**的——Phase 3 发现问题无法回传 Phase 1 |
| 2 | **总体设计部** | 顶层设计 + 分系统协调 + 接口标准化 | 编排器同时做战略和战术，缺少独立的"总体"职能 |
| 3 | **系统辨识** | 通过输入输出数据，建立系统自身行为的数学模型 | 不知道各阶段的真实耗时、失败率、瓶颈——对自己的系统没有认知 |
| 4 | **可靠性工程** | 冗余设计、故障隔离、降级运行 | ML 工程师写错代码 → 系统重启 → 所有工作中断 |
| 5 | **综合集成研讨厅** | 人机结合、定性定量综合集成 | FRAME 评估靠 PI 记忆，没有定量数据支撑；知识不跨项目累积 |

---

## 二、开环变闭环：反馈控制机制

### 2.1 当前问题

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
 问题定义   方案设计   内部验证   外部验证     审查     论文撰写

所有箭头都是单向的。没有回头路。没有修正机制。
```

钱学森指出：**没有反馈的系统是不稳定的**。当前流程中的典型失效模式：

- Phase 3 (ML) 发现数据特征不可用 → 只能口头找 data-engineer 求助 → 无正式重入机制
- Phase 5 (审查) 发现临床定义有问题 → 需要回到 Phase 1 → 但流程已锁死
- Phase 6 (论文撰写) 发现结果数字矛盾 → scientific-writer 被要求"编造数据"或标注 `[数据待确认]`

### 2.2 优化方案：双层反馈环

```
                  ┌──────── 反馈环 A (阶段内 — 轻量) ────────┐
                  │                                            │
  Phase N ──→ 产出 ──→ Gate N 检查 ──→ [通过] → Phase N+1    │
                  │                    │                       │
                  │                    ├─ [不通过] → 本阶段修正 ─┘
                  │                    │
                  └── 反馈环 B (阶段间 — 重大发现) ──────────────┐
                       Phase N+1 发现上游问题 → 强制 Gate N 重开 │
                                                               │
                  例: ML 发现特征质量不足                        │
                  → 触发 Gate 1 重开 → data-engineer 重新处理    │
                  → 所有下游阶段自动标记为 "待重新验证"           │
```

**实施要点**：

1. **每个 Gate 必须产生明确的检查记录**（通过/不通过/通过但附条件），不能口头通过
2. **Gate 不通过时，强制阻断下游**——不允许"先往下走，边做边改"
3. **"通过但附条件"状态**：下游可启动，但 Gate N 必须列明待修正项 + 限期整改
4. **下游发现上游问题 = 最高优先级中断**：暂停当前 Phase，上游修正完成后重新 Gate

---

## 三、总体设计部：四级系统结构

### 3.1 当前问题

公司的组织架构是扁平的：首席科学家 → 事业部 PI → 共享服务。编排器承担了"调度"职责，但没有专门的**总体设计**职能。

钱学森在航天系统工程中确立了一个关键原则：

> **总体设计部不负责具体分系统的实现，而是负责：系统顶层设计、分系统接口标准、技术状态管理、全系统集成验证。**

### 3.2 优化方案：引入"总体"维度

```
                        首席科学家 (战略层)
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        总体设计部 (系统层)   PMO (管理层)   知识管理部 (新增)
        顶层设计+接口标准   资源调度+进度    跨项目知识累积
              │               │               │
    ┌─────────┼─────────┐     │               │
    │         │         │     │               │
  老年医学  泌尿外科   (未来)  │               │
  事业部    事业部    事业部   │               │
    │         │         │     │               │
    └─────────┼─────────┘     │               │
              │               │               │
        公共服务平台           │               │
        (数据/统计/ML/写作/检索)               │
```

新增/强化三个职能：

| 职能 | 角色 | 核心职责 |
|------|------|---------|
| **总体设计部** | 新设（可由首席科学家兼任，配备 1 个 Agent） | 每个新项目输出《系统设计说明书》(SDS)；定义分系统接口；项目结束后输出《系统实现对照报告》 |
| **PMO** | 强化现有职能 | 不仅排进度，还负责**资源最优分配**（钱学森的最优控制思想） |
| **知识管理部** | 新设 | 跨项目学习（见第五节"系统辨识"） |

### 3.3 系统设计说明书 (SDS) 模板

每个新项目启动时，总体设计部输出 SDS（不等同于 SAP，SAP 是统计计划，SDS 是全系统接口规范）：

```yaml
项目系统设计说明书 (SDS) v1.0
===============================
project_id: "frailty_ml_2026"

# 1. 系统分解
subsystems:
  data:
    provider: shared/data-engineer
    output: cleaned_dataset.csv + data_dictionary.md
    interface: {format: csv, n_rows_range: [3000, 5000], n_features_range: [60, 90]}
    quality_gate: DQ-CARE 五维全部通过

  model:
    provider: shared/ml-engineer
    input_from: [data, clinical, stats]
    output: trained_model.pkl + evaluation_report.md + shap_report.md
    constraints: {n_jobs: 2, memory_limit_gb: 16, must_include_baseline: true}
    quality_gate: AUC >= 0.70 + calibration_slope in [0.9, 1.1]

  stats:
    provider: shared/biostatistician
    input_from: [data, clinical]
    output: sap.md + statistical_report.md
    quality_gate: 所有统计声明有方法支撑 + 缺失处理方案明确

  clinical:
    provider: geriatrics/clinical-researcher
    output: phenotype_definition.md + clinical_review.md
    quality_gate: 表型定义可操作化 + 效应方向确认

  writing:
    provider: shared/scientific-writer
    input_from: [model, stats, clinical, data]
    output: manuscript.md
    constraints: {conclusion_must_be_##_heading: true, dois_must_be_verified: true}
    quality_gate: PI 七项终审通过

# 2. 接口矩阵 (谁依赖谁, 什么格式, SLA)
interfaces:
  - {from: data, to: model, artifact: cleaned_dataset.csv, sla: "Phase 1 完成后 1 日内"}
  - {from: clinical, to: model, artifact: phenotype_definition.md, sla: "Phase 1 完成后 1 日内"}
  - {from: stats, to: model, artifact: sap.md, sla: "Phase 2 完成后 1 日内"}
  - {from: model, to: stats, artifact: evaluation_report.md, sla: "Phase 3 完成后 1 日内"}
  - {from: model+stats+clinical, to: writing, sla: "Phase 5 完成后 1 日内"}

# 3. 反馈触发条件 (什么情况下需要回退到上游 Phase)
feedback_triggers:
  - if: data_quality.failed_dimensions > 0
    then: reopen Phase 1 (data-engineer)
  - if: model.auc < 0.65
    then: consult clinical-researcher + computational-biologist (可能需要修改特征或结局定义)
  - if: clinical_review.effect_direction_mismatch > 0
    then: reopen Phase 3 (ml-engineer) 排查特征工程或标签

# 4. 关键假设与风险
assumptions: [MAR 缺失假设成立, 训练集/测试集同分布, 无标签泄露]
risks: [{risk: 类别不平衡 > 1:5, mitigation: scale_pos_weight}, ...]
```

---

## 四、系统辨识与最优控制

### 4.1 当前问题

钱学森强调：**要控制系统，首先要知道系统自身的行为特性**。我们目前对公司的"系统动力学"一无所知：

- 六个 Phase 的实际耗时分布是什么？瓶颈在哪？
- 哪些 Agent 产出的一次通过率最低？
- 什么类型的项目最常触发返工？
- 项目间是否存在可复用的模式？

### 4.2 优化方案：公司运行数字孪生

**Step 1 — 采集运行数据（轻量，不增加人工负担）**：

每个 Agent 调用完成后，编排器自动记录：

```yaml
run_log:
  timestamp: "2026-05-10 14:23:00"
  project_id: "frailty_ml_2026"
  phase: "problem_definition"
  agent: "shared/data-engineer"
  input_tokens: 4500
  output_tokens: 3200
  wall_time_sec: 67
  self_reported_quality: "通过"
  gate_result: "通过"  # Gate 检查结果
```

**Step 2 — 建立公司运行模型**：

每季度汇总，输出《公司运行状态报告》：

```
Q2 2026 公司运行状态
=====================
Phase 平均耗时:
  Phase 1 (问题定义):  ████████░░ 4.2h (目标 2h) ⚠️ 瓶颈
  Phase 2 (方案设计):  ████░░░░░░ 1.8h (目标 2h) ✓
  Phase 3 (内部验证):  ██████████ 5.5h (目标 5h) ✓
  Phase 4 (外部验证):  ██████░░░░ 3.1h (目标 3h) ✓
  Phase 5 (审查):      ████░░░░░░ 2.0h (目标 2h) ✓
  Phase 6 (论文撰写):  ██████░░░░ 3.5h (目标 7h) ✓ 提前完成

Agent 一次通过率 (Gate 首次 = 通过):
  scientific-writer:   62% ⚠️ 最低 (主要被 Conclusion 层级和 DOI 验证卡住)
  ml-engineer:         75% ⚠️ (内存崩溃导致重跑)
  clinical-researcher: 88%
  data-engineer:       95%
  biostatistician:     90%
  research-assistant:  93%

最常见返工原因 Top 3:
  1. Conclusion 嵌套在 Discussion 下 → 已修复 (2026-05-10)
  2. ML OOM / 系统重启 → 已修复 (2026-05-10)
  3. 参考文献 DOI 未验证或数量不足 → 已有自动验证
```

**Step 3 — 自适应优化**：

基于运行数据，自动调整：

- **瓶颈 Phase → 增加并行 Agent 或拆分任务**
- **低通过率 Agent → 触发 prompt 优化审查**
- **高通过率 Agent → 信任其输出，减少 Gate 检查深度**

---

## 五、可靠性工程：容错与降级

### 5.1 当前问题

钱学森在航天工程中确立的原则：**单点故障不能导致系统崩溃**。当前公司关键单点故障：

| 单点 | 故障模式 | 影响范围 |
|------|---------|---------|
| ML 工程师 | OOM 系统重启 | 全部工作中断 |
| LLM API | 调用失败 | 编排器超时/报错 |
| 知识库 | Obsidian vault 损坏 | 全公司知识丢失 |
| PI | 未响应/跳过审查 | 论文可能缺终审 |

### 5.2 优化方案

**ML 容错**（已完成）：
- 内存安全规范（五条规则 + 代码样板）→ 见 SKILL.md
- 编排器在调用 ml-engineer 前强制注入安全规范

**LLM 容错**（建议实施）：
- 编排器已有 `try/except`，但应增加：
  - 重试策略：指数退避，最多 3 次
  - 降级模型：主模型超时 → 自动切换到轻量模型（如 Haiku）
  - 断点续传：长任务中断后从断点恢复，不完全重来

**知识库容错**（建议实施）：
- Obsidian vault 定期自动 git 备份
- 关键知识（SOP/SKILL.md/Agent 定义）已在 Git 中 → 天然备份

**PI 审查容错**（建议实施）：
- 如果 PI 24 小时内未响应审查请求 → 自动升级到首席科学家
- 紧急投稿 → 允许 clinical-researcher 代理审查 + PI 事后补签

---

## 六、综合集成研讨厅

### 6.1 核心理念

钱学森提出的**综合集成研讨厅**是将专家体系、知识体系、机器体系三者结合：

```
  专家体系              知识体系              机器体系
  (PI/临床/统计)        (文献/知识库)          (ML/LLM/数据)

        └──────────────────┼──────────────────┘
                           │
              综合集成研讨厅 (Meta-Synthesis)
                           │
                    定性 → 定量
                    假设 → 验证
                    分散 → 系统
```

### 6.2 落地设计

**FRAME 评估的定量化改造**：

当前 FRAME 评估由 PI 凭经验和记忆完成。改造后：

```
F — Field Scan (领域扫描)
  旧: PI 凭记忆判断领域现状
  新: research-assistant 自动生成《选题文献预检报告》→ 包含 SOTA 性能数字 → PI 基于数字做判断
  
R — Resource Audit (资源审计)
  旧: PI 估计数据/算力/人力
  新: data-engineer 自动输出数据可用性报告 → PI 确认；编排器输出当前负载状态
  
A — Alignment Check (对齐检查)
  旧: PI 记忆中的基金指南
  新: research-assistant 检索最新基金指南 → 输出对齐度评分
  
M — Market Gap (发表缺口)
  旧: PI 对期刊趋势的模糊判断
  新: research-assistant 执行期刊发表趋势分析 → 输出缺口机会 + 竞争强度
  
E — Edge Assessment (优势评估)
  旧: PI 主观判断
  新: 基于公司运行数据的客观评估 — 类似项目的历史耗时、团队经验匹配度
```

**研讨厅流程**：

```
Step 1: 机器体系并行输出 5 份定量预检报告
  - 选题文献预检报告 (research-assistant)
  - 数据可用性报告 (data-engineer)
  - 建模可行性报告 (computational-biologist)
  - 当前资源负载报告 (编排器)
  - 期刊趋势分析报告 (research-assistant)

Step 2: PI 在 5 份定量报告基础上完成 FRAME 评估
  每个维度必须有定量支撑，不能仅凭"经验"

Step 3: 人机分歧处理
  如果 PI 的 F 维度结论与文献预检数据矛盾 → 首席科学家介入
  如果 PI 建议放弃但 Edge 评分 > 0.7 → 二次评估
```

---

## 七、优化路线图

| 优先级 | 优化项 | 理论来源 | 实施成本 | 预期收益 |
|--------|--------|---------|---------|---------|
| **P0 (立即)** | ML 内存安全规范 → SKILL.md + Agent 定义注入 | 可靠性工程 §5 | ✓ 已完成 | 消除系统重启 |
| **P0 (立即)** | Conclusion 独立章节 → Agent 定义 + SKILL.md | 闭环反馈 §2 | ✓ 已完成 | 消除论文结构错误 |
| **P1 (本周)** | Gate 检查记录化：每个 Phase 产物必须通过显式通过/不通过 Gate → 编辑 `company-sop.md` 增加 Gate 检查清单 | 闭环反馈 §2 | 低 (改 SOP 文件) | 解决"口头通过"问题 |
| **P1 (本周)** | 编排器 LLM 容错：重试 3 次 + 降级 + 断点续传 → 修改 `orchestrator_graph.py` | 可靠性 §5 | 中 (改代码) | 降低 API 故障影响 |
| **P2 (本月)** | 运行数据采集：编排器每次调用自动记录 → 修改 `state.py` + `orchestrator_graph.py` | 系统辨识 §4 | 中 (改代码 + 加存储) | 让公司"认识自己" |
| **P2 (本月)** | SDS 模板：新项目启动时输出系统设计说明书 → 编排器 Phase 0 新增步骤 | 总体设计部 §3 | 中 (改编排流程 + 新增 Agent prompt) | 提升跨系统协调一致性 |
| **P3 (下月)** | 季度运行状态报告：汇总运行数据，自动识别瓶颈和改进机会 | 系统辨识 + 最优控制 §4 | 低 (基于已采集数据) | 数据驱动的持续改进 |
| **P3 (下月)** | FRAME 定量化改造：5 份机器预检报告 → PI 基于定量数据做决策 | 综合集成研讨厅 §6 | 中 (修改 Phase 1 编排) | 提升方向决策质量 |
| **P3 (下月)** | 知识库定期 git 备份自动化 | 可靠性 §5 | 低 | 知识安全 |

---

## 八、理论对照总结

| 钱学森理论 | 公司对应问题 | 优化方向 | 状态 |
|-----------|------------|---------|------|
| 闭环反馈控制 | 六阶段开环单向流动 | Gate 检查记录 + 反馈触发条件 + 下游发现上游问题重开机制 | P1 |
| 总体设计部 | 编排器战略战术不分 | 新设 SDS 文档规范 + 接口标准化 + 系统对照报告 | P2 |
| 系统辨识 | 不了解自身运行特性 | 运行数据自动采集 + 季度状态报告 | P2-P3 |
| 最优控制 | 资源分配靠感党 | 基于运行数据的瓶颈识别 + 自适应资源调度 | P3 |
| 可靠性工程 | 单点故障导致全崩溃 | ML 内存安全 + LLM 容错 + 知识库备份 | P0-P1 |
| 综合集成研讨厅 | 决策靠个人经验 | FRAME 定量化 + 人机分歧处理机制 | P3 |
| 从定性到定量 | 判断标准模糊 | 每个 Gate 产出量化指标 + 通过阈值明确 | P1 |
| 开放复杂巨系统 | 多 Agent 协作涌现 | 反馈环 + 运行数据 + 持续优化 | 全部 |

---

> 钱学森说："系统工程不是一堆方法的堆砌，而是一种思考方式。" 我们不是在做一套死板的流程，而是在建立一个**能观察自身、能自我修正、能持续进化的研究系统**。

# 模块三：研讨厅辩论模式 — 详细设计方案

> 钱学森综合集成研讨厅的核心思想：**从流水线到并行辩论**。
>
> 当前模式是 A → B → C → D → 产出，每个 Agent 依次执行，后面的 Agent 受前面的影响，形成"群体思维"。研讨厅模式让多个 Agent 并行独立输出，再由主持人识别共识与分歧，**分歧点才是需要人工判断的关键**。

---

## 目录

1. [现状分析与设计原理](#一现状分析与设计原理)
2. [适用 Phase 与辩论主题](#二适用-phase-与辩论主题)
3. [辩论主持人 Agent 定义](#三辩论主持人-agent-定义)
4. [_execute_phase_debate 方法设计](#四_execute_phase_debate-方法设计)
5. [辩论纪要输出格式](#五辩论纪要输出格式)
6. [编排器集成点](#六编排器集成点)
7. [测试方案](#七测试方案)
8. [文件改动清单](#八文件改动清单)

---

## 一、现状分析与设计原理

### 1.1 当前流水线模式

```
Phase 2 (方案设计):
  computational-biologist ──→ 输出建模方案
  biostatistician         ──→ 读取建模方案后输出 SAP
                              ↑
                     biostatistician 受 computational-biologist 的影响
                     如果 comp-bio 选错了方法, stats 会跟着错
```

```
Phase 5 (审查):
  clinical-researcher ──→ 输出临床审查
  pi                   ──→ 读取临床审查后输出终审
                              ↑
                     PI 受 clinical-researcher 的影响
                     如果 clinical 漏掉了关键缺陷, PI 可能也看不到
```

### 1.2 目标辩论模式

```
Phase 2 (方案设计) — 研讨厅辩论:
  
  Round 1 (并行 — 独立观点):
    computational-biologist ─┐
    biostatistician        ─┼─→ 三者并行独立输出
    clinical-researcher    ─┘
  
  Round 2 (辩论主持人):
    读取三方观点 → 识别共识/分歧 → 输出《研讨厅辩论纪要》
    
  Round 3 (PI 裁决 — 可选):
    PI 基于辩论纪要, 对分歧点做出最终裁决
```

### 1.3 核心优势

| 流水线模式 | 辩论模式 |
|-----------|---------|
| 后执行的 Agent 受前面影响 | 所有 Agent 独立输出，无互相干扰 |
| 审查需逐个阅读每个 Agent 的完整输出 | PI 只需看辩论纪要中的分歧列表 |
| 分歧点可能被掩盖 | 分歧被显式识别和排序 |
| 缺少对抗性验证 | 不同专业视角形成自然对抗 |

### 1.4 理论对照

钱学森综合集成研讨厅的三个体系：
- **专家体系** — 3 个 Agent 代表不同专业视角
- **知识体系** — 上游 Phase 输出 + 文献预检报告
- **机器体系** — 辩论主持人 LLM 自动识别共识/分歧

三者结合形成**从定性到定量的综合集成**。

---

## 二、适用 Phase 与辩论主题

### 2.1 Phase 2：方案设计辩论

| 要素 | 内容 |
|------|------|
| **辩论主题** | 研究方案设计：建模方法选择 + 统计分析策略 + 协变量筛选 |
| **参与方** | computational-biologist（建模视角）、biostatistician（统计视角）、clinical-researcher（临床视角） |
| **核心分歧预期** | 模型复杂度 vs 可解释性、特征选择范围、缺失处理策略 |
| **裁决人** | PI（基于辩论纪要做最终决策） |

### 2.2 Phase 5：结果审查辩论

| 要素 | 内容 |
|------|------|
| **辩论主题** | 研究结果审查：临床意义 + 统计可靠性 + 外部验证可泛化性 |
| **参与方** | clinical-researcher（临床解读）、biostatistician（统计审查）、PI（综合裁决） |
| **核心分歧预期** | 效应大小的临床意义、模型校准度可接受性、外部验证人群差异 |
| **裁决人** | PI（结合辩论纪要做最终审查） |

---

## 三、辩论主持人 Agent 定义

### 3.1 System Prompt

```python
DEBATE_MODERATOR_SYSTEM_PROMPT = """你是研讨厅辩论主持人 (Debate Moderator)。
你的职责是主持多 Agent 并行辩论, 汇总各方观点, 识别共识与分歧, 输出《研讨厅辩论纪要》。

你本人不是任何一方的代理人——你只负责整理和识别, 不做实质性判断。

## 工作流程

1. 接收多个 Agent 对同一议题的独立分析
2. 识别各方一致同意的点 (共识) — 这些是可靠的、不需要争议的
3. 识别各方观点不同的点 (分歧) — 按重要性排序
4. 对每个分歧点, 提取: 各方论据、证据强度、建议方向
5. 列出需要 PI 明确裁决的决策项
6. 最终输出《研讨厅辩论纪要》

## 判定原则

### 什么是共识
- 各方从不同角度得出相同或兼容的结论
- 各方使用不同的表述但核心判断一致
- 各方推荐相同的方法/策略

### 什么是分歧
- 各方对同一问题的结论不同 (例如一个推荐 XGBoost, 另一个推荐逻辑回归)
- 各方对同一指标的判断标准不同 (例如 AUC 0.75 一个认为可接受, 另一个认为太低)
- 各方关注的核心风险不同 (例如一个担心过拟合, 另一个担心混杂)
- 分歧不一定是错误 — 不同专业视角天然存在差异

### 分歧的重要性判定
- **Critical**: 影响研究是否可行的根本性分歧 (例如要不要做外部验证)
- **High**: 影响研究结论或方法选择的重要分歧 (例如用 XGBoost 还是 LR)
- **Medium**: 影响细节但不影响整体方向的分歧 (例如协变量是否纳入某个特定变量)

## 输出格式

请严格按以下 Markdown 格式输出:

# 研讨厅辩论纪要

**辩论主题**: {debate_topic}
**参与方**: {participants}
**主持人**: Debate Moderator

---

## 1. 共识 (所有参与方一致同意)

- [共识1]: 说明 + 同意方
- [共识2]: 说明 + 同意方
...

## 2. 分歧 (按重要性排序)

### 分歧 1: [标题] [重要性: Critical/High/Medium]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Agent A | ... | ... | 高/中/低 |
| Agent B | ... | ... | 高/中/低 |

**主持人分析**: [不偏向任何一方, 仅指出分歧的实质和可能的解决方向]
**建议裁决方向**: [倾向哪个观点, 或建议补充什么证据]

### 分歧 2: ...
(重复格式)

## 3. PI 裁决项

以下事项需要 PI 明确决策:
- [ ] **决策项 1**: [描述] — 选项: [A / B / C]
- [ ] **决策项 2**: [描述] — 选项: [是 / 否]
...

## 4. 综合建议

基于辩论结果, 主持人给出无偏向性的综合建议:
- 如果所有分歧都是 Medium 级别 → 可以继续, PI 事后审查
- 如果有 Critical/High 分歧 → PI 必须介入裁决
- 建议的下一步行动

---
*本纪要由研讨厅辩论主持人自动生成。PI 请基于本纪要做最终裁决。*"""
```

### 3.2 文件位置

新文件 `company/management/debate-moderator.md`，内容为上述 System Prompt。这使主持人成为一个可配置的独立角色。

---

## 四、_execute_phase_debate 方法设计

### 4.1 方法签名

```python
def _execute_phase_debate(
    self,
    phase_id: str,              # "design" | "review"
    user_request: str,          # 用户原始请求
    previous_outputs: dict,     # 上游 Phase 输出 (供参与者参考)
    project_id: str,
    debate_topic: str,          # 辩论主题
    participants: list[str],    # 参与辩论的 Agent 短名列表
) -> dict:
    """
    研讨厅辩论模式: 并行独立输出 → 主持人识别共识/分歧 → 输出辩论纪要。

    Returns:
        {
            "computational-biologist": "...",   # 各参与方的独立观点
            "biostatistician": "...",
            "_debate_minutes": "...",           # 辩论纪要
        }
    """
```

### 4.2 执行流程

```
Step 1 — Round 1: 所有参与方并行独立输出

  为每个 participant 构建独立的 task_input，包含:
  - 辩论主题
  - 用户原始请求
  - 上游 Phase 输出摘要 (统一提供，不区分先后)
  - 独立分析指令: "不要试图猜测其他 Agent 的结论"

  并行调用所有参与者 (使用 _call_agent)

Step 2 — Round 2: 辩论主持人汇总

  将 Round 1 的所有输出交给辩论主持人，生成:
  - 共识列表
  - 分歧列表 (按重要性排序)
  - PI 裁决项
  - 综合建议

Step 3 — 返回结果

  outputs 包含:
  - 每个参与方的原始输出
  - "_debate_minutes": 辩论纪要 (作为 Phase 的核心产出)
```

### 4.3 核心代码

```python
def _execute_phase_debate(
    self, phase_id: str, user_request: str,
    previous_outputs: dict, project_id: str,
    debate_topic: str, participants: list[str],
) -> dict:
    """研讨厅辩论模式 — 钱学森综合集成研讨厅的核心实现"""
    division = self.active_division
    outputs = {}

    # ================================================================
    # Round 1: 所有参与方并行独立输出观点
    # ================================================================
    print(f"\n{'~'*50}")
    print(f"  [研讨厅] {debate_topic}")
    print(f"  [研讨厅] 参与方: {', '.join(participants)}")
    print(f"  [研讨厅] Round 1/2: 并行独立观点陈述")
    print(f"{'~'*50}")

    # 构建上游摘要 (所有参与者共享, 公平提供)
    upstream_summary = self._summarize_for_debate(previous_outputs)

    debate_input_template = f"""## 研讨厅辩论: {debate_topic}

### 用户原始需求
{user_request}

### 上游阶段产出摘要
{upstream_summary}

### ⚠️ 辩论规则

你正在参与一场多学科并行辩论。请遵守以下规则:

1. **独立分析**: 只从你的专业视角给出独立判断。不要试图猜测其他 Agent 的结论。
2. **证据驱动**: 每个主张必须有数据、文献、或理论推理支撑。
3. **标注确信度**: 对每个关键判断标注确信度: [高/中/低]
4. **明确边界**: 如果某个问题超出了你的专业范围，注明"超出本专业知识范围"。
5. **输出格式**: 
   - ## 我的核心观点 (3-5 条)
   - ## 我的推荐方案 (具体、可操作)
   - ## 关键风险 (我看到的)
   - ## 确信度说明"""

    # 并行调用所有参与方
    round1_outputs = {}
    for agent_short_name in participants:
        agent_id = f"{division}/{agent_short_name}" if agent_short_name not in ("biostatistician", "ml-engineer", "data-engineer", "research-assistant", "scientific-writer") else f"shared/{agent_short_name}"

        # 给每个 Agent 定制的辩论指令
        task_input = debate_input_template
        if agent_short_name == "computational-biologist":
            task_input += "\n\n你的专业视角: 建模可行性、方法选择、特征工程、模型评估策略。"
        elif agent_short_name == "biostatistician":
            task_input += "\n\n你的专业视角: 统计方法适当性、样本量、缺失处理、多重比较校正、效应量估计。"
        elif agent_short_name == "clinical-researcher":
            task_input += "\n\n你的专业视角: 临床相关性、表型可操作化、效应方向的临床解释、外部有效性。"
        elif agent_short_name == "pi":
            task_input += "\n\n你的专业视角: 整合各视角、期刊策略、研究贡献评估、风险收益权衡。"

        result = self._call_agent(
            agent_id, task_input,
            phase_id=f"{phase_id}_debate_r1",
            project_id=project_id,
        )
        round1_outputs[agent_short_name] = result
        outputs[agent_short_name] = result

    print(f"  [研讨厅] Round 1 完成: {len(round1_outputs)} 份独立观点")

    # ================================================================
    # Round 2: 辩论主持人汇总共识与分歧
    # ================================================================
    print(f"  [研讨厅] Round 2/2: 主持人汇总")

    moderator_prompt = f"""## 研讨厅辩论纪要任务

**辩论主题**: {debate_topic}
**参与方**: {', '.join(participants)}

### 各方独立观点:
"""
    for name, output in round1_outputs.items():
        # 截断长输出以节省 token
        truncated = output[:3000] + ("...(截断)" if len(output) > 3000 else "")
        moderator_prompt += f"\n#### {name}\n{truncated}\n---\n"

    moderator_prompt += """
请基于以上各方独立观点，整理输出《研讨厅辩论纪要》，格式见你的 System Prompt。"""

    # 主持人使用独立的 System Prompt (DEBATE_MODERATOR_SYSTEM_PROMPT)
    moderator_output = self._call_agent_with_custom_prompt(
        agent_id="debate-moderator",
        system_prompt=DEBATE_MODERATOR_SYSTEM_PROMPT,
        task_input=moderator_prompt,
        phase_id=f"{phase_id}_debate_r2",
        project_id=project_id,
    )
    outputs["_debate_minutes"] = moderator_output

    print(f"  [研讨厅] Round 2 完成: 辩论纪要已生成")
    return outputs
```

### 4.4 辅助方法

```python
def _summarize_for_debate(self, previous_outputs: dict) -> str:
    """为辩论参与者构建精简的上游摘要，避免信息过载"""
    if not previous_outputs:
        return "无上游产出 (当前为首个执行 Phase)"

    parts = []
    for agent_id, output in previous_outputs.items():
        # 截断到 800 字符，保留关键信息
        if len(output) > 800:
            truncated = output[:800] + "..."
        else:
            truncated = output
        agent_short = agent_id.split("/")[-1]
        parts.append(f"**{agent_short}**: {truncated}")

    return "\n\n".join(parts)

def _call_agent_with_custom_prompt(
    self, agent_id: str, system_prompt: str, task_input: str,
    phase_id: str = "", project_id: str = "",
) -> str:
    """使用自定义 System Prompt 调用 Agent (用于辩论主持人等非标准角色)"""
    print(f"  → 调用 {agent_id} (custom prompt)...")
    t0 = time.time()
    success = False
    degraded = False
    in_tokens = out_tokens = 0
    output_len = 0
    error_type = ""

    try:
        response = self.llm.chat(system_prompt=system_prompt, user_message=task_input)
        content = response.content
        success = True
        degraded = getattr(response, 'degraded', False)
        usage = getattr(response, 'usage', {}) or {}
        in_tokens = usage.get("input_tokens", 0)
        out_tokens = usage.get("output_tokens", 0)
        output_len = len(content)
        print(f"  ← {agent_id}: {output_len} 字符" + (" ⚡降级" if degraded else ""))
        return content
    except Exception as e:
        error_type = type(e).__name__
        print(f"  ✗ {agent_id}: {error_type}")
        raise
    finally:
        wall_time = time.time() - t0
        self._append_run_log(
            timestamp=datetime.now().isoformat(),
            project_id=project_id, division=self.active_division,
            phase_id=phase_id, agent_id=agent_id,
            success=success, degraded=degraded,
            wall_time_sec=round(wall_time, 2),
            input_tokens=in_tokens, output_tokens=out_tokens,
            output_len=output_len, error_type=error_type,
            gate_status="skip", rework_of="",
        )
```

---

## 五、辩论纪要输出格式

### 5.1 完整示例

```markdown
# 研讨厅辩论纪要

**辩论主题**: 研究方案设计: 建模方法选择 + 统计分析策略 + 协变量筛选
**参与方**: computational-biologist, biostatistician, clinical-researcher
**主持人**: Debate Moderator
**生成时间**: 2026-05-10 14:30

---

## 1. 共识 (所有参与方一致同意)

- [共识1]: 应使用 CHARLS 2013 wave 作为训练集, 2015 wave 作为内部验证集 — 三方同意
- [共识2]: 主要结局应为 2 年衰弱转换 (二分类) — 三方同意
- [共识3]: 必须包含 Logistic Regression 作为 baseline — comp-bio + stats 同意, clinical 无异议
- [共识4]: 缺失数据采用多重插补 (MICE) — stats 提议, comp-bio 同意, clinical 同意

## 2. 分歧 (按重要性排序)

### 分歧 1: 主模型选择 — XGBoost vs Elastic Net [重要性: High]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| computational-biologist | 推荐 XGBoost | 可捕获非线性关系, 文献综述显示类似研究用XGBoost效果最佳 | 中 |
| biostatistician | 推荐 Elastic Net | 变量数~60, 担心 XGBoost 过拟合; Elastic Net 可同时做特征选择 | 中 |
| clinical-researcher | 两种均可 | 临床更关注可解释性而非方法细节 | 低 |

**主持人分析**: 核心分歧在于 非线性能力 vs 正则化。两位的论据都有道理。建议的解决方向: 两者都跑, 比较 AUC 和校准度, 选择验证集上更优的。

**建议裁决方向**: 两者都跑 (baseline: LR, 主模型: XGBoost + Elastic Net), 根据内部验证结果决定最终模型。这样可以搁置此分歧继续推进。

### 分歧 2: 是否纳入 "多重用药" 作为协变量 [重要性: Medium]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| clinical-researcher | 应纳入 | 多重用药是衰弱的重要混杂 | 高 |
| biostatistician | 需谨慎 | 多重用药与衰弱可能存在共线性, 需先做 VIF 检验 | 中 |
| computational-biologist | 先纳入 | 让模型自己学, SHAP 分析会告诉我们它是否重要 | 中 |

**主持人分析**: 三方都同意它可以纳入, 分歧在于对共线性的担忧程度。biostatistician 的建议 (先做 VIF) 是一个低成本的安全检查。

**建议裁决方向**: 纳入多重用药, 前提是 VIF < 5, 否则做共线性处理 (去掉或用 PCA)。

## 3. PI 裁决项

以下事项需要 PI 明确决策:
- [ ] **决策项 1**: 是否同意"XGBoost + Elastic Net 都跑, 根据验证结果选择"? — 选项: [同意 / 只跑一个 (指定) / 两个都跑但我指定最终选择标准]
- [ ] **决策项 2**: 协变量筛选策略 — 选项: [全变量 + SHAP 后筛选 / Elastic Net 自动筛选 / 临床先验筛选]

## 4. 综合建议

- 本场辩论有 4 项共识, 2 项分歧
- 分歧均为 High/Medium 级别, 无 Critical 分歧
- 建议: PI 对 2 项 PI 裁决项做出决策后, 可以进入 Phase 3
- 如果 PI 决定两者都跑, 预计 Phase 3 执行时间增加约 30%

---
*本纪要由研讨厅辩论主持人自动生成。PI 请基于本纪要做最终裁决。*
```

---

## 六、编排器集成点

### 6.1 PROJECT_PHASES 改动

两个 Phase 增加 `debate_mode` 和相关配置:

```python
"design": {
    ...
    "debate_mode": True,
    "debate_topic": "研究方案设计: 建模方法选择 + 统计分析策略 + 协变量筛选",
    "debate_participants": ["computational-biologist", "biostatistician", "clinical-researcher"],
},
"review": {
    ...
    "debate_mode": True,
    "debate_topic": "研究结果审查: 临床意义 + 统计可靠性 + 外部验证可泛化性",
    "debate_participants": ["clinical-researcher", "biostatistician", "pi"],
},
```

### 6.2 _run_project_workflow 路由改动

在现有的 Phase 执行路由中，增加辩论模式分支:

```python
# 当前 routing:
if phase_def.get("two_round"):
    phase_result = self._execute_phase_two_round(...)
else:
    phase_result = self._execute_phase(...)

# 改为:
if phase_def.get("debate_mode"):
    phase_result = self._execute_phase_debate(
        phase_id=phase_id,
        user_request=user_request,
        previous_outputs=upstream_outputs,
        project_id=project_id,
        debate_topic=phase_def["debate_topic"],
        participants=phase_def["debate_participants"],
    )
elif phase_def.get("two_round"):
    phase_result = self._execute_phase_two_round(...)
else:
    phase_result = self._execute_phase(...)
```

### 6.3 辩论后的 Gate 检查

辩论纪要不走标准的 Gate 检查（没有自动检查项需要验证辩论纪要）。但一致性检查仍然生效——检查 clinical ↔ PI 等的一致性。

如果辩论纪要中标注了 Critical 分歧且未解决，Gate 会被一致性检查标记为 FAIL。

### 6.4 辩论 Agent 的 ID 解析

辩论参与者的 Agent ID 需要正确解析：

```python
# agent_short_name → full agent_id mapping:
# "pi"                → "{division}/pi"
# "clinical-researcher" → "{division}/clinical-researcher"  
# "computational-biologist" → "{division}/computational-biologist"
# "biostatistician" → "shared/biostatistician"
# "ml-engineer" → "shared/ml-engineer"
# 等共享服务
```

使用现有的 `_get_phase_agents()` 中的映射逻辑保持一致。

---

## 七、测试方案

### 7.1 单元测试

| 测试 | 输入 | 期望 |
|------|------|------|
| 3 方并行输出 | Phase 2 辩论 | 3 份独立观点, 各含 "核心观点" |
| 主持人汇总 | 3 份模拟观点 (包含明显共识和明显分歧) | 输出含 "共识" + "分歧" + "PI 裁决项" |
| 分歧检测 | comp-bio: "XGBoost", stats: "LR" | 主持人在分歧表中列出此分歧 |
| 共识检测 | 三方都说 "需要外部验证" | 主持人在共识表中列出 |
| 空上游 | 无上游输出 | 上游摘要显示 "无上游产出" |
| 单方辩论 | 只有 1 个参与方 | 主持人标注 "无分歧 (仅一方参与)" |

### 7.2 集成测试

| 场景 | 输入 | 期望 |
|------|------|------|
| Phase 2 辩论 → Phase 3 | 正常用户请求 | Phase 2 生成辩论纪要, Phase 3 基于纪要执行 |
| Phase 5 辩论 → Phase 6 | Phase 4 产出完整 | 辩论纪要包含 clinical ↔ stats ↔ PI 三方 |
| 辩论后一致性检查 | 三方输出 | Phase 5 的 clinical↔PI 一致性检查读取辩论输出 |
| 辩论模式 + Gate | 辩论纪要完整 | Gate 正常通过 (辩论无 auto check) |
| 辩论模式 + 反馈B | 辩论发现上游问题 | 反馈B 检测到关键词 → 触发回退 |

### 7.3 手动验证

```python
# 启动一个真实的项目 (用简单请求测试辩论模式)
result = orchestrator.run("用 CHARLS 数据预测衰弱转换, 帮我设计方案")
# 预期:
# 1. Phase 2 输出包含 "研讨厅辩论纪要"
# 2. 辩论纪要包含 "共识" + "分歧" + "PI 裁决项"
# 3. computational-biologist, biostatistician, clinical-researcher 三方观点都有
```

---

## 八、文件改动清单

| 文件 | 改动类型 | 改动内容 | 预计行数 |
|------|---------|---------|---------|
| `engine/core/orchestrator_graph.py` | 修改 | 新增 `DEBATE_MODERATOR_SYSTEM_PROMPT` 常量 + `_execute_phase_debate()` + `_summarize_for_debate()` + `_call_agent_with_custom_prompt()` + 修改 `_run_project_workflow()` 路由 + 更新 `PROJECT_PHASES` (design/review) | +180 / -10 |
| `company/management/debate-moderator.md` | **新文件** | 辩论主持人 Agent 定义 (可独立修改的 prompt) | ~50 |
| `tests/test_debate_mode.py` | **新文件** | 辩论模式单元测试 (6 cases) + 集成测试 (5 scenarios) | ~180 |

---

## 九、与其他模块的关系

```
                      ┌──────────────────────┐
                      │   研讨厅辩论模式        │
                      │   (Phase 2 / Phase 5) │
                      └──────────┬───────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │ 模块一        │    │ 模块二        │    │ 模块三        │
   │ 反馈控制       │    │ 可靠性        │    │ 系统辨识      │
   │              │    │              │    │              │
   │ Gate 检查     │    │ 一致性交叉验证 │    │ 运行数据采集  │
   │ 反馈环B       │    │ (辩论后检查    │    │ (记录辩论参与  │
   │              │    │  各方一致性)   │    │  方耗时/通过率)│
   └──────────────┘    └──────────────┘    └──────────────┘

具体交互:
- 辩论输出经过一致性检查 (模块二): clinical ↔ PI 矛盾检测
- 辩论中发现的错误触发反馈B (模块一): 如发现上游表型定义问题
- 辩论参与方的耗时/成功率被记录 (模块三): 用于后续自适应调度
```

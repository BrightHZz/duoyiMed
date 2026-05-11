# Few-Shot 示例 — PI Agent

## Example 1: FRAME 评估新方向 (定量化 — 基于机器预检报告)

### Input

```
团队提议: "用 CHARLS 2013 基线数据预测 2 年衰弱转换风险"
Round 1 机器预检报告已就绪, 请基于以下数据做 FRAME 评估:

=== 文献预检报告 (research-assistant) ===
- Top 1: Zhang et al. 2025, XGBoost on CHARLS 2011, AUC=0.81, N=4,200
  缺口: 未使用 2013 基线(含握力/步速), 无时间验证
- Top 2: Li et al. 2024, Ensemble on CLHLS, AUC=0.83, N=3,800
  缺口: CLHLS 人群年龄偏高, 社区代表性弱于 CHARLS
- Top 3: Wang et al. 2023, LR on ELSA, AUC=0.78, N=5,100
  缺口: 欧洲人群, 非中国
→ SOTA 天花板: AUC ~0.83, 仍有提升空间
→ 竞争强度: 中等 (3 篇直接相关, 但均有明确缺口)

=== 数据可用性报告 (data-engineer) ===
- CHARLS 2013 含握力+步速 (之前波次没有) → 独特优势
- 目标变量: Fried Phenotype 可操作化, 缺失率 12% (MAR)
- 候选特征: 78 个, 覆盖 6 个类别, 样本量 ~4,500
- DQ-CARE: Completeness 88%, Accuracy 合格

=== 建模可行性报告 (computational-biologist) ===
- XGBoost + SHAP 方案成熟, N=4,500 足够
- 建议加入时间验证 (2015→2018) 作为泛化证据
- 需注意: 认知评估的记忆效应 (MMSE 在 2011/2013/2015 重复测量)
```

### Reasoning (Chain of Thought)

```
F — Field Scan: 基于文献预检报告数据
  - SOTA AUC 天花板 0.83 (Zhang 2025, CLHLS)
  - 3 篇直接竞争但均有明确缺口 → 竞争中等, 非红海
  - 我们使用 2013 基线(含握力)是差异化优势

R — Resource Audit: 基于数据可用性报告
  - CHARLS 2013: 4,500 样本, 78 特征, Fried 可操作化 ✓
  - 缺失率 12% → MICE 插补可行 (引用报告中的 MAR 假设)
  - 握力+步速变量独特性 → 核心优势

A — Alignment: 基于专业知识
  - 衰弱预测与老龄化战略高度对齐
  - 临床转化路径清晰 (筛查工具)

M — Market Gap: 基于文献预检报告
  - 3 篇直接相关, 但: Zhang 无 2013 基线, Li 人群偏差, Wang 欧洲数据
  - 缺口明确 → 发表空间充足
  - 目标期刊: GeroScience (Tier 2)

E — Edge: 基于数据+团队
  - 数据独特性: 2013 基线含握力 (CHARLS 独有窗口)
  - 方法成熟度: XGBoost+SHAP 已有成功经验
  - 时间验证策略 (2015→2018) → 增强泛化证据
```

### Output

```markdown
## FRAME 评估 — CHARLS 2013 衰弱转换预测

### F — Field Scan (领域扫描)
*数据源: 文献预检报告 (research-assistant)*

- SOTA AUC 天花板: 0.83 (Zhang 2025, CLHLS); 0.81 (Zhang 2025, CHARLS 2011)
- 3 篇直接竞争论文, 但均存在明确缺口:
  - Zhang 2025: 未使用 2013 基线, 缺握力/步速
  - Li 2024: CLHLS 人群偏差 (超高龄为主)
  - Wang 2023: 欧洲 ELSA 数据, 不可直接迁移到中国人群
- 结论: 竞争强度中等, 差异化空间明确 ✓

### R — Resource Audit (资源审计)
*数据源: 数据可用性报告 (data-engineer)*

- CHARLS 2013: N≈4,500, 78 候选特征, Fried Phenotype 可操作化
- 缺失率 12% (报告判定为 MAR) → MICE 插补可行
- ⭐ 独有优势: 2013 是 CHARLS 首次纳入握力+步速测量的波次
- 人力: 团队有 XGBoost+SHAP 经验, 技术栈成熟
- 结论: 数据可行 ✓

### A — Alignment Check (对齐检查)

- 基金对齐: 衰弱早期识别高度契合老龄化战略方向
- 临床需求: 社区筛查工具需求明确 (门诊快速识别衰弱前期)
- 战略对齐: 与团队计算老年医学路线图一致
- 结论: 对齐 ✓

### M — Market Gap (发表缺口)
*数据源: 文献预检报告 + 期刊趋势分析*

- 3 篇直接竞争者各有明确缺口 → 发表空间充足
- 我们的差异化: 2013 基线(握力) + 时间验证 + SHAP 交互
- 推荐期刊: GeroScience (Tier 2), 备选 JAGS (Tier 2)
- 结论: 缺口明确 ✓

### E — Edge Assessment (优势评估)

- 数据独特性: CHARLS 2013 基线窗口 (握力+步速) 为团队独有切入点
- 方法成熟度: XGBoost+SHAP 管线已验证, 6 个月内可产出
- 时间验证策略 (2015→2018) 增强泛化性 → 审稿人认可度更高
- 结论: 优势明确 ✓

### 🟢 综合判断: 启动

**理由**: 五个维度全部通过。数据可行 (R), 竞争可控 (F), 缺口明确 (M),
对齐战略 (A), 团队有优势 (E)。建议 Phase 2 设计阶段加入时间验证方案。
```

---

## Example 2: 论文终审

### Input

```
待审稿件: CHARLS衰弱预测 ML 论文
目标期刊: GeroScience

请做终审, 判断是否达到投稿标准。
```

### Reasoning

```
逐项检查终审清单:
1. 研究问题: 清晰, 有临床价值 ✓
2. 方法: 合理, 但需确认 nested CV 是否正确实现 ?
3. 结果: 完整, 但校准度稍有问题 ⚠️
4. 讨论: 需要检查局限性是否坦诚
5. 贡献: 核心增量是什么? 是否存在增量不足的问题?
  - 已有 Zhang 2025 用 XGBoost 在 CHARLS 做衰弱预测
  - 我们的增量: 2013基线(含握力) + 时间验证 + SHAP交互 + 竞争风险
  → 增量足够
```

### Output

```markdown
## 终审意见 — 衰弱预测 ML 论文

### 总体判断: ✅ 批准, 但需 3 项修改后投稿

### 逐项审查

| 维度 | 评分 | 意见 |
|------|------|------|
| 研究问题 | ✓ | 2年衰弱转换预测是明确的临床需求 |
| 方法 | ✓ | Nested CV + 时间验证 + 敏感性充分 |
| 结果 | ⚠️ | 校准度有问题(见下) |
| 讨论 | ⚠️ | 局限性不够坦诚(见下) |
| 贡献 | ✓ | 增量清晰(首次在CHARLS用2013基线+握力) |

### ⚠️ 修改要求

1. **校准度** (关键):
   - 高风险区间校准不足必须讨论, 不能只说"Brier=0.14"
   - 建议: 在Limitations中加入 "the model may underestimate risk for 
     the highest-risk individuals, warranting caution in individual 
     risk communication"

2. **与 Zhang 2025 的区别必须明确**:
   - 不能在 Introduction 中回避这篇最相关的文献
   - 在 Discussion 中正面比较: 我们用了2013基线(含握力) vs 他们用2011
     我们的时间验证策略 vs 他们仅内部CV

3. **局限性补充**:
   - 缺失 CHARLS→CLHLS 外部验证 (这是我们计划的下一步)
   - 观察性设计的残余混杂
   - 2年窗口期可能太短, 衰弱是一个更长期的过程

### 投稿建议
- **目标期刊**: GeroScience (Tier 2) — 合适
- **Cover Letter 强调点**: 
  ① 首次在CHARLS用含握力的完整Fried定义做基线
  ② 时间验证证明2年跨度的泛化性
  ③ SHAP交互效应揭示功能×年龄的非线性交互
  ④ 竞争风险敏感性分析(衰弱文献中少见)

### 修改后: ✅ 可投稿
```

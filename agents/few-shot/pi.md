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

=== 数据可用性报告 (data-engineer) ===
- CHARLS 2013 含握力+步速 (之前波次没有) → 独特优势
- 目标变量: Fried Phenotype 可操作化, 缺失率 12% (MAR)
- DQ-CARE: Completeness 88%, Accuracy 合格

=== 建模可行性报告 (computational-biologist) ===
- XGBoost + SHAP 方案成熟, N=4,500 足够
- 建议加入时间验证 (2015→2018) 作为泛化证据
```

### Reasoning (Chain of Thought)

```
F — Field Scan: 基于文献预检报告
  - SOTA AUC 天花板 0.83, 3 篇直接竞争但均有缺口

R — Resource Audit: 基于数据可用性报告
  - 2013 基线含握力 → 独特优势, N=4,500, 缺失 12%

A — Alignment: 衰弱预测与老龄化战略对齐 ✓

M — Market Gap: 缺口明确, 3 篇竞争论文均无法覆盖 2013 基线

E — Edge: 数据独特 + 方法成熟 + 6 月可产出
```

### Output

```markdown
## FRAME 评估 — CHARLS 2013 衰弱转换预测

### F — Field Scan (领域扫描)
*数据源: 文献预检报告*

- SOTA AUC 天花板: 0.83 (Zhang 2025 CLHLS); 0.81 (Zhang 2025 CHARLS 2011)
- 3 篇直接竞争但各有缺口: 无 2013 基线 / 人群偏差 / 欧洲数据
- 结论: 竞争中等, 差异化空间明确 ✓

### R — Resource Audit (资源审计)
*数据源: 数据可用性报告*

- CHARLS 2013: N≈4,500, 78 特征, Fried 可操作化
- 缺失率 12% (MAR) → MICE 可行
- ⭐ 独有优势: 2013 是 CHARLS 首次纳入握力+步速
- 结论: 数据可行 ✓

### A — Alignment Check (对齐检查)
- 衰弱早期识别高度契合老龄化战略, 临床转化路径清晰
- 结论: 对齐 ✓

### M — Market Gap (发表缺口)
*数据源: 文献预检报告*

- 3 篇竞争者各有缺口 → 发表空间充足
- 差异化: 2013 基线(握力) + 时间验证 + SHAP 交互
- 推荐: GeroScience (Tier 2), 备选 JAGS
- 结论: 缺口明确 ✓

### E — Edge Assessment (优势评估)
- 数据独特性 + 方法成熟度 + 时间验证策略
- 估计 6 个月内可产出
- 结论: 优势明确 ✓

### 🟢 综合判断: 启动

理由: 五个维度全部通过。建议 Phase 2 加入时间验证方案。
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

2. **与 Zhang 2025 的区别必须明确**:
   - 在 Discussion 中正面比较: 我们用了2013基线(含握力) vs 他们用2011
     我们的时间验证策略 vs 他们仅内部CV

3. **局限性补充**:
   - 缺失 CHARLS→CLHLS 外部验证

### 投稿建议
- **目标期刊**: GeroScience (Tier 2) — 合适
- **修改后**: ✅ 可投稿
```

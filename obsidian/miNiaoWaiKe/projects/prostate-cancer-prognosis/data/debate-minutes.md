# 研讨厅辩论纪要

**辩论主题**: 前列腺癌住院不良结局预测 — 建模方法选择 + 统计分析策略 + 协变量筛选
**参与方**: Computational Biologist, Biostatistician, Clinical Researcher
**主持人**: Debate Moderator
**日期**: 2026-05-10

---

## 1. 共识 (所有参与方一致同意)

- **[共识 1]**: 主模型应使用 XGBoost，而非深度学习或多模型 ensemble — 同意方: CB, Biostat, Clin。所有三方均从不同角度得出相同结论: CB 从方法适当性，Biostat 从可解释性要求，Clin 从审稿接受度。
- **[共识 2]**: 5-fold cross-validation 必须按 patient_id 分层，避免同一患者的数据泄漏到 train/validation 的两侧 — 同意方: CB, Biostat, Clin
- **[共识 3]**: PSA 是最关键的肿瘤标志物特征，必须在模型中包含，且需要精细操作化 (log-transform, 时间窗限制) — 同意方: CB, Biostat, Clin
- **[共识 4]**: Gleason 评分和 TNM 分期的缺失是本研究最大的 limitation，必须在 Discussion 中明确声明 — 同意方: CB, Biostat, Clin
- **[共识 5]**: SHAP 可解释性分析必须包含在最终报告中 — 同意方: CB, Biostat, Clin
- **[共识 6]**: 内部验证完成后，MIMIC-III 是唯一可行的外部验证数据源 — 同意方: CB, Biostat, Clin
- **[共识 7]**: 类别不平衡通过 XGBoost 的 `scale_pos_weight` 处理，不使用 SMOTE — 同意方: CB, Biostat, Clin (Biostat 额外要求: 报告 PR-AUC)
- **[共识 8]**: 缺失值的 Multiple Imputation 必须在每个 CV fold 内独立进行 (防信息泄漏) — 同意方: CB, Biostat (Clin: 超出本专业知识范围, 信任统计师)

---

## 2. 分歧 (按重要性排序)

### 分歧 1: 是否需要 Logistic Regression 作为 baseline model [重要性: Critical]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Biostatistician | 必须包含 LR baseline | 医学期刊 TRIPOD 指南要求; 审稿人必然追问; 若 ΔAUC < 0.05 需论证 ML 的必要性 | 高 (TRIPOD 指南, 审稿惯例) |
| Computational Biologist | 不需要 LR, 仅 XGBoost | 多模型增加复杂度; 本任务特征多且含非线性交互, LR 已知不适合 | 中 (逻辑推理) |
| Clinical Researcher | 未直接表态 | 超出本专业知识范围 | — |

**分歧实质**: 这不是技术分歧，是对"审稿人期望"的不同权重。Biostat 从审稿合规性出发，CB 从建模效率出发。两者的核心关切没有冲突——加入 LR 的成本很低 (几行代码)，但缺失 LR 的风险很高 (审稿被拒或要求大修)。

**建议解决方向**: PI 裁决。建议倾向 Biostat — 加入 LR baseline 的成本极小 (scikit-learn 一行代码)，但缺失它的审稿风险很大。

---

### 分歧 2: 是否需要 LASSO 做特征预筛选 [重要性: Critical]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Biostatistician | 必须 LASSO pre-filtering (λ.1se) | EPV ~10-14 处于边界; LASSO 减少过拟合; 保留 ≥3/5 folds 稳定的特征 | 高 (统计理论 + Harrell 的 EPV 指南) |
| Computational Biologist | 不做特征筛选, 依赖 SHAP 事后分析 | SHAP importance = 0 的特征自然移除; 事前筛选可能丢失弱信号 | 中 (ML 工程实践) |
| Clinical Researcher | 部分特征强制纳入 (年龄/PSA/骨转移), 其余可被 LASSO 筛选 | 临床知识需要保护; 不可被纯数据驱动移除关键变量 | 高 (临床领域知识) |

**分歧实质**: 三方对"特征筛选的适度程度"有不同标准。Biostat 从统计过拟合风险出发，CB 从 ML 实践出发，Clin 从保护临床知识出发。这三个关切其实可以兼顾。

**建议解决方向**: PI 裁决一个三层特征策略:
- Tier 1 (Clinical Mandatory): age, PSA, bone_metastasis, admission_type, CCI — 强制保留
- Tier 2 (LASSO Candidate): 其余实验室+人口学 — LASSO λ.1se 筛选
- Tier 3 (XGBoost Final): T1 + T2 筛选后特征 → XGBoost 训练
- Sensitivity: 对比"全特征 XGBoost"和"LASSO 筛选后 XGBoost"的性能差异

---

### 分歧 3: 复合结局的使用方式 [重要性: High]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Computational Biologist | 复合结局直接作为单一 outcome | 最大化事件数, 提高统计 power | 中 |
| Biostatistician | Composite primary + 各成分 secondary | 平衡 power 与临床解释性 | 高 (CONSORT 复合结局报告指南) |
| Clinical Researcher | 强烈要求分别分析, 死亡和 ICU 是本质不同的临床终点 | 合并会模糊模型的临床解释; 临床医生无法基于复合结局做决策 | 高 (临床实践推理) |

**分歧实质**: CB 关心统计 power，Clin 关心临床可解释性。Biostat 的折中方案 (Primary composite + Secondary per-component) 同时满足了两个关切。

**建议解决方向**: PI 裁决。建议采纳 Biostat 的折中方案 — 这是 CONSORT 指南推荐的处理复合结局的标准方式。这同时满足了 Clin 的核心关切 (secondary analyses 必须做)。

---

### 分歧 4: 报告指标的最小集合 [重要性: Medium]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Biostatistician | AUC + PR-AUC + Brier + Calibration Slope/Plot + DCA | TRIPOD 指南要求多维度评估; J Urology 期望 DCA | 高 (TRIPOD) |
| Computational Biologist | AUC + Calibration Slope + SHAP | 精简但不遗漏核心指标 | 中 |
| Clinical Researcher | AUC + 分层AUC + Calibration + DCA | DCA 对临床决策支持工具很重要 | 中 |

**分歧实质**: 对"多少指标够用"的偏好差异。这不影响研究设计，影响的是最终报告的长度和审稿合规性。

**建议解决方向**: 建议采纳 Biostat 的完整指标集 (与 TRIPOD 指南对齐 = 降低审稿风险)。分层 AUC 作为 Clin 的额外要求纳入 exploratory analysis。

---

### 分歧 5: ICU vs 死亡的预测因子差异分析的必要性 [重要性: Medium]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Clinical Researcher | 如果两个成分的 SHAP 特征差异很大, 应作为独立发现写入 Discussion | 这本身就是有价值的临床发现 | 中 (临床判断) |
| Biostatistician | 同意作为 sensitivity analysis | 但要注意统计 power 不足 (单独死亡的 events ~128) | 中 |
| Computational Biologist | 未直接讨论 | — | — |

**分歧实质**: 不是是否做，而是在论文中给多少篇幅。

**建议解决方向**: 做两个成分的 SHAP 对比。如果确实发现显著差异 → Discussion 中一个段落讨论。如果差异不大 → 一句话带过。

---

## 3. PI 裁决项

- [ ] **决策项 1**: LR baseline — 是否加入 Logistic Regression 作为标准 baseline model?
  - 选项 A: 加入 LR (Biostat 推荐) — 成本低, 审稿安全
  - 选项 B: 不加入 LR (CB 推荐) — 简化流程

- [ ] **决策项 2**: 特征筛选策略 — 选择哪种方案?
  - 选项 A: Clinical Mandatory (Tier 1) + LASSO (Tier 2) → XGBoost (Tier 3) 三层策略
  - 选项 B: 全特征直接 XGBoost + SHAP 事后筛选 (CB 方案)
  - 选项 C: 纯 LASSO 筛选 → XGBoost (无临床强制变量保护)

- [ ] **决策项 3**: 结局策略 — 选择哪种方案?
  - 选项 A: Primary composite + Secondary per-component analyses + SHAP 成分对比 (Biostat+Clin 折中方案)
  - 选项 B: 仅复合结局 (CB 方案)
  - 选项 C: 仅 ICU 入院 (放弃死亡)

- [ ] **决策项 4**: 报告指标 — 选择最小指标集?
  - 选项 A: 完整 TRIPOD 指标集 (AUC + PR-AUC + Brier + Calibration Slope/Plot + DCA + Subgroup AUC)
  - 选项 B: 精简集 (AUC + Calibration Slope + SHAP)

- [ ] **决策项 5**: MIMIC-III 外部验证队列探查 — 是否在 Phase 4 前先探查 MIMIC-III 前列腺癌队列的可行性?
  - 选项 A: Phase 3 完成后立即探查 MIMIC-III 队列 → 决定是否进入 Phase 4
  - 选项 B: 直接进入 Phase 4 (不做事前探查)

---

## 4. 综合建议

本次辩论三方从各自专业视角出发，共识覆盖了 8 个核心问题 (含建模方法、验证策略、可解释性)，反映了研究方案的基本骨架已经稳定。

主要分歧集中在 **5 个方法论细节** (LR baseline, LASSO, 复合结局使用方式, 报告指标, 成分分析)。这些分歧的实质是"技术最优解" vs "审稿合规性" vs "临床可解释性"之间的权衡，而非方向性矛盾。

建议 PI 在裁决时:
1. **分歧 1-3 (Critical/High)** 建议倾向审稿合规和临床可解释性 — 加入 LR baseline、LasSO + 临床强制变量、复合结局 + 成分分析
2. **分歧 4-5 (Medium)** 建议满足审稿期望 — 完整 TRIPOD 指标集, 成分 SHAP 对比作为 exploratory finding

---

*本纪要由研讨厅辩论主持人自动生成。PI 请基于本纪要做最终裁决。*

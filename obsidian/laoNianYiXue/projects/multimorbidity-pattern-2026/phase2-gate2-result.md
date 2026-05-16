# Gate 2 — 方案设计闸门检查

**项目**: multimorbidity-pattern-2026
**Phase**: Phase 2 (方案设计)
**时间**: 2026-05-11
**状态**: ✅ PASS

---

## Auto Checks (4 项)

### 1. check_baseline_included — ✅ PASS
- **标准**: 建模方案含 Logistic Regression 作为基线模型
- **结果**: 
  - computational-biologist 方案含 M0: Logistic (年龄+性别) 作为 baseline
  - biostatistician SAP 含 M0-M4 五层 Logistic 模型链
  - "基线必做"原则已落实

### 2. check_sensitivity_analysis_count — ✅ PASS
- **标准**: 敏感性分析 ≥ 3 项
- **结果**: biostatistician SAP 列出 5 项:
  1. 缺失数据处理 (MICE vs CCA vs 缺失指示法)
  2. 不同 k 的 LCA (k ± 1)
  3. 聚类不确定性 (后验概率 >0.7 子集)
  4. 排除极端值
  5. E-value 未测混杂评估
- **+1** (PI 裁决新增): 实测慢病定义敏感性分析

### 3. check_subgroup_count — ✅ PASS
- **标准**: 亚组 ≤ 5 个
- **结果**: 4 个预设亚组:
  - 年龄 (45-64 / 65-74 / ≥75)
  - 性别 (男/女)
  - 城乡 (城镇/农村)
  - CCI (0-2 / 3-4 / ≥5)
- 交互项检验策略明确, 不采用亚组内单独检验

### 4. check_smd_balance — ⏭️ SKIP
- **说明**: Phase 2 为方案设计阶段, 无实际 SMD 值 (Phase 3 执行后检查)
- Gate 2 不要求 SMD 值, 仅要求方案中声明 SMD < 0.1 标准 → ✅ 已声明

---

## LLM Checks (3/3 PASS)

### 1. 建模方案与临床问题是否对齐 (PICO-ML 映射)? — ✅
- P (老年多病共存人群) → 纳入 ≥45 岁, CHARLS 全国代表性
- I (LCA 聚类标签) → 无监督聚类映射为预测因子
- C (CCI 传统共病计数) → 作为对比基线, 增量价值验证
- O (死亡/ADL失能/住院) → 三个结局分开报告
- ML: LCA (聚类) + XGBoost (预测) 与 PICO 对齐

### 2. SAP 是否包含样本量/缺失处理/敏感性分析? — ✅
- 样本量/功效分析: 完整 (LCA ≥560→实际 8,000-10,000, 死亡事件 400-800, power≈0.85)
- 缺失处理: MICE (m=10) 主分析 + CCA + 缺失指示法
- 敏感性分析: 5+1 项

### 3. 模型评估策略是否合理 (内部+外部验证)? — ✅
- 内部验证: 10-fold nested CV, DeLong 95% CI
- 外部验证: Wave 2→4 时间验证 (ΔAUC 阈值检查)
- 区分度 + 校准度 + 临床决策曲线

---

## SAP 签批状态 (biostatistician Pre-Execution Sign-Off)

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 结局变量定义, 无循环论证 | ✅ |
| 2 | 缺失数据处理策略明确 (MICE) | ✅ |
| 3 | 亚组定义 + 验证规划 | ✅ |
| 4 | 中介分析: N/A (非中介研究) | ✅ |
| 5 | 效应量报告规范 (OR + 95% CI) | ✅ |

**SAP 签批**: 5/5 → APPROVED ✅

---

## PI 裁决执行确认

| 裁决项 | 决策 | 执行确认 |
|--------|------|---------|
| 决策 1: 多重用药 | 纳入核心特征 (需确认变量可用性) | ✅ 原方案已更新 |
| 决策 2: 结局报告 | 三个分开为主, 复合为敏感性 | ✅ SAP 已调整 |
| 决策 3: LCA 上限 | k=2:8 搜索, PI 临床约束 | ✅ |
| 决策 4: 实测慢病 | 增加敏感性分析 (若数据可用) | ✅ 已追加 |

---

## Gate 2 判定: ✅ PASS

全部 3 项 auto checks PASS (1 项 skip) + 3 项 llm checks PASS。
**冻结 Phase 2 基线 v1.0**。准入 Phase 3 (执行/内部验证)。

---

## Phase 2 基线快照

| 产出物 | 文件 | 状态 |
|--------|------|------|
| 建模方案 (comp-bio) | phase2-computational-biologist.md | ✅ |
| 统计分析计划 (biostat) | phase2-biostatistician.md | ✅ SAP APPROVED |
| 临床审阅 (clinical) | phase2-clinical-researcher.md | ✅ |
| 研讨厅辩论纪要 | phase2-debate-minutes.md | ✅ |
| PI 裁决 | phase2-pi-adjudication.md | ✅ |
| Gate 2 结果 | phase2-gate2-result.md | ✅ PASS |

**下一步**: Phase 3 — 执行/内部验证 (ml-engineer: LCA + XGBoost 实现)

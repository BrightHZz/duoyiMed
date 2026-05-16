# 系统设计说明书 (SDS) v1.0

**项目**: prostate-cancer-metastasis-pattern
**事业部**: urology
**生成时间**: 2026-05-14
**设计师**: System Architect (Orchestrator)
**触发**: 用户选择 B5 — 转移模式与生存预后

---

## 1. 研究问题操作化

**用户需求**: 仅骨转移 vs 内脏转移前列腺癌的生存差异及预后因素

**操作化研究问题**:
> 基于 SEER 癌症登记数据（2010-2023），系统比较不同转移模式（仅骨转移 vs 内脏转移 ± 骨转移 vs 仅远处淋巴结转移）前列腺癌患者的生存差异，识别每种转移模式下独立的预后因素，并构建转移模式特异性预后预测模型。

**PICO-ML 映射**:

| PICO | 操作化 |
|------|--------|
| P (Population) | SEER 数据库中 2010-2023 年确诊的 de novo M1 前列腺癌患者，年龄 ≥ 18 岁 |
| I (Intervention/Index) | 转移模式分类（3-4 组互斥分组）+ 转移模式内 ML 预后模型 |
| C (Comparison) | 不同转移模式间的生存差异；同一转移模式内不同风险组的预后差异 |
| O (Outcome) | 主要结局：总生存 (OS)；次要结局：肿瘤特异性生存 (CSS) |
| ML | 按转移模式分层：在每个亚组内构建 XGBoost 3 年生存预测模型 + 识别模式特异性预后因子 |

### 核心创新点

1. **当前 TNM 分期将 M1 视为单一类别**，但临床经验显示仅骨转移、内脏转移和仅 LN 转移的生存差异巨大（中位生存可能从 48 月到 12 月不等）
2. **转移模式特异性预后因子**：某一因素（如 Gleason、年龄）在不同转移模式中的重要性可能完全不同——骨转移中 Gleason 可能仍是关键，内脏转移中治疗选择和器官功能可能更决定预后
3. **竞争风险视角**：M1 前列腺癌患者中，心血管死亡是主要的竞争风险，Fine-Gray 模型可分离肿瘤特异性死亡与其他原因死亡

---

## 2. 系统分解

### 子系统 1：文献预检与差距分析
- **provider**: shared/research-assistant
- **output**: 《选题文献预检报告》+《转移模式预后研究差距分析》
- **interface**:
  - 输入: 研究问题 PICO
  - 输出: Markdown 报告（≥3 篇 SEER M1 转移模式预后论文，含研究设计/AUC/样本量/转移分类方案）
  - SLA: Phase 1 Round 1
- **quality_gate**:
  - 对标论文 ≥ 3 篇
  - 鉴定现有文献的转移分类方案（二分类 vs 四分类 vs 连续变量）
  - 确认本研究与已有工作不重复

### 子系统 2：DQ-CARE 数据质量评估（聚焦转移变量）
- **provider**: shared/data-engineer
- **output**: 《DQ-CARE 数据质量报告》+ 转移变量专题分析
- **interface**:
  - 输入: 研究队列定义（PICO-P）+ SEER 数据文件路径
  - 输出: DQ-CARE 报告 + 转移变量覆盖率/time-window 完整性分析
  - SLA: Phase 1 Round 1
- **quality_gate**:
  - 2010-2023 M1 前列腺癌样本量确认
  - 六部位转移变量（bone/brain/liver/lung/distant LN/other）缺失率 < 20%
  - 生存数据（survival months + vital status + COD）完整性 > 95%
  - Gleason/PSA/Age 关键变量缺失率评估

### 子系统 3：转移模式操作化定义
- **provider**: urology/clinical-researcher
- **output**: 《前列腺癌转移模式分类方案》（含互斥分组逻辑 + 临床指南依据）
- **interface**:
  - 输入: 文献预检报告 + 数据字典 + DQ-CARE 报告
  - 输出: Markdown（分组算法伪代码 + 临床依据）
  - SLA: Phase 1 Round 2
- **quality_gate**:
  - 分组互斥且全面（每个 M1 患者只属一个组）
  - 分组与 NCCN/EAU 指南对转移性前列腺癌的分层逻辑一致
  - 每组的预期样本量 ≥ 500

### 子系统 4：FRAME 五维评估
- **provider**: urology/pi
- **output**: 《FRAME 五维评估报告》→ 明确建议: [启动/观望/放弃]
- **interface**:
  - 输入: 文献预检 + DQ-CARE + 转移分类方案 + 建模可行性
  - 输出: FRAME 五维评分 + 最终建议
  - SLA: Phase 1 Round 2

### 子系统 5：方案设计 — 研讨厅辩论
- **provider**: urology/computational-biologist, shared/biostatistician, urology/clinical-researcher
- **output**: 《研讨厅辩论纪要》（含完整 SAP）
- **interface**:
  - 输入: FRAME 评估 + SDS + 转移分类方案
  - 输出: 辩论纪要 + 统计分析方法 + 建模方案 + SAP
  - SLA: Phase 2
- **quality_gate**:
  - SAP 包含: 样本量计算 / 缺失处理 / 评估指标 / 统计检验方法 / 多重比较校正
  - 竞争风险分析方案明确
  - PI 对分歧项完成裁决

### 子系统 6：数据工程与特征构建
- **provider**: shared/data-engineer
- **output**: `analysis_ready.parquet`（全队列）+ `met_pattern_train.parquet`（训练集）
- **interface**:
  - 输入: SEER CSV + 转移分类方案 + SAP
  - 输出: 清洗后数据集（含 met_pattern 列 + 衍生特征）
  - SLA: Phase 3 前半
- **quality_gate**:
  - met_pattern 列完整（无 NULL）
  - 训练/测试/外验按年份分层划分（2020-2023 作为时间验证集）
  - 数据集行数与纳入标准一致

### 子系统 7：生存分析与预后因子识别（描述性）
- **provider**: shared/biostatistician
- **output**: 《生存分析报告》（KM + Cox + Fine-Gray + 交互检验）
- **interface**:
  - 输入: analysis_ready.parquet + SAP
  - 输出: 生存分析报告（含森林图 + KM 曲线 + 竞争风险累计发生率图）
  - SLA: Phase 3 前半
- **quality_gate**:
  - 至少 4 条 KM 曲线（按 met_pattern 分组）
  - Cox PH 假设检验通过（Schoenfeld residuals）
  - Fine-Gray 模型含 ≥ 3 个协变量
  - 效应方向与临床预期一致

### 子系统 8：ML 预后模型 — 按转移模式分层
- **provider**: shared/ml-engineer
- **output**: 《ML 预后模型报告》+ 3 个转移模式特异性模型 + SHAP 分析
- **interface**:
  - 输入: analysis_ready.parquet + SAP + 生存分析结果
  - 输出: 训练报告（每个 met_pattern 子集的 XGBoost/LR 性能 + SHAP 重要性排序）
  - SLA: Phase 3 后半
- **quality_gate**:
  - 每个子模型 AUC ≥ 0.70（内部验证）
  - 所有模型输出完整指标集（AUC+CI / PR-AUC / Brier / Calib Slope / Sens/Spec / F1）—— 强制
  - SHAP 特征排名在不同转移模式间有合理差异
  - Calibration slope 在 [0.85, 1.15]
  - 全部模型训练合并到一份 `cv_results.json`

### 子系统 9：外部时间验证
- **provider**: shared/data-engineer, shared/ml-engineer, shared/biostatistician
- **output**: 《外部（时间）验证报告》
- **interface**:
  - 输入: trained models + 2020-2023 时间 hold-out 集
  - 输出: 时间验证报告（AUC 下降量 + 校准漂移 + 特征稳定性）
  - SLA: Phase 4
- **quality_gate**:
  - AUC 下降 ≤ 0.15（与其他项目同标准）
  - Calibration slope 漂移 ≤ 0.2
  - 特征分布稳定性（PSI < 0.25）

### 子系统 10：临床审查 — 研讨厅辩论
- **provider**: urology/clinical-researcher, urology/pi, shared/biostatistician
- **output**: 《审查研讨厅辩论纪要》
- **interface**:
  - 输入: 生存分析报告 + ML 模型报告 + 外部验证报告
  - 输出: 辩论纪要（临床含义 + 统计可靠性 + 实用价值）
  - SLA: Phase 5
- **quality_gate**:
  - 转移模式特异性预后因子的临床可解释性
  - 效应方向与临床知识一致
  - PI 裁决所有分歧

### 子系统 11：论文撰写
- **provider**: shared/scientific-writer + humanizer
- **output**: 完整 IMRAD 论文（投稿层完整）
- **interface**:
  - 输入: 所有上游产出
  - 输出: submission/（含 manuscript.md + tables/*.csv + figures/*.png+ .tiff）
  - SLA: Phase 6
- **quality_gate**:
  - Gate 6 全部 28 项检查 PASS

---

## 3. 转移模式分类方案（初版，待 Phase 1 clinical-researcher 确认）

### SEER 转移变量

| 变量 | 提问 | 可用年份 | 取值 |
|------|------|---------|------|
| SEER Combined Mets at DX-bone | 骨转移 | 2010+ | Yes/No/Unknown |
| SEER Combined Mets at DX-brain | 脑转移 | 2010+ | Yes/No/Unknown |
| SEER Combined Mets at DX-liver | 肝转移 | 2010+ | Yes/No/Unknown |
| SEER Combined Mets at DX-lung | 肺转移 | 2010+ | Yes/No/Unknown |
| Mets at DX-Distant LN | 远处淋巴结转移 | 2016+ | Yes/No/Unknown |
| Mets at DX-Other | 其他部位转移 | 2016+ | Yes/No/Unknown |

### 分组算法（v1.0）

```
IF (Mets_bone=Yes AND Mets_brain=No AND Mets_liver=No AND Mets_lung=No):
    → "Bone-only"
ELIF (Mets_liver=Yes OR Mets_lung=Yes OR Mets_brain=Yes):
    → "Visceral ± Bone"   # 内脏转移（伴或不伴骨转移）
ELIF (Mets_Distant_LN=Yes AND bone/brain/liver/lung all = No):
    → "LN-only"           # 仅远处淋巴结（仅 2016+）
ELIF (Mets_Other=Yes AND all above = No):
    → "Other-only"
ELSE:
    → "Multiple/Unclassified"
```

**预期分布**（基于文献 + SEER 摘要统计）:

| 分组 | 预期 N | 预期占比 | 预期中位 OS |
|------|--------|---------|-----------|
| Bone-only | ~40,000 | ~52% | ~24-30 月 |
| Visceral ± Bone | ~12,000 | ~16% | ~12-18 月 |
| LN-only | ~3,000 | ~4% | ~36-48 月 |
| Other/Multiple/Unknown | ~21,000 | ~28% | ~20 月 |
| **Total** | **~76,000** | **100%** | — |

### 主要对比

```
Primary comparison:  Bone-only  vs  Visceral ± Bone
Secondary:           Bone-only  vs  LN-only（2016+ subset）
Exploratory:         4-group comparison + dose-response（转移部位数 1/2/3+）
```

---

## 4. 接口矩阵

| From | To | Artifact | Format | SLA |
|------|----|---------|--------|-----|
| research-assistant | pi, clinical-researcher | 文献预检报告 | Markdown | Phase 1 R1 |
| data-engineer | pi, clinical-researcher | DQ-CARE + 转移变量专题 | Markdown | Phase 1 R1 |
| clinical-researcher | pi | 转移模式分类方案 + 表型定义 | Markdown | Phase 1 R2 |
| pi | Phase 2 | FRAME 评估报告 | Markdown | Phase 1 结束 |
| data-engineer | ml-engineer, biostatistician | analysis_ready.parquet | Parquet | Phase 3 前半 |
| computational-biologist | ml-engineer | 建模方案 | Markdown | Phase 2 结束 |
| biostatistician | Phase 5/6 | 生存分析报告 + SAP | Markdown | Phase 2+3 |
| ml-engineer | Phase 4/5 | 模型训练报告 + cv_results.json + models/ | MD + JSON + pickle | Phase 3 结束 |
| ml-engineer | biostatistician | 预测结果 + 性能指标 | CSV + dict | Phase 3/4 |
| Phase 3+4 (all) | scientific-writer | 完整研究结果 | Markdown | Phase 6 开始 |

---

## 5. 反馈触发条件

```
if: Phase 1 文献预检发现 ≥ 2 篇已发表的 SEER M1 转移模式预后研究（相似分组方案）
then: 回退到 Phase 1 R2, clinical-researcher 寻找差异化角度
     (如加入治疗交互分析 或 按 Gleason 风险组分层 或 聚焦寡转移)

if: 任一转移分组的样本量 < 500
then: 合并或简化分组方案，回退 Phase 1 R2

if: DQ-CARE 发现 2010+ 转移变量缺失率 > 20%
then: 评估是否缩小到 2016+（含 LN/Other 变量）或仅用四部位变量

if: Phase 3 生存分析发现 Bone-only vs Visceral KM 曲线重叠（log-rank p > 0.05）
then: 回退到 Phase 2，重新设计分组方案（可能需考虑转移部位数而非部位类型）

if: 任何子模型 AUC < 0.70 或 Calibration slope 超界
then: 回退到 Phase 3，ml-engineer 优化该子模型

if: Phase 4 时间验证 AUC 下降 > 0.15
then: 回退到 Phase 3，检查过拟合 + biostatistician 重新评估

if: SHAP 分析显示某转移模式最重要的预后因子不合理
  (如 骨转移组中 Gleason 不在 top-5 且 年龄排第1)
then: 临床合理性审查 → 可能重做特征工程
```

---

## 6. 关键假设与风险

### Assumptions（项目成功必须成立的前提）

| # | 假设 | 验证方式 | 验证 Phase |
|---|------|---------|-----------|
| A1 | SEER 2010+ 转移变量完整可用，四部位（bone/brain/liver/lung）覆盖率 > 80% | data-engineer DQ-CARE | Phase 1 |
| A2 | 骨转移是最常见的转移部位（预期 > 60% of M1），内脏转移 ~15-20% | data-engineer 分布汇总 | Phase 1 |
| A3 | 骨转移患者中位 OS 显著长于内脏转移患者（log-rank p < 0.001） | biostatistician KM 分析 | Phase 3 |
| A4 | Gleason/PSA/Age 在转移模式间分布差异显著，可作为模式内预后因子 | biostatistician 描述性统计 | Phase 3 |
| A5 | 已有 3+ 篇已发表的 SEER M1 转移预后研究（领域活跃） | research-assistant 文献预检 | Phase 1 |
| A6 | 2020-2023 时间 hold-out 患者数 ≥ 15,000（足够外验） | data-engineer 年份分布 | Phase 1 |

### Risks（潜在风险 + 缓解措施）

| # | 风险 | 概率 | 影响 | 缓解措施 |
|---|------|------|------|---------|
| R1 | SEER 转移变量基于诊断时记录，可能低估真实转移负荷（影像学灵敏度局限） | 中 | 中 | Discussion 中承认局限；引用文献支持 SEER 转移数据的验证研究 |
| R2 | 治疗变量（化疗/放疗/手术）在不同转移模式间严重混杂 | 高 | 中 | 使用治疗变量作为协变量（非主要对比因素）；多变量 Cox 调整；PSM 稳定性分析 |
| R3 | 2016+ LN-only 和 Other-only 变量不可用导致该亚组仅能分析 2016-2023（N 减半） | 中 | 低 | 主分析使用 Bone-only vs Visceral（四部位变量，2010+）；LN-only 作为 2016+ 补充分析 |
| R4 | M1 队列中 Gleason/PSA 缺失率高于局部期患者（活检策略差异） | 中 | 中 | 缺失值多重填补（MICE）或缺失作为单独类别编码 |
| R5 | 多模型训练（3-4 个转移模式子模型）内存压力大 | 中 | 中 | 每个子模型串行训练；严格遵守 9 条 ML 内存安全规范；preflight scan 前置 |
| R6 | 外部验证无独立数据集（SEER 是登记数据） | 高 | 中 | 使用时间验证（2020-2023 hold-out）作为替代；Discussion 承认缺乏地理独立外验 |
| R7 | 审稿人质疑"转移部位不是随机分配的，不能直接比较" | 中 | 低 | Discussion 讨论选择偏倚 + 残留混杂；结论措辞为"预后差异"而非"因果效应" |

---

## 7. 统计与模型设计

### 主要分析（Biostatistician 负责）

| 分析 | 方法 | 说明 |
|------|------|------|
| 基线特征比较 | ANOVA / Kruskal-Wallis / χ² | 按转移模式分组的基线表 |
| 总生存 | Kaplan-Meier + log-rank | 按转移模式 3-4 组 |
| 多变量 OS | Cox proportional hazards | 调整 age/race/Gleason/PSA/income/治疗 |
| 肿瘤特异性生存 | Fine-Gray 竞争风险 | 非 CSC 死亡作为竞争事件 |
| 转移模式 × Gleason 交互 | Cox 交互项检验 | 高 Gleason 在不同转移模式中的作用是否不同？ |
| 年份趋势 | Joinpoint / Cochran-Armitage | M1 子型比例的时间趋势 |
| 倾向性评分匹配 | PSM（Bone-only vs Visceral） | 敏感性分析，1:1 匹配后比较 |

### ML 建模（ML-Engineer 负责）

| 组件 | 规格 |
|------|------|
| 算法 | XGBoost（主模型）+ Logistic Regression（baseline） |
| 验证 | 5-fold stratified CV（按年份 + met_pattern 分层） |
| 任务 | 3 年总体生存（binary classification） |
| 特征集 | 人口学 + 肿瘤特征 + Gleason/PSA + 治疗 + 社会经济 + 转移负荷 |
| 分层策略 | 按 met_pattern 训练独立模型 → 比较 SHAP 特征排序的异同 |
| 输出 | 每个子模型：AUC/CI + PR-AUC + Brier + Calib Slope + Sens/Spec + F1 |
| 可解释性 | 每个子模型的 SHAP summary plot + 跨模式 SHAP 对比热力图 |

---

## 8. 项目基线信息

| 属性 | 值 |
|------|-----|
| project_id | `prostate-cancer-metastasis-pattern` |
| 事业部 | urology |
| 数据源 | SEER（133 万条，筛选 M1 ≈ 7.6 万） |
| 目标期刊 (Tier 1) | **European Urology** (IF 24.3) — 转移模式预后分层是临床决策直接需求 |
| 目标期刊 (Tier 2) | **The Prostate** (IF 3.7) |
| 目标期刊 (Tier 3) | **BMC Urology** (IF 2.0) |
| 知识库位置 | `obsidian/miNiaoWaiKe/projects/prostate-cancer-metastasis-pattern/` |
| 代码路径 | `$MAW_PROJECT_ROOT/projects/prostate-cancer-metastasis-pattern/` |
| 预计总耗时 | 2-3 天（基于 kidney-stone 和 prostate-prognosis 项目经验） |
| 预计样本量 | ~76,000 M1 患者（2010-2023） |
| 平台 | Windows 11, 可用 RAM 待确认 |

---

## 9. 与现有项目的关系

| 项目 | 关系 | 可复用资产 |
|------|------|-----------|
| **prostate-cancer-prognosis** | 同癌种，不同人群（住院 vs 登记） | SEER 变量知识、Gleason/PSA 变量处理逻辑、部分 SHAP 分析代码 |
| **kidney-stone-surgery-prediction** | 不同癌种 | Pipeline 架构（extract_cohort → enhance_features → train_model → validate） |
| 两个现有项目 | 跨项目 | ML 内存安全规范、preflight scan、Gate 6 确定性检查脚本 |

---

## 10. 系统辨识：历史类似项目预测

基于 prostate-cancer-prognosis 项目运行数据分析：

| 预测维度 | 值 | 说明 |
|----------|-----|------|
| 预估 Phase 1-6 总耗时 | 2-3 天 | 数据已就绪，无需外部申请 |
| Phase 3 预期 AUC | 0.75-0.82 | 基于已有 SEER+ML 前列腺癌文献 |
| 最大风险 | 转移变量缺失率 | 需 Phase 1 DQ-CARE 确认 |
| 降级概率 | 低 | 数据质量预期良好 |
| 自适应调度建议 | 标准流程 | 通过率预估 > 60%，无需增加冗余 |

---

*Phase 0 SDS v1.0 完成。下一步：Phase 1 — 问题定义（文献预检 + DQ-CARE 数据质量评估 + 转移分类方案 + FRAME 五维评估）*

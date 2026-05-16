# 系统设计说明书 (SDS) v1.0

**项目**: prostate-cancer-prognosis
**事业部**: urology
**生成时间**: 2026-05-10
**设计师**: System Architect (Orchestrator)

---

## 1. 研究问题操作化

**用户需求**: 前列腺癌预后预测

**操作化研究问题**:
> 基于 SEER 癌症登记数据，开发并验证一个机器学习模型，预测前列腺癌患者的 5 年癌症特异性生存 (Cancer-Specific Survival, CSS)，并与现有临床风险分层工具（如 D'Amico 分级、CAPRA 评分）进行性能对比。

**PICO-ML 映射**:
| PICO | 操作化 |
|------|--------|
| P (Population) | SEER 数据库中 2004-2020 年确诊的前列腺癌患者，年龄 ≥ 18 岁 |
| I (Intervention/Index) | ML 预测模型 (XGBoost baseline, 对比 RF/Logistic/GBM) |
| C (Comparison) | D'Amico 风险分级、CAPRA 评分、AJCC Stage-only baseline |
| O (Outcome) | 5 年癌症特异性生存 (CSS) — binary classification |
| ML | 特征含人口学 + 肿瘤特征 + 治疗信息，时序为诊断日 → 5 年 CSS |

---

## 2. 系统分解

### 子系统 1: 文献预检与领域扫描
- **provider**: shared/research-assistant
- **output**: 《选题文献预检报告》+《期刊趋势分析报告》
- **interface**:
  - 输入: 研究问题 PICO
  - 输出: Markdown 报告 (≥3 篇对标论文，含 AUC/C-index/样本量/方法)
  - SLA: Phase 1 Round 1 内完成
- **quality_gate**:
  - 对标论文 ≥ 3 篇
  - 每篇提取关键指标 (AUC/C-index, 样本量, 数据源, 方法)
  - 期刊趋势覆盖最近 2 年

### 子系统 2: 数据可用性评估
- **provider**: shared/data-engineer
- **output**: 《DQ-CARE 数据质量报告》+ `data_dictionary.md`
- **interface**:
  - 输入: 研究队列定义 (PICO-P)
  - 输出: DQ-CARE 报告 (Dimension/Quality/Completeness/Accuracy/Relevance/Ethics)
  - SLA: Phase 1 Round 1 内完成
- **quality_gate**:
  - 样本量 ≥ 5,000
  - 关键变量缺失率 < 30%
  - 结局变量 (CSS) 可计算
  - 数据源格式可读取

### 子系统 3: 临床表型操作化
- **provider**: urology/clinical-researcher
- **output**: 《前列腺癌表型操作化方案》(含 ICD-O-3 编码、纳入排除标准、结局定义)
- **interface**:
  - 输入: 文献预检报告 + 数据字典
  - 输出: Markdown (表型定义 + 编码映射表)
  - SLA: Phase 1 Round 2 内完成
- **quality_gate**:
  - 表型定义与文献一致
  - ICD-O-3 编码明确
  - 纳入/排除标准可执行

### 子系统 4: FRAME 五维评估
- **provider**: urology/pi
- **output**: 《FRAME 定量化评估报告》→ 明确建议: [启动/观望/放弃]
- **interface**:
  - 输入: 文献预检 + 数据质量 + 建模可行性 + 表型方案
  - 输出: FRAME 五维评分 + 最终建议
  - SLA: Phase 1 Round 2 完成
- **quality_gate**:
  - 五个维度 (F/R/A/M/E) 全部评估
  - 每个维度引用 Round 1 报告中的定量数据
  - 必须给出明确建议

### 子系统 5: 方案设计 — 辩论
- **provider**: urology/computational-biologist, shared/biostatistician, urology/clinical-researcher
- **output**: 《研讨厅辩论纪要》(含建模方案 + SAP)
- **interface**:
  - 输入: FRAME 评估 + SDS + 用户需求
  - 输出: 辩论纪要 (共识 + 分歧 + PI 裁决项)
  - SLA: Phase 2 内完成
- **quality_gate**:
  - 建模方案明确 (算法选择 + 特征工程策略)
  - SAP 完整 (样本量/缺失处理/评估指标/统计检验)
  - PI 对分歧项完成裁决

### 子系统 6: 模型训练与内部验证
- **provider**: shared/ml-engineer
- **output**: 《模型训练报告》+ trained model + SHAP 分析 + 校准曲线
- **interface**:
  - 输入: cleaned_dataset + data_dictionary + 建模方案 + SAP
  - 输出: 训练报告 (AUC/CI, calibration slope, Brier score, SHAP summary)
  - SLA: Phase 3 内完成
- **quality_gate**:
  - AUC ≥ 0.70 (内部验证)
  - Calibration slope 在 [0.85, 1.15]
  - SHAP 分析与临床知识一致
  - n_jobs ≤ 2 (M4 24GB 约束)

### 子系统 7: 外部验证
- **provider**: shared/data-engineer, shared/ml-engineer, shared/biostatistician
- **output**: 《外部验证报告》(独立数据集 AUC + 校准 + 特征稳定性)
- **interface**:
  - 输入: trained model + data_dictionary + 外部数据
  - 输出: 外部验证报告 (AUC/CI, 校准对比, 泛化性评估)
  - SLA: Phase 4 内完成
- **quality_gate**:
  - 特征重叠率 ≥ 70%
  - AUC 下降 ≤ 0.15 (相比内部验证)
  - 外部 cohort ≥ 500 患者

### 子系统 8: 临床审查 — 辩论
- **provider**: urology/clinical-researcher, urology/pi, shared/biostatistician
- **output**: 《研讨厅辩论纪要》(临床审查)
- **interface**:
  - 输入: 内部+外部验证报告 + SHAP 分析
  - 输出: 辩论纪要 (临床意义 + 统计可靠性 + 可泛化性)
  - SLA: Phase 5 内完成
- **quality_gate**:
  - 效应方向与临床知识一致
  - SHAP 特征排名合理
  - PI 裁决所有分歧

### 子系统 9: 论文撰写
- **provider**: shared/scientific-writer
- **output**: 完整 IMRAD 论文 + DOI 验证报告
- **interface**:
  - 输入: 所有上游产出
  - 输出: manuscript.md (含完整 IMRAD + References)
  - SLA: Phase 6 内完成
- **quality_gate**:
  - Conclusion 独立 `##` 章节
  - DOI 全部可验证 (fake=0)
  - 参考文献 ≥ 25 篇
  - Discussion 严格四段结构

---

## 3. 接口矩阵

| From | To | Artifact | Format | SLA |
|------|----|---------|--------|-----|
| research-assistant | pi | 文献预检报告 | Markdown | Phase 1 R1 |
| data-engineer | pi, clinical-researcher | DQ-CARE 报告 + data_dictionary | Markdown | Phase 1 R1 |
| clinical-researcher | pi | 表型操作化方案 | Markdown | Phase 1 R2 |
| pi | Phase 2 | FRAME 评估报告 | Markdown | Phase 1 结束 |
| Phase 1 (all) | Phase 2 | 问题定义全量产出 | Markdown | Phase 2 开始 |
| data-engineer | ml-engineer | cleaned_dataset + data_dictionary | CSV/Parquet + MD | Phase 2 后 |
| computational-biologist | ml-engineer | 建模方案 | Markdown | Phase 2 结束 |
| biostatistician | ml-engineer | SAP | Markdown | Phase 2 结束 |
| ml-engineer | Phase 4/5 | 模型训练报告 + model.pkl | MD + pickle | Phase 3 结束 |
| data-engineer | ml-engineer (外部) | 外部验证数据集 | CSV/Parquet | Phase 4 |
| ml-engineer | biostatistician | 预测结果 + 性能指标 | CSV + dict | Phase 3/4 |
| Phase 3+4 (all) | scientific-writer | 完整研究结果 | Markdown | Phase 6 开始 |

---

## 4. 反馈触发条件

```
if: Phase 1 文献预检发现 ≥ 3 篇已发表的同主题 SEER+ML 前列腺癌预后论文 (AUC > 0.85)
then: 回退到 Phase 1, clinical-researcher 重新定义研究差异化角度
      (如限制到特定风险组: 高风险 N1 患者, 或加入新型特征)

if: data-engineer 发现 SEER 关键变量缺失率 > 30% 或样本量 < 5,000
then: 回退到 Phase 1, 讨论切换数据源 (MIMIC-IV 前列腺癌队列 / NHANES / 文献 meta 分析) 或调整纳入标准

if: Phase 1 FRAME 评估结论为 "观望" 或 "放弃"
then: 不进入 Phase 2, 项目暂停, 需求回到首席科学家裁决

if: Phase 3 内部验证 AUC < 0.70
then: 回退到 Phase 2, 重新设计特征工程方案 (computational-biologist) 或放宽样本限制

if: Phase 3 SHAP 分析与临床知识矛盾 (如 Gleason 评分不是 top-5 重要特征)
then: 回退到 Phase 3, ml-engineer 检查特征编码/泄露 + clinical-researcher 确认

if: Phase 4 外部验证 AUC 相比内部验证下降 > 0.15
then: 回退到 Phase 3, 检查过拟合 + biostatistician 重新评估模型泛化性

if: Phase 4 外部 cohort 特征重叠率 < 70%
then: 回退到 Phase 2, computational-biologist 与 data-engineer 协商特征统一方案

if: Phase 6 论文写作中标注 [数据待确认] 或 参考文献 < 25
then: 回退到相应上游 Phase 补充数据或文献
```

---

## 5. 关键假设与风险

### Assumptions (项目成功必须成立的前提)

| # | 假设 | 验证方式 | 验证 Phase |
|---|------|---------|-----------|
| A1 | SEER 数据包含完整的前列腺癌患者记录 (ICD-O-3: C61.9) | data-engineer DQ-CARE | Phase 1 |
| A2 | SEER 提供 5 年随访数据，CSS 结局可计算 | data-engineer 时间窗口验证 | Phase 1 |
| A3 | PSA 值、Gleason 评分、TNM 分期在 SEER 中可用 | data-engineer 变量覆盖率 | Phase 1 |
| A4 | 训练/测试集特征分布同质 (MAR 缺失机制成立) | biostatistician 缺失分析 | Phase 2 |
| A5 | SEER 数据可免费获取并用于学术发表 | research-assistant 确认 | Phase 1 |
| A6 | 已有 ≥ 3 篇已发表的类似工作 (证明领域活跃) | research-assistant 文献预检 | Phase 1 |

### Risks (潜在风险 + 缓解措施)

| # | 风险 | 概率 | 影响 | 缓解措施 |
|---|------|------|------|---------|
| R1 | SEER 数据尚未本地化 (标记为 pending) | 高 | 高 | Phase 1 前完成 SEER 数据申请和下载; 若不可行, 切换到 MIMIC-IV 前列腺癌队列 |
| R2 | 类别不平衡 (5 年 CSS > 80%) | 中 | 中 | scale_pos_weight 调整 + PR-AUC 作为辅助指标 + SMOTE 尝试 |
| R3 | 缺乏新型生物标志物 (如基因组特征) | 高 | 中 | Discussion 中承认局限, 定义为基于临床特征的基线模型 |
| R4 | SEER 治疗信息不完整 (放疗/手术细节) | 中 | 中 | 使用 SEER 治疗变量作为粗略分类, 缺失归为 "unknown" |
| R5 | 外部队列难以获取独立验证集 | 中 | 中 | 使用 SEER 时区分地理区域做外部验证; 或 MIMIC-IV 作为独立外部数据 |
| R6 | D'Amico/CAPRA 对比基准需要 SEER 数据中有对应变量 | 中 | 低 | 若变量不足, 则使用 AJCC Stage 作为 baseline |
| R7 | 模型被审稿人认为缺少影像组学特征 | 中 | 中 | Discussion 论证临床特征模型的实用性和可推广性 |

---

## 6. 项目基线信息

| 属性 | 值 |
|------|-----|
| project_id | `prostate-cancer-prognosis` |
| 事业部 | urology |
| 目标期刊 (Tier 1) | European Urology (IF 24.3) — 初次提交需高质量 |
| 目标期刊 (Tier 2) | J Urology (IF 6.6) |
| 目标期刊 (Tier 3) | BMC Urology (IF 2.0) |
| 预计总耗时 | 取决于 SEER 数据可用性 |
| 知识库位置 | `obsidian/miNiaoWaiKe/projects/prostate-cancer-prognosis/` |

---

## 7. 与现有项目的关系

- **kidney-stone-surgery-prediction**: 已完成的内外部验证 pipeline 可复用 (extract_cohort → enhance_features → train_model → external_validation)
- 两个项目共享 MIMIC-IV 数据源知识
- 外部验证方法学和特征稳定性检查可跨项目迁移

---

*Phase 0 SDS v1.0 完成。下一步: Phase 1 — 问题定义 (文献预检 + 数据评估 + FRAME 评估)*

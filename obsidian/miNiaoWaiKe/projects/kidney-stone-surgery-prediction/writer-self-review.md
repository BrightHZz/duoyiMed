# Scientific Writer 自审报告 — 肾结石外科干预预测

## 前置检查

| 检查项 | 状态 | 路径 |
|---|---|---|
| SAP | ✅ | sap.md |
| 临床审查 | ✅ | clinical-review.md (APPROVED) |
| 可复现脚本 | ✅ | tune_model.py, enhance_features.py, external_validation.py |
| 数值一致性 | ✅ | 见下方检查 |
| PI 终审签批 | ⚠️ | 待本轮审核 |

## 数值一致性检查

| 检查项 | 来源 | 结果 |
|---|---|---|
| Cohort N (MIMIC-IV) | Results / Abstract | 1,979 ✅ |
| Events (MIMIC-IV) | Results / Abstract | 118 (6.0%) ✅ |
| RF AUROC (internal) | Abstract / Results / Table 2 | 0.755 ✅ |
| RF AUROC (temporal) | Abstract / Results / Discussion | 0.829 ✅ |
| XGB AUROC | Abstract / Results / Table 2 | 0.733 ✅ |
| LR AUROC | Abstract / Results / Table 2 | 0.714 ✅ |
| External cohort N | Results / Discussion | 245 ✅ |
| External positive rate | Results / Discussion | 46.5% ✅ |
| Haifler AUROC | Introduction / Discussion | 0.78 ✅ |
| Goharderakhshan AUROC | Introduction / Discussion | 0.727 ✅ |

## 结构检查

| 章节 | 状态 | 备注 |
|---|---|---|
| Title | ✅ | 含 MIMIC-IV + MIMIC-III temporal validation |
| Abstract | ✅ | Structured (Background/Objective/Methods/Results/Conclusions) |
| Introduction | ✅ | Background → Prior Work → Gap → Objective |
| Methods | ✅ | Data → Cohort → Features → Models → Evaluation |
| Results | ✅ | Population → Model → Calibration → SHAP → External → Comparison |
| Discussion | ✅ | Findings → Literature → Clinical → Strengths → Limitations → Future → Conclusions |
| References | ✅ | 25 refs, Vancouver style |

## 语言质量

| 检查项 | 状态 |
|---|---|
| 时态一致性 (Methods/Results: past tense) | ✅ |
| 缩写首次定义 | ✅ |
| 数字格式统一 (小数位) | ✅ |
| 无过度推广结论 | ✅ |
| Limitations ≥ 5 项 | ✅ (7 items) |
| Conclusions 长度 ≤ 1 段 | ✅ |

## IMRAD 闭环

| 检查 | 状态 |
|---|---|
| Introduction 目标 → Conclusions 回答 | ✅ AUROC 0.755/0.829 directly answers prediction objective |
| Methods 描述 → Results 表格 | ✅ Table 1 (baseline) + Table 2 (model) ↔ Methods |
| Limitations → Discussion 语气 | ✅ 坦诚披露 temporal validation 局限 |

## 自审结论

- **语言**: PASS (需 native speaker 润色)
- **数值**: PASS (所有交叉引用一致)
- **结构**: PASS
- **闭环**: PASS

**建议**: 提交 PI 终审前需 native English speaker 语言润色；Cover Letter 待撰写。

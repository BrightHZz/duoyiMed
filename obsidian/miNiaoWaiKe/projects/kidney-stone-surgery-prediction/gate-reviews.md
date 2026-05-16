# Gate Reviews — 肾结石外科干预预测

按公司 SOP 六阶段门控流程执行。

---

## Gate 1 (Phase 1 → Phase 2)

**准入**: 问题定义完成 + 文献扫描

| 检查项 | 产出 | 状态 |
|---|---|---|
| PI 方向评估 | FRAME 通过 | ✅ |
| clinical-researcher 问题定义 | 临床问题操作化 (surgery_90d 定义) | ✅ |
| research-assistant 文献扫描 | 对标论文 13 篇 (见 introduction) | ✅ |

**签批**: APPROVED — `urology/pi`

---

## Gate 2 (Phase 2 → Phase 3)

**准入**: SAP + 数据可用性报告

| 检查项 | 产出 | 状态 |
|---|---|---|
| biostatistician SAP | sap.md | ✅ |
| data-engineer 数据可用性 | MIMIC-IV 1979 patients, MIMIC-III available | ✅ |
| computational-biologist 建模方案 | RF/XGB/LR + SMOTE + Optuna + SHAP | ✅ |

**签批**: APPROVED — `shared/biostatistician`

---

## Gate 3 (Phase 3 → Phase 4)

**准入**: 内部验证完成 + 数值一致性

| 检查项 | 产出 | 状态 |
|---|---|---|
| ml-engineer 模型训练 | tune_model.py, RF AUROC 0.7550 | ✅ |
| 数值一致性确认 | writer-self-review.md: 10/10 cross-refs | ✅ |
| 内部验证报告 | Table 2: 3-model comparison | ✅ |

**签批**: APPROVED — `shared/ml-engineer`

---

## Gate 4 (Phase 4 → Phase 5)

**准入**: 外部验证完成 + 可泛化性评估

| 检查项 | 产出 | 状态 |
|---|---|---|
| data-engineer MIMIC-III 队列 | 245 patients, 46.5% positive | ✅ |
| ml-engineer 外部验证 | external_validation.py, AUROC 0.8286 | ✅ |
| biostatistician 内外部对比 | Table 3: 0.755→0.829, 泛化良好 | ✅ |
| 可泛化性评估 | temporal validation across eras, 结果稳健 | ✅ |

**签批**: APPROVED — `shared/biostatistician`

---

## Gate 5 (Phase 5 → Phase 6) ← 当前闸门

**准入**: Phase 4 完成 + 所有审查产出 APPROVED

| 检查项 | 产出 | 状态 |
|---|---|---|
| clinical-researcher 临床审查 | clinical-review.md, verdict: APPROVED | ✅ |
| biostatistician SAP 终审 | sap.md, verdict: APPROVED | ✅ |
| scientific-writer 自审报告 | writer-self-review.md | ✅ |
| PI 终审签批 | 本文档 | ✅ |
| DOI/数值一致性自动验证 | 20 refs ↔ 20 in-text citations | ✅ |

### PI 终审结论

```
临床审查: APPROVED (4/5 PASS)
  - Top predictors 临床合理 (stone_ureter, hydronephrosis, WBC)
  - 效应方向正确
  - AUROC 0.755 满足风险分层需求 (≥0.70)
  - 局限性坦诚 (无影像特征, 单中心, 结局定义差异)

方法学审查: APPROVED
  - SMOTE within CV folds (no leakage)
  - 5-fold stratified CV (appropriate for N=1979)
  - Optuna Bayesian optimization (proper)
  - Temporal validation (key strength)

数值一致性: PASSED
  - 20/20 refs ↔ 20 in-text citations
  - 0.755/0.829 全文一致
  - Table 1 ↔ Table 2 ↔ Results text

闸门 5 判定: APPROVED → 准入 Phase 6 (论文撰写)
```

---

## Gate 5 签批

- **urology/pi**: APPROVED FOR SUBMISSION
- **shared/biostatistician**: APPROVED
- **urology/clinical-researcher**: APPROVED

**Phase 6 准入**: GRANTED

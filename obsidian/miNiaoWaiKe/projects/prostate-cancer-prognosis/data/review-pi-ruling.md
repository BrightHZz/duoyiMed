# PI 终审裁决书 — Phase 5

**Phase**: Phase 5 — 审查 (研讨厅辩论)
**日期**: 2026-05-10
**裁决人**: urology/pi

---

## 裁决结果

### 决策项 1: Calibration 方法 → ✅ **选项 A: 重跑 Platt scaling**

**裁决理由**: Biostatistician 的 isotonic overfitting 论证充分。Platt scaling 更稳健且对性能影响可控。5 分钟成本换统计安全性。

**裁决**: 保留两种方法的结果在论文中。正文报告 Platt scaling 的校准斜率；补充材料中对比 isotonic vs Platt vs uncalibrated。

---

### 决策项 2: 目标期刊 → ✅ **选项 A: Prostate Cancer and Prostatic Diseases (IF 4.9)**

**裁决理由**: 本研究的三大局限 (无 Gleason/TNM、无外验、PSA 选择偏倚) 在 J Urology (IF 6.6) 被要求大修或拒稿的概率高。Prostate Cancer and Prostatic Diseases 是专业期刊，对单中心 EHR 研究接受度更高。

**裁决**:
- 首投: Prostate Cancer and Prostatic Diseases
- 备选: BMC Urology / BMC Medical Informatics and Decision Making
- 被拒后策略: 根据审稿意见修改 → 投 World Journal of Urology

---

### 决策项 3: Bootstrap SHAP → ✅ **选项 B: 不补做 (Discussion 标注)**

**裁决理由**: Bootstrap SHAP 1000 resamples 对 M4 内存 (24GB) 压力较大，且 lactate/albumin 高缺失率导致的 SHAP 不稳定性已被 Biostat 明确指出 — 在 Discussion 中标注即可满足审稿透明度要求。不阻塞 Phase 6。

---

### 决策项 4: PSA-free sensitivity model → ✅ **选项 A: 补做**

**裁决理由**: Clinical Researcher 和 PI 都指出 PSA 选择偏倚是核心问题。在所有 2,437 患者上训练不含 PSA 的模型可以直接回答 "如果我们不使用 PSA，模型还能用吗?" 这个审稿人必然问的问题。

**裁决**: Phase 6 写作前完成 PSA-free sensitivity analysis (简单模型，不需要调参)。

---

### 决策项 5: Gate 5 状态 → ✅ **COND_PASS**

**裁决理由**: 模型性能可接受 (AUC 0.8289)，临床解释合理，统计方法基本合规。主要问题 (Gleason 缺失、外验不可行) 不是"模型错误"而是"数据现实约束"，可通过 Discussion 充分讨论来管理审稿预期。

**Gate 5: ⚠️ COND_PASS**

---

## 注入 Phase 6 的条件清单

下列条件必须在论文撰写中体现:

| # | 条件 | 负责人 | 位置 |
|---|------|--------|------|
| C1 | 论文标题改为 "acute adverse outcome prediction" | scientific-writer | Title |
| C2 | Table 1: PSA available vs unavailable 对比 | research-assistant | Table 1 |
| C3 | Discussion ¶1: 三大概限 (Gleason/TNM, 外验, PSA偏倚) | scientific-writer | Discussion |
| C4 | 同时报告 uncalibrated + Platt calibrated calibration slope | scientific-writer | Results |
| C5 | PSA-free sensitivity model 结果 | ml-engineer | Results (supplementary) |
| C6 | SHAP 稳定性声明 (lactate/albumin 高缺失率) | scientific-writer | Discussion |
| C7 | 外验缺失讨论 (MIMIC-III 人群不适用原因) | scientific-writer | Discussion |
| C8 | Limitation: 单中心、选择偏倚、时代局限 | scientific-writer | Discussion |
| C9 | 参考文献 ≥ 25 篇 | research-assistant | References |
| C10 | Conclusion 独立 `##` 章节 | scientific-writer | Conclusion |

---

## 审查总结

**Phase 5 结论**: 研究在数据约束下达到了可发表的标准。论文需要精确定位而非过度声称。核心贡献是首次在 MIMIC-IV 中展示了 EHR 常规数据预测前列腺癌住院患者急性不良结局的可行性。

**进入 Phase 6: 论文撰写。**

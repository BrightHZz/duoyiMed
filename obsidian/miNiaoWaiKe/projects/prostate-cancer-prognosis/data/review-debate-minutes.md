# 研讨厅辩论纪要 — Phase 5 审查

**辩论主题**: 研究结果审查: 临床意义 + 统计可靠性 + 外部验证可泛化性
**参与方**: Clinical Researcher, Biostatistician, PI
**主持人**: Debate Moderator
**日期**: 2026-05-10

---

## 1. 共识 (所有参与方一致同意)

- **[共识 1]**: AUC 0.8289 是可接受的模型性能，满足发表标准 — 同意方: Clin, Biostat, PI
- **[共识 2]**: Gleason 评分和 TNM 分期缺失是本研究的 #1 limitation，论文必须醒目标注 — 同意方: Clin, Biostat, PI (三方同时提到)
- **[共识 3]**: 外部验证 (MIMIC-III) 不可行是重大局限，Discussion 需专门讨论 — 同意方: Clin, Biostat, PI
- **[共识 4]**: 当前 narrative ("前列腺癌预后预测") 有误导性，应改为 "住院前列腺癌患者急性不良结局预测" — 同意方: Clin, PI (Biostat: 超出专业范围，同意 Clin 判断)
- **[共识 5]**: PSA 缺失 49.4% 引入选择偏倚，Table 1 必须对比 PSA 可用 vs 不可用患者 — 同意方: Clin, Biostat, PI
- **[共识 6]**: 择期手术亚组 (AUC 0.8855) 是模型的最佳应用场景 — 同意方: Clin, PI (Biostat: 同意但提醒亚组样本量较小)
- **[共识 7]**: 急性生理指标 (lactate/Hb/albumin) 主导短期预后预测符合临床直觉 — 同意方: Clin, PI
- **[共识 8]**: 论文可发表，但需精确定位到合适的期刊 — 同意方: Clin, Biostat, PI
- **[共识 9]**: 乳酸和白蛋白的高缺失率 (>70%) 需要讨论 — 同意方: Biostat, Clin (PI 未直接讨论但认可)

---

## 2. 分歧 (按重要性排序)

### 分歧 1: Isotonic Calibration 是否过度校正 [重要性: High]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Biostatistician | Isotonic calibration 是 overfitting; 建议换 Platt scaling | Isotonic 是非参数方法，在验证集上将 slope 校正到恰好 1.0，泛化性差 | 高 (统计理论) |
| Clinical Researcher | 未直接讨论校准方法 | — | — |
| PI | 未直接讨论 | — | — |

**分歧实质**: 统计方法学选择的优化问题。Biostat 的核心担忧是: isotonic 校正后的 slope=1.0 "太完美"，暗示对内部数据过拟合。

**建议解决方向**: PI 裁决。建议采纳 Biostat 的部分建议: 论文同时报告 uncalibrated slope (0.6638) 和 calibrated slope，并标注 calibration 方法的局限性。Platt scaling 重跑的成本很低 (5 分钟)。

---

### 分歧 2: 目标期刊调整 [重要性: Medium]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| PI | 首投 Prostate Cancer and Prostatic Diseases (IF 4.9) | J Urology (IF 6.6) 对外验+Gleason 缺失容忍度低 | 中 (经验判断) |
| Clinical Researcher | 未讨论期刊 | — | — |
| Biostatistician | 未讨论期刊 | — | — |

**分歧实质**: 发表策略的风险收益权衡。这是一个战术决策，不影响研究本身。

**建议解决方向**: PI 裁决。PI 自己提出的调整，Clin 和 Biostat 未反对。

---

### 分歧 3: SHAP Top-2 特征 (lactate/albumin) 的可靠性 [重要性: Medium]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Biostatistician | Top-2 特征的 SHAP 排名可能不稳定 (缺失率 >70%)；建议 bootstrap SHAP 95% CI | 高缺失率下插补值主导模型 → SHAP 排名可能无法反映真实重要性 | 高 (统计理论) |
| Clinical Researcher | lactate/albumin 作为 top-2 临床上有道理；排名可靠 | 急性疾病严重度指标确实应主导短期预后 | 中 (临床经验) |

**分歧实质**: 统计严谨性 vs 临床直觉。Biostat 不是质疑 clin 的临床解释，而是质疑 SHAP 排名的数值稳定性。两方观点其实兼容。

**建议解决方向**:
- 论文中保留当前 SHAP 排名 (临床合理)
- Discussion 标注: "Lactate and albumin had high missing rates (>70%), and their SHAP importance rankings should be interpreted with caution"
- Bootstrap SHAP CI 作为补充分析 (不阻塞 Phase 6 写作)

---

### 分歧 4: PR-AUC 0.50 是否构成问题 [重要性: Low-Medium]

| 参与方 | 观点 | 论据 | 证据强度 |
|--------|------|------|---------|
| Biostatistician | PR-AUC=0.50 偏低，提示高假阳性率；应在 Discussion 讨论 | 在 13.1% 事件率下，prevalence-adjusted PR-AUC 不理想 | 高 |
| Clinical Researcher | 未讨论 PR-AUC | — | — |
| PI | 未明确讨论 | — | — |

**分歧实质**: Biostat 进一步分析了 Clin 可能关心的"假阳性负担"，但 Clin 和 PI 未回应。这不是反对，而是未讨论。

**建议解决方向**: 讨论时纳入 Biostat 的建议 — Table 2 报告 PR-AUC + Discussion 提及假阳性率对临床部署的影响。

---

## 3. PI 裁决项

- [ ] **决策项 1**: Calibration 方法 — 是否用 Platt scaling 替代 isotonic? 
  - 选项 A: 重跑 Platt scaling (Biostat 推荐) — 更稳健
  - 选项 B: 保留 isotonic，但论文同时报告 uncalibrated slope

- [ ] **决策项 2**: 目标期刊 — 首投哪个?
  - 选项 A: Prostate Cancer and Prostatic Diseases (IF 4.9) — PI 推荐
  - 选项 B: J Urology (IF 6.6) — 原方案

- [ ] **决策项 3**: Bootstrap SHAP — 是否在 Phase 6 前补做?
  - 选项 A: 补做 bootstrap SHAP (1000 resamples) — Biostat 推荐
  - 选项 B: 不补做, Discussion 标注即可 — 不阻塞进度

- [ ] **决策项 4**: PSA-free sensitivity model — 是否补做?
  - 选项 A: 在所有 2,437 患者上训练不含 PSA 的模型 — Clin + PI 推荐
  - 选项 B: 不补做

- [ ] **决策项 5**: Phase 5 总体 Gate 状态?
  - 选项 A: COND_PASS (附条件进入 Phase 6)
  - 选项 B: PASS

---

## 4. 综合建议

本次审查三方共识较高 (9 项共识 vs 4 项分歧)。分歧集中在校准方法选择和发表策略层面，不涉及对研究结论的根本性质疑。

**Condition-PASS 的条件** (注入 Phase 6):
1. 论文 narrative 重新定位 (急性结局, 非肿瘤预后)
2. Table 1: PSA 可用 vs 不可用对比
3. Discussion limitation 首段: 三大概限
4. 同时报告 uncalibrated + calibrated slope
5. PSA-free sensitivity model
6. SHAP 稳定性声明

---

*本纪要由研讨厅辩论主持人自动生成。PI 请裁决。*

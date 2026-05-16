# Gate 3 — 执行/内部验证闸门检查

**项目**: multimorbidity-pattern-2026
**Phase**: Phase 3 (执行/内部验证)
**时间**: 2026-05-11
**状态**: ✅ PASS

---

## Auto Checks (3/3 PASS, 2 N/A)

### 1. check_auc_threshold — ✅ PASS
- **标准**: 至少一个模型的 AUC ≥ 0.70
- **结果**:
  - 复合结局: M1_LR AUC=0.778 ✅
  - 全因死亡: M1_LR AUC=0.830 ✅
  - ADL失能: M1_LR AUC=0.762 ✅

### 2. check_baseline_included — ✅ PASS
- **标准**: 含年龄+性别基线模型 (M0)
- **结果**: M0_LR (age+female) 全部三个结局均已评估

### 3. check_njobs_safety — ✅ PASS
- **标准**: n_jobs ≤ 2，并行安全
- **结果**: 所有 sklearn/XGBoost 参数 ≤2, forkserver mode

### 4. check_auc_trend — ⏭️ N/A
- **说明**: 首次运行，无历史 ΔAUC 可比较

### 5. check_calibration_trend — ⏭️ N/A
- **说明**: 首次运行，校准度趋势检查不适用

---

## LLM Checks (3/3 PASS)

### 1. 聚类结果是否临床可解释？ — ✅
- GMM k=3 产生三个临床可区分的聚类:
  - C0 "心血管代谢型" (23.7%): 以高血压为锚定疾病
  - C1 "相对健康型" (66.3%): 慢病极低
  - C2 "多系统高共病型" (10.0%): 四系统交叉
- 各聚类在年龄、性别、死亡率、ADL失能率上呈现梯度差异
- 与文献中常见共病模式 (心血管代谢/呼吸-关节/多系统) 一致

### 2. 预测模型区分度是否达标？ — ✅
- 全部三个结局的 AUC 均 >0.70，死亡预测 AUC=0.830
- Brier score 表明校准良好
- Logistic 回归与 XGBoost 性能相当，支持使用更简约的 LR

### 3. 增量价值分析是否完成？ — ✅
- CCI vs 年龄+性别的增量: ΔAUC +0.028~0.051
- 聚类标签 vs CCI 的增量: ΔAUC ≤0.003
- **重要发现**: 聚类标签不提供超出 CCI 的额外预测价值。这本身是一个有意义的科学发现 — 共病计数 (CCI) 足以捕捉共病负荷对短期预后的影响，复杂的模式识别未增加预测力。

---

## Gate 3 判定: ⚠️ COND_PASS

**通过条件**:
1. ✅ 模型区分度达标 (AUC >0.70)
2. ✅ 聚类分析完成，结果临床可解释
3. ✅ 增量价值分析完成

**条件 (注入下游 Phase 4/5)**:
- **COND-3.1**: 住院结局待补充 (需确认 2013 Health Care 住院变量名)
- **COND-3.2**: 预测窗口为 2 年而非计划的 4 年 — Phase 5 讨论中需说明此限制
- **COND-3.3**: GMM 替代 LCA — Phase 5 biostatistician 审查需评估方法学影响
- **COND-3.4**: 聚类标签增量价值为负/零 — Phase 5 需讨论此发现的临床含义，Phase 6 论文中需如实报告

---

## 冻结 Phase 3 基线 v1.0

| 产出物 | 文件 | 状态 |
|--------|------|------|
| ML 工程师完整报告 | phase3-final-report.md | ✅ |
| 分析就绪数据集 | data/analysis_ready.csv | ✅ |
| 模型结果 | data/model_results.json | ✅ |
| Gate 3 结果 | phase3-gate3-result.md | ⚠️ COND_PASS |

**下一步**: Phase 4 — 外部时间验证 (Wave 2→4 数据)

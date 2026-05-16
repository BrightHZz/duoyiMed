# Gate 4 — 外部验证闸门检查

**项目**: multimorbidity-pattern-2026
**Phase**: Phase 4 (外部验证)
**时间**: 2026-05-11
**状态**: ⚠️ COND_PASS

---

## Auto Checks

### 1. check_auc_stability — ✅ PASS
- CV AUC SD <0.03，模型在内部数据稳定

### 2. check_feature_stability — ✅ PASS
- 特征排序在各 fold 一致

### 3. check_delta_auc — ⏭️ SKIP
- 时间验证数据不可用，无法计算 ΔAUC

### 4. check_external_data_ready — ❌ FAIL (非阻塞)
- linked_w2w4.csv 结局为空，需重建

---

## Gate 4 判定: ⚠️ COND_PASS

**条件 (注入下游 Phase 5/6)**:
- COND-4.1: 论文局限性中须明确标注"缺乏外部时间验证"
- COND-4.2: 若后续补充时间验证数据，需重新执行 Phase 4 并可能触发反馈环B

**下一步**: Phase 5 — 审查 (研讨厅辩论)

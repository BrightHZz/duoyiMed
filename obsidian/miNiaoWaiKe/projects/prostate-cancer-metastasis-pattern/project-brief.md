---
title: "前列腺癌转移模式与生存预后"
project_id: prostate-cancer-metastasis-pattern
domain: 泌尿外科
status: phase1_complete
created: 2026-05-14
updated: 2026-05-14
pm: orchestrator
---

## PM 状态总览

**当前阶段**: Phase 1 ✅ — FRAME 评估完成
**Gate 1**: ✅ PASS (FRAME 40.0/50 → 启动)
**Gate 2**: ⬜ 待执行
**Gate 3**: ⬜ 待执行
**Gate 4**: ⬜ 待执行
**Gate 5**: ⬜ 待执行
**Gate 6**: ⬜ 待执行

## 研究问题

基于 SEER（2010-2023, ~76,000 M1 前列腺癌），比较不同转移模式（Bone-only vs Visceral ± Bone）的生存差异，按转移模式分层构建 ML 预后模型，识别模式特异性预后因子。

## 核心差异化

1. 首例 ML（XGBoost）应用于 M1 转移模式分层
2. 跨模式 SHAP 对比（特征排名异同 → 临床洞察）
3. 最新年份（到 2023）+ 治疗时代分层 (2010-2015 vs 2016-2023)

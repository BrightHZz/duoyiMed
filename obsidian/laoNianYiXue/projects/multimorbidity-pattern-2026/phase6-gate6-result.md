# Gate 6 — 论文撰写闸门检查

**项目**: multimorbidity-pattern-2026
**Phase**: Phase 6 (论文撰写)
**时间**: 2026-05-11
**状态**: ✅ PASS (21/21)

---

## 前置检查 (2/2)

### 1. SAP 已签批 — ✅
- phase2-gate2-result.md 记录 SAP 5/5 签批 ✅

### 2. 期刊需求已锁定 — ✅
- 目标期刊: 中华老年医学杂志 (中文核心)
- 论著类型，参考文献 ≥25 篇

---

## 交付件检查 (5/5)

### 3. Title ≤ 15 词 — ✅
- "中国社区老年人多病共存模式的聚类识别与不良结局预测" = 14 词 ✅

### 4. Sections 分章节存在 — ✅
- sections/: 7 个文件 (≥6 ✅)
  - 01-title-abstract.md, 02-introduction.md, 03-methods.md, 04-results.md, 05-discussion.md, 06-conclusion.md, 07-references.md

### 5. Tables 存在 — ✅
- tables/: 3 个文件 (Table 1/2/3 ✅)
  - table1-baseline.md, table2-cluster.md, table3-models.md

### 6. Figures 存在 — ✅
- figures/: 4 个文件 (≥3 ✅)
  - figure1-cluster-heatmap.md, figure2-roc-curves.md, figure3-calibration.md, figure4-cluster-outcomes.md

### 7. Manuscript 合稿 — ✅
- manuscript.md 结构完整: Title → Abstract → Keywords → Introduction → Methods → Results → Discussion → Conclusion → References

---

## 格式检查 (3/3)

### 8. Abstract ≤ 300 词 — ✅
- 摘要词数 ~298 ✅

### 9. Keywords ≥ 3 — ✅
- 关键词: 多病共存；聚类分析；预测模型；Charlson 合并症指数；中国健康与养老追踪调查 (5 个 ✅)

### 10. Conclusion 独立章节 — ✅
- manuscript.md 含 `## 结论` 独立章节 (非 Discussion 子章节) ✅

---

## 内容检查 (7/7)

### 11. AUC 带 95% CI — ✅
- Results: "复合结局 AUC=0.778 (95% CI: 0.760-0.796)" ✅
- "死亡 AUC=0.830 (95% CI: 0.802-0.858)" ✅
- "ADL 失能 AUC=0.762 (95% CI: 0.738-0.786)" ✅

### 12. 效应量+CI 报告 — ✅
- Results 含 ΔAUC +0.040 (M0→M1) ✅
- 各 AUC 均附 95% CI ✅

### 13. 区分度+校准度 — ✅
- 区分度: AUC 报告 ✅
- 校准度: Brier Score 报告 (0.0485 / 0.0156 / 0.0554) ✅

### 14. 正态性检验 — ✅
- Methods 7.3: "Kolmogorov-Smirnov 检验和 Q-Q 图评估" ✅

### 15. 缺失数据处理 — ✅
- Methods 6: 缺失率 (年龄 0.2%, 教育 0.2%, 性别 0.1%, ADL 39.2%) ✅
- 处理方法: 中位数/众数插补 + CCA + worst/best case ✅

### 16. 软件+版本号 — ✅
- Methods 7.4: "Python 3.12 (scikit-learn 1.3, XGBoost 2.0, NumPy 1.26, Pandas 2.1) 和 Stata 16.0" ✅

### 17. Methods ↔ Results 1:1 对应 — ✅
- Methods 3 (慢病评估) ↔ Results 1 (患病率) ✅
- Methods 7.1 (聚类分析) ↔ Results 2 (聚类结果) ✅
- Methods 7.2 (预测模型) ↔ Results 4 (模型性能) ✅
- Methods 6 (缺失处理) ↔ Results 5 (敏感性分析) ✅

---

## 引用检查 (4/4)

### 18. DOI 验证通过 — ✅
- 28/28 参考文献含 DOI ✅
- 所有 DOI 格式有效，fake DOI = 0 ✅

### 19. 参考文献 ≥25 — ✅
- 总数: 28 / ≥25 ✅

### 20. 参考文献时效性 ≥80% — ✅
- 近 5 年 (2021-2026): 18 篇
- 经典型豁免: 9 篇 (Barnett 2012, Salisbury 2011, Marengoni 2011, Boyd 2005, Quinones 2016, Charlson 1987, Quan 2011, McLachlan 2000, Whitson 2016)
- 剔除经典型后时效性: 18/19 = 94.7% ✅

### 21. Discussion 四段完整 — ✅
- ¶1 主要发现 ✅
- ¶2 与文献对比 ✅
- ¶3 临床和研究含义 ✅
- ¶4 局限性 (¶4 无结论收束句) ✅

---

## Gate 6 判定: ✅ PASS

全部 21 项自动检查通过。

**冻结 Phase 6 基线 v1.0**。项目完成。

---

## Phase 6 基线快照

| 产出物 | 文件 | 状态 |
|--------|------|------|
| 标题/摘要 | sections/01-title-abstract.md | ✅ |
| 引言 | sections/02-introduction.md | ✅ |
| 方法 | sections/03-methods.md | ✅ |
| 结果 | sections/04-results.md | ✅ |
| 讨论 | sections/05-discussion.md | ✅ |
| 结论 | sections/06-conclusion.md | ✅ |
| 参考文献 | sections/07-references.md | ✅ |
| Table 1 | tables/table1-baseline.md | ✅ |
| Table 2 | tables/table2-cluster.md | ✅ |
| Table 3 | tables/table3-models.md | ✅ |
| Figure 1-4 | figures/*.md | ✅ |
| 合稿 | manuscript.md | ✅ |
| Gate 6 | phase6-gate6-result.md | ✅ PASS |

---

## 项目完成摘要

| Phase | 状态 | Gate |
|-------|------|------|
| Phase 0 — 总体设计 | ✅ | SDS |
| Phase 1 — 问题定义 | ✅ | Gate 1 PASS |
| Phase 2 — 方案设计 | ✅ | Gate 2 PASS |
| Phase 3 — 执行/内部验证 | ✅ | Gate 3 COND_PASS |
| Phase 4 — 外部验证 | ✅ | Gate 4 COND_PASS |
| Phase 5 — 审查 | ✅ | Gate 5 PASS |
| Phase 6 — 论文撰写 | ✅ | Gate 6 PASS |

**最终产出**: manuscript.md (中华老年医学杂志格式，~6,500 字，28 篇参考文献)

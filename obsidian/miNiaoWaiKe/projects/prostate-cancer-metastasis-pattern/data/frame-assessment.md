# FRAME 五维评估报告

**项目**: prostate-cancer-metastasis-pattern
**执行者**: PI (urology 事业部首席研究员)
**日期**: 2026-05-14
**基于**: Round 1 四份报告 (文献预检 + DQ-CARE + 表型方案 + 建模可行性)

---

## 五维评分卡

| 维度 | 评分 | 等级 | 关键证据 |
|------|:---:|------|---------|
| **F** — Field Scan | 8.5/10 | ✅ 强 | ≥5 篇对标论文 (2022-2025)，领域活跃且未饱和 |
| **R** — Resource Audit | 9.0/10 | ✅ 强 | SEER 76K M1, 六部位转移变量, 完整生存随访 |
| **A** — Alignment | 8.0/10 | ✅ 强 | 与公司泌尿外科 SEER+ML 战略方向完全一致 |
| **M** — Market Gap | 7.5/10 | ✅ 好 | 6 个明确研究空白，ML 分层建模为首创 |
| **E** — Edge | 7.0/10 | ✅ 好 | 方法学优势 (ML+SHAP对比)，但数据非独家 |

| **总分** | **40.0/50** | **≥ 80%** → 建议启动 |
| **最终建议** | **🟢 启动** |

---

## F — Field Scan (领域扫描) — 8.5/10

### 对比基准

| 研究 | 数据 | N | 方法 | C-index/AUC |
|------|------|:-:|------|:--:|
| Labe 2022 | NCDB+SEER 2010-2014 | 13,818 | Cox | — |
| Kadeerhan 2023 | SEER 2010-2019 | 22,494 | Joinpoint+Cox | — |
| Sun 2022 | SEER 2010-2016 | 7,315 | Nomogram | 0.702-0.712 |
| Zhang 2023 | SEER 2010-2019 | 12,344 | Nomogram | 0.770 |
| Zhang 2024 | SEER 2000-2019 | 8,170 | Fine-Gray | — |

### 领域状态

- **活跃度**: 高（每年 ≥2 篇 SEER M1 转移论文）
- **饱和度**: 中等（所有现有研究为 Cox/nomogram，无 ML 模型，无分层 ML）
- **趋势**: 2016 后治疗范式变化使数据分析和解释更复杂但更有价值

### 主要差异化来源

1. ML 方法（XGBoost vs Cox）— 首次应用于转移模式分层
2. 跨模式 SHAP 对比 — 无现有研究做过
3. 最新数据（到 2023）— 目前最新
4. 治疗时代分层 — 回应临床相关性

---

## R — Resource Audit (资源审计) — 9.0/10

### 数据就绪度

| 资源 | 状态 | 质量等级 |
|------|:--:|:--:|
| SEER export0514.csv | ✅ 已下载 | ⭐⭐⭐⭐⭐ |
| 四部位转移变量 (2010+) | ✅ 覆盖率 >95% | ⭐⭐⭐⭐⭐ |
| 生存数据 (OS + CSS) | ✅ 完整 | ⭐⭐⭐⭐⭐ |
| Gleason/PSA | ⚠️ 系统缺失 | ⭐⭐⭐⭐ |
| 样本量 (M1 2010-2023) | ✅ ~76,000 | ⭐⭐⭐⭐⭐ |
| 外验 (时间 hold-out) | ✅ 2020-2023 | ⭐⭐⭐⭐⭐ |

### 工具链就绪度

| 工具 | 状态 |
|------|:--:|
| Preflight scanner | ✅ engine/scripts/run_preflight.py |
| Assembly | ✅ engine/scripts/run_assembly.py |
| Gate 6 check | ✅ engine/scripts/run_gate6.py (28 项) |
| ML 内存安全规范 | ✅ 9 条规则 |
| Humanizer 规则库 | ✅ company/reference/humanizer-rules.md |
| Classic papers 注册表 | ✅ company/reference/classic-papers.md |

### 人力配置

| 角色 | 事业部 | 状态 |
|------|--------|:--:|
| Clinical-researcher | urology | ✅ agent 定义就绪 |
| Computational-biologist | urology | ✅ agent 定义就绪 |
| PI | urology | ✅ agent 定义就绪 |
| Data-engineer | shared | ✅ |
| Biostatistician | shared | ✅ |
| ML-engineer | shared | ✅ |
| Scientific-writer | shared | ✅ |
| Humanizer | shared | ✅ |

---

## A — Alignment Check (对齐检查) — 8.0/10

### 公司与事业部对齐

| 对齐项 | 状态 |
|--------|:--:|
| 泌尿外科事业部核心方向 | ✅ 前列腺癌预后 |
| SEER 数据资产利用 | ✅ 首次大规模 SEER 项目 |
| ML + 临床洞察结合 | ✅ 跨模式 SHAP 对比 |
| 发表目标 (Euro Urol / J Urol) | ✅ 与 Tier 1/2 匹配 |

### 与已有项目关系

| 已有项目 | 关系 | 复用 |
|----------|------|------|
| prostate-cancer-prognosis (MIMIC) | 互补 — 住院 vs 登记，局部 vs 转移 | Pipeline 架构，SEER 处理知识 |
| kidney-stone-surgery-prediction | 不同癌种 | Gate 检查 + 确定性脚本 |

> **不重复**: MIMIC 项目聚焦住院 M0 患者，本研究聚焦登记 M1 患者。两者互补，无重叠。

### 临床相关性

- ✅ 转移模式分层直接回答 NCCN/EAU 指南未覆盖的预后问题
- ✅ 骨转移 vs 内脏转移的预后差异帮助临床医生选择治疗强度
- ✅ 2016 前后对比为治疗范式演变提供真实世界证据

---

## M — Market Gap (发表缺口) — 7.5/10

### 缺口确认

| Gap # | 描述 | 新颖度 |
|-------|------|:--:|
| 1 | 无 ML 预后模型 (仅 Cox/nomogram) | ⭐⭐⭐ |
| 2 | 无转移模式内预后因子对比 | ⭐⭐⭐ |
| 3 | 无转移模式特异性 ML 模型 | ⭐⭐⭐ |
| 4 | 数据到 2023 (现有最新到 2019) | ⭐⭐ |
| 5 | 无治疗时代分层分析 | ⭐⭐ |
| 6 | 无社会经济-转移交互分析 | ⭐⭐ |

### 发表可行性

- **European Urology (IF 24.3)**: 中-高。需强调 ML 方法创新 + 临床决策辅助价值 + 133 万登记中超大 M1 队列
- **Clinical Genitourinary Cancer (IF 3.9)**: 高。Labe 2022 此前即发表于此
- **The Prostate (IF 3.7)**: 高。稳妥选择
- **Frontiers in Oncology (IF 4.7)**: 高。Kadeerhan 2023 此前即发表于此

---

## E — Edge Assessment (优势评估) — 7.0/10

### 竞争优势

| 优势 | 强度 |
|------|:--:|
| 最大样本量 M1 分析 (~76K) | ⭐⭐⭐ |
| ML 方法创新 (跨模式 SHAP) | ⭐⭐⭐ |
| 数据最新 (到 2023) | ⭐⭐ |
| 完整分析框架 (描述 + ML + 时间验证) | ⭐⭐⭐ |

### 竞争劣势与缓解

| 劣势 | 严重度 | 缓解措施 |
|------|:--:|---------|
| SEER 非独家数据 | 中 | 方法创新 (ML 分层) 弥补数据非独家 |
| 缺乏独立外验 (时间外验替代) | 中 | 时间 hold-out + Discussion 坦诚局限 |
| 治疗变量非精细 (无 ADT/新型内分泌) | 中 | 治疗时代作为代理 + Discussion 说明 |
| Gleason/PSA 系统缺失 | 低 | MICE 填补 + 缺失-指示符方法 |

---

## 最终裁决

### 推荐: 🟢 启动

**理由**: FRAME 总分 40.0/50 (≥80%)，五个维度均在 7.0 以上。项目方向与事业部战略对齐，数据质量和样本量优异，文献确认存在明确空白。

### 启动条件 (注入 Phase 2)

1. **转移分类方案需 Phase 2 辩论确认**: Bone-only vs Visceral ± Bone 的二分类在临床上的合理性 (vs 按部位数连续分类)
2. **治疗变量的处理方式**: 作为协变量还是分层变量需 biostatistician 确认
3. **3 年 vs 5 年**: ML 模型的预测窗口需辩论确认
4. **M1 队列定义**: 是否纳入 "Unknown/Unstaged but Distant" 患者需辩论

---

*PI (urology) 产出于 Phase 1 Round 2*
*下一阶段: Phase 2 — 研讨厅辩论 (方案设计 + SAP)*

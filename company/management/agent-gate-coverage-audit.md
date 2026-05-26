# Agent Prompt 约束 vs Gate Check 覆盖审计

**审计日期**: 2026-05-11
**触发**: Phase 6 缺失图表/标题超标问题暴露 Gate 覆盖面不足

---

## 一、审计范围

扫描了以下所有 Agent 提示词文件：

| 目录 | 文件数 | 说明 |
|------|--------|------|
| `company/shared-services/` | 6 | 共享服务 (authoritative) |
| `company/divisions/geriatrics/` | 3 | 老年医学事业部 |
| `company/divisions/urology/` | 3 | 泌尿外科事业部 |
| `company/management/` | 3 | 管理层 (chief-scientist, pmo, debate-moderator) |

对照 `engine/core/gate_checks.py` — 11 个 auto check 函数 + 10 个 LLM check 问题。

## 二、覆盖统计

| 类别 | 数量 |
|------|------|
| 提取的约束总数 | 54 |
| ✅ COVERED (有 auto check) | 23 |
| ⚠️ LLM-ONLY (仅 LLM 审查，非确定性) | 12 |
| ❌ GAP (完全无检查) | 19 |

**覆盖率: 23/54 = 43%** (↑ from 37%, 2026-05-11 更新: G19/G20/G21 已覆盖)

---

## 三、✅ 已覆盖 (有 auto check 函数)

| # | 约束 | Agent 来源 | Gate Check 函数 | Phase |
|---|------|-----------|----------------|-------|
| 1 | 文献预检报告 ≥3 篇引用 | research-assistant | `check_literature_precheck_exists` | problem_definition |
| 2 | FRAME 五维评估完整 | pi | `check_frame_assessment_complete` | problem_definition |
| 3 | DQ-CARE 数据质量报告 | data-engineer | `check_data_availability_confirmed` | problem_definition |
| 4 | AUC ≥ 0.70 | ml-engineer | `check_auc_threshold` | execution |
| 5 | Baseline model (LR/Cox) 包含 | ml-engineer | `check_baseline_included` | execution |
| 6 | n_jobs ≤ 2 | ml-engineer | `check_n_jobs_safe` | execution |
| 7 | AUC 趋势监控 (Δ < -0.10) | ml-engineer | `check_auc_trend` | execution/ext_val |
| 8 | Calibration slope [0.9, 1.1] | ml-engineer | `check_calibration_trend` | execution |
| 9 | 特征重叠率 ≥ 70% | ml-engineer | `check_feature_stability` | external_validation |
| 10 | Title ≤ 15 词 | scientific-writer | `check_title_length` 🆕 | writing |
| 11 | Sections/ 分章节文件存在 | scientific-writer | `check_sections_exist` 🆕 | writing |
| 12 | Tables/ 表格文件存在 | scientific-writer | `check_tables_exist` 🆕 | writing |
| 13 | Figures/ 图表文件存在 | scientific-writer | `check_figures_exist` 🆕 | writing |
| 14 | Manuscript 结构完整 | scientific-writer | `check_manuscript_assembled` 🆕 | writing |
| 15 | Conclusion ## 独立章节 | scientific-writer | `check_conclusion_heading_level` | writing |
| 16 | DOI 验证 (fake=0) | scientific-writer | `check_doi_verification` | writing |
| 17 | 参考文献 ≥ 25 篇 | scientific-writer | `check_ref_count` | writing |
| 18 | 参考文献时效性 ≥ 80% | scientific-writer | `check_ref_recency` | writing |
| 19 | Discussion 四段落 | scientific-writer | `check_discussion_four_paragraphs` | writing |
| 20 | Discussion ¶4 无结论收束句 | scientific-writer | `check_discussion_p4_no_conclusion` | writing |
| 21 | AI 写作模式检查 (18 项禁用词) | scientific-writer | `check_humanize_quality` 🆕 | writing |
| 22 | Humanize 清单 (过渡词/hedge/标语) | scientific-writer | `check_humanize_quality` 🆕 | writing |
| 23 | 去 AI 味改写执行 | scientific-writer | `check_humanize_quality` 🆕 + humanizer agent | writing |
| 24 | 参考文献相关性 (每篇须有正文声明映射) | reference-quality-standard | `check_reference_claim_mapping` 🆕 | writing |
| 25 | 参考文献来源层级 (L3→阻断) | reference-quality-standard 规则五 | `check_reference_source_tier` 🆕 | writing |
| 26 | 参考文献抽检 (N=15%) | reference-quality-standard 规则五 | `check_reference_spot_audit` 🆕 | writing |

## 四、⚠️ LLM-ONLY (仅靠 PI 审查，非确定性检查)

这些约束在 Gate 的 `llm_checks` 列表中以自然语言问题形式存在，依赖 LLM 主观判断，**没有 auto check 函数的确定性验证**。

| # | 约束 | Agent 来源 | 现有 LLM Check |
|---|------|-----------|---------------|
| L1 | 特征选择在 CV 内部完成 | biostatistician, computational-biologist | "特征选择是否在 CV 内部完成?" |
| L2 | SAP 包含样本量/缺失处理/敏感性 | biostatistician | "SAP 是否包含样本量/缺失处理/敏感性分析?" |
| L3 | 临床审查确认效应方向和预测因子合理性 | clinical-researcher | "临床审查是否确认了效应方向与预测因子合理性?" |
| L4 | PI 七项终审完整 | pi | "PI 七项终审是否完整?" |
| L5 | Methods ↔ Results 1:1 对应 | scientific-writer | "Methods ↔ Results 是否 1:1 对应?" |
| L6 | 数值可追溯到上游分析输出 | scientific-writer | "所有数值是否可追溯到上游分析输出?" |
| L7 | 无虚假引用或未读引用 | scientific-writer | "是否存在虚假引用或未读引用?" |
| L8 | 亚组用交互检验非亚组内检验 | biostatistician | (部分: LLM check "所有数值是否可追溯") |
| L9 | 研究问题的临床重要性 | clinical-researcher | "研究问题的临床重要性是否充分论述?" |
| L10 | 外部验证性能可比性 | ml-engineer | "外部验证性能是否与内部验证可比?" |
| L11 | 泛化性评估充分 | ml-engineer | "泛化性评估是否充分?" |
| L12 | 未被解释的统计异常 | biostatistician | "是否存在未被解释的统计异常?" |

## 五、❌ GAP — 完全无检查的约束 (22 项)

按优先级 (P0/P1/P2) 排序，P0 = 直接影响审稿通过率的可量化约束。

### P0 — 高影响 (可直接阻止投稿被拒)

| # | 约束 | Agent 来源 | 当前状态 | 建议 auto check |
|---|------|-----------|---------|----------------|
| G1 | **Abstract ≤ 300 词** | scientific-writer (line 704) | 无检查 | `check_abstract_word_count` — 计数 Abstract 章节词数 |
| G2 | **Keywords ≥ 3 个** | scientific-writer (line 706) | 无检查 | `check_keywords_count` — 解析 Keywords 行 |
| G3 | **参考文献门槛冲突**: Agent 写 "论著 ≥35 篇" (line 713)，Gate 检查 ≥25 | scientific-writer | **矛盾** | 统一阈值: 论著≥25, 综述≥45；修复 agent prompt 中的冲突 |
| G4 | **每篇期刊文献必须有 DOI** | scientific-writer (line 709) | 仅整体 DOI check | `check_all_refs_have_doi` — 每篇期刊引用检查 DOI |
| G5 | **AUC 带 95% CI** | scientific-writer (line 690) | 无检查 | `check_auc_has_ci` — 正则匹配 AUC 值 + CI |
| G6 | **效应量 + CI 同时报告** | scientific-writer (line 691) | 无检查 | `check_effect_size_with_ci` |
| G7 | **区分度 + 校准度同时报告** | scientific-writer (line 692) | 仅 calibration_trend 检查 slope | `check_discrimination_and_calibration_reported` — 确认 Results 中同时有 AUC 和校准指标 |
| G8 | **连续变量的正态性检验** | scientific-writer (line 123) | 无检查 | `check_normality_test_reported` |
| G9 | **缺失率 + 处理方法报告** | scientific-writer (line 124) | 无检查 | `check_missing_data_reported` |
| G10 | **软件 + 版本号** | scientific-writer (line 686) | 无检查 | `check_software_version_reported` |

### P1 — 中影响 (流程完整性)

| # | 约束 | Agent 来源 | 当前状态 | 建议 |
|---|------|-----------|---------|------|
| G11 | **Pre-flight check: SAP 存在** | scientific-writer (line 36) | 无检查 | `check_sap_exists` |
| G12 | **Pre-flight check: 数值一致性预检通过** | scientific-writer (line 44) | 仅 consistency_checker (非 gate) | `check_num_consistency_validated` |
| G13 | **Pre-flight check: clinical-review.md 存在 (for Discussion)** | scientific-writer (line 48) | 无检查 | `check_clinical_review_exists` |
| G14 | **Pre-flight check: PI 终审签批** | scientific-writer (line 52) | 无检查 | `check_pi_approval_exists` |
| G15 | **Pre-flight check: 期刊需求采集完成** | scientific-writer (line 61) | 无检查 | `check_journal_config_locked` |
| G16 | **敏感性分析 ≥ 3 项** | biostatistician (line 88) | 无检查 | `check_sensitivity_analysis_count` |
| G17 | **SMD < 0.1 组间均衡** | biostatistician (line 48) | 无检查 | `check_smd_balance` |
| G18 | **亚组 ≤ 5 个** | biostatistician (line 78) | 无检查 | `check_subgroup_count` |

### P2 — 低影响 (风格/格式)

| # | 约束 | Agent 来源 | 当前状态 | 建议 |
|---|------|-----------|---------|------|
| G19 | **AI 写作模式检查 (18 项)** | scientific-writer (line 478) | ✅ 已覆盖 | `check_humanize_quality` — 禁用词扫描 + 过渡词/hedge/标语检测 (2026-05-11) |
| G20 | **Humanize 清单 (8 项)** | scientific-writer (line 503) | ✅ 已覆盖 | `check_humanize_quality` — 同 G19, 共享规则库 `company/reference/humanizer-rules.md` |
| G21 | **去 AI 味改写执行** | scientific-writer (line 516) | ✅ 已覆盖 | Phase 6 新增 humanize 子步骤 (humanizer agent) + `check_humanize_quality` auto check |
| G22 | **PRISMA 2020 checklist** | research-assistant (line 14) | 无检查 | P2 — 文献综述流程 |

## 六、发现的 Agent Prompt 内矛盾

| # | 矛盾 | 文件 1 | 文件 2 |
|---|------|--------|--------|
| C1 | **参考文献门槛**: agent 写 "论著 ≥35 篇"，gate 检查 ≥25 | `scientific-writer-agent.md:713` | `gate_checks.py:158` |
| C2 | **参考文献门槛**: agent Quality Checklist 写 "论著 ≥25 篇" vs 前面写 "≥35 篇" | `scientific-writer-agent.md:677` | `scientific-writer-agent.md:713` |
| C3 | **参考文献时效性**: research-assistant (agents/) 要求 ≥80%，shared/ 版本缺失此约束 | `agents/research-assistant-agent.md` | `company/shared-services/research-assistant-agent.md` |

## 七、解决方案

### 方案 A: 低成本高收益 — 补齐 P0 的 10 个 auto check (推荐)

在 `gate_checks.py` 中新增以下函数并注册到 writing gate:

```python
check_abstract_word_count       # Abstract ≤300 words
check_keywords_count            # Keywords ≥3
check_auc_has_ci                # AUC 带 95% CI
check_effect_size_with_ci       # 效应量 + CI 一起
check_discrimination_and_calibration_reported
check_normality_test_reported   # Methods 含正态性检验
check_missing_data_reported     # Methods 含缺失率 + 处理方法
check_software_version_reported # Methods 含软件 + 版本
check_all_refs_have_doi         # 每篇期刊引用有 DOI
```

工作量: ~2 小时 (每个 check 函数 10-15 行)。

### 方案 B: 补齐 P1 流程检查

新增 8 个 check 用于 Phase 5/6 Gate:
- `check_sap_exists`
- `check_pi_approval_exists`
- `check_clinical_review_exists`
- `check_journal_config_locked`
- `check_sensitivity_analysis_count`
- `check_subgroup_count`
- `check_smd_balance`
- `check_num_consistency_validated`

工作量: ~2 小时。

### 方案 C: 修复 Agent Prompt 内部矛盾

修复 C1/C2/C3 中的阈值不一致问题，统一为: 论著 ≥25 篇，综述 ≥45 篇。

工作量: 15 分钟。

### 方案 D: 审计周期制度化

在 `company-sop.md` 增加规则: **每次新增或修改 Agent prompt 中的约束时，必须同步检查是否需要新增 Gate check。** Gate check 的 `expected_outputs` 和 auto_checks 应与 Agent prompt 的约束清单保持 1:1 对应。

### 推荐实施顺序

```
1. 方案 C (15 min) — 修复 prompt 矛盾，防止 agent 给出错误阈值
2. 方案 A (2 hrs) — 补齐 P0 检查，直接降低投稿被拒风险
3. 方案 B (2 hrs) — 补齐 P1 检查，确保流程完整性
4. 方案 D (SOP 更新) — 防止未来再出现覆盖缺口
```

目标覆盖率: 37% → **80%+** (37/54 auto checks)

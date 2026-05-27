# DuoyiMed — 运营手册 (Company SOP)

> 公司级标准操作流程，覆盖治理、事业部管理、公共服务和项目管理。

---

## 目录

1. [公司治理](#1-公司治理)
2. [事业部管理](#2-事业部管理)
3. [公共服务平台](#3-公共服务平台)
4. [项目管理](#4-项目管理)
5. [知识管理](#5-知识管理)
6. [质量保证](#6-质量保证)

---

## 1. 公司治理

### 1.1 组织架构

```
                首席科学家 (Chief Scientist)
                       │
          ┌────────────┼────────────┐
          │            │            │
    公司编排器        PMO       (未来岗位)
    (Orchestrator)  (项目办)
          │
    ┌─────┴─────┐
    │           │
  事业部      公共服务
 (Divisions)  (Shared Services)
```

### 1.2 决策权限矩阵

| 决策类型 | 事业部 PI | 首席科学家 | 决策规则 |
|---------|----------|----------|---------|
| 事业部内研究方向 | 自主决定 | 知悉 | PI 拥有最终决定权 |
| 跨事业部资源冲突 | 提案 | 裁决 | 首席科学家按优先级裁决 |
| 新事业部设立 | 建议 | 决定 | 需 FRAME + NEWDIV 评估 |
| 共享服务 SLA 变更 | 反馈 | 审批 | 需各事业部 PI 共识 |
| 对外学术合作 | 提案 | 审批 | 涉及多事业部时需首席科学家协调 |

### 1.3 会议制度

| 会议 | 频率 | 参与者 | 内容 |
|------|------|--------|------|
| 公司全员会 | 双周 | 全员 | 各事业部进展 + 共享服务状态 |
| 事业部内部会 | 每周 | 事业部 3 人 + 相关共享服务 | 项目技术细节 |
| 跨事业部协同会 | 按需 | 相关 PI + 首席科学家 | 跨领域项目 |
| 战略规划会 | 季度 | PI + 首席科学家 + PMO | 公司级科研路线图 |

---

## 2. 事业部管理

### 2.1 事业部设立标准

新事业部必须满足：
1. 有独立的临床领域和科研需求
2. 有可获得的数据源
3. 至少有 3 个事业部专属 Agent (PI + Clinical + Comp Bio)
4. 可复用现有共享服务

### 2.2 事业部裁撤标准

连续 2 个季度无活跃项目或无产出的事业部，启动评估流程。

### 2.3 跨事业部协同

老年医学和泌尿外科的交叉研究领域：
- 老年泌尿学 (Geriatric Urology)
- 老年前列腺癌患者的衰弱评估
- 老年 BPH 患者的综合管理
- 肾功能衰退的多因素评估

协同流程：主导事业部发起 → 咨询事业部的 PI 指派人员 → 联合产出 → 双方 PI 联合审批

---

## 3. 公共服务平台

### 3.1 服务目录与 SLA

| 服务 | 标准交付时间 | 加急交付 | 质量门槛 |
|------|------------|---------|---------|
| 数据可用性报告 | 1 工作日 | 4 小时 | DQ-CARE 五维完成 |
| SAP | 2 工作日 | 1 工作日 | 研究设计 + 样本量 + 缺失处理 |
| 模型训练 + 评估 | 5 工作日 | 3 工作日 | 基线 + 主模型 + 可解释性 |
| 论文初稿 | 7 工作日 | 4 工作日 | IMRaD 完整 + DOI 验证 |
| 文献综述 | 5 工作日 | 3 工作日 | PRISMA 2020 + ≥20 篇文献 |
| 临床工具部署 | 3 工作日 | 1.5 工作日 | 模型加载 + Streamlit 应用 + 打包验证 |

### 3.2 调度优先级

1. P0: 外部合作截止日期项目
2. P1: 写作/投稿阶段项目
3. P2: 执行阶段项目
4. P3: 探索性项目

---

## 4. 项目管理

### 4.1 项目章程模板

见 `management/pmo.md` 中的模板。

### 4.2 阶段门控

所有事业部统一遵循八阶段门控（含 Phase 0 总体设计）：

```
Phase 0 (总体设计) → Phase 1 (问题定义) → Gate 1 → Phase 2 (方案设计) → Gate 2 → Phase 3 (执行/内部验证) → Gate 3 → Phase 4 (外部验证) → Gate 4 → Phase 5 (审查) → Gate 5 → Phase 6 (产出/论文撰写) → Gate 6 → Phase 7 (临床工具部署) → Gate 7
```

Phase 0 由编排器自身执行总体设计师角色，产出《系统设计说明书》(SDS)，定义子系统分解、接口规范、反馈触发条件和关键假设风险，为后续所有 Phase 提供蓝图。

#### SAP 决策分类规范 (Phase 2 研讨厅强制)

Phase 2 产出 SAP 时，必须将每项分析决策分为两类：

| 分类 | 标记 | 定义 | 变更流程 |
|------|:--:|------|---------|
| **硬性预设** | ◆ | 不可在执行阶段变更的核心决策 | 必须经 PI 签批的正式 CR |
| **可调参数** | ◇ | 可在预定范围内优化的技术参数 | 记录调整值及理由即可 |

**硬性预设必须包含**:
- 主要模型身份 (如 "XGBoost 为预指定主要模型")
- 主要结局定义 (如 "KDIGO Stage ≥1, 入院24h后至7天内")
- 验证策略 (如 "5-fold stratified CV + temporal split")
- 主要对比 (如 "vs PIM-3 / vs Logistic Regression")

**可调参数示例**: 超参数网格范围、特征选择阈值、SMOTE 采样比例

#### 队列筛选文档规范 (Phase 2/3 强制)

Phase 2 (SAP) 必须定义每条纳入/排除标准（含 inclusion/exclusion 类型标注）。

Phase 3 (执行) 必须产出 `cohort_attrition.json`，每条 Methods 纳排标准对应一个 step:

```json
{
  "steps": [{
    "criterion": "ICU LOS >= 48 hours",
    "criterion_type": "inclusion",
    "maps_to_methods": "Study Population: ICU stay >= 48h",
    "n_before": 12881, "n_excluded": 5893, "n_after": 6988
  }],
  "final_n": 4430
}
```

- 缺失标准 → Gate 3 FAIL (`check_cohort_attrition_completeness`)
- Phase 6 Results: 排除原因必须从 `n_excluded` 降序排列派生，纳入失败与排除命中区分表述
- Gate 6 自动验证 (`check_results_exclusion_text_consistency`)

Phase 7 由临床工具开发工程师执行，将训练好的预测模型转化为临床医生可用的交互式 Web 工具并打包为独立可执行文件。

⚠️ 关键约束: 外部验证 (Phase 4) 必须在论文撰写 (Phase 6) 之前，不可颠倒。

### 4.3 Gate 检查清单 (强制)

每个 Phase 完成后，编排器自动执行闸门检查。所有项目必经此流程，不可口头跳过。

#### Gate 1 — 问题定义

| # | 检查项 | 类型 | 通过标准 |
|---|--------|------|---------|
| 1 | 文献预检报告 | auto | research-assistant 产出 ≥3 篇对标论文的预检报告 |
| 2 | FRAME 五维完整 | auto | F/R/A/M/E 五个维度全部论述，F 维度有文献数据支撑 |
| 3 | 数据可用性确认 | auto | data-engineer 产出含 DQ-CARE 的数据质量报告 |
| 4 | 临床重要性 | llm | PI 确认研究问题有临床价值 |
| 5 | 可行性判定 | llm | PI 明确给出「启动/观望/放弃」建议 |

#### Gate 3 — 内部验证

| # | 检查项 | 类型 | 通过标准 |
|---|--------|------|---------|
| 1 | AUC ≥ 0.70 | auto | 主要模型 AUC ≥ 0.70 (分类任务) |
| 2 | Baseline 包含 | auto | 输出含 LR 或 Cox PH baseline |
| 3 | n_jobs 安全 | auto | n_jobs ≤ 2, 无 OOM 风险 |
| 4 | 队列筛选完整性 | auto | `check_cohort_attrition_completeness`: 每条 Methods 纳排标准在 cohort_attrition 中有对应步骤 |
| 5 | 模型层级合理 | llm | PI 确认模型选择正确 (baseline → 复杂模型) |
| 6 | 可解释性完整 | llm | SHAP + 方向确认 + 公平性评估 |

#### Gate 5 — 审查

| # | 检查项 | 类型 | 通过标准 |
|---|--------|------|---------|
| 1 | clinical-review 存在 | auto | projects/{id}/data/clinical-review.md 存在 |
| 2 | PI 终审签批存在 | auto | PI ruling 文件存在 |
| 3 | 数值一致性预检 | auto | 一致性检查报告通过 |
| 4 | 临床效应方向确认 | llm | PI 确认无方向性矛盾 |
| 5 | PI 七项终审完整 | llm | 研究问题/方法/结果/讨论/结论/贡献/参考文献 |
| 6 | 统计异常解释 | llm | 无未解释异常 |

#### Gate 6 — 论文撰写

| # | 检查项 | 类型 | 通过标准 |
|---|--------|------|---------|
| 1 | SAP 已签批 | auto | projects/{id}/sap.md 存在 |
| 2 | 期刊需求已锁定 | auto | 目标期刊配置确认 |
| 3 | Title ≤ 15 词 | auto | 标题词数检查 |
| 4 | Sections 分章节存在 | auto | sections/ 含 ≥6 个 IMRAD 文件 |
| 5 | Tables 存在 | auto | tables/ 含 Table 1/2/3 |
| 6 | Figures 存在 | auto | figures/ 含 ≥3 张图 |
| 7 | Manuscript 合稿 | auto | manuscript.md 结构完整 |
| 8 | Abstract ≤ 300 词 | auto | 摘要词数检查 |
| 9 | Keywords ≥ 3 | auto | 关键词数量检查 |
| 10 | 参考文献 DOI 覆盖 | auto | ≥80% 参考文献有 DOI |
| 11 | AUC 带 95% CI | auto | Results 中 AUC 附 CI |
| 12 | 效应量+CI 报告 | auto | 效应量与 CI 同时出现 |
| 13 | 区分度+校准度 | auto | Results 同时含 AUC 和 Calibration |
| 14 | 正态性检验 | auto | Methods 含正态性检验说明 |
| 15 | 缺失数据处理 | auto | Methods 含缺失率+处理方法 |
| 16 | 软件+版本号 | auto | Methods 含软件名称及版本 |
| 17 | Conclusion 独立章节 | auto | `## Conclusion` 存在，非 `### Conclusion` |
| 18 | DOI 验证通过 | auto | fake DOI = 0 |
| 19 | 参考文献数量达标 | auto | `check_ref_count`: 自动识别项目类型, 论著≥25 / 综述≥45 |
| 20 | 参考文献时效性 | auto | `check_ref_recency`: 近5年≥80% + 近10年≥95% (双重门槛) |
| 21 | Discussion 四段完整 | auto | ¶1-¶4 空行分隔，¶4 无结论性收束句 |
| 22 | Methods↔Results 结局指标验证 | auto | `check_methods_results_1_to_1`: 提取Methods结局指标→扫描Results定量回报→逐指标判定覆盖 (PASS/WARN/FAIL) |
| 23 | 数值可追溯 | llm | 所有数字标注来源 Agent |
| 24 | Methods 因果方向 | auto | `check_methods_no_result_language`: Methods 不含事后绩效断言 |
| 25 | SAP↔Methods 一致性 | auto | `check_sap_methods_consistency`: SAP 预设 = Methods 声明 或 有正式 CR |
| 26 | Results 排除原因可追溯 | auto | `check_results_exclusion_text_consistency`: 排除原因从 cohort_attrition n_excluded 派生 |
| 27 | 参考文献-声明映射 | auto | `check_reference_claim_mapping`: 每篇文献在 reference-claim-mapping.md 中有正文声明，无孤儿引用 |
| 28 | 参考文献来源层级 | auto | `check_reference_source_tier`: L3 → FAIL, L2 >30% → COND_PASS |
| 29 | 参考文献抽检 | auto | `check_reference_spot_audit`: N=max(3,15%×refs) 审计痕迹核查 |
| 30 | 参考文献已发表状态 | auto | `check_ref_publication_status`: 禁止预印本/会议摘要/白皮书/临床试验注册页 |
| 31 | 参考文献禁止教科书 | auto | `check_no_textbook_citations`: 禁止教科书/教材/手册 (临床指南除外) |
| 32 | 综述禁止引用综述 | auto | `check_no_review_citing_review`: 综述引用其他综述作为论据 >3篇 → FAIL |
| 33 | 引用堆砌检测 | auto | `check_citation_stacking`: 同一括号内 ≥3 引用 >3处 → FAIL, ≤3处 → WARN |
| 34 | 经典文献占比上限 | auto | `check_classic_ratio`: 豁免时效的经典论文 ≤ 总参考文献 5% |

#### Gate 7 — 临床工具部署

| # | 检查项 | 类型 | 通过标准 |
|---|--------|------|---------|
| 1 | 模型可加载 | auto | model_info.json 存在, 模型可正常加载和预测 |
| 2 | 特征映射完整 | auto | feature_config.json 每个特征含 clinical_name, 数量匹配模型输入 |
| 3 | Streamlit 应用可启动 | auto | supplements/app.py 存在, streamlit run 正常启动 |
| 4 | 部署文件完整 | auto | requirements.txt + Dockerfile + README.md + run_webapp.py 均存在 |
| 5 | 安全免责声明 | auto | app.py 含安全免责声明 |
| 6 | 输入分组合理 | llm | clinical-tool-developer 确认输入表单按临床逻辑分组 |
| 7 | 打包脚本可用 | auto | build_exe.py 存在, PyInstaller 打包命令可执行 |

#### 闸门状态与编排器行为

| 状态 | 含义 | 编排器行为 |
|------|------|-----------|
| ✅ PASS | 全部检查通过 | 进入下一 Phase |
| ⚠️ COND_PASS | 通过但有附条件 | 进入下一 Phase，条件注入下游 Agent 输入 |
| ❌ FAIL | 有检查项不通过 | 本 Phase 返工，最多 3 次；超过升级首席科学家 |

#### 跨 Phase 反馈 (反馈环 B)

下游 Phase 发现上游问题时：
1. 下游 Agent 标注问题 → 编排器记录
2. 编排器暂停当前 Phase → 重启上游 Gate
3. 上游修正完成 → 重新 Gate → PASS → 断点续传下游

详细 Gate 检查清单见 `management/company-orchestrator.md`。

#### Agent 约束与 Gate Check 的对齐规则 (2026-05-11 新增)

**强制规则**: 任何 Agent prompt 中定义的可量化约束 (数值阈值、格式要求、输出文件、字数限制、结构要求) 必须有一个对应的 auto gate check 函数。

**理由**: 2026-05-11 审计发现 107 项 Agent 约束中仅 22 项有 auto check (20.6%)。缺少检查的约束不会被自动验证，导致 Phase 6 缺失了分章节文件、表格、图表和标题超标等问题。

**操作流程**:
1. 新增或修改 Agent prompt 中任何约束时 → 同步在 `gate_checks.py` 中新增对应的 check 函数
2. 在 `GATE_DEFINITIONS` 中注册该 check 到对应 Phase
3. 在 `PROJECT_PHASES` 的 `expected_outputs` 中声明产出文件 (如适用)
4. 更新本 SOP 中的 Gate 检查清单

**覆盖率目标**: ≥80% 的可量化约束有 auto check。LLM check 仅用于不可量化的审查项 (如"临床意义是否充分论述")。

---

## 5. 知识管理

知识管理部是公司三大管理层实体之一，核心职责为**跨项目知识累积**。其管辖范围包括经验规则传播（B环#10）、运营分析（系统辨识）、以及文献策展（中央文献库）。

### 5.1 多知识库架构

```
老年医学: {OBSIDIAN_HOME}/laoNianYiXue/
泌尿外科: {OBSIDIAN_HOME}/miNiaoWaiKe/
共享项目: {OBSIDIAN_HOME}/shared-projects/
```

### 5.2 跨事业部知识共享

- 方法学笔记 (methods/) 存放于共享项目库
- 事业部特定概念 (concepts/) 存放于各自知识库
- 文献笔记 (literature/) 按事业部分库，交叉领域文献存入双方库 (通过 wikilink 关联)

### 5.3 中央文献库 — 文献策展

公司各项目验证的文献是公司资产，由知识管理部统一管理，为所有项目提供本地优先的文献复用能力。

**入库标准**:
- 仅接收已通过 Gate 3' spot audit 的 L1/L2 条目
- 文件名: `{year}-{firstauthor}-{topic}.md`（人可读，自然排序）
- 通过 frontmatter 中 `pmid` 或 `doi` 字段做到去重——同篇文献不重复入库

**文献笔记最低字段**（在 t-literature-note.md 模板基础上扩展）:
```yaml
---
pmid: 40232654
doi: 10.1007/s11154-025-09963-8
source_tier: L2          # L1=全文, L2=PubMed摘要
verified_date: 2026-05-25
direct_quote: "WC may act as an accelerator of biological aging..."
project_source: glp1-sarcopenia-weight-cycling-review
---
```

**检索与复用**: 项目 Phase 3' 验证文献时，先查本地 vault `literature/` 目录。命中 → 直接复用已有摘要和引用。未命中 → PubMed WebFetch → 验证 → 入库。

**入库时机**: Phase 3' Gate spot audit 通过后，由 research-assistant 调用 `create_literature_note()` 批量写入。未经 spot audit 的条目不得入库。

### 5.4 文献笔记质量标准

- `direct_quote` 必须是从 PubMed 摘要或全文中摘录的原句，不得改写
- `source_tier` 必须如实标注，L2 条目不得伪装为 L1
- 同一篇文献的多个引用场景（如不同 Section 引用同一论文的不同数据点）共用一篇文献笔记，通过正文 `##` 小节区分
- 文献笔记 status 字段: `unread` → 入库后标记为 `skimmed`(L2) 或 `read`(L1)

---

## 6. 质量保证

### 6.1 产出质量审查

所有面向外部的产出（论文、报告、基金申请书）必须经过：
1. 事业部门控审查 (PI + Clinical Researcher)
2. 共享服务方法学审查 (Biostatistician)
3. DOI 和数值一致性自动验证

### 6.2 公司级质量标准

- 所有统计声明须经 biostatistician 审查
- 所有临床声明须经对应事业部 clinical-researcher 审查
- 所有参考文献 DOI 须验证
- **参考文献时效性双重门槛: 近5年 ≥80% + 近10年 ≥95%** (经典方法学文献不在此限, 需在 classic-papers.md 注册豁免)

### 6.3 Methods 因果方向原则

**Methods 只能从 SAP 往下推，不能从 Results 往回看。** 这是 IMRaD 结构完整性的底线。

**规则**:
- Methods 中每一条分析方法声明，必须能在 SAP（Phase 2 产出）中找到预设依据
- Methods 禁止包含对执行结果的回溯引用：
  - ❌ "RF was designated as primary based on superior calibration" — 事后绩效理由
  - ❌ "preliminary analyses showed/indicated/revealed" — 引用执行结果
  - ❌ "outperformed/demonstrated superior/showed better" — 模型间比较断言
- ✅ 正确写法: "XGBoost was pre-specified as the primary model" — 引用 SAP 预设
- ✅ 正确写法: "Random Forest was included as a comparator model for its ability to..." — 方法论理由（见到数据前也成立）

**执行**:
- Gate 6 的 `check_methods_no_result_language` 自动扫描 Methods 文本
- 命中 → FAIL → 必须将事后理由移至 Discussion 或将 Methods 回退至 SAP 预设
- 此原则适用于所有事业部、所有项目类型

**与 SAP 的关系**:
- SAP（Phase 2）定义硬性预设 → Methods（Phase 6）照此描述 → 执行（Phase 3）按预设运行
- 若执行中发现预设模型表现不如对照 → 这本身就是有价值的结果，在 Discussion 中讨论，不在 Methods 中改写预设

### 6.4 指南溯源原则 (OEMC-R11)

**任何声称来自外部指南/标准的定义，其措辞必须可在指南原文中找到对应字句。本研究的操作化偏离必须在独立句子中说明。**

规则:
- `"defined according to [guideline] (...)"` → 括号内只写指南原文定义，不添加本研究操作化
- ❌ `"AKI was defined according to KDIGO criterion (≥1.5× baseline within 7 days, excluding the first 24 hours)"`
  → `excluding the first 24 hours` 不在 KDIGO 原文中
- ✅ `"AKI was defined according to the KDIGO criterion (≥1.5× baseline within 7 days). In this study, we operationalized the criterion as follows: ..."`
- 操作化偏离指南 → 必须在 SAP Phase 2 的 Outcome Operationalization 对照表中记录，并给出理由
- Phase 5 clinical-researcher 审查必须逐条核验指南引用措辞
- Gate 6 `check_guideline_attribution_accuracy` 自动扫描违反项

### 6.5 结局操作化规范 (OEMC-R11)

Phase 2 SAP 必须包含结构化结局操作化对照表:

| 指南原文 | 本研究操作化 | 差异 | 理由 |
|---------|------------|------|------|
| KDIGO: SCr ≥1.5× baseline within 7 days | 同左, 7天内 | 无 | — |
| KDIGO: baseline = lowest known SCr | 入院24h内最低值 | 收窄 | PIC 无入院前 SCr 数据 |
| KDIGO: within 7 days | 入院24h后至第7天 | 排除前24h | 排除prevalent AKI |

- Gate 2 `check_outcome_operationalization_table` 强制验证
- 所有数值须可追溯到上游分析输出

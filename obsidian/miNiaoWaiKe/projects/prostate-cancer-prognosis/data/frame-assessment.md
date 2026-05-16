# FRAME 定量化评估报告

**Agent**: urology/pi
**Phase**: Phase 1 Round 2 — 专家决策 (FRAME 五维评估)
**评估日期**: 2026-05-10
**基于**: Round 1 三份机器预检报告 + 表型操作化方案

---

## FRAME 总览

| 维度 | 评分 | 关键数据来源 |
|------|------|-------------|
| F — Field Scan (领域扫描) | ⭐⭐⭐⭐ 中上 | 文献预检报告 |
| R — Resource Audit (资源审计) | ⭐⭐⭐ 中 | DQ-CARE 报告 |
| A — Alignment (对齐) | ⭐⭐⭐⭐ 中上 | PI 专业判断 |
| M — Market Gap (发表缺口) | ⭐⭐⭐⭐⭐ 高 | 文献预检 + 期刊趋势 |
| E — Edge Assessment (优势) | ⭐⭐⭐⭐ 中上 | 建模可行性 + 团队经验 |

**总体**: 20/25 — **建议: ✅ 启动 (方案 A: 复合结局)**

---

## F — Field Scan (领域扫描)

### 引用文献预检数据

**对标论文性能对比** (来自 research-assistant 文献预检):

| 对标论文 | 数据 | 样本量 | 方法 | 最佳性能 | 对比本项目的差异 |
|---------|------|--------|------|---------|----------------|
| Tang et al. (2024) Cancer Science | SEER | 140,294 | CatBoost | AUC 0.939 | SEER 长期生存 vs MIMIC 短期预后 |
| Conditional CS (2025) Sci Reports | SEER | 301,441 | LASSO+Cox | C-index 0.869 | 长期 CSS vs 30天复合结局 |
| EACCD (2025) Diagnostics | SEER | TBD | Ensemble | C-index 0.8504 | 癌症登记 vs EHR 时序 |
| Momenzadeh et al. (2021) | SEER | TBD | XGBoost | Acc 86.28% | 同 SEER |
| Lee et al. (2021) Lancet Digital Health | SEER | TBD | Novel ML | — | 领域标杆 |

### SOTA 对比判断

- **所有对标论文均使用 SEER 数据** — 存在一个明确的缺口: **没有论文使用 EHR 时序数据进行前列腺癌短期预后预测**
- SEER 的性能天花板 (AUC 0.85-0.94) 与本项目的 MIMIC EHR 任务 (预期 AUC 0.80-0.85) 是不同临床问题，不应直接比较
- **竞争强度**: SEER + 前列腺癌 + ML 的市场较拥挤 (系统综述覆盖 47 篇研究, Ahuja 2024)。本项目用 EHR 数据做短期预后是该赛道的差异点

### Field Scan 结论

**竞争位置**: 本项目在所有对标论文中**不占样本量优势** (2,497 vs 140K+)，但占据**差异化位置**: EHR 时序 + 短期结局 + 临床可部署性。这不是正面竞争，是蓝海细分。

---

## R — Resource Audit (资源审计)

### 引用 DQ-CARE 报告数据

| 关键资源 | 状态 | 数据来源 |
|---------|------|---------|
| SEER 数据 | ❌ 不可用 | data-engineer 探查 |
| MIMIC-IV 前列腺癌患者 | ✅ 2,497 人, 3,956 次入院 | DuckDB 查询 |
| PSA 测量值 | ✅ 76,282 次, 21,640 患者 | labevents 查询 |
| Gleason 评分 | ❌ 不可用 (需 Note 模块) | DQ-CARE 评估 |
| TNM 分期 | ❌ 不可用 (同上) | DQ-CARE 评估 |
| 30天死亡事件 | 128 例 (3.2%) | DuckDB 查询 |
| ICU 入院 | 678 例 (17.1%) | DuckDB 查询 |
| 前列腺切除术 | 214 例 | DuckDB 查询 |
| 复合结局事件 | ~700+ (估算) | 死亡+ICU 组合 |
| TCGA-PRAD | ❌ 不可用 | data-engineer 探查 |

### 资源审计判断

- ⚠️ **关键肿瘤特征缺失**: Gleason 评分和 TNM 分期是最重要的前列腺癌预后因子，但需要 MIMIC-IV-Note 模块 (非结构化文本)
  - 缓解: v1 版本使用实验室+人口学+合并症特征，v2 可加入 Note NLP
- ⚠️ **30天死亡率低 (3.2%)**: 单独作为结局有可能模型不稳定
  - 缓解: 使用复合结局 (死亡 OR ICU)，预期事件率 ~17%+
- ✅ **PSA 可用**: 最关键的肿瘤标志物数据丰富
- ⚠️ **样本量中等 (2,497)**: 足够 ML 建模，但需要控制特征数

### 数据能否支撑研究目标?

**可以，但需要合理调整期望**: 不能做「前列腺癌预后预测」的泛化声明，应聚焦于「住院前列腺癌患者的短期不良结局预测」，明确定位为临床决策支持工具。

---

## A — Alignment Check (对齐检查)

### 与事业部战略的对齐

- ✅ **泌尿外科事业部首个新项目**: 需建立 EHR-ML pipeline 为新项目打样
- ✅ **与 kidney-stone 项目的协同**: 两个项目共享 MIMIC-IV 数据源、特征工程 pipeline、外部验证方法学
- ✅ **临床需求**: 前列腺癌患者住院期间的风险分层是真实的临床需求
- ✅ **基金与学科方向**: 临床预测模型 + AI + 泌尿外科是 NIH/AHRQ 的热门方向

### 对齐度

研究直接服务于泌尿外科事业部的扩展目标，同时为共享服务的 EHR-ML pipeline 建设做贡献。

---

## M — Market Gap (发表缺口)

### 引用文献预检的期刊趋势分析

**SEER + 前列腺癌 + ML** 已发表 47+ 篇 (系统综述, Ahuja 2024):
- 竞争强度: 高
- 发表空间: 较小 (需差异化)

**EHR + 前列腺癌 + 短期预后 + ML**:
- 文献检索未找到直接对标论文
- 竞争强度: 低
- 发表空间: 较大

### 目标期刊策略

| Tier | 期刊 | IF | 匹配度 | 策略 |
|------|------|-----|--------|------|
| Tier 1 | European Urology | 24.3 | 低 | 现阶段不建议投; 需大样本+多中心 |
| **Tier 2** | **J Urology** | **6.6** | **中高** | **首投目标** — 临床可操作性强 |
| Tier 3 | BMC Urology | 2.0 | 高 | 保底目标 — 接受单中心 EHR 研究 |
| 备选 | Prostate Cancer and Prostatic Diseases | 4.9 | 高 | 专业期刊 |
| 备选 | BMC Medical Informatics & Decision Making | 3.3 | 中 | 信息学视角 |

### 发表缺口判断

该方向在目标期刊有**明确的发表空间** — EHR 数据驱动的短期预后预测是一个与已有 SEER 研究互补的细分方向。首投建议 J Urology (强调临床实用性) 或 Prostate Cancer and Prostatic Diseases (强调疾病专业化)。

---

## E — Edge Assessment (优势评估)

### 引用建模可行性报告 + 团队经验

**团队能力匹配**:

| 能力 | 匹配度 | 依据 |
|------|--------|------|
| EHR 数据提取 | ✅ 高 | kidney-stone 项目已完成 MIMIC-IV cohort 提取 (extract_cohort.py) |
| 特征工程 | ✅ 高 | kidney-stone 项目已有 enhance_features.py pipeline |
| ML 模型训练 | ✅ 高 | ml-engineer 已在 kidney-stone 项目中训练 5 个模型, AUC 0.755 |
| SHAP 可解释性 | ✅ 高 | ml-engineer 熟悉 SHAP 分析 |
| 外部验证 | ✅ 高 | data-engineer 完成 MIMIC-III 外部验证 (AUC 0.8286) |
| 统计方法 | ✅ 高 | biostatistician 已有 SAP 模板 |
| 前列腺癌领域知识 | ⚠️ 中 | 临床研究员需要补充前列腺癌特定知识 |

**技术成熟度**: 方法学风险低 — XGBoost + SHAP 是经过验证的方案，现有 pipeline 可复用

**关键差异化优势**:
1. **Pipeline 复用**: kidney-stone 项目的完整 pipeline 可直接迁移 (预计节省 30-40% 开发时间)
2. **EHR 时序数据能力**: 团队已有 EHR 多表 JOIN 和特征时间窗口构建经验
3. **外部验证经验**: 已验证 MIMIC-III → MIMIC-IV 的跨版本验证策略

**估计 6 个月可产出成果**: **高概率** (75-80%) — 风险降低因素: pipeline 复用 + 方法成熟; 风险增加因素: 特征不确定 (Gleason 缺失) + 样本量中等

---

## 最终建议: ✅ 启动 (方案 A: 复合结局)

### 批准的研究问题

> **"Development and internal validation of a machine learning model to predict 30-day mortality or ICU admission in hospitalized prostate cancer patients using MIMIC-IV EHR data"**

### 启动条件 (注入下游 Phase)

1. **C1**: 使用复合结局 (30天死亡 OR ICU 入院)，不单独使用死亡结局
2. **C2**: 特征集以实验室 + 人口学 + 合并症为主，Gleason/TNM 缺失需在 Discussion 中明示
3. **C3**: 样本量 ≥ 1,500 (首次入院去重后)，正例 ≥ 200
4. **C4**: 目标期刊调整为 J Urology (Tier 2) / Prostate Cancer P.D. (备选)，不做 European Urology
5. **C5**: 若外部验证可行，尽量使用 MIMIC-III 作为外部验证队列

### 不启动原方案 (SEER) 的原因

SEER 长期生存预测的研究竞争激烈 (47+ 篇)，且 SEER 数据不可用。本项目用 EHR 做短期预后是该赛道的差异化路线。

---

*FRAME 评估完成。进入 Phase 2: 方案设计 (研讨厅辩论模式)*

# Pediatrics PI — Few-Shot Example

## Example: FRAME 评估 — PICU 死亡率预测项目

**用户请求**: "评估用 PIC 数据做 PICU 死亡风险预测这个方向是否值得投入"

### FRAME 评估报告

#### 研究问题
基于 PIC 数据库入 PICU 24 小时内的临床数据，预测 PICU 死亡风险

#### F — 领域扫描
- 发表趋势: 上升，年发文量约 20-40 篇 (PubMed "PICU mortality prediction" + "machine learning")
- 顶刊活跃度: 中等 — Pediatric Critical Care Medicine 近 2 年发了 5-8 篇儿科 ML 文章
- 主要竞争者: CHOP (USA), Boston Children's (USA), Great Ormond Street (UK), 复旦大学儿科医院 (China)
- 判断: **蓝海** — 基于中国人群 PICU 数据的 ML 预测模型几乎空白

#### R — 资源审计
- 数据: PIC 含 ~12,881 患者，其中 PICU ~5,000-6,000，死亡事件 ~250-400 例
- 算力: 表格数据 + 时序特征，M4 MPS 完全足够 (XGBoost + LSTM)
- 团队能力: 儿科临床知识 ✓, ML 工程 ✓, 重症评分系统 (PRISM III/pSOFA) 需学习
- 预期首篇产出周期: 3-4 个月

#### A — 对齐检查
- 临床需求: 强 — PICU 死亡风险分层直接影响资源分配和家长沟通，现有评分 (PRISM III) AUC ~0.75-0.85，有提升空间
- 基金对齐: 是 — 国自然面上项目儿科方向
- 战略对齐: 是 — 精准医疗在儿科重症监护的落地

#### M — 发表缺口
- 推荐目标期刊: Pediatric Critical Care Medicine (Tier 2, IF~4) 或 Pediatrics (Tier 2, IF~8)
- 竞争激烈程度: 低-中 — 中国 PICU 数据的 ML 预测研究极少
- 判断: 6 个月内完成可抢占先机

#### E — 优势评估
- 核心优势: (1) PIC 是中国最大的单中心儿科重症数据库, 具有独特价值 (2) NICU/PICU/CCU 覆盖完整儿科重症谱 (3) 含时序数据 (生命体征/实验室), 可做纵向建模

### 综合判断
- 推荐: **启动** (高优先级)
- 理由: 蓝海方向 + 数据独特 + 强临床需求 + 发表窗口存在
- 注意事项: 单中心数据需要明确讨论可推广性限制; 死亡事件数需确认 power 是否足够

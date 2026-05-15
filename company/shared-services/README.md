# 公共服务平台 (Shared Services Platform)

为所有事业部提供方法学执行支持。共享服务 Agent 是**领域无关的方法学专家**——他们不拥有临床领域知识，而是执行标准化的方法学任务。

## 服务目录

| 服务 ID | 服务名称 | 服务描述 | 服务所有事业部 |
|---------|---------|----------|--------------|
| `shared/data-engineer` | 数据工程 | 多源数据 ETL、数据质量检查 (DQ-CARE)、OMOP 标准化、数据字典编制 | 全部 |
| `shared/biostatistician` | 生物统计 | 研究设计、SAP 撰写、因果推断、统计审查 | 全部 |
| `shared/ml-engineer` | 机器学习工程 | 模型实现与调优、特征工程、MLOps、可解释性报告 | 全部 |
| `shared/scientific-writer` | 学术写作 | 论文 IMRaD 撰写、润色、投稿准备、DOI 验证 | 全部 |
| `shared/research-assistant` | 科研辅助 | 文献检索与综述 (PRISMA 2020)、EDA、基线实验 | 全部 |
| `shared/clinical-tool-developer` | 临床工具开发 | 预测模型临床部署、Streamlit Web 工具生成、可执行文件打包 | 全部 |

## 服务调度机制

1. 事业部通过 company-orchestrator 向共享服务发起请求
2. PMO 维护每个共享服务的状态（idle/busy）和排队队列
3. 当服务被占用时，新请求进入队列等待
4. 优先级规则（由首席科学家制定）：
   - P0: 有外部合作截止日期的项目
   - P1: 处于写作/投稿阶段的项目
   - P2: 处于执行阶段的项目
   - P3: 探索性项目
5. 同等优先级：先到先得

## Division Context Detection

共享服务 Agent 在处理请求时，通过通信协议的 `division` 和 `data_sources` 字段识别当前服务的事业部和数据源：

- **事业部识别**: 从 `division` 字段读取，用于选择领域知识库（geriatrics vault vs urology vault）和目标期刊
- **数据源选择**: 从 `data_sources` 字段读取（公司级资产，所有事业部均可使用任何数据源），用于定位数据目录和选择数据工具
- 数据源不再绑定到特定事业部 — 例如 geriatrics 事业部可以使用 MIMIC-IV，urology 事业部也可以使用 CHARLS

## 服务质量标准

| 指标 | 标准 |
|------|------|
| SAP 产出时间 | ≤ 2 个工作日 |
| 数据质量报告 | ≤ 1 个工作日 |
| 模型训练 + 评估 | ≤ 5 个工作日 |
| 论文初稿 | ≤ 7 个工作日 |
| 文献综述 | ≤ 5 个工作日 |
| 临床工具部署 | ≤ 3 个工作日 |

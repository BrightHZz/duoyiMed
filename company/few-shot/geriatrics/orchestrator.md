# Few-Shot 示例 — Orchestrator Agent

## Example 1: 新项目启动编排

### Input

```
用户: "我想用 CHARLS 数据做一个预测 2 年衰弱的模型,
帮我设计完整方案并启动项目。"
```

### Reasoning (Chain of Thought)

```
触发关键词: "预测模型" + "衰弱" + "CHARLS"
→ computational-biologist, clinical-researcher, data-engineer, research-assistant

编排计划:
  Phase 1 (并行): 
    - clinical-researcher: 临床问题操作化
    - data-engineer: 变量可用性评估
    - research-assistant: 文献扫描
  这三者互不依赖, 可并行

  Phase 2 (串行, 依赖 Phase 1):
    - computational-biologist: 建模方案 (需要 Phase 1 的全部输出)
    - biostatistician: SAP (需要 clinical+data 输出)

  Phase 3 (串行):
    - PI: FRAME 评估 + 最终审核方案
```

### Output

```markdown
## 任务分解 — CHARLS 衰弱预测建模

### 理解
用户希望基于 CHARLS 数据, 开发一个预测社区老年人 2 年内衰弱恶化的机器学习模型。

### 编排计划

```
Phase 1 ─── 信息收集 (并行) ───
├──→ clinical-researcher:
│    任务: 定义临床问题 — 目标人群、纳入排除、Fried表型CHARLS变量映射
│    输出: 临床问题操作化文档
│
├──→ data-engineer:
│    任务: 评估 CHARLS 各 wave 衰弱相关变量可用性
│    输出: 变量覆盖矩阵 + 缺失率报告
│
└──→ research-assistant:
     任务: 扫描近2年"ML预测衰弱"文献
     输出: 结构化文献笔记 + 领域简报

Phase 2 ─── 方案设计 (依赖 Phase 1) ───
├──→ computational-biologist:
│    任务: 接收 Phase 1 输出, 设计建模方案
│    输出: 建模方案文档 (→ Obsidian)
│
└──→ biostatistician:
     任务: 撰写 SAP
     输出: 统计分析计划

Phase 3 ─── 决策 ───
└──→ PI:
     任务: FRAME评估 + 方案终审
     输出: Go/No-go 决策
```

### 下一步
我将按 Phase 1 并行启动三个 Agent。可否确认开始？
```

---

## Example 2: 处理 Agent 间冲突

### Input

```
computational-biologist 说: 
  主模型用 XGBoost, 特征选择用 Boruta

biostatistician 说: 
  Boruta 在 CV 外部做特征选择 → 会导致信息泄露 → 不准用

两个 Agent 的建议冲突了, 怎么办?
```

### Reasoning

```
分析冲突:
  - computational-biologist 推荐 Boruta 是因为它的稳健性
  - biostatistician 反对是因为 Boruta 如果在 CV 外执行会导致信息泄露
  - 两人可能并不矛盾: Boruta 可以用, 但必须在 CV 内

解决方案: 
  - 不是二选一, 而是"在 CV 内部做 Boruta"
  - 这需要 ml-engineer 评估性能成本 (每 fold 做一次 Boruta 较慢)
  - 如果太慢, 可以用 Elastic Net 替代 (在 CV 内自然完成特征选择)
```

### Output

```markdown
## 冲突裁决 — 特征选择方法

### 冲突点
- computational-biologist: 推荐 Boruta (稳健性)
- biostatistician: Boruta 可能导致数据泄露 (方法学严谨性)

### 分析
双方各有道理, 但并不是非此即彼:
  - biostatistician 的担忧是执行方式 (Boruta in CV 外), 而不是 Boruta 本身
  - computational-biologist 可以接受"Boruta in CV 内"的替代方案

### 裁决
1. **如果计算资源允许**: 在 nested CV 内部每 fold 做 Boruta → 最稳健
2. **如果计算资源有限 (更可能)**: 
   用 Elastic Net (alpha=0.5) 替代 Boruta → 自然在CV内完成特征选择
3. **决策**: 选方案 2 (Elastic Net), 因为:
   - 样本量 N≈5,000, Elastic Net 足够
   - 性能更优 (比每 fold Boruta 快 10 倍+)
   - biostatistician 的方法学担忧完全解决

### 通知
→ computational-biologist: 更新建模方案, Boruta → Elastic Net
→ biostatistician: 方法学担忧已解决, SAP 可继续
→ ml-engineer: 使用 Elastic Net 做特征选择, 集成在 Pipeline 中
```

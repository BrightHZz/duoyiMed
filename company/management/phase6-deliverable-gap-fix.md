# Phase 6 交付件缺失 — 根因分析与改进方案

**日期**: 2026-05-10
**触发**: 前列腺癌项目 Phase 6 完成后发现缺少分章节文件、表格和图表
**范围**: 编排引擎 Phase 6 子编排 + Gate 6 检查项 + 项目产出声明

---

## 一、根因分析

### 根因 1 (核心): Phase 6 被建模为单 Agent 原子操作

当前 `orchestrator_graph.py:128-134`:

```python
"writing": {
    "agents": ["scientific-writer"],   # 仅一个 Agent
    "parallel": False,
    "description": "论文撰写...",
    "depends_on": ["review"],
    "next": None,
}
```

Phase 6 调用 scientific-writer **一次**，期待一个 LLM 响应输出全部内容。但实际上论文撰写的交付件包含多种类型（文本、表格、图表），需要多次调用不同 Agent：

| 子任务 | 负责方 | 产出类型 |
|--------|--------|---------|
| Table 1/2/3 | research-assistant + ml-engineer 数据提取 | Markdown 表格 |
| Figure 1-4 | ml-engineer 出数据 + plot 脚本 | PNG 图像 |
| IMRAD 各节初稿 | scientific-writer | Markdown 文本 |
| 全文合稿 | scientific-writer 组装 | manuscript.md |

**没有子编排环节，单次 LLM 调用的输出天然无法保证多文件产出。**

### 根因 2: Gate 6 检查项全是文本内容检查，无文件存在性检查

当前 `gate_checks.py` Phase 6 的 auto_checks (6项):

| 检查项 | 检查内容 |
|--------|---------|
| `conclusion_heading` | Conclusion 必须是 `##` 层级 |
| `doi_verified` | DOI 可验证 |
| `ref_count` | 参考文献 ≥ 25 |
| `ref_recency` | ≥ 80% 近 5 年文献 |
| `discussion_paragraphs` | Discussion 四段结构 |
| `discussion_no_conclusion` | 第四段无结论性收束句 |

**全部 6 项检查的都是文本内容字符串的属性，没有一项检查文件系统。** 缺失的检查:
- `check_sections_exist` — sections/ 目录下是否有独立的 IMRAD 文件
- `check_tables_exist` — tables/ 目录下是否有 Table 1/2/3
- `check_figures_exist` — figures/ 目录下是否有图像文件
- `check_manuscript_assembled` — manuscript.md 是否存在

### 根因 3: Phase 定义缺少 expected_outputs 声明

当前 PROJECT_PHASES 的 Phase 定义结构:

```python
"writing": {
    "agents": [...],
    "parallel": False,
    "description": "...",
    "depends_on": [...],
    "next": None,
}
```

缺少一个 `expected_outputs` 字段来声明该 Phase 应该产出的文件清单。每个 Phase 都应该声明自己的交付件，Gate 检查时自动验证。

### 根因 4: Agent 文件契约与编排能力不匹配

scientific-writer 的 Agent prompt 中声明了输出包括:

```
- 论文分节文件 (sections/*.md)
- 完整编译稿件 (manuscript.md)
- Cover Letter
```

但编排层没有机制把这些"承诺"转化为实际的文件系统写入操作。

---

## 二、改进方案

### 改进 1: Phase 6 子编排 (核心修改)

**目标**: 将 Phase 6 从一个原子调用拆分为多步骤子工作流。

修改 `orchestrator_graph.py`，为 Phase 6 增加专门的执行方法 `_execute_phase_writing`:

```python
def _execute_phase_writing(self, ...):
    """Phase 6 子编排: 表格→图表→分节→合稿→验证"""
    outputs = {}

    # Step 1: 生成表格 (research-assistant 提取数据)
    outputs['tables'] = self._generate_tables(upstream_outputs)

    # Step 2: 生成图表 (调用 plot 脚本)
    outputs['figures'] = self._generate_figures()

    # Step 3: 分章节撰写 (scientific-writer, 每个 IMRAD 节一次调用)
    for section in ['introduction', 'methods', 'results', 'discussion', 'conclusion']:
        outputs[section] = self._call_agent("scientific-writer", section_prompt)

    # Step 4: 合稿
    outputs['manuscript'] = self._assemble_manuscript(outputs)

    # Step 5: 写入文件系统
    self._write_phase6_files(outputs)

    return outputs
```

### 改进 2: Gate 6 增加文件存在性检查

在 `gate_checks.py` 中新增 4 个 auto check 函数:

```python
def check_sections_exist(outputs, orchestrator):
    """检查 sections/ 目录下是否有完整的分章节文件"""
    required = ['introduction', 'methods', 'results', 'discussion', 'conclusion']
    # 扫描 sections/ 目录
    ...

def check_tables_exist(outputs, orchestrator):
    """检查 tables/ 目录下是否有 Table 1/2/3"""
    required = ['table1_baseline', 'table2_model_performance', 'table3_subgroup']
    ...

def check_figures_exist(outputs, orchestrator):
    """检查 figures/ 目录下是否有至少 4 张图"""
    ...

def check_manuscript_assembled(outputs, orchestrator):
    """检查 manuscript.md 是否存在且包含所有 IMRAD 章节"""
    ...
```

### 改进 3: Phase 定义增加 expected_outputs

在每个 Phase 的 PROJECT_PHASES 定义中增加:

```python
"writing": {
    "agents": ["scientific-writer", "research-assistant", "ml-engineer"],
    "parallel": False,
    "description": "论文撰写",
    "depends_on": ["review"],
    "next": None,
    "expected_outputs": [
        "sections/01_title.md",
        "sections/02_abstract.md",
        "sections/03_introduction.md",
        "sections/04_methods.md",
        "sections/05_results.md",
        "sections/06_discussion.md",
        "sections/07_conclusion.md",
        "sections/08_references.md",
        "tables/table1_baseline.md",
        "tables/table2_model_performance.md",
        "tables/table3_subgroup.md",
        "figures/roc_curve.png",
        "figures/calibration.png",
        "figures/feature_importance.png",
        "figures/dca.png",
        "manuscript.md",
    ],
    "output_dir": "projects/{project_id}/",  # 产出写入的项目目录
}
```

Gate 检查时自动遍历 `expected_outputs` 验证文件存在性。

### 改进 4: 增加 figure-generation 工具

在 `tools.py` 中注册绘图工具，让 orchestration 层可以直接调用生成标准化图表:

```python
# tools.py 新增
def generate_roc_curve(y_true, y_prob, output_path):
    """生成 ROC 曲线图"""
    ...

def generate_calibration_plot(y_true, y_prob, output_path):
    """生成校准曲线图"""
    ...

def generate_shap_importance(feature_names, shap_values, output_path):
    """生成 SHAP 特征重要性图"""
    ...
```

---

## 三、实施优先级

| 优先级 | 改进项 | 影响范围 | 实现难度 |
|--------|--------|---------|---------|
| **P0** | Gate 6 文件存在性检查 | `gate_checks.py` + 4 个函数 | 低 (30 分钟) |
| **P0** | Phase 定义加 expected_outputs | `orchestrator_graph.py` PROJECT_PHASES | 低 (15 分钟) |
| **P1** | Phase 6 子编排 | `orchestrator_graph.py` 新增方法 | 中 (2-3 小时) |
| **P2** | 绘图工具注册 | `tools.py` 新增工具函数 | 中 (1-2 小时) |

**P0 改进立即可做，能防止同样的问题再次发生**（下次 Phase 6 的 Gate 会 FAIL 因为没有文件存在）。P1 改进需要重构 Phase 6 执行逻辑，建议在下一个项目开始前完成。

## 补充: Title 长度约束缺失 (2026-05-10 发现)

`scientific-writer-agent.md:92` 和 `:457` 明确要求 **Title ≤ 15 词** (`### Title — ≤15词`)，但同样没有对应的 Gate check。已随 P0-1 一并新增 `check_title_length` 检查函数。

## 四、实施记录 (2026-05-10)

| 优先级 | 改进项 | 状态 | 文件 |
|--------|--------|------|------|
| P0-1 | Gate 6 新增 5 个检查 | ✅ 已完成 | `engine/core/gate_checks.py` |
| P0-2 | 全部 Phase 增加 expected_outputs | ✅ 已完成 | `engine/core/orchestrator_graph.py` |
| P1 | Phase 6 multi_step 子编排 | ✅ 已完成 | `engine/core/orchestrator_graph.py` |
| P2 | 绘图工具注册 | ✅ 已完成 | `engine/core/tools.py` |
| 额外 | Title ≤15词 check | ✅ 已完成 | `engine/core/gate_checks.py` |

---

## 五、临时缓解措施 (本项目的 manual fix)

对于当前前列腺癌项目，已手动补齐:
- `sections/01-08_*.md` (8 个分章节文件)
- `tables/table1-3_*.md` (3 个表格)
- `figures/*.png` (4 张图表) + 5 个图注
- `generate_figures.py` (图表生成脚本)

# Phase 6 执行规范

## Python+LLM 混合执行

**背景**: Phase 6 此前完全依赖编排器 Agent 手工操作, 5 次事故中 4 次是因为 Agent 遗漏或误操作。根源: 自然语言约束无强制执行机制。

**Python+LLM 分工原则**:
- **Python 脚本**: 负责确定性检查 — 文件存在性、命名格式、数值一致性 (diff < 0.1%)、计数/字数/禁用词 regex。规则明确、无歧义, `exit 1` 阻断。
- **LLM Agent**: 负责语义评估 — Discussion 段落结构是否真正七段式、Methods↔Results 是否 1:1 对应、缩写是否正确引入、去 AI 味是否真正改善了自然度。
- **不可口头通过**: Python `exit 1` 和 LLM 审查 FAIL 均阻断流程, 编排器不可跳过任何一项。

## 执行序列 (编排器必须严格按此顺序调用)

```
1. python run_preflight.py              → exit 0 = SAFE,   exit 1 = BLOCKED (安全扫描, 纯 Python)
2. [编排器调用 scientific-writer]      → 产出 imrad_blueprint.md (含层级结构图/字数预算/Methods↔Results 映射表/数值溯源表) + 触发研讨厅三方并行评审 + PI 签批
3. python generate_figures.py           → 输出 Figure[N]_*.png + .tiff (纯 Python)
4. python generate_tables.py            → 输出 tables/*.csv + tables/*.md (纯 Python)
5. [编排器调用 scientific-writer]      → 基于蓝图撰写 sections/*.md (LLM, 唯一需要创造力的步骤)
6. python run_imrad_check.py            → exit 0 = IMRAD 结构合规, exit 1 = FAIL (纯 Python)
7. python run_humanize.py + LLM review  → 两层: Python 扫描禁用词/过渡词/hedge + LLM 评估自然度改善
8. python run_assembly.py               → exit 0 = 投稿层完整, exit 1 = FAIL (纯 Python)
9. python run_gate6.py + LLM Gate       → 两层: Python 执行 33 项确定性 auto check + LLM 执行 4 项语义检查
```

## 各脚本职责与阻断条件

| 脚本 | Python 职责 (exit 1 阻断) | LLM 职责 (FAIL 阻断) |
|------|--------------------------|---------------------|
| `run_preflight.py` | 扫描安全配置 (n_jobs, thread limits, pickle 覆盖, 跨脚本一致性) | — (无需 LLM) |
| `imrad_blueprint.md` + 研讨厅评审 | scientific-writer 产出蓝图 + PI/biostatistician/clinical-researcher 三方评审 | 研讨厅辩论: 三方独立审阅 → Writer 修订 → PI 签批 |
| `generate_figures.py` | 从 cv_results.json 生成 Figure[N]_*.png + .tiff + _data.json + _caption.md | — (无需 LLM) |
| `generate_tables.py` | 从 cv_results.json 生成 Table 1/2/3 的 .csv 和 .md | — (无需 LLM) |
| `run_imrad_check.py` | 4 项 IMRAD 结构验真: heading层级/Methods↔Results映射/Discussion结构/Conclusion独立性 | — (纯确定性规则) |
| `run_humanize.py` + LLM | 扫描所有 sections/*.md: banned > 0 或 trans > 3 → exit 1 | 评估去 AI 味改写是否真正改善了自然度 |
| `run_assembly.py` | 拼接 manuscript + strip Classic + 复制 figures tables → submission/ + 5 条否定约束 + 自检 | — (纯确定性操作) |
| `run_gate6.py` + LLM Gate | 33 项 Python auto check → exit 1 | 4 项 LLM semantic check → 任何 FAIL 阻断 |

## 编排器错误做法 (已被此机制阻断)

- ❌ 不产出 IMRAD 蓝图直接写 sections → Gate 6 #30 阻断
- ❌ 不触发研讨厅评审就对蓝图签批 → Gate 6 #30 阻断
- ❌ 手动 cp -r sections/ submission/ → `run_assembly.py` 不会创建 sections/, Gate 6 #28 阻断
- ❌ 手动 cat sections/*.md 但不 strip Classic → `run_assembly.py` 内置 `re.sub(r'\[Classic[^]]*\]', '', text)`
- ❌ 跳过 IMRAD check → `run_imrad_check.py` 未执行 → heading 层级错误 → Gate 6 #31-33 阻断
- ❌ 跳过 humanize → `run_gate6.py` #22 检查禁用词/过渡词 + LLM 语义评估
- ❌ 口头说 "Gate 6 通过" → 必须 `python run_gate6.py` 返回 exit 0
- ❌ 只用 Python regex 检查去 AI 味 (没有 LLM) → 表面替换无法通过语义评估

---

## Assembly 精确定义

**assembly 输入/输出**:

| 输入 (零件层, root) | 操作 | 输出 (投稿层, submission/) |
|------|------|------|
| `sections/0*.md` | **拼接为单文件** | `manuscript.md` |
| `tables/*.csv` | **复制** | `tables/*.csv` |
| `figures/*.png` | **复制** | `figures/*.png` |
| `figures/*.tiff` | **复制** | `figures/*.tiff` |

**assembly 否定约束 (强制)**:
```
1. submission/ 下不得存在 sections/ 目录
2. submission/figures/ 下仅允许 .png 和 .tiff 文件
3. submission/tables/ 下仅允许 .csv 文件
4. 零件层的 .md caption、.json 数据文件留在 root figures/ 和 root tables/, 不进入 submission/
5. Classic 标注不得保留在投稿层: root sections/08_references.md 中的 [Classic — ...] 标记为内部元数据, assembly 拼接时必须 strip 或替换为空字符串
```

**assembly 执行后自检**:
```
check_submission_structure_integrity(project_dir):
    sub = project_dir / "submission"
    → sub/sections/ 目录存在 → FAIL
    → sub/figures/ 下有 .md 文件 → FAIL
    → sub/figures/ 下有 .json 文件 → FAIL
    → sub/tables/ 下有 .md 文件 → FAIL
    → sub/ 下无 manuscript.md → FAIL
    → sub/figures/ 下 .png 缺对应的 .tiff → FAIL
    → sub/manuscript.md 中含有 "[Classic" 文本 → FAIL
```

---

## Figure 文件命名规范

**命名格式**: `Figure[N]_[descriptor].[ext]`

| Figure 编号 | 内容 | 文件名 |
|------------|------|--------|
| Figure 1 | 研究流程图 (手动) | `Figure1_cohort-flow-diagram.png` |
| Figure 2 | ROC 曲线 | `Figure2_roc-curve.png` |
| Figure 3 | 校准曲线 | `Figure3_calibration-plot.png` |
| Figure 4 | 特征重要性 | `Figure4_feature-importance.png` |
| Figure S1 | 决策曲线分析 | `FigureS1_decision-curve-analysis.png` |

**data.json 和 caption 同步命名**:
```
Figure2_roc-curve_data.json      (不是 figure2_data.json)
Figure3_calibration-plot_data.json
Figure4_feature-importance_data.json
Figure2_caption.md               (不是 fig2_caption.md)
Figure3_caption.md
```

---

## Figure 防重叠规范 (6 条强制规则)

1. **全局布局约束**: 每张图必须 `fig.set_constrained_layout(True)` 或 `fig.tight_layout(pad=1.08)`, subplots 必须显式传 figsize≥(8,5)
2. **图例防遮挡**: 条目 >3 时置于绘图区外 `bbox_to_anchor=(1.02, 1)`, 背景半透明 `framealpha=0.7`
3. **刻度标签防重叠**: x 轴标签 >8 或字符 >5 时旋转 `rotation=45, ha='right'`, y 轴数值 >1000 时转 k/M 单位
4. **文本标注防碰撞**: 使用 `ax.annotate()` 须设 xytext 偏移, 多点标注(>5)推荐 adjustText 库
5. **多面板间距**: subplots 后必须调 `fig.subplots_adjust()` 或 constrained_layout, 共享轴仅在最外轴显示 label
6. **保存前检查**: savefig 前禁止 `plt.show()`, 使用 `bbox_inches='tight'` + dpi≥300

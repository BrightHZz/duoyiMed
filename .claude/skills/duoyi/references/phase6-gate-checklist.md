# Phase 6 完整 Gate Check 清单

共 33 项 auto check: 29 存在性/格式性/数值 + 4 IMRAD 结构验真。

## 33 项检查清单

| # | 检查项 | 检查目标层 | 通过标准 |
|---|--------|----------|---------|
| 1 | SAP 已签批 | root | projects/{id}/sap.md 存在 |
| 2 | 期刊需求已锁定 | root | 目标期刊配置确认 |
| 3 | Title ≤ 15 词 | 投稿层 | 标题词数检查 |
| 4 | Sections 分章节存在 | **零件层 (root)** | root `sections/` 含 ≥6 个 IMRAD 文件 (此为供 assembly 消费的零件, **非** submission/sections/) |
| 5 | Tables 存在 (双格式) | **零件层 + 投稿层** | root `tables/` 含 Table 1/2/3 `.md` + `submission/tables/` 含 Table 1/2/3 `.csv` |
| 6 | Figures 存在 + 命名格式 (双格式) | **零件层 + 投稿层** | root `figures/` 含 ≥3 张 `.png` + **文件名匹配 `Figure[N]_[descriptor].[ext]` 格式** + `submission/figures/` 含 ≥3 张 `.png` + 对应 `.tiff` |
| 7 | Manuscript 合稿 | 投稿层 | `submission/manuscript.md` 结构完整 |
| 8 | Abstract ≤ 300 词 | 投稿层 | 摘要词数检查 |
| 9 | Keywords ≥ 3 | 投稿层 | 关键词数量检查 |
| 10 | 参考文献 DOI 覆盖 | 投稿层 | ≥80% 参考文献有 DOI |
| 11 | AUC 带 95% CI | 投稿层 | Results 中 AUC 附 CI |
| 12 | 效应量+CI 报告 | 投稿层 | 效应量与 CI 同时出现 |
| 13 | 区分度+校准度 | 投稿层 | Results 同时含 AUC 和 Calibration |
| 14 | 正态性检验 | 投稿层 | Methods 含正态性检验说明 |
| 15 | 缺失数据处理 | 投稿层 | Methods 含缺失率+处理方法 |
| 16 | 软件+版本号 | 投稿层 | Methods 含软件名称及版本 |
| 17 | Conclusion 独立章节 | 投稿层 | `## Conclusion` 存在 |
| 18 | DOI 验证通过 | 投稿层 | fake DOI = 0 |
| 19 | 参考文献 ≥25/≥45 | 投稿层 | 论著≥25, 综述≥45 |
| 20 | 参考文献时效性 ≥80% | 投稿层 | ≥80% 近5年文献 |
| 21a | Discussion 无子标题标记 (**Python**) | 投稿层 | Python regex 扫描, 禁止任何形式子标题: `###` / `**粗体段名**` (≤6词独立行) / `___下划线___` / 全大写段名行 / 数字编号段名 (如 `1. Findings`)。七段之间仅用空行分隔 |
| 21b | Discussion 七段语义结构 (**LLM**) | 投稿层 | LLM 逐段判断: ¶1核心发现/¶2机制解释/¶3文献一致/¶4文献不一致/¶5含义/¶6优势/¶7局限+未来方向。与 21a 独立执行, 21a PASS 不豁免 21b |
| 22 | 去 AI 味质量检查 (**Python+LLM 两层**) | 投稿层 | **Python 层**: 禁用词 0 命中 + 过渡词 ≤ 3/全文 + hedge 不超限 + 无终结标语; **LLM 层**: 语义评估自然度(句子节奏/转折自然性/模板痕迹) |
| 23 | 缩写规范 (**LLM 辅助**) | 投稿层 | Python 检测 "XXX (ABBR)" 模式存在; **LLM 扫描全文确认每个缩写首次出现时给出全称** |
| 24 | 特征重要性图数一致 | 投稿层 | `figure2_data.json` 各 key 的值与 `cv_results.json.feature_importance` 对应 key 偏差 < 0.1% |
| 25 | 表格数一致 | 投稿层 | tables/*.md 中的 AUC/样本量/事件率 与 cv_results.json 对应字段偏差 < 0.1% |
| 26 | 正文数值可追溯 | 投稿层 | submission/manuscript.md 中所有 XX.X% / X.XXXX 格式的数值可追溯到 cv_results.json 或 tables/*.md |
| 27 | Figure 产自基线数据 | 投稿层 | generate_figures.py 中每个图的数据源可追溯到 Phase 3 baseline 文件, 禁止从模型对象重新提取 |
| 28 | 投稿层结构完整性 | **投稿层** | `submission/` 下无 `sections/` 目录 + `submission/figures/` 下仅 `.png`/`.tiff` + `submission/tables/` 下仅 `.csv` + `submission/manuscript.md` 存在 + `submission/manuscript.md` 中不含 `[Classic` 标注 |
| 29 | Figure 元素防重叠 | 投稿层 | `generate_figures.py` 必须含 constrained_layout/tight_layout + 图例外置(>3条目时+bbox_to_anchor) + 刻度标签旋转(>8个或>5字符时) + dpi≥300 |
| 30 | IMRAD 蓝图存在且签批 | root | `imrad_blueprint.md` 存在 + 末尾含 `APPROVED by {division}/pi on {date}` |
| 31 | IMRAD heading 层级验真 | 投稿层 | manuscript.md 的 markdown 层级: ## 必须恰好 5 个 (Introduction/Methods/Results/Discussion/Conclusion) + Methods/Results 必须有且仅有 5 个标准 ### 子标题 + Discussion 下禁止任何 ###/#### |
| 32 | Methods ↔ Results 1:1 映射 | 投稿层 | IMRAD 蓝图中映射表 ≥3 行; Methods 中每个分析方法声明必须能在 Results 中找到对应结果回报 |
| 33 | IMRAD 字数预算 | 投稿层 | 各节实际字数与蓝图预算偏差 <50%; 全文总字数 ≤5000 |

## Gate 6 Python/LLM 分工

正则能判定的归 Python，需理解语义的归 LLM。任一 FAIL 均阻断。

### Python auto checks (27 项，确定性)

| # | 检查项 | 为什么 Python 足够 |
|---|--------|-------------------|
| 1-2 | SAP/期刊需求 | 文件存在 + 关键词匹配 |
| 3 | Title ≤15 词 | `len(title.split())` |
| 4-7 | Sections/Tables/Figures/Manuscript 存在 | `os.path.exists()` + glob 计数 |
| 6b | Figure 命名格式 | regex `Figure[N]_[descriptor].ext` |
| 6c | Figure caption↔image 对应 | 每个 `Figure[N]_caption.md` 必须有对应 `Figure[N]_*.png` |
| 6d | Figure 正文引用 | grep manuscript 确认每个 `Figure[N]_*` 文件名在正文中有对应 (Figure N) 引用 |
| 8 | Abstract ≤300 词 | `len(words)` |
| 9 | Keywords ≥3 | 逗号分隔计数 |
| 10 | DOI 覆盖 ≥80% | regex `10.\d{4,}` 计数 |
| 11-13 | AUC+CI / 效应量+CI / 区分度+校准度 | regex 关键词匹配 |
| 14-16 | 正态性检验/缺失数据/软件版本 | regex 关键词匹配 |
| 17 | Conclusion ## 层级 | regex `## Conclusion` |
| 18 | fake DOI = 0 | DOI resolver API |
| 19 | 参考文献 ≥25 | 编号计数 |
| 19b | 每篇参考文献在正文被引用 | 交叉对比 References [n] 与正文 [n] |
| 20 | 时效性 ≥80% | 年份 regex + 经典豁免表 |
| 24-27 | 数值一致性 (feature importance/table/manuscript/figure baseline) | JSON diff < 0.1% |
| 27b | 数值精度一致性 | 跨 manuscript/tables/figures 交叉检查同指标小数位数统一 |
| 21a | Discussion 无任何形式子标题 | regex 多模式扫描: `###` / `**粗体行**`(≤6词) / `___下划线___` / 全大写段名 / 编号段名 |
| 28 | 投稿层结构完整性 | `os.path.exists()` + glob + regex `[Classic` |
| 29 | Figure 元素防重叠 | 扫描 `generate_figures.py`: constrained_layout 或 tight_layout 调用; 图例>3条目时 bbox_to_anchor; tick_params rotation 当 x 标签>8; savefig dpi≥300; 禁止 plt.show() |

### LLM semantic checks (4 项，需语义理解)

| # | 检查项 | 为什么 Python 不够 | LLM 审查 Prompt 要点 |
|---|--------|-------------------|---------------------|
| 21b | Discussion 七段语义结构 | Python 21a 已确保无子标题标记, 但无法判断每段的语义是否真正围绕其主题 | "阅读 Discussion，逐段评估: ¶1 是否简洁重申核心发现? ¶2 是否给出机制解释+替代解释? ¶3 是否将发现与一致文献对比? ¶4 是否列出不一致发现+可能原因? ¶5 每条含义是否有 because+supported by? ¶6 优势是否简洁具体? ¶7 局限是否按优先级+配缓解+以具体未来方向收尾?" |
| 22 | 去 AI 味质量 (语义层) | Python regex 可检测禁用词但无法判断文本是否真正自然 | "评估文本的自然度: 句子长度是否有变化? 段落节奏是否有起伏? 转折词使用是否自然? hedge 词是否适度保留? 是否仍能感觉到模板痕迹?" |
| 23 | 缩写规范 | regex 可检测模式存在但无法判断缩写是否在首次出现时被引入 | "列出文中所有非通用缩写。对每个缩写找到其首次出现的位置，检查该位置是否给出了全称，格式为 '全称 (ABBR)'。" |
| 整体 | 结构一致性 (语义层) | Python 只能检查 Methods 和 Results 节是否存在，无法判断两节的内容是否 1:1 对应 | "逐条检查 Methods 中声明的每个分析方法是否在 Results 中有对应的结果报告。" |

### LLM semantic check 强制触发规则

LLM semantic checks (21b/22/23/整体) 为强制步骤, 不因对应 Python check 通过而跳过。尤其 21b (Discussion 七段语义) 与 21a (无子标题标记) 互相独立:
- 21a PASS → 仅确认无 markdown/粗体/下划线等标记, 不保证七段语义正确
- 21b 必须由 LLM 独立审查, 编排器不可因 21a PASS 而口头豁免 21b

## Phase 6 Gate 6 检查的编排器调用

```
编排器在 run_humanize.py 和 run_gate6.py 的 Python 部分通过后，调用 PI 或 humanizer Agent 执行 LLM 审查。
LLM 审查返回: {check_id: pass|fail, detail: str}
任何 fail → 编排器不得口头通过，必须返工或记录为 COND_PASS (带条件注入下游)。
```

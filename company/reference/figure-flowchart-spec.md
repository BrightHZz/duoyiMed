# PRISMA / 流程图生成规范 (Graphviz DOT)

> 公司所有项目生成流程图类 Figure 时必须参照此规范。生成前将本文作为提示词传给 AI。

---

Generate a publication-quality PRISMA flow diagram using Graphviz DOT language.

Requirements:
- Nature/Lancet style scientific figure
- Avoid default Graphviz appearance
- Use strict symmetrical layout
- Use rankdir=TB
- Manually control node spacing and ranks
- Equal box widths
- Consistent vertical spacing
- Rounded rectangles with thin gray borders
- Minimalist academic aesthetics
- White background
- Straight orthogonal connectors
- Avoid crossing edges
- Avoid compressed layout
- Use subtle muted colors only
- Helvetica font
- High readability for journal publication

Node styling:
- shape=box
- style="rounded,filled"
- penwidth=1.2
- fontsize=18–22
- margin balanced
- width normalized
- fixedsize=false

Edge styling:
- color=gray30
- penwidth=1.2
- arrowsize=0.7
- splines=ortho

Layout tuning:
- nodesep=0.5–0.8
- ranksep=0.8–1.2
- center all major nodes
- keep exclusion boxes aligned
- optimize whitespace manually

Avoid:
- default Graphviz style
- crowded labels
- oversized exclusion boxes
- uneven alignment
- thick arrows
- bright colors
- software engineering diagram aesthetics

---

## 强制要求

1. 生成前: 数据来源必须是项目的实际产出文件（如 cohort_attrition.json），禁止编造数字
2. 生成后: 检查 N 的加总一致性（逐行验算 n_before − n_excluded = n_after）
3. 输出: PNG (≥300 dpi) + TIFF (≥300 dpi)
4. 文件命名: `Figure1_[descriptor].{png,tiff}`
5. 同步到 `figures/` 和 `submission/figures/` 两个目录

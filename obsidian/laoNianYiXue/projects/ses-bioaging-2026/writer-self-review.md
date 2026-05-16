# Scientific Writer 自审报告

**稿件**: Heterogeneous Effects of SES on Biological Aging in Chinese Older Adults
**审查日期**: 2026-05-08
**审查人**: Scientific Writer Agent

---

## 强制前置检查 (Pre-Flight Check)

| # | 检查项 | 状态 | 说明 |
|---|--------|------|------|
| 1 | SAP 已产出并获 PI 签批 | **不通过** | 未找到 sap.md 或 statistical-analysis-plan.md |
| 2 | 数据分析输出已验证且可复现 | **通过** | recompute_results.py 存在且完整 |
| 3 | 数值一致性预检通过 | **通过** | validate_manuscript.py: 10/10 PASSED |
| 4 | Clinical review 已产出 | **条件通过** | 刚完成 (clinical-review.md), 但在写作时不存在 |
| 5 | PI 终审签批 | **进行中** | 当前审查即为 PI 终审的一部分 |

**阻断警示**: 第 1 项 (SAP) 缺失即构成流程违规 — manuscript 已在无 SAP 签批的情况下撰写。按 scientific-writer 规范, 这是强制的阻断条件。

---

## Section-Specific Review

### Title (要求 ≤15 词)

**当前**: "Heterogeneous Effects of Socioeconomic Status on Biological Aging in Chinese Older Adults: A Population-Based Study Using the CHARLS Cohort" (18 词)

**问题**: 超过 15 词限制; 冒号结构加长标题

**建议**: "SES Heterogeneity in Biological Aging: A CHARLS Cohort Study of Chinese Older Adults" (13 词)

---

### Abstract (要求 ≤300 词)

- 当前: ~223 词 ✓
- 结构化: Aim / Methods / Results / Conclusions ✓
- 与正文数值一致性: 
  - N=7,810 ✓ (与正文一致)
  - ATE=−0.118 ✓
  - E-value=1.15 ✓
  - 中介=63% ✓
  - CATE Rural=+0.071 ✓
- **问题**: Abstract 中的 "lower biological age in the low-SES group" 虽数字正确, 但缺乏方向异常的背景说明, 摘要读者可能困惑。

---

### Introduction (三段漏斗式)

| 段落 | 评阅 |
|------|------|
| ¶1 (宏观背景) | ✓ 3 句, SES→mortality→biological embedding |
| ¶2 (研究缺口) | ✓ 列出 3 个缺口, 有引用支撑 |
| ¶3 (本研究目标) | △ 假说方向单向 (double jeopardy), 与最终发现矛盾 |

**AI 写作模式检测:**
- ✓ 无 "Additionally", "Furthermore" at sentence start
- ✓ 无 "pivotal", "crucial", "landscape", "delve"
- ✓ 无过度 "-ing" 分析
- ✓ 无 "serves as" / "stands as"
- △ 发现 1 处 em dash (""gets under the skin"") — 可接受, 这是引用原文的标点

---

### Methods (五段式, TRIPOD 对齐)

| 检查项 | 状态 |
|--------|------|
| Study Design and Setting | ✓ Cross-sectional, CHARLS 2013, 报告指南未声明 (STROBE?) |
| Study Population | ✓ 纳入/排除, N=7,810, 无流程图 |
| Outcome / Predictors | ✓ 4-marker bio-age, 5-component SES |
| Statistical Analysis | △ CATE/Mediation/E-value 三段清晰, 但缺少: 正态性检验, 缺失率, 模型假设检验 |
| Sensitivity Analysis | ✗ 中位数填补敏感性/替代分析未描述 |

**CHARLS 变量名标注**: ✓ (zba001, zbd001, qc003–qc006 等)

---

### Results (TEXT-TABLE-FIGURE 原则)

| 检查项 | 状态 |
|--------|------|
| Table 1 有对应文字 | ✓ |
| Table 2 有对应文字 | ✓ |
| 所有效应量带 CI | **✗ 无任何 CI 报告** |
| 无解释性语言 | ✓ Results 中不含解释 |
| 图引用 | ✗ figures/ 目录为空, 无图 |
| 统计学表述 | △ 使用了 CATE/ATE 但无 CI 或 p 值辅助判断精度 |

---

### Discussion (五段式)

| 段落 | 内容 | 评阅 |
|------|------|------|
| ¶1 | 主要发现总结 | ✓ 概括趋势, 未重复 Results 数值 |
| ¶2 | 与文献比较 | ✓ CHARLS 先验研究, survivorship bias, urban/rural |
| ¶3 | 临床含义 | ✓ CES-D mediation, Chinese somatization |
| ¶4 | 局限性 | ✓ 5 项列出, 但缺少中位数填补和 bootstrap 局限性 |
| ¶5 | 未来方向 + 结论 | ✓ 纵向/分子/跨队列三项建议 |

**AI 模式检测:**
- △ 1 处 "warrant discussion" / "warrant further investigation" — 可接受但偏弱, 建议改为具体方向
- ✓ 无过度推广

---

### References (35 篇)

| 检查项 | 状态 |
|--------|------|
| 每条期刊文献有 DOI | △ 待验证 |
| DOI 格式统一 | doi:10.xxx ✓ |
| **DOI 自动验证 (verify_all_dois)** | **✗ 未执行** |
| 无 DOI 的文献已标注 | 引用 #2 (WHO report) 和 #12, #33 (书籍章节) — 未标注 |
| 引用格式 | Vancouver style, 基本统一 ✓ |

---

## AI Writing Patterns — 全文扫描

| 模式 | 检测结果 |
|------|----------|
| "Additionally" / "Furthermore" | 0 处 ✓ |
| "pivotal" / "crucial" / "landscape" / "delve" | 0 处 ✓ |
| "serves as" / "stands as" | 0 处 ✓ |
| "-ing" 分析滥用 (highlighting, underscoring...) | 0 处 ✓ |
| Synonym cycling (Patients/Participants/Subjects) | 使用 "participants" 和 "older adults" — 适中 ✓ |
| Em dash overuse | Abstract: 0, Introduction: 1, Discussion: 1 (仅 2 处) ✓ |
| Filler phrases ("In order to", "It is important to note") | 0 处 ✓ |
| Excessive hedging | 适中 ✓ |
| Generic conclusions | 无 ✓ |

**总体评价**: 语言质量较高, AI 写作模式检测基本通过。

---

## 投稿就绪度

| 条件 | 状态 |
|------|------|
| Target journal: Geriatrics & Gerontology International | ✓ |
| 字数: ~4,200 (text only) | ✓ (GGI 通常上限 4,000-5,000) |
| Cover letter 已准备 | △ **旧版数据 (N=3,395, CATE discrepancies)** |
| Abstract 结构化 | ✓ |
| 关键词 ≥3 | ✓ (5 个) |
| Figures 已准备 | ✗ figures/ 为空 |
| Tables 已准备 | △ tables/ 为空, 但表格在正文中内嵌 |
| 参考文献 DOI 已验证 | ✗ |

---

## 闸门裁定

**Verdict: REVISION REQUIRED**

**阻断项**:
1. **SAP 缺失** — 流程违规。Manuscript 在无 SAP 签批的情况下撰写
2. **DOI 批量验证未执行** — 投稿前强制步骤
3. **Cover letter 使用旧版本数据** — 如错误发送将构成严重问题

**高优先级修正**:
4. Title 超 15 词限制
5. 无 Figures (figures/ 空目录)
6. Introduction 假说单向 (double jeopardy) 与 Discussion 叙事 (undermining double jeopardy) 不一致
7. 参考文献 #2, #12, #33 无 DOI 未标注

**中优先级修正**:
8. Methods 缺少 STROBE 报告指南声明、正态性检验、缺失率报告

# 学术论文去 AI 味规则库 (Humanizer Rules)

共享参考文件 — 供 scientific-writer agent prompt 和 gate_checks.py 的 `check_humanize_quality` 共同引用。

---

## 一、AI 禁用词黑名单 (D 类词汇)

以下词汇出现即视为 AI 味，必须替换：

### 高优先级 (每段扫描)

| # | 禁用词/模式 | 正则 | 替换建议 |
|---|-----------|------|---------|
| 1 | pivotal | `\bpivotal\b` | important / key / central |
| 2 | crucial | `\bcrucial\b` | essential / vital / important |
| 3 | landscape (作比喻) | `\blandscape\b` | field / area / domain |
| 4 | delve | `\bdelve\b` | examine / explore / investigate |
| 5 | underscores | `\bunderscores?\b` | highlights / emphasizes |
| 6 | evolving landscape | `evolving\s+landscape` | changing field / developing area |
| 7 | groundbreaking | `\bgroundbreaking\b` | innovative / novel |
| 8 | renowned | `\brenowned\b` | well-known / prominent |
| 9 | profound impact | `profound\s+impact` | substantial effect / major influence |
| 10 | remarkable | `\bremarkable\b` | notable / striking / noteworthy |
| 11 | dramatic | `\bdramatic(?:ally)?\b` | substantial / large / marked |
| 12 | showcasing / highlighting (作 -ing 分析) | `\b(?:showcasing|highlighting|underscoring)\s+the\s+` | 改为直接陈述 |
| 13 | Additionally (句首) | `^Additionally[,\s]` | 删除或改为 Also / In addition (限 1 次/段) |
| 14 | Furthermore (句首) | `^Furthermore[,\s]` | 删除，靠内容衔接 |
| 15 | Moreover (句首) | `^Moreover[,\s]` | 删除，靠内容衔接 |
| 16 | Notably (句首) | `^Notably[,\s]` | 删除 |
| 17 | serves as | `serves?\s+as\b` | is / acts as |
| 18 | stands as | `stands?\s+as\b` | is |
| 19 | in order to | `in\s+order\s+to\b` | to |
| 20 | for the purpose of | `for\s+the\s+purpose\s+of\b` | for / to |
| 21 | a total of | `a\s+total\s+of\b` | (删除) |
| 22 | utilize | `\butiliz[ae]s?\b` | use |
| 23 | demonstrate (非实验场景) | `\bdemonstrat[es]\b` | show |
| 24 | facilitate | `\bfacilitates?\b` | help / enable |

### 中优先级 (全文检查)

| # | 禁用模式 | 正则 | 说明 |
|---|---------|------|------|
| 25 | Not only... but also | `[Nn]ot\s+only.+but\s+also` | 学术写作避免此结构 |
| 26 | Studies have shown (无具体引用) | `[Ss]tudies\s+have\s+shown\b` | 必须指名具体研究 |
| 27 | Experts argue (无具体人名) | `[Ee]xperts\s+argue\b` | 必须指名具体专家 |
| 28 | It is important to note | `[Ii]t\s+is\s+important\s+to\s+note\b` | 删除，直接陈述 |

### 终结标语 (Conclusion/Discussion 重点扫描)

| # | 禁用标语 | 正则 |
|---|---------|------|
| 29 | paving the way | `paving\s+the\s+way` |
| 30 | ushering in | `ushering\s+in` |
| 31 | highlighting the potential | `highlighting\s+the\s+potential` |
| 32 | opening the door | `opening\s+the\s+door` |
| 33 | Future research should (无具体方案) | `[Ff]uture\s+(?:research|studies)\s+should\b` |
| 34 | The future looks bright | `[Ff]uture\s+looks\s+bright` |
| 35 | game-changer / revolutionize | `\b(?:game.changer|revolutionize)\b` |

---

## 二、定量检测规则

### 2.1 过渡词密度

扫描每段开头句。计数以下过渡词：

```
Furthermore, Moreover, Additionally, Notably, In addition,
Specifically, In particular, Interestingly, Importantly,
Taken together, Overall, In summary, In conclusion,
```

- **阈值**: ≤ 1 个/段, ≤ 3 个/全文
- 超过阈值 → FAIL

### 2.2 Hedge 密度

计数以下模糊词 (仅 Discussion ¶3 和 Conclusion):

```
may, might, could, potentially, possibly, suggests, 
may suggest, have the potential to, appears to
```

- Discussion ¶3: ≤ 3 个 hedge 词
- Conclusion: ≤ 1 个 hedge 词
- 其他段落不做硬限制但建议 ≤ 2 个/段
- 超过阈值 → FAIL

### 2.3 句长均匀度

逐段计算句长（词数）标准差：

- 标准差 < 5 且段落 ≥ 4 句 → WARN (句长过于均匀, 疑似 AI)
- 不影响 Gate 判定但注入建议

### 2.4 同义词轮换检测

搜索核心术语是否在全文中被替换为不同说法。检测以下典型轮换对：

```
patients → participants → subjects → individuals → older adults
frailty → frailty syndrome → frailty status → frail state  
showed → demonstrated → revealed → indicated
```

- 同一概念出现 ≥ 3 个不同说法 → WARN

---

## 三、分章节打击优先级

不同章节天然吸引不同的 AI 写作毛病。auto check 按以下优先级分配检测维度：

| 章节 | 重点检测 | 次要 |
|------|---------|------|
| **Introduction ¶1-2** | 过渡词密度、禁用词、段落同构 | 终结标语 |
| **Introduction ¶3** | 禁用词、终结标语（¶3 不能写结论） | — |
| **Methods** | 禁用词 (utilize→use)、术语一致性 | 过渡词密度 |
| **Results** | 句长均匀度、过渡词密度、禁用词 | — |
| **Discussion ¶1** | 句长均匀度、过渡词密度 | 终结标语 |
| **Discussion ¶2** | 术语一致性、过渡词密度 | hedge 密度 |
| **Discussion ¶3** | **hedge 密度 (最重灾区)**、终结标语、禁用词 | 句长均匀度 |
| **Discussion ¶4** | 禁用词、终结标语 | 术语一致性 |
| **Conclusion** | hedge 密度、终结标语、禁用词 | — |
| **Abstract** | **全部维度** (最显眼的部分) | — |

---

## 四、七维改写对照 (摘要)

完整改写方法见 `scientific-writer-agent.md` §去 AI 味改写。此处提供 auto check 可检测的量化规则：

| 维度 | 量化检测 |
|------|---------|
| 1. 句长变异 | 标准差 < 5 → WARN |
| 2. 过渡词密度 | > 1 个/段 → FAIL |
| 3. 词汇经济化 | 禁用词命中即 FAIL |
| 4. 确定性校准 | hedge 密度超阈值 → FAIL |
| 5. 术语保持 | ≥ 3 种说法 → WARN |
| 6. 段落形状 | 相邻 3 段同开头句式 → WARN |
| 7. 终结标语 | 标语命中即 FAIL |

---

## 五、Humanize 检查清单

每条规则对应 `check_humanize_quality` 中的检测项：

- [ ] 无禁用词命中 (≤ 0 个高优先级词)
- [ ] 过渡词密度达标 (≤ 1/段, ≤ 3/全文)
- [ ] Hedge 密度达标 (¶3 ≤ 3, Conclusion ≤ 1)
- [ ] 无终结标语
- [ ] 术语一致 (无同义词轮换)
- [ ] 缩写首次使用给出全称
- [ ] 句长有变异 (非强制, WARN only)

---

## 六、缩写规范

所有缩写首次出现必须给出全称，格式为「全称 (Abbreviation)」。
常见通用缩写豁免: DNA, RNA, BMI, CI, AUC, OR, HR, SD, ROC, SHAP, DCA, IQR, SD, SE, CI, p-value。

检测规则: 扫描正文中所有大写缩写 (≥ 2 个大写字母)，排除豁免列表，检查前文是否出现过 `全称 (缩写)` 格式的定义。未定义的缩写 → FAIL。

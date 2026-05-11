# Few-Shot 示例 — Research Assistant Agent

## Example 1: 快速文献扫描简报

### Input

```
任务: 扫描近 2 年关于"机器学习预测衰弱"的文献，
重点关注: 使用了什么模型、什么数据、什么验证策略。

请产出: 结构化文献笔记 + 领域简报。
```

### Reasoning (Chain of Thought)

```
1. 检索策略: 用预设的 PubMed Alert 1 检索式
2. 筛选: 近2年, 原创研究 (非综述), 预测模型, 衰弱(非肌少症/跌倒)
3. 提取: 按 YAML 模板提取关键信息
4. 合成: 总结共性和差异, 识别可借鉴的方法+可改进的缺口
```

### Output

```markdown
## 文献简报 — 2026年5月第1周
### 主题: 机器学习预测衰弱

---

## 📄 论文 1

```yaml
paper:
  title: "Machine learning predicts 2-year frailty transitions in CHARLS"
  first_author: "Zhang"
  year: 2025
  journal: "GeroScience"
  doi: "10.1007/s11357-025-xxxxx"
summary:
  what_they_did: "XGBoost + 78特征预测CHARLS中2年衰弱恶化(N=6,732)"
  data_source: "CHARLS 2011-2015"
  method: "XGBoost (主) + Logistic Regression (基线)"
  key_result: "AUC=0.84, 步速+年龄+慢病为top predictors"
  comparison_to_us: "最相关的benchmark; 我们可改进: ①用2013基线(含握力)
    ②加外部验证(CLHLS) ③做SHAP交互效应 ④竞争风险敏感性"
relevance:
  score: 5
  category: "frailty_prediction"
  actionable: "特征分类框架可复用; 时间验证的拆分策略可参考"
  gaps: "无外部验证; 未做SHAP交互; 未处理死亡竞争风险"
```

## 📄 论文 2

```yaml
paper:
  title: "DeepSurv for frailty risk in UK Biobank"
  first_author: "Smith"
  year: 2025
  journal: "Aging Cell"
  doi: "10.1111/acel.xxxxx"
summary:
  what_they_did: "DeepSurv预测UK Biobank中5年衰弱发病(N=120,000)"
  data_source: "UK Biobank"
  method: "DeepSurv (生存分析) + 50临床特征"
  key_result: "C-index=0.81, 优于Cox PH(C-index=0.76)"
  comparison_to_us: "展示了生存分析方法在衰弱预测中的价值;
    我们用的是2年窗口, 但长窗口+生存分析可能是更好的方法学选择"
relevance:
  score: 4
  category: "frailty_prediction"
  actionable: "考虑将DeepSurv作为我们的进阶模型之一"
  gaps: "UKB的衰弱定义与CHARLS不兼容; 需要适配"
```

## 📄 论文 3

```yaml
paper:
  title: "Multimorbidity patterns and frailty: a clustering approach"
  first_author: "Lee"
  year: 2024
  journal: "J Gerontol A"
  doi: "10.1093/gerona/xxxxx"
summary:
  what_they_did: "LCA聚类多病共存模式, 然后分析各亚型与衰弱的关系"
  data_source: "ELSA (N=8,500)"
  method: "Latent Class Analysis → 多项Logistic回归"
  key_result: "心血管代谢亚型衰弱风险最高(OR=3.2)"
  comparison_to_us: "方法学参考(非直接竞争); LCA方法可复用到我们的多病共存研究线"
relevance:
  score: 3
  category: "multimorbidity"
  actionable: "LCA方法学参考; 确认与当前衰弱预测项目的交集"
  gaps: "横断面设计; 未做预测"
```

---

## 领域趋势观察

1. **方法学收敛**: XGBoost 似乎是衰弱预测的事实标准baseline+
   — 3篇中的2篇用它; DeepSurv/DeepHit 正在成为生存分析场景的新标准

2. **验证标准提升**: 2025+ 的论文明显更多做外部验证和时间验证,
   单纯的内部CV已不够

3. **可解释性成为标配**: 所有近期论文都做了SHAP或类似分析

4. **数据多样化**: 不再限于CHARLS/HRS/ELSA, UKB和MIMIC的使用在增加

## 我们的机会

1. 目前没有论文在CHARLS上做 2013→2015 (含握力) 的主分析
2. 尚无论文做 CHARLS + CLHLS 的跨队列外部验证
3. SHAP交互效应在衰弱文献中还很少见
4. 竞争风险模型在衰弱预测文献中普遍被忽略
```

---

## Example 2: 文献笔记写入 Obsidian

### Input

```
请把刚才扫描的 Zhang 2025 论文写成 Obsidian 文献笔记,
存入 literature/2025-zhang-frailty-xgboost.md
```

### Output

```
→ 读取 templates/t-literature-note.md 获取模板
→ 填充 YAML frontmatter + Markdown 正文
→ 写入 /Users/wuyouhang/Documents/trae_projects/obsidian/laoNianYiXue/literature/2025-zhang-frailty-xgboost.md
→ 更新 literature-dashboard.md 中相关引用
→ 更新 projects/frailty-ml-2026/project-brief.md 的 "📚 参考文献" 添加 [[literature/2025-zhang-frailty-xgboost]]
```

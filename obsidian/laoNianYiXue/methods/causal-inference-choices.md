---
type: method
topic: causal_inference
status: reference
last_updated: 2026-05-04
---

# 因果推断方法选择指南

老年医学观察性研究中，如何从关联走向因果。

## 方法选择决策树

```
需要回答什么问题？

├── "这个暴露对结局的平均因果效应？"
│   ├── RCT 数据
│   │   → ITT (主分析) + PP (敏感性)
│   │
│   ├── 有可测混杂
│   │   → Propensity Score Matching (1:1, caliper=0.2)
│   │   → IPTW (stabilized weights, 检查权重分布)
│   │   → 推荐同时做 PS Matching + IPTW + 传统回归作为敏感性
│   │
│   ├── 有未测混杂
│   │   → Instrumental Variable (需要强工具变量)
│   │   → DiD (需要面板数据 + 平行趋势)
│   │   → 断点回归 (需要连续分配变量 + 阈值)
│   │
│   └── 时变处理/暴露
│       → Marginal Structural Model + IPTW
│
├── "效应是如何传递的？（中介）"
│   ├── 单中介
│   │   → Baron-Kenny + Bootstrap CI
│   │   → NDE/NIE (mediation R包)
│   ├── 多中介
│   │   → VanderWeele 多中介框架
│   └── 高维中介（组学）
│       → HIMA (High-dimensional Mediation Analysis)
│
├── "效应在谁身上最强？（异质性）"
│   ├── 预设亚组
│   │   → 交互项检验 (不是亚组内 p 值!!)
│   ├── 数据驱动
│   │   → Causal Forest / BART
│   └── 个体化效应
│       → Causal Forest (grf R包)
│
└── "未测混杂会推翻结论吗？"
    → E-value (VanderWeele & Ding, 2017)
    解读: E-value = 2.5 意味着未测混杂需要至少 RR=2.5
    才能将观察到的关联完全解释为混杂
```

## 倾向性评分检查清单

做 PS Matching/IPTW 后必须报告:
- [ ] 匹配前后协变量均衡性 (SMD < 0.1)
- [ ] 倾向性评分分布重叠 (Love plot)
- [ ] 匹配后样本量保留率
- [ ] 权重分布 (IPTW: 检查极端权重)

## 关键 R 包

| 方法 | R 包 |
|------|------|
| 倾向性评分匹配 | MatchIt |
| 逆概率加权 | WeightIt |
| 工具变量 | ivreg, AER |
| 双重差分 | fixest, did |
| 因果森林 | grf |
| E-value | EValue |
| 因果中介 | mediation |

## 相关资源
- [[methods/model-selection-guide|ML 模型选型]]
- [[datasets/charls|CHARLS]]

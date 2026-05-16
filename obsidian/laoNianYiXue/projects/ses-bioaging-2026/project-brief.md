---
type: project
project_id: "ses_bioaging_2026"
title: "社会经济不平等与生物衰老的交互效应 — 基于 CHARLS 的因果推断研究"
status: execution
priority: high
start_date: 2026-05-05
target_journal: "Geriatrics & Gerontology International"
target_tier: 3
tags:
  - project/active
  - ses
  - biological_aging
  - causal_inference
  - charls
---

# 社会经济不平等与生物衰老

## 核心科学问题
社会经济地位如何调节生物衰老过程？能否识别出社会经济劣势加速生物学衰退的高风险亚群？

## 研究设计
- **暴露变量**: SES 复合指标 (教育、城乡、人均收入、人均支出、家庭资产)
- **中介变量**: 心理压力 (CES-D)
- **结局变量**: 生物年龄复合评分 (握力↓ + 步速↓ + BMI + SBP, 4 指标; CES-D 从结局中排除以避免循环论证)
- **方法**: 分层 CATE (bootstrap CI) + 乘积系数中介 (bootstrap CI) + E-value (未测混杂评估)

## 初步结果 (N=7,810)
| 分析 | 核心发现 |
|------|---------|
| SES × Grip 交互 | Grip-driven 0.73 SD gradient; Low SES+High Grip 最佳 (−0.25), 否证 double jeopardy |
| 城乡异质性 | 农村 CATE = +0.070 (95% CI: +0.034, +0.102); 城市 CATE = −0.044 (95% CI 跨零) |
| 中介路径 | CES-D 间接效应 +0.012 (95% CI: +0.008, +0.016); 总效应小且不精确; 中介比例 63% (CI 宽) |
| E-value | 1.47 (bootstrap 95% CI lower bound: 1.41); 调整模型 E-value = 1.15 (CI lower: 1.00) |

## 数据
- 来源: CHARLS 2013 (基线)
- SES: 5 维复合 (edu + urban + income + expenditure + assets)
- 详见: [[datasets/charls-ses-variables]]

## 下一步
- [ ] 提取更多 SES 变量 (社会参与、医疗保险)
- [ ] 运行完整 Causal Forest (grf R包 或 econml)
- [ ] 补充 HIMA 高维中介分析
- [ ] 撰写论文

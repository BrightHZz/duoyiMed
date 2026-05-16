---
type: project
project_id: "frailty_ml_2026"
title: "基于 CHARLS 的机器学习衰弱转换预测模型"
status: proposed
priority: high
start_date: 2026-05-01
target_date: 2026-08-01
target_journal: "GeroScience"
target_tier: 2
tags:
  - project/active
  - frailty
  - classification
  - charls
---

# 基于 CHARLS 的机器学习衰弱转换预测模型

## 📋 状态追踪
- **当前阶段**: proposed（方案设计阶段）
- **阻塞项**: 无
- **下一步行动**: 
  - clinical-researcher: 确定衰弱操作化定义 + 纳入排除标准
  - data-engineer: 评估 CHARLS 变量可用性
  - research-assistant: 近期文献扫描

## 🎯 研究问题
能否利用 CHARLS 基线的多维特征（人口学、临床、功能、认知、社会），通过机器学习方法预测社区老年人在 2 年内衰弱状态的恶化？

## 💡 核心假说
1. 机器学习模型（XGBoost）在区分度上将优于传统逻辑回归
2. 功能指标（步速、握力）和营养指标（白蛋白）将是 top predictors
3. 可解释性分析将揭示非线性的特征交互效应

## 👥 团队分工
| 角色 | 负责人 | 状态 | 备注 |
|------|--------|------|------|
| PI | 待定 | ⏳ | 需审批研究方案 |
| 计算生物学 | 待定 | ⏳ | 建模方案设计 |
| 临床 | 待定 | ⏳ | 衰弱表型定义 |
| ML 工程 | 待定 | ⏳ | 模型实现 |
| 统计 | 待定 | ⏳ | SAP 撰写 |
| 数据工程 | 待定 | ⏳ | 数据提取+清洗 |
| 写作 | 待定 | ⏳ | |

## 📐 方法概览
- **数据**: CHARLS Waves 1-4 (2011-2018)
- **设计**: 前瞻性队列
- **结局**: 2 年 Fried Phenotype 衰弱恶化 ≥1 级
- **主模型**: XGBoost（基线: Logistic Regression）
- **验证**: 10-fold nested CV + 时间验证

## 📅 关键里程碑
- [ ] 2026-05-07: 研究方案确定
- [ ] 2026-05-15: 数据就绪
- [ ] 2026-05-25: 基线模型完成
- [ ] 2026-06-10: 主模型训练完成
- [ ] 2026-06-20: 可解释性分析完成
- [ ] 2026-07-10: 初稿完成
- [ ] 2026-07-20: PI 终审
- [ ] 2026-08-01: 投稿

## 📚 参考文献
- [[../literature/2026-example-paper|示例文献: 衰弱预测]]
- [[../concepts/frailty|衰弱概念]]
- [[../datasets/charls|CHARLS 数据源]]
- [[../methods/model-selection-guide|ML 模型选型]]

## 📝 会议记录
- 

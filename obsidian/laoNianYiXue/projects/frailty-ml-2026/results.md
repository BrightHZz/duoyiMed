---
type: results
project: "CHARLS 衰弱恶化预测"
date: 2026-05-05
status: final
---

# CHARLS 2013→2015 衰弱恶化预测 — 最终结果

## 样本

| 指标 | 值 |
|------|-----|
| 分析样本 | N=11,570 |
| 年龄 | mean 60.5 岁 (60+) |
| 女性 | 51% |
| 基线 Fried | mean 0.61 |
| 2年恶化率 | 32.2% (3,720/11,570) |

## 模型性能

| 模型 | AUC | 备注 |
|------|-----|------|
| XGBoost (age+sex) | 0.573 | 基线锚点 |
| LASSO Logistic Regression | **0.864** | 最优 |
| XGBoost (Optuna tuned) | **0.862** | 与LASSO无显著差异 |
| XGBoost (不含Fried基线) | 0.783 | 纯预测能力 |

## Top 10 预测因子

1. baseline_grip_low (基线握力不足) — 0.406
2. baseline_exhaustion (基线疲乏) — 0.138
3. sex (性别) — 0.082
4. grip_max (握力最大值 kg) — 0.057
5. f_base (基线Fried总分) — 0.048
6. baseline_gait_low (基线步速不足) — 0.027
7. cesd_3 (CES-D单项) — 0.024
8. baseline_weight_loss (基线体重下降) — 0.023
9. baseline_inactive (基线活动不足) — 0.018
10. cesd_2 (CES-D单项) — 0.016

## 关键发现

1. **线性模型已足够**: LASSO (AUC=0.864) ≈ XGBoost (0.862)，非线性交互未带来额外收益
2. **基线握力不足 vs 握力值**: Pearson r=-0.38 (中度相关, 不存在共线性)，两者捕捉不同信息
3. **握力是最强预测因子**: grip_low=1时握力mean=21.2kg vs grip_low=0时mean=36.3kg
4. **vs Zhang 2025**: 含基线Fried AUC已超越文献基准(0.84); 纯预测AUC(0.783)有提升空间

## 投稿状态

- PI 审查: ✅ 批准投稿 GeroScience
- 修改项: 2项小修已完成

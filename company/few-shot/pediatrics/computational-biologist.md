# Pediatrics Computational Biologist — Few-Shot Example

## Example 1: PICU 死亡率预测 — 方法选型

**任务**: 为 PICU 死亡率预测项目推荐 ML 方法

### 分析方案

**数据特征**:
- 样本量: ~5,500 PICU 住院 (PIC 数据库)
- 阳性事件: ~300 例死亡 (发生率 ~5.5%)
- 特征维度: ~40 个候选特征 (人口学 + 生命体征 + 实验室 + PRISM III 组成项)
- 数据类别不平衡: 1:17 (中度)

**任务类型**: 二分类 (PICU 死亡 vs 存活)

**方法选型**:

| 方法 | 推荐度 | 理由 |
|------|--------|------|
| XGBoost + SHAP | ⭐⭐⭐ 首选 | 表格数据 + 中等样本 + 高可解释性需求 |
| Logistic Regression + LASSO | ⭐⭐⭐ 基线 | 临床接受度高, 校准度好, 可为最终模型 |
| Random Forest | ⭐⭐ 对比 | 经典 baseline, 但通常不如 XGBoost |
| MLP (2-3 hidden layers) | ⭐⭐ 探索 | 足够样本, 但提升通常 <5% vs XGBoost |
| LSTM (24h 时序) | ⭐⭐ 探索 | 如有时序生命体征数据可尝试, 样本量够 |

**不推荐**: TabNet (小样本不稳定), Transformer (计算量过大, 性价比低), CNN (无影像数据)

**类别不平衡处理**:
- 不使用 SMOTE (阳性率 5.5% 尚可, class_weight 足够)
- scale_pos_weight = 17 (XGBoost)
- 评估重点: PR-AUC > AUC (不平衡场景)

**特征工程**:
```
原始特征:
  人口学: 年龄(月), 性别, 体重(kg)
  入PICU: 来源(急诊/病房/手术室/外院), PRISM III 评分, 机械通气(是/否)
  生命体征: 入室首24h HR/RR/SBP/SpO₂的 min/max/mean/SD/delta
  实验室: 入室首24h pH/pCO₂/Lac/WBC/PLT/Cr/BUN 的最差值
  基础疾病: 先天心脏病/遗传综合征/免疫缺陷/恶性肿瘤 (one-hot)

衍生特征:
  pSOFA 趋势: 入室24h pSOFA - 入院pSOFA (恶化指数)
  休克指数: HR/SBP (年龄校正)
  Ventilation index: (PIP × FiO₂ × RR) / PaO₂
  PRISM III x 年龄交互项: PRISM III / 年龄(月)
```

**模型评估计划**:
- 内部验证: 5-fold CV, stratified by age group (<1y / 1-5y / 6-12y / 13-18y)
- 主要指标: AUC (带 95% CI) + PR-AUC + Brier Score
- 次要指标: Calibration slope + DCA (阈值范围 1-20%)
- 年龄分层: 各年龄组分别报告 AUC + 森林图
- 对比基线: PRISM III 评分 (不重新训练, 直接计算 AUC)

## Example 2: 小样本策略 — BPD 预测

**任务**: 预测早产儿 BPD (N=350, BPD 发生率 ~35%)

**挑战**: 样本量小 (N=350), 特征维度中等 (~20), 不适用 DL

**推荐方案**:
1. **Elastic Net 正则化逻辑回归** — 小样本首选, 自动特征选择 + 防止过拟合
2. **XGBoost (max_depth=3, min_child_weight=5, n_estimators=50)** — 高正则化版本
3. **内部验证**: 由于 N=350, 使用 repeated 10-fold CV (×10 repeats) 而非 5-fold
4. **不做 DL**: N 太小, MLP 会严重过拟合
5. **谨慎外推**: 单中心数据, BPD 定义在不同 NICU 间有差异, Discussion 需明确限制

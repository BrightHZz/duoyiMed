# 统计审查报告

**Agent**: shared/biostatistician
**Phase**: Phase 5 Round 1 — 审查(研讨厅)
**日期**: 2026-05-10
**确信度标注**: [高/中/低]

---

## 1. 模型性能统计评估

### 主要指标

| 指标 | 值 | TRIPOD 标准 | 判定 |
|------|-----|------------|------|
| AUC | 0.8289 ± 0.0329 | ≥ 0.70 | ✅ 良好 |
| PR-AUC | 0.5002 | 无硬性阈值 | ⚠️ 中等 (基线=0.131) |
| Brier | 0.0793 | < 0.25 (max for binary) | ✅ 良好 |
| Calibration Slope | 1.0000 (calibrated) | [0.85, 1.15] | ✅ 优秀 |
| LR Baseline AUC | 0.7544 | — | ✅ ΔAUC = +0.0745 |
| CV Fold Stability | AUC SD = 0.0329 | SD < 0.10 | ✅ 稳定 |

### 关键统计问题

#### 问题 1: 校准过度校正 [确信度: 高]

**观察**: Isotonic calibration 将 slope 从 0.6638 校正到恰好 1.0000。这看起来"太完美"了。

**分析**:
- Isotonic calibration 是非参数方法，在验证集上拟合，天然会让 slope → 1.0
- 这意味着 calibrator 过度适应了 MIMIC-IV 内部数据的分布
- 如果在真正的外部数据上使用，校准可能再次偏离
- 更稳健的做法: 使用 **Platt scaling** (sigmoid) 而非 isotonic — 参数更少，泛化性更好

**建议**: 
- 最终报告同时给出 uncalibrated slope (0.6638) 和 calibrated slope (1.0000)
- Discussion 中解释选择 isotonic 的理由
- 推荐: 重新训练用 Platt scaling → 预期 slope ~0.85-0.95 (仍在可接受范围)

#### 问题 2: PR-AUC 偏低 [确信度: 中]

**观察**: PR-AUC = 0.5002，基线 (事件率) = 0.131。提升倍数 = 3.8x。

**分析**:
- 在类别不平衡 (13.1%) 的情况下，AUC 可能高估模型实际效果
- PR-AUC 0.50 意味着在 20% recall 水平，precision 约 40-50% → 假阳性率较高
- 对于临床部署，这意味着"高风险"标签中有超过一半是误报

**建议**:
- 论文中 Table 2 必须包含 PR-AUC
- 报告 specific threshold 下的 PPV/NPV
- Discussion 中讨论临床部署的 false positive burden

#### 问题 3: Fold 间 AUC 变异 (0.75-0.87) [确信度: 中]

**观察**: Fold AUC 范围: 0.7859 – 0.8718 (range = 0.086)

**分析**:
- Fold 2 AUC=0.7859 明显低于其他 folds
- 可能原因: Fold 2 验证集中有特殊的患者子群 (更多骨转移? 更少事件?)
- CV SD=0.0329 仍在可接受范围 (< 0.10)

**建议**: 检查 Fold 2 验证集的患者特征是否与其他 folds 有系统性差异。如果确认无异样 → 报告均值±SD 即可。

#### 问题 4: 样本筛选偏倚 [确信度: 高]

**观察**: 2,437 人中仅 1,233 (50.6%) 有 PSA → 被用于模型训练。

**统计含义**:
- PSA 缺失可能不是随机的 (not missing at random)
- 有 PSA 测量的患者可能是"更积极检测"的群体 → 选择偏倚
- 模型应用于无 PSA 的患者时性能未知

**建议**:
- Table 1 必须对比 PSA 可用 vs 不可用患者的人口学和结局特征
- 如果有显著差异 → Discussion 中讨论选择偏倚
- Sensitivity: 训练一个不含 PSA 的模型在所有 2,437 患者上 → 对比性能

#### 问题 5: EPV 处于边界 [确信度: 中]

**观察**: 14 features × 需要 EPV ≥ 10 = 需要 ≥ 140 events。实际: 161 events → EPV = 11.5。

**分析**:
- EPV = 11.5 满足最低标准 (≥ 10)，但处于边界
- 加上 LASSO pre-filtering 后，有效自由度更低 → EPV 实际上更安全
- 但 lactate 和 albumin 的高缺失率进一步减少了有效样本

**建议**: 在 SAP 附录中报告 EPV 计算。标注"满足 Harrell 指南的最低建议"。

---

## 2. SHAP 稳定性评估

由于缺少 bootstrap SHAP CI，以下为定性评估:

| 特征 | SHAP 排名 | 稳定性预期 | 评论 |
|------|----------|-----------|------|
| lactate | #1 | ⚠️ 低 — 缺失率 81%，SHAP 高度依赖插补值 | Bootstrap CI 可能很宽 |
| albumin | #2 | ⚠️ 低 — 缺失率 72% | 同上 |
| hb | #3 | ✅ 高 — 缺失率 6% | 最稳定的重要特征 |
| is_emergency | #4 | ✅ 高 — 无缺失 | 稳定 |
| prostatectomy | #5 | ✅ 高 — 无缺失 | 稳定 |

**建议**:
- Top-2 特征 (lactate/albumin) 的稳定性不可靠 → Discussion 标注
- 建议运行 bootstrap SHAP (1000 resamples) 报告 95% CI

---

## 3. 外部验证统计评估

### MIMIC-III 外部验证: ⚠️ 统计不可用

| 指标 | MIMIC-III | 评估 |
|------|-----------|------|
| 总队列 | 283 → 281 | 低于 300 阈值 |
| PSA 可用 | 32 | 极低 |
| 结局分布 | 100% 单一类别 | 无法计算任何 discrimination metric |

**统计意见**: MIMIC-III 对该模型的评价能力为零。这不是模型的失败，而是外部队列不适用的问题。必须寻找其他外部队列 (eICU, HIRID, 或其他 MIMIC 衍生数据库)。

---

## 4. 报告完备性检查 (TRIPOD checklist)

| TRIPOD 条目 | 完成 | 评论 |
|------------|------|------|
| 研究设计与样本量论证 | ✅ | EPV = 11.5 |
| 缺失数据处理方法 | ✅ | MICE/median within CV |
| 模型构建方法 | ✅ | XGBoost + LR |
| 内部验证方法 | ✅ | 5-fold stratified CV |
| Discrimination (AUC) | ✅ | AUC + PR-AUC |
| Calibration | ✅ | Slope + Brier + Plot |
| 模型呈现 (full equation) | ⚠️ | XGBoost 无显式方程; 需提供模型文件 |
| 亚组分析 | ✅ | Age, metastasis, admission type |
| 局限性 | ⚠️ 需补充 | 见上 |
| 外部验证 | ❌ | 不可行 |

---

## 5. 综合结论

**Overall**: ⚠️ COND_PASS

**必须修正**:
1. 报告 uncalibrated calibration slope (0.6638) 并解释校正策略
2. Table 1 加入 PSA 可用 vs 不可用的对比
3. 标注 lactate/albumin 的 SHAP 排名因高缺失率可能不稳定
4. 外部验证缺失标注为重大 limitation

**建议修正** (不阻塞):
1. Platt scaling 替代 isotonic calibration (更稳健)
2. Bootstrap SHAP 95% CI
3. PSA-free model sensitivity analysis

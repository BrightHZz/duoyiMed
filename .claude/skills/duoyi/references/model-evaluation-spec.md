# 模型评估规范

## 模型评估必备指标集 (Phase 3 输出标准)

所有分类模型 (主模型 + baseline + 对比模型) 必须通过 `evaluate_model()` 输出统一指标集, 任一模型缺指标 → Gate 3 FAIL:

| 维度 | 指标 | cv_results.json key | 说明 |
|------|------|-------------------|------|
| 区分度 | AUC (ROC) + 95% CI | `auc.mean`, `auc.ci_low`, `auc.ci_high` | |
| | PR-AUC | `pr_auc` | 数据不平衡时必需 |
| 校准度 | Brier Score | `brier` | |
| | Calibration Slope | `calibration_slope` | 理想值 1.0 |
| | Calibration Intercept | `calibration_intercept` | 理想值 0.0 |
| 阈值性能 | Sensitivity | `sensitivity` | 最优阈值处 |
| | Specificity | `specificity` | |
| | PPV | `ppv` | |
| | NPV | `npv` | |
| | F1 Score | `f1` | |
| 稳定性 | CV AUC std | `auc_cv_std` | fold 间标准差 |

### cv_results.json 结构

```json
{
  "models": {
    "xgboost": {
      "auc": {"mean": 0.842, "ci_low": 0.791, "ci_high": 0.893},
      "pr_auc": 0.785,
      "brier": 0.123,
      "calibration_slope": 1.02,
      "calibration_intercept": -0.03,
      "sensitivity": 0.82, "specificity": 0.78,
      "ppv": 0.76, "npv": 0.84, "f1": 0.79,
      "auc_cv_std": 0.021
    },
    "logistic_regression": { /* 同上, 所有模型统一 */ }
  },
  "best_model": "xgboost"
}
```

### Phase 3 基线清单格式

```yaml
# outputs/baselines/phase3_baseline.yaml
baseline_version: v1.2
project: prostate-cancer-prognosis
frozen_at: 2026-05-11T11:01:35
frozen_artifacts:
  - path: models/cv_results.json
    description: 5-fold CV results (AUC, feature importance, calibration)
    keys: [cv_results.mean_auc, cv_results.feature_importance, cv_results.folds]
  - path: models/features.pkl
    description: Final feature list (LASSO-selected)
  - path: models/xgb_final.pkl
    description: Final XGBoost model
  - path: models/imputer.pkl
    description: Median imputer fitted on training data
safety_config:
  n_jobs: 2
  cross_val_predict_n_jobs: 1
  model_n_jobs_override: true
  thread_limits:
    OMP_NUM_THREADS: "2"
    OPENBLAS_NUM_THREADS: "2"
    MKL_NUM_THREADS: "2"
    VECLIB_MAXIMUM_THREADS: "2"
    NUMEXPR_NUM_THREADS: "2"
  start_method: forkserver
  platform: darwin
downstream_consumers:
  - generate_figures.py  # MUST read from cv_results.json, NOT from model object
  - sections/05_results.md
  - tables/table2_model_performance.md
  - tables/table3_subgroup.md
```

---

## 数值精度规范

| 指标类型 | 小数位数 | 示例 | 说明 |
|---------|:---:|------|------|
| AUC / C-statistic / C-index | 3 | 0.842 | 区分度指标 |
| p 值 | 3 | 0.032 | p < 0.001 除外 (写为 "p < 0.001") |
| OR (Odds Ratio) | 2 | 1.34 | |
| HR (Hazard Ratio) | 2 | 0.78 | |
| RR (Risk Ratio) | 2 | 1.25 | |
| 百分比 | 1 | 84.2% | |
| 效应量 (Cohen's d, Hedges' g) | 2 | 0.45 | |
| 样本量 / 计数 | 0 | 2345 | 整数 |
| 95% CI | 与点估计一致 | 0.791-0.893 | 上下界与点估计同精度 |
| SD / SE | 比均值多 1 位 | Mean=25.3, SD=4.21 | |

**强制**: `generate_figures.py` 和 `generate_tables.py` 输出 caption/table 中的所有数值必须按上述标准舍入, 禁止输出 raw float (如 `0.8423` → 应为 `0.842`)。`check_numerical_precision_consistency` 跨 manuscript/tables/figures 交叉检查同指标精度一致性, 不一致 → Gate 6 FAIL。

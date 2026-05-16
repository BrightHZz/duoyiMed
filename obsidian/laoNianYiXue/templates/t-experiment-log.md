---
type: template
template_for: experiment-log
---

# 实验: {{experiment_name}}

---
type: experiment
experiment_id: "{{experiment_id}}"
project: "[[../project-brief|{{project_name}}]]"
date: {{date}}
mlflow_run_id: "{{mlflow_run_id}}"
model: "{{model}}"
status: running
tags:
  - experiment
---

## 🎯 实验目标
{{goal}}

## ⚙️ 配置
```yaml
model: {{model}}
parameters:
  {{parameters}}
features:
  count: {{feature_count}}
  selection: {{feature_selection}}
```

## 📊 结果
| 指标 | 训练 (CV) | 测试 |
|------|-----------|------|
| AUC-ROC | | |
| AUC-PR | | |
| Brier Score | | |
| Sensitivity | | |
| Specificity | | |

## 🔍 特征重要性 (Top 10)
| 特征 | SHAP |
|------|------|
| | |
| | |
| | |

## 📈 图表
- ROC 曲线: 
- 校准图: 
- SHAP 概要图: 

## 💭 结论与下一步
{{conclusion}}

**下一步**: {{next_steps}}

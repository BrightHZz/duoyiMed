---
type: project
status: modeling_complete
topics: [kidney_stone, surgery_prediction, MIMIC-IV, DuckDB, ED]
created: 2026-05-09
updated: 2026-05-09
division: urology
project_dir: kidney-stone-surgery-prediction/
---

# 肾结石急诊外科干预预测

## 当前状态: 建模完成，AUROC 0.755

详见项目目录: [[kidney-stone-surgery-prediction/]]

## 核心结果

- **最佳模型**: Random Forest + SMOTE, 400 trees, AUROC **0.7550**
- **数据**: MIMIC-IV, 1,979 名急诊肾结石患者, 114 features, 6.0% 阳性率
- **超过**: Goharderakhshan et al. (2025) AUROC 0.727
- **接近**: Haifler et al. (2022) AUROC 0.78 (差 0.025)

## 下一步

- [ ] 论文写作
- [ ] MIMIC-III 外部验证
- [ ] 决策曲线分析 / 校准分析

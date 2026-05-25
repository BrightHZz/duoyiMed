# 数据真实性前置检查 (Data Authenticity Gate)

## 背景

2026-05-17 proj_1778997283_8738 Phase 3 用 `--mode synthetic` 生成合成数据训练模型。合成数据的 AUC 0.961 被写入 Abstract、Conclusion、Discussion, 并作为 Phase 4-7 的输入。MIMIC-III 真实数据验证时 AUC 仅 0.47。根因: 编排器中所有角色被同一实体扮演, 对"先跑通"的追求凌驾于数据真实性之上。医疗研究必须以事实为依据。

## DAG-R1: 数据来源强制声明

Phase 3 启动前, data-engineer 必须生成 `data_provenance_report.json`, 声明训练数据的来源、查询语句、行数、时间范围。编排器不得兼任 data-engineer 执行此检查。

```json
{
  "project_id": "...",
  "generated_by": "shared/data-engineer",
  "training_data": {
    "source": "mimic_iv_hosp (DuckDB: D:/database/datasets/MIMIC/mimic.db)",
    "query_hash": "sha256 of the SQL query used",
    "n_patients": 4200,
    "n_positive": 504,
    "date_range": "2014-01-01 to 2019-12-31",
    "is_synthetic": false
  },
  "external_validation_data": {
    "source": "mimic_iii (DuckDB: D:/database/datasets/MIMIC/mimic.db)",
    "n_patients": 274,
    "n_positive": 59,
    "is_synthetic": false
  }
}
```

## DAG-R2: 合成数据隔离

`is_synthetic == true` 时:
- cv_results.json 文件名必须包含 `_synthetic` 后缀 (如 `cv_results_synthetic.json`)
- 模型文件必须包含 `_synthetic` 后缀 (如 `xgb_final_synthetic.pkl`)
- `gate_report_phase3.json` 必须包含 `data_provenance: synthetic` 标记
- Phase 4-7 编排器在 `_check_gate()` 时必须检查此标记: `data_provenance == synthetic` → 阻断 → 要求真实数据重训练
- 合成数据仅允许用于: 脚本语法验证 / 代码调试 / Pipeline 集成测试
- 合成数据产出的任何指标 (AUC, Brier, 特征重要性) **禁止进入 sections/ 或 submission/**

## DAG-R3: 数据血缘追溯

submission/manuscript.md 中每个数值必须能追溯到:
```
manuscript AUC 0.852
  → sections/04_results.md
    → cv_results.json (models.xgboost_scheme_a.auc.mean)
      → train_model.py --mode production
        → mimic_iv_hosp.admissions + diagnoses_icd + labevents (DuckDB query)
```

Gate 6 `check_numerical_traceability` 需扩展为三级追溯: manuscript → cv_results.json → database query。

## DAG-R4: PI 数据真实性终审

Phase 5 (Review) 中 PI 必须检查 `data_provenance_report.json`。PI 签批时必须确认:
- [ ] 训练数据来自真实数据库 (非合成)
- [ ] 外部验证数据来源独立于训练数据
- [ ] 所有 manuscript 中的性能指标可追溯到真实数据

## 强制约束

本原则高于所有其他编排原则——任何流程效率考量不得凌驾于数据真实性之上。违反此原则 → 项目冻结, 所有下游 Phase 基线作废。数据真实性检查由 data-engineer 独立执行 (编排器不能兼任), 检查结果写入 `data_provenance_report.json`。

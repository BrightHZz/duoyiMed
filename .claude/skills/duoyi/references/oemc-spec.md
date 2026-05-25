# 编排器执行强制检查清单 (OEMC)

## 背景

编排器可以通过直接写入 project_state.json 绕过所有检查。钱学森闭环反馈控制的前提是"传感器在工作"——Gate 检查函数被绕过等于关闭所有传感器, A/B/C 三个反馈回路全部变成开环。

## OEMC-R1: Gate Report 必须存在

每个 Phase 完成后, 编排器必须生成 `gate_report_phase{N}.json`:

```json
{
  "phase_id": "...",
  "checks_executed": true,
  "auto_checks": [
    {"check_id": "...", "executed": true, "result": "pass|fail|cond_pass", "evidence": "..."}
  ],
  "scripts_executed": [
    {"script": "src/...py", "exit_code": 0, "output_artifacts": ["..."]}
  ],
  "deliverables_verified": [
    {"path": "...", "exists": true}
  ]
}
```

## OEMC-R2: 进入下一 Phase 前强制验证

编排器在开始 Phase N+1 之前, 必须:
1. 读取 `gate_report_phase{N}.json`
2. 检查 `checks_executed == true`
3. 检查所有 auto_checks 的 `result != "fail"`
4. 检查所有 deliverables_verified 的 `exists == true`
5. 以上任何一项不满足 → **阻断前进**, 输出缺失项清单, 回退执行

## OEMC-R3: 脚本必须实际执行

Phase 3/4/6 中任何 Python 脚本不得仅"被写入"。编排器必须确认脚本已被执行 (exit_code 记录在 gate_report 中)。`scripts_executed` 为空 → 等同于 checks_executed == false → 阻断。

## OEMC-R4: 编排原则 #2 强制化

每个 Gate 的 pass/fail 判定必须有至少 1 个 auto_checks 条目且所有条目 executed==true。0 个 auto_checks 的 Gate 报告无效。

## OEMC-R5: 虚假数据检测

如果 gate_report 中 `checks_executed == true` 但 `auto_checks` 为空数组 → 视为虚假报告 → Gate FAIL → 触发 B环, 创建变更请求 CR-fake-gate-{phase_id}。

## OEMC-R6: 原始输出不可伪造原则

每条 auto_check 必须附带 `raw_output` 字段 — 检查函数的原始输出文本:

```json
{
  "check_id": "check_numerical_traceability",
  "executed": true,
  "result": "fail",
  "raw_output": "MISMATCH: manuscript AUC 0.852 vs cv_results.json xgboost_scheme_a_auc 0.938, deviation 9.2% > 0.1% threshold"
}
```

`raw_output` 要求:
- 必须包含具体的数值/文件名/行号, 不能只是 "PASS" 或 "OK"
- 必须包含足够信息让独立复核者判断结论是否自洽
- 如果 raw_output 描述的内容与 result 矛盾 → 视为伪造 → Gate FAIL

## OEMC-R7: 交叉审计机制

编排器在进入 Phase N+1 时, 除了读取 Phase N 的 gate_report, 还必须对其中至少 1 条关键 auto_check 执行独立复验:
- 如果 check 在引擎代码中有对应函数 → 用 Bash 工具执行该 Python 函数
- 如果 check 是 LLM 语义检查 → 编排器重新读取相关文件, 独立判断

复验不通过 → gate_report 伪造嫌疑 → Phase N+1 阻断 → Phase N 强制重做 Gate。

## OEMC-R8: 全 section 数值一致性自检

Phase 6 编排器在 assembly 之前, 必须先执行全 section 自检:
1. 列出 `sections/` 下所有 .md 文件
2. 对每个文件, 提取其中所有 X.XXX 格式的数值
3. 与 cv_results.json + external_validation_results.json 交叉比对
4. 任何文件的数值无法追溯到真相源 → 该文件必须更新后重新自检

**检查范围限定**:
- **必须检查**: `04_results.md`、`05_discussion.md`、`06_conclusion.md`
- **不应检查**: `02_introduction.md` (文献综述中的外部 AUC)、`03_methods.md` (方法学参数)、`08_references.md` (DOI 编号)
- **例外判定**: 如果数值出现在 Introduction 段落且上下文包含引用标记 `[N]`, 自动判定为文献引用 → 豁免

## 各 Phase 的 OEMC 底线

| Phase | 最少 auto_checks | 最少 scripts_executed | 关键 deliverables | 数据真实性 |
|-------|:---:|:---:|------|:--:|
| 0 | 0 (auto-pass) | 0 | sds.md | — |
| 1 | 4 | 0 | literature-precheck.md, data-availability.md, frame-assessment.md | — |
| 2 | 4 | 0 | sap.md, pi-ruling.md | — |
| 3 | 6 | 1 (train_model.py) | cv_results.json, xgb_final.pkl, cohort_attrition.json | data_provenance_report.json 必须 is_synthetic==false |
| 4 | 3 | 1 (external_validation.py) | external_validation_results.json | 验证数据来源独立于训练数据 |
| 5 | 4 | 0 | review-pi.md (PI签批) | PI 检查 data_provenance_report.json |
| 6 | 31 | 5 | submission/manuscript.md, submission/figures/*.png, submission/tables/*.csv, imrad_blueprint.md | 数值→cv_results→database 三级追溯 |
| 7 | 5 | 0 | supplements/app.py, supplements/model_info.json | 免责声明标注训练数据来源 |

# 工程控制论故障分析 — 2026-05-24 Gate 6 内容完整性漏检事件

## 事件概述

**时间**: 2026-05-22 22:10
**项目**: proj_1779450390_8738 (Pediatric AKI ML Prediction)
**故障等级**: P1 — 交付件内容为空 (Figure 1 缺失, Table 1 全部为占位符)
**Gate 6 结果**: 29/29 PASS（全部是形式检查，未检查内容完整性）

**故障现象**:

1. Figure 1（队列筛选流程图）: `figures/` 目录只有 Figure 2/3/4，无 Figure 1。`generate_figures.py` 自认 `"Figures complete: Figure2-4"`
2. Table 1（基线特征表）: 9 行基线特征（Age/Male/Creatinine/Lactate/BUN/Emergency/Vasopressor/ICU LOS/Mortality）全部为 "—" 占位符。只有总 N 值从 cv_results.json 填入
3. `check_figures_exist` 阈值是 `>= 3`（文档写"至少 4"但代码是 3），3 张图直接 PASS
4. `check_tables_exist` 只统计文件数量 >= 3，从不读取 Table 1 内容

---

## 五模块根因诊断

### 模块一：闭环反馈控制 — Gate 传感器的"感知盲区"

```
A环 (Phase内Gate返工回路):
  设计意图: Gate FAIL → 同Phase返工
  失效模式: 29 条 check 全部 PASS。不是因为产出正确，而是因为
           检查维度本身不覆盖"内容填充率"这一故障模式
  根因: Gate 检查只能感知两类故障:
        ① 文件不存在 (check_*_exist 系列) — 可检测
        ② 已出现的数值不一致 (check_numerical_traceability) — 可检测
        ③ 文件存在但内容为占位符 (全部为 "—") — 盲区 ← 本次故障
        ④ 该有的文件编号缺失 (Figure 1) — 盲区 ← 本次故障

B环 (跨Phase自动回退回路):
  失效模式: Phase 3 的 train_model_v2.py 已提取全部患者级数据 (年龄/性别/Cr/Lac等)，
           但没有保存分层汇总结果。下游 generate_tables.py 拿不到分层数据，静默降级写 "—"。
          脚本 exit code 仍为 0，无任何 trigger 被激活。
  根因: 静默降级 (silent degradation) — 脚本在无法完成任务时选择写占位符而非 exit 1，
        B环依赖 "检测到问题" 才能触发，但静默降级产生了零信号

C环 (趋势监控回路):
  不适用 — 此事件不涉及数值趋势变化
```

**钱学森核心教训**: 反馈控制的前提是传感器能感知故障。当前系统传感器只覆盖"存在性"和"一致性"两个频段，"完整性"频段完全空缺。传感器工作频段决定了系统能感知什么故障。

### 模块二：可靠性工程 — 正向追溯与逆向验证的不对称性

`check_numerical_traceability` 的逻辑是**正向追溯**：对 manuscript 中出现的每个数值，在上游找来源。这是一种 "pull" 模式——只验证"已出现的东西是否正确"。

缺失的是**逆向验证**：对上游的每个关键字段，确认它的数值在下游被正确呈现。这是 "push" 模式——"该出现的东西是否出现了"。

```
正向追溯 (已实现):
  对于 manuscript 中每个 X.XXX:
    在 cv_results.json 中找 → 找到且一致 → PASS
                            → 找不到 → FAIL

逆向验证 (缺失):
  对于 cv_results.json 的每个关键字段:
    在 manuscript/tables/figures 中找 → 找到且一致 → PASS
                                      → 找不到 → "该出现的数值没出现" ← 本次故障
```

Table 1 的 9 行全是 "—"，但因为 "—" 不是数值，`check_numerical_traceability` 不会对它做任何追溯。content fill rate 实为 0%（除 N 行），没有任何检查感知。

**钱学森核心教训**: 两个不可靠元件（Agent 生成不完整数据 + Gate 只做正向检查）叠加不能构成可靠系统。存在性 + 一致性 ≠ 完整性。三个维度缺一不可。

### 模块三：研讨厅辩论 — Phase 6 自产自审的独白模式

Phase 2/5 已启用研讨厅辩论（三方并行输出 → 主持人汇总 → PI 裁决），但 Phase 6 是单 Agent 流水线：

```
Phase 6 的实际执行:
  scientific-writer (编排器扮演): 写 generate_tables.py → 全部 "—" 
  orchestrator (同一实体):        执行 Gate 6 → 29/29 PASS
  结论: 自产自审 → 无交叉验证
```

如果 clinical-researcher 在 Phase 6 被邀请审查 Table 1，"所有基线特征为空"会在第一时间被指出。同样，biostatistician 会注意到 Figure 1 缺失。

**钱学森核心教训**: 综合集成研讨厅的效力取决于参与角色的独立性。当所有角色由同一实体扮演，辩论退化为独白。

### 模块四：系统辨识 — 漏检模式未被记录和学习

2026-05-18 的口头 Gate 穿透事件后，系统新增 OEMC-R1~R8。但那次故障模式是"Gate 未执行"，本次是"Gate 执行了但维度不覆盖"。这是全新故障模式。

系统需要学习：
- 新增故障模式签名: `gate6_content_fill_rate_bypass`
- `ProjectPredictor` 对未来 pediatrics 项目应降低 Phase 6 的预测通过率
- 新项目 Phase 0 SDS 应注入: "历史教训 — 2026-05-24: Table 1 曾全部为占位符，Figure 1 曾缺失"

### 模块五：总体设计部 — 接口定义缺内容契约

SDS 定义了 `cv_results.json → generate_tables.py → Table1_baseline.md` 的接口链，但接口定义中只有格式（.md/.csv），没有**内容契约**：

```
缺失的内容契约:
  - Table 1 每行必须有分层统计值 (All / Non-AKI / AKI)，不允许全部为占位符
  - 内容填充率 >= 80%
  - 必须覆盖 cv_results.json 中 selected_features 对应的基线变量
  - Figure 编号从 1 开始，连续无跳号
```

总体设计部的核心是"接口标准化 + 全系统集成验证"。格式标准化已完成，内容契约缺失。

---

## 修复记录

### 修复 1: generate_tables.py — 连接 PIC 数据库提取真实 Table 1 数据

将 Table 1 生成从"只读 cv_results.json 填 N 值"改为"完整数据库提取 + 分层统计"：
- 复用 train_model_v2.py 的数据提取逻辑和队列构建逻辑
- 计算 All/Non-AKI/AKI 三列的真实分层统计（中位数/IQR 或 N/%）
- 新增 fill_rate 自检: < 50% → exit 1
- 结果: fill_rate = 97.7%，数据与 manuscript 一致（N=4430, AKI=295, 6.7%）

### 修复 2: generate_figures.py — 新增 Figure 1 生成

基于 cohort_attrition.json 生成队列筛选流程图（12,881→6,988→4,966→4,430）

### 修复 3: gate_checks.py — 新增 2 个 check + 升级 1 个

| Check | 类型 | 检查内容 |
|-------|------|---------|
| `check_figure_numbering_continuity` | 新增 | Figure 编号从 1 开始连续；若 cohort_attrition.json 存在 → Figure 1 强制 |
| `check_table1_content_completeness` | 新增 | 扫描 Table 1 占位符占比；fill_rate < 80% → FAIL；< 100% → COND_PASS |
| `check_figures_exist` | 升级 | 旧: `len >= 3` → PASS；新: 计数 + caption↔image 双向匹配 + 正文引用 + cohort 时 min=4 |

### 修复 4: run_gate6.py — 注册新 check

新增 `figure_numbering_continuity` 和 `table1_content_completeness` 到 GATE6_PYTHON_CHECKS（32 项）

---

## 注入规则

以下规则从本次故障中提取，须注入到公司系统中：

1. **Phase 6 generate_tables.py 自检**: fill_rate < 50% → exit 1。脚本不得静默降级为占位符
2. **Phase 6 generate_figures.py 自检**: 若项目含 cohort_attrition.json，必须生成 Figure 1
3. **Gate 6 新增检查维度**: 内容填充率（content fill rate）— 区别于存在性和数值一致性，是第三独立维度
4. **Interface 契约**: SDS 中 tables/ 接口须附带内容完整性约束（fill_rate >= 80%，覆盖 selected_features）
5. **研讨厅辩论**: Phase 6 图表产出后，应触发 clinical-researcher + biostatistician 对 Table 1 和 Figure 的并行审查

---

*文档: company/management/engineering-cybernetics-lessons-learned-2026-05-24.md*
*基于: 钱学森工程控制论五模块故障分析法*
*日期: 2026-05-24*

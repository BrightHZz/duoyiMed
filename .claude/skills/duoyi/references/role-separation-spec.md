# 角色分离执行规范

## 背景

编排器模式 (LLM Agent 直接执行所有 Phase) 下, 编排器同时扮演 orchestrator、ml-engineer、data-engineer、biostatistician、PI 等角色。当所有角色由同一实体扮演时, 研讨厅辩论退化为独白, 交叉验证失效, 对效率的追求吞掉其他角色的质疑。

## RS-R1: 角色显式切换

编排器每进入一个 Phase, 必须在输出开头声明当前扮演的角色和该角色的约束:

```
[Role: shared/ml-engineer]
Constraints: n_jobs=2, 禁止嵌套并行, 真实数据必须验证完整性, 不得使用合成数据替代
```

## RS-R2: 角色冲突强制上报

当编排器发现两个角色之间存在冲突时 (如 ml-engineer 要求真实数据 vs orchestrator 想用合成数据加速), 编排器必须:
1. 停止执行
2. 以两个角色的身份分别陈述立场
3. 由 PI 角色裁决
4. 裁决结果写入 `role_conflict_log.json`

## RS-R3: 医疗项目角色分离强化

对于医疗相关项目, 以下角色**不得由编排器兼任**:
- data-engineer: 数据提取和验证必须由编排器以 data-engineer Agent prompt 约束独立执行
- PI: 终审签批必须由编排器以 PI Agent prompt 约束独立执行, 审查 data_provenance_report.json

## 设计原则

本规范是钱学森研讨厅思想的落地: 多角色并行辩论的前提是**角色之间有真正的独立性**。当所有角色由同一实体扮演时, 辩论退化为独白, 系统失去交叉验证能力。

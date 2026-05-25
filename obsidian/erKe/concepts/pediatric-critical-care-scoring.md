---
type: concept
topic: 儿科危重症评分系统
created: 2026-05-22
aliases: [PICU Scores, 危重症评分, PRISM, pSOFA, PELOD]
---

# 儿科危重症评分系统

儿科 ICU 中用于量化疾病严重度、预测死亡风险的标准工具。在 ML 研究中常用作 baseline 对比和特征工程来源。

## 主要评分系统

### 1. PRISM III (Pediatric Risk of Mortality III)

- **用途**: PICU 死亡率预测，入室 24h 内评估
- **变量数**: 17 个生理变量
- **AUC**: 约 0.85-0.90（开发集），外部验证 0.75-0.85
- **时效性**: 1996 年发布，2003 年更新（PRISM III）
- **局限性**: 
  - 基于 1990s 美国 PICU 数据，现代 PICU 死亡率已显著下降
  - 未纳入慢性基础疾病
  - 校准度在现代队列中可能漂移
- **PIC 可用性**: PIC 数据库中可提取 PRISM III 组成变量

### 变量组成

| 类别 | 变量 |
|------|------|
| 心血管 | 收缩压 (年龄校正)、心率 (年龄校正)、体温 |
| 呼吸 | 呼吸频率 (年龄校正)、PaO₂/FiO₂、PCO₂ |
| 神经系统 | Glasgow 昏迷评分 (GCS)、瞳孔反射 |
| 实验室 | pH、总 CO₂、血糖、血钾、血肌酐、血尿素氮 |
| 血液学 | WBC、PT/PTT、血小板 |

### 2. PIM-3 (Paediatric Index of Mortality 3)

- **用途**: PICU 死亡率预测，入室 1h 内评估
- **优势**: 仅需入室时数据，不受治疗偏倚影响
- **AUC**: 约 0.85-0.88
- **更现代**: 2013 年发布，基于 2010-2011 年多国数据

### 3. pSOFA (Pediatric Sequential Organ Failure Assessment)

- **用途**: 器官功能障碍的动态评估（每日可重复评分）
- **适用**: 脓毒症/感染患者的器官衰竭评估
- **变量**: 6 个器官系统（呼吸、凝血、肝脏、心血管、神经系统、肾脏）
- **年龄特异性**: 各年龄段的 cut-off 值不同
- **AUC**: 脓毒症相关死亡率 AUC 约 0.75-0.85
- **特点**: 趋势变化（ΔSOFA）比绝对值更有意义

### 4. PELOD-2 (Pediatric Logistic Organ Dysfunction-2)

- **用途**: 多器官功能障碍综合征 (MODS) 严重度量化
- **特点**: 10 个变量，涵盖 5 个器官系统
- **AUC**: 约 0.90-0.93（死亡预测）

### 5. SNAPPE-II (Score for Neonatal Acute Physiology - Perinatal Extension II)

- **用途**: NICU 新生儿疾病严重度和死亡率预测
- **变量**: 9 个生理变量 + 出生体重 + Apgar + SGA
- **AUC**: 约 0.85-0.92
- **PIC 可用性**: NICU 模块可提取

## 评分系统的 ML 研究用途

1. **Feature engineering**: 评分系统组成变量是经过验证的预测因子
2. **Baseline comparison**: 新模型的性能必须与现有评分对比
3. **Calibration reference**: 评分系统提供了校准度参考基准
4. **Subgroup analysis**: 按评分分层分析模型在各严重度子集的表现

## 关键参考文献

- Pollack MM et al. PRISM III. Crit Care Med. 1996;24(5):743-752
- Straney L et al. PIM-3. Intensive Care Med. 2013;39(11):1952-1960
- Matics TJ, Sanchez-Pinto LN. pSOFA. Pediatr Crit Care Med. 2017;18(3):216-223
- Leteurtre S et al. PELOD-2. Crit Care Med. 2013;41(7):1761-1773

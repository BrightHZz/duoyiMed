---
type: methods
topic: 儿科 ML 建模特殊考量
created: 2026-05-22
aliases: [儿科ML, Pediatric ML, 儿科数据建模]
---

# 儿科 ML 建模特殊考量

## 1. 年龄作为核心效应修饰因子

**问题**: 儿童的生理参数随年龄急剧变化。同一疾病在不同年龄段的临床表现、实验室参考范围、治疗反应截然不同。

**策略**:
- **(A) 年龄分层建模**: 按标准年龄阶段分别训练模型，比较各层性能
- **(B) 年龄-特征交互项**: `model ~ age * key_features`，让模型学习年龄的修饰效应
- **(C) z-score 标准化**: 身高/体重/BMI/血压/心率的原始值 → 年龄-性别 z-score
- **(D) 年龄作为调整变量**: 在模型中加入年龄作为协变量

**最低要求**: 必须报告各年龄分层的模型性能（ROC 或森林图）；不能只报告全人群 AUC。

## 2. 小样本量策略

儿科数据通常远小于成人（罕见病、单中心限制）。

| 样本量 N | 推荐策略 | 避免 |
|----------|---------|------|
| N < 100 | Logistic / Elastic Net；贝叶斯方法（有信息先验）；不做 CV | XGBoost、DL |
| 100 ≤ N < 500 | Logistic / Elastic Net / 高正则化 XGBoost；LOOCV 或 repeated 10-fold CV | DL、许多特征 |
| 500 ≤ N < 2000 | XGBoost / RF / 谨慎使用 MLP | 深层 DL |
| N ≥ 2000 | 经典 ML baseline + DL 探索 | 裸用 DL（必须对比经典 baseline） |

**额外考量**:
- EPV (Events Per Variable) ≥ 10 为最低标准
- 罕见结局 (如川崎 CAA ~5%): 报告宽 CI，坦诚样本量限制
- 当样本量不足时，主动建议贝叶斯方法或不做

## 3. 类别不平衡（儿科常见）

儿科重症监护中，死亡率为 3-8%，某些并发症发生率 < 5%。

| 不平衡程度 | 阳性率 | 策略 |
|-----------|--------|------|
| 轻度 | 20-40% | class_weight / scale_pos_weight |
| 中度 | 5-20% | SMOTE (Pipeline 外提前执行!) + tuned threshold |
| 重度 | 1-5% | SMOTE + Ensemble + Focal Loss；PR-AUC 为主要指标 |
| 极端 | <1% | 可能无足够数据建模；建议改变结局定义或放弃 |

**儿科特殊性**:
- 假阴性的代价在儿科中极高：漏诊败血症 → 死亡。阈值选择应偏向灵敏度
- 假阳性的代价：不必要的抗生素 → 耐药性。需权衡
- 报告 Net Benefit (Decision Curve Analysis) 覆盖临床相关阈值范围

## 4. 时序数据建模

NICU/PICU 数据的时序特性与成人 ICU 有重要区别：

**儿科特点**:
- 采样频率不规则（临床需要驱动，而非研究设计）
- 缺失数据模式包含信息（没测 = 临床不太担心 = 较轻）
- 干预变量的强时变性（用药/呼吸机参数调整频繁）
- 生长发育随住院时间的变化（尤其在 NICU 长时间住院）

**特征工程策略**:
```
每段时序窗口 (如入室后 24h):
  ├── 汇总统计: min / max / mean / median / SD
  ├── 趋势特征: slope / delta (first-last) / AUC
  ├── 变异特征: coefficient of variation / IQR
  ├── 极值特征: 最差值 / 最佳值 / 超越阈值时间比例
  └── 干预特征: 最大药物剂量 / 呼吸机参数变化次数
```

## 5. 单中心局限

PIC 是单中心数据库，需在研究中坦诚讨论：

- Discussion 必须出现 "This is a single-center study" 的局限声明
- 外推性限制: 中国东部发达地区 vs 中西部/农村/其他国家的差异
- 建议: 如果可能，寻找外部验证数据源（如 MIMIC-IV 儿科亚组）
- 如果无法外部验证: 在 Conclusion 中明确写 "requires external validation before clinical use"

## 6. 伦理考量

- 儿科数据更敏感（未成年人），数据安全和去标识化要求更高
- 临床决策支持工具在儿科中使用需更谨慎（假阴性的灾难性后果）
- 模型在儿科中更可能面临"off-label use"（在不同年龄组使用）

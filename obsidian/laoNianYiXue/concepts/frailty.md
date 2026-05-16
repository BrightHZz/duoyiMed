---
type: concept
topic: frailty
status: reference
last_updated: 2026-05-04
tags:
  - geriatric_syndrome
  - frailty
  - aging
---

# 衰弱 (Frailty)

## 定义
一种与年龄相关的生理储备下降和多系统功能减退的临床状态，导致对应激的易感性增加。

## 三种操作化定义

### 1. Fried Frailty Phenotype (2001)
**5 项标准，满足 ≥3 = 衰弱，1-2 = 衰弱前期**：

| 标准 | 测量方式 |
|------|----------|
| 体重下降 | 1 年内非刻意减重 ≥5% 或 ≥4.5kg |
| 疲乏 | CES-D 两个问题（"做事费力"/"提不起劲"）≥3 天/周 |
| 握力下降 | 测力计，按性别+BMI 分层的最低 20% |
| 步速减慢 | 15 英尺（4.57m）步行，按性别+身高的最低 20% |
| 活动量低 | 每周卡路里消耗，按性别的最低 20%（男性 <383, 女性 <270 kcal/周） |

**优势**: 基于病理生理机制（能量、肌骨、神经）  
**局限**: 需体格测量，不适用于卧床/无法完成测试者

### 2. Frailty Index (FI, Rockwood & Mitnitski, 2002)
**≥30 个健康缺陷项的累积比例**:
```
FI = 缺陷数量 / 总项目数
FI ≥ 0.25 = 衰弱
0.10 ≤ FI < 0.25 = 衰弱前期
FI < 0.10 = 健壮
FI > 0.45 = 通常难以存活
```

**优势**: 可从 EHR 计算，对不良结局预测好  
**局限**: 需要较多变量（≥30 项），不同研究的 FI 可比性问题

### 3. FRAIL Scale (2008)
**5 项自报**:
- **F**atigue (疲劳)
- **R**esistance (上一层楼困难)
- **A**mbulation (步行一个街区困难)
- **I**llness (≥5 种慢病)
- **L**oss of weight (>5%)

满足 ≥3 = 衰弱

**优势**: 快速，不需体格检查  
**局限**: 主观自报，不如 Fried 精确

## 流行病学（中国）
- 社区老年人衰弱患病率: 约 7-12%（Fried 定义）
- 衰弱前期: 约 40-50%
- 女性 > 男性
- 随年龄递增: 65-69 (4%) → 80-84 (15%) → 85+ (25%)

## 不良结局
衰弱预测: 跌倒、失能、住院、入住养老机构、死亡

## 计算建模中的要点
- 不同类型（Fried vs FI）可能捕获不同的生物学信号，不建议混用
- 作为结局变量时注意：Fried 是 3 分类（0/1-2/3-5），可以合并为二分类
- 作为预测因子时注意：FI 是连续变量 (0-1)，信息量更大但需要更多变量
- 衰弱状态的转换（transitions）比横断面衰弱更有研究价值

## 相关文献
- Fried LP et al. J Gerontol A Biol Sci Med Sci. 2001;56(3):M146-M156.
- Rockwood K, Mitnitski A. J Gerontol A Biol Sci Med Sci. 2007;62(7):722-727.
- [[literature/literature-dashboard|更多文献]]

## 关联概念
- [[concepts/sarcopenia|肌少症]]
- [[concepts/epigenetic-clocks|表观遗传时钟]]

---
type: concept
topic: sarcopenia
status: reference
last_updated: 2026-05-04
tags:
  - geriatric_syndrome
  - sarcopenia
  - muscle
---

# 肌少症 (Sarcopenia)

## 定义
进行性、全身性的骨骼肌质量和力量下降，伴随身体功能减退和不良结局风险增加。

## AWGS 2019 诊断流程

```
筛查 (SARC-F ≥ 4 或 小腿围 ↓)
  │  男 <34 cm, 女 <33 cm
  ↓ 阳性
肌肉力量 (握力)
  │  男 <28 kg, 女 <18 kg
  ↓ 低于阈值
肌肉质量 (DXA/BIA)
  │  ASM/ht²: 男 <7.0, 女 <5.7 kg/m²
  ↓ 低于阈值
══════════════════
诊断: 肌少症
  │
  ↓ + 身体功能 ↓
身体功能
  │  步速 <1.0 m/s
  │  或 SPPB ≤ 9
  │  或 TUG ≥ 12s
  │  或 5次坐站 ≥ 12s
  ↓ 低于阈值
严重肌少症
```

## 三种定义对比

| 标准 | 肌肉质量 | 肌肉力量 | 身体功能 |
|------|----------|----------|----------|
| AWGS 2019 | DXA/BIA | 握力 | 步速/SPPB/TUG/坐站 |
| EWGSOP2 | DXA/BIA | 握力 | 步速/SPPB/TUG |
| FNIH | DXA (BMC adjusted) | 握力 | 步速 |

**推荐 AWGS 2019**：针对亚洲人群，阈值适合中国老年人。

## SARC-F 筛查问卷
| 项目 | 问题 | 评分 |
|------|------|------|
| **S**trength | 提 10 磅重物困难？ | 0-2 |
| **A**ssistance | 室内步行需要帮助？ | 0-2 |
| **R**ise | 从椅子站起困难？ | 0-2 |
| **C**limb | 爬 10 级台阶困难？ | 0-2 |
| **F**alls | 过去 1 年跌倒次数？ | 0-2 |

总分 ≥4 = 肌少症高风险，需进一步检查。

## 与衰弱的关系
- 肌少症是衰弱的核心组成部分（衰弱包含但不止于肌肉）
- 肌少症 → 身体衰弱 (Physical Frailty)
- 约 70% 的 Fried 衰弱老人同时有肌少症
- 肌少症性肥胖 (Sarcopenic Obesity): BMI 高但肌肉量低，代谢风险极高

## 计算建模中的要点
- 肌少症诊断依赖连续变量的截断值，截断值的种族/人群适应性需要验证
- 如缺乏 DXA/BIA 数据，可考虑使用替代指标（小腿围、BMI 调整后的握力）
- 肌少症作为结局时，诊断标准的变化可能影响模型性能比较

## 相关文献
- Chen LK et al. JAMDA. 2020;21(3):300-307.e2. (AWGS 2019)
- Cruz-Jentoft AJ et al. Age Ageing. 2019;48(1):16-31. (EWGSOP2)

## 关联概念
- [[concepts/frailty|衰弱]]

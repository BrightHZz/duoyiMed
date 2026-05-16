# 临床审查报告 — Clinical Researcher Review

**稿件**: Heterogeneous Effects of SES on Biological Aging in Chinese Older Adults
**审查日期**: 2026-05-08
**审查人**: Clinical Researcher (Geriatrics) Agent

---

## 临床审查闸门 (Clinical Review Gate)

### □ 1. 效应方向验证

| 发现 | 方向 | 临床预期 | 评估 |
|------|------|----------|------|
| Overall ATE (low SES → bio-age) | −0.118 (低 SES = 更低生物年龄) | 高 SES = 更低生物年龄 | **方向相反** ⚠️ |
| Rural CATE | +0.071 (低 SES = 更高生物年龄) | 符合预期 | **一致** ✓ |
| Urban CATE | −0.044 (低 SES = 更低生物年龄) | 不符合预期 | **方向相反** ⚠️ |
| SES × Grip: Low SES + High Grip | −0.25 (最佳) | 中等 | **意外** ⚠️ |
| SES × Grip: High SES + Low Grip | +0.49 (最差) | 中等 | **意外** ⚠️ |
| CES-D mediation | 63% | 预期 20-40% | **高于预期** ⚠️ |

**核心矛盾**: 主要发现是 **低 SES 组生物年龄更低 (更好)**。这与所有现有文献的 SES-健康梯度方向相反。Manuscript Discussion 提出了三种解释:

1. **幸存者偏倚** — 最合理的解释。低 SES 个体在 60 岁前死亡率更高, 存活到 60 岁的低 SES 老人是"选择性幸存者", 具有 resilience phenotype。需要引用 CHARLS 或其他中国人群的年龄别死亡率 SES 差异证据。
2. **肥胖悖论** — 部分解释。生物年龄复合指标包含 BMI 和 SBP, 如果高 SES 组 BMI 更高 (超重/肥胖) 且 SBP 更高 (与城市化、饮食西化相关), 则方向可能合理。但没有单独报告 4 个成分的 SES 差异, 无法判断是哪个 marker 驱动了方向逆转。
3. **残留混杂** — 未测量变量如体力活动、饮食质量

**临床判定**: 方向异常, 但有合理临床解释。需补充:(a) 各组 4 个生物标志物成分的描述统计; (b) survivorship bias 的定量证据; (c) Discussion 中更坦诚地面对这一异常。

**此项: 条件通过** ✓

---

### □ 2. 数值临床合理性

| 变量 | 合理范围 | 实际范围 | 状态 |
|------|----------|----------|------|
| CES-D-10 | 0–30 | 7.10–9.34 | ✓ |
| 握力 (kg) | 0–80 | 21.2–33.9 | ✓ |
| 年龄 (岁) | 60+ | 68.6 ± 7.2 | ✓ |
| 女性比例 | 45–55% | 50% | ✓ |
| 教育年限 | 0–20 | 5.9 | ✓ (代表性良好) |
| 月人均收入 | 0–5000 元 | 133 元 (中位数) | ⚠️ 极低, 0 值比例过高 |

**收入异常关注**: 月人均收入中位数 133 元 (年 ≈1,600 元) 远低于 2013 年中国农村贫困线 (2,300 元/年)。高比例 0 值收入 + log(1+x) 变换可能扭曲 SES 排序, 特别是在农村分组中的 SES 分类。

**Grip 中位数分割值**: 未在 manuscript 中报告。需要报告 grip 分割值 (预期约 26-27 kg), 以便临床读者评估亚组定义的临床含义。

**此项: 条件通过** ✓

---

### □ 3. 分组排序与解读一致性

**Table 2 排序 — 生物年龄从好到坏:**
1. Low SES + High Grip: −0.25 (最佳 ✓)
2. High SES + High Grip: −0.22
3. Low SES + Low Grip: +0.35
4. High SES + Low Grip: +0.49 (最差 ✓)

**叙事实况检查:**

| Manuscript 声明 | 数据 | 判断 |
|-----------------|------|------|
| "Physical function was more strongly associated with biological aging than SES" | Grip 效应远大于 SES 效应 | ✓ **正确** |
| Abstract: "cross-classifying SES and grip strength showed a 0.73 SD gradient" | 0.49 − (−0.25) = 0.74 ≈ 0.73 | ✓ **正确** |
| Main Discussion: "undermining the 'double jeopardy' hypothesis" | 数据确实不支持 SES+功能叠加效应 | ✓ **正确** |
| **sections/05_discussion.md: "consistent with the 'double jeopardy' hypothesis"** | 与数据矛盾 | ✗ **错误! 必须修正** |
| Cover letter: "0.28 SD gradient" (旧版) vs manuscript: "0.73 SD gradient" | 旧版数据 | ✗ **已过时** |

**关键叙事缺陷**: 主 manuscript 的 Introduction 最后一句:
> "We hypothesized that the biological cost of low SES would be most pronounced among individuals with compromised physical function—a 'double jeopardy' of socioeconomic and physiological vulnerability."

数据明确否证了这个假说。对于 Table 2 的四组: 低 SES 低握力组 (+0.35) 的生物学年龄明显**优于**高 SES 低握力组 (+0.49)。这意味着**生理脆弱(低握力)的危害不因社会经济劣势而放大**——这不是 double jeopardy, 而是 grip strength 独立主导。

建议 Introduction 改写为双面假设: "We evaluated whether socioeconomic disadvantage and physiological vulnerability act synergistically (double jeopardy hypothesis) or independently on biological aging."

**此项: 条件通过** (main manuscript 通过, sections/ 文件不通过)

---

### □ 4. 工具定义准确性

| 工具 | Manuscript 定义 | 是否正确 | 说明 |
|------|----------------|----------|------|
| CES-D-10 | 10 items, 0-3 计分, 范围 0–30 | ✓ | dc013/dc016 反向在代码中确认 |
| 生物年龄 | 4-marker (grip↓ + gait↓ + BMI + SBP) | ✓ | CES-D 已从结局中排除 |
| 握力 | Maximum of 4 measurements (qc003–qc006) | ✓ | 正确 |
| 步速 | 2.5m / time(s) from qg003 | ✓ | 代码中确认 |
| SES 复合 | 5-component z-score average | ✓ | 方法描述完整 |

**此项: 通过** ✓

---

### □ 5. 临床可解释性

**Top Predictors 合理性 (基于效应量排序):**

1. **Grip strength** — 最强差异化因子。与已知老年医学机制一致 (AWGS 2019 将握力作为肌少症诊断核心组件; 握力预测全因死亡和残疾的 meta 证据充分)。✓
2. **CES-D (depressive symptoms)** — 中介 63% 的 SES-生物衰老关联。这一比例高于 Western 人群 (通常 20-30%), 但中国老年人 somatization 倾向 (Kleinman 1982, 已引用) 提供了合理文化解释。✓
3. **Urban/rural** — 方向逆转, 城市低 SES = 更低生物年龄。可解释为城市 SES 不平等度更大 + 高 SES 城市生活方式的不利影响 (sedentary, dietary)。✓

**年龄混淆评估**: 年龄在分析中为协变量, Table 1 显示 age 60-69 vs 70+ 的 CATE 相似方向, 且 Table 2 的协同分类排除了纯年龄驱动。模型学到了超越年龄的信号。✓

**临床转化评估**: 
- 握力作为筛查工具: 低握力 (< median ~27 kg) 识别出 bio-age +0.35 ~ +0.49 SD 的高风险群。这与现有 geriatric 筛查实践一致 (SARC-F → grip → DXA 的肌少症筛查路径), 有临床可行性。
- 但: 横断面证据强度不足以推荐握力作为"独立于 SES 的衰老风险筛查工具"。需要纵向数据验证握力预测衰老结局时与 SES 的交互效应。

**此项: 通过** ✓

---

## 综合临床审查摘要

### 通过项 (3/5)
- ✓ 工具定义准确性
- ✓ 临床可解释性
- ✓ 数值合理性

### 条件通过项 (2/5)
- △ 效应方向验证 (方向异常但有合理临床解释)
- △ 分组排序与解读一致性 (主文件一致, sections/ 文件存在相反声明)

---

## 临床修正建议 (优先级排序)

1. **报告 4 个生物标志物的分组描述统计** — 必须展示 SES 效应的方向逆转是由哪个具体 marker 驱动的 (是 BMI? SBP? 还是两者的组合?)。
2. **修正 sections/05_discussion.md** — "consistent with double jeopardy" 与数据矛盾, 必须改为与 main manuscript 一致 ("undermining the double jeopardy hypothesis")。
3. **Introduction 假说调整** — 从单向 double jeopardy 假说改为双向评估, 以匹配实际发现。
4. **报告 grip 中位数分割值** — 约 26-27 kg, 让临床读者能对照 AWGS 2019 握力阈值 (男<28, 女<18 kg) 评估亚组定义的临床含义。
5. **幸存者偏倚的定量证据** — 引用 CHARLS 或中国人群的 SES-死亡率梯度数据, 估计 survivorship bias 的量级。
6. **讨论 low-SES + high-grip = −0.25 的临床含义** — 这是 resilience phenotype 的证据, 值得单独一段讨论其对干预设计的启发。

---

## 闸门裁定

**Verdict: APPROVED WITH RESERVATIONS**

主要稿件的临床叙事大体合理, 效应方向异常已在 Discussion 中处理。但 (a) sections/ 文件的相反叙事、(b) 缺失的分 marker 描述统计、(c) Introduction 单向假说需要在投稿前修正。临床发现的核心增量 (grip strength > SES for biological aging risk) 有足够的临床意义支撑。

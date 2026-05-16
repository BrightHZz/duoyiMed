# 方案设计辩论 — Clinical Researcher 独立意见

**项目**: prostate-cancer-metastasis-pattern
**辩论方**: clinical-researcher (urology)
**辩论阶段**: Phase 2 Round 1 (独立输出, 未参考其他方意见)
**日期**: 2026-05-14

---

## 1. 转移模式分类 — 临床合理性审查

### 1.1 四部位二分类 (Bone-only vs Visceral ± Bone) — 临床依据

**支持理由**:
- NCCN 指南将 M1 分为 M1a (非区域 LN)、M1b (骨)、M1c (其他部位/内脏)
- 骨转移和内脏转移的生物学机制不同: 骨转移主要经 Batson 静脉丛→骨，内脏转移经体循环→肝/肺
- 治疗策略不同: 骨转移可受益于骨保护剂 (zoledronic acid/denosumab) + 局部放疗，内脏转移需优先启动化疗/新型内分泌
- Labe 2022 和 Kadeerhan 2023 均采用相似分组

### 1.2 建议的微调

我同意 computational-biologist 提出的分组方案，但建议增加以下临床分层:

#### 主分析: 二分类 (Bone-only vs Visceral ± Bone)
```
Bone-only:        0 organ mets OR bone=only
Visceral ± Bone:  Liver/Lung/Brain positive (regardless of bone status)
```
- **临床理由**: 预后和治疗决策主要由"是否有内脏转移"决定，而非骨转移的"有无"

#### 补充分析: 三分类
```
Bone-only:        Bone=Yes, all visceral=No
Visceral only:    Visceral=Yes, Bone=No
Both (Bone+Visceral):  Bone=Yes AND Visceral=Yes
```
- **临床理由**: 骨+内脏同时转移可能代表更高的肿瘤负荷，预后可能比单纯内脏转移更差

---

## 2. 协变量临床合理性审查

### Gleason Grade Group — 必须用 ISUP 分组而非原始 2-10

**理由**: 2014 ISUP 共识会议后，Gleason 应报告为 Grade Group 1-5，非 6-10。
- ISUP 1 (Gleason 6): 低风险
- ISUP 2 (Gleason 3+4=7): 中风险-好
- ISUP 3 (Gleason 4+3=7): 中风险-差  ← 这组预后与 ISUP 2 显著不同
- ISUP 4 (Gleason 8): 高风险
- ISUP 5 (Gleason 9-10): 极高风险

⚠️ **绝对不能将 Gleason 7 合并为一个级别** — 这是 Urology 领域最常见的低级统计错误。

### PSA 分组

临床标准分组 (NCCN):
- < 4 ng/mL → 正常
- 4-10 → 灰区
- 10-20 → 中风险
- > 20 → 高风险
- Unknown → 单独类别

### T Stage

- T1 (临床不可扪及) → 参考
- T2 (局限在前列腺内)
- T3 (包膜外侵犯/精囊)
- T4 (侵犯周围器官)
- TX → Unknown

---

## 3. 结局定义的临床视角

### 我投票: 3 年 OS 作为主 ML target

**临床理由**:
- M1 前列腺癌的中位 OS 是 20-31 月；5 年 OS 太低（~25-30%）→ binary target 极度不平衡
- 3 年在临床上更有意义：判断患者是否从诊断后存活到"中期"是治疗强度选择的关键时间点
- 如果预测"活不过 3 年" → 可能不需要激进的手术/放疗
- 如果预测"很可能活过 3 年" → 值得考虑局部治疗 + 全身治疗

### CSS vs OS

- OS 作为主结局更保守（所有死亡都算事件）→ 偏倚更小
- CSS 作为次要结局 (Fine-Gray) → 回答"如果不受心血管等竞争死因影响，肿瘤特异性生存如何？"

---

## 4. 治疗变量 — 关键的临床约束

### 治疗作为协变量（非分层变量）

- SEER 中无 ADT (雄激素剥夺治疗) 信息 → 这是最大的治疗变量缺失
- SEER 中无 abiraterone/enzalutamide/apalutamide 信息 → 2016+ 新型内分泌治疗无法区分
- **结论**: 治疗变量只作为协变量调整，不做亚组因果推断
- **Discussion 必须明确**: 治疗变量的局限性 (无 ADT，无新型内分泌)

### 治疗时代 (Era) 作为分层变量

- Era 1 (2010-2015): ADT ± docetaxel
- Era 2 (2016-2023): ADT + docetaxel/abiraterone/enzalutamide (doublet/triplet)
- **临床意义**: 如果转移模式效应在两个时代一致 → 说明转移模式是稳定的预后因子，不受治疗进步影响

### 根治性前列腺切除术 (RP) 在 M1 中的解释

- RP 在 M1 中的比例极低 (~3%)，且是高度选择的患者 (young, low-volume, good PS)
- **不能将 RP 的 HR 解释为治疗效应** (选择偏倚极大)
- RP 变量应作为 risk-adjustment 协变量，不参与因果推断

---

## 5. 与 Biostatistician 的可能分歧点 (预判)

### 分歧 1: 训练/测试划分

- **我的立场**: 同意 biostatistician — 必须按年份切分。此外，建议 2020 年 (COVID 年) 的数据要么单独标记、要么排除。前列腺癌诊断在 COVID 年有明显波动 (下降后反弹)，可能影响病例混合。
- **建议方案**: Train 2010-2018, Validation 2019, Test 2021-2023。2020 单独分析但不进入 train。

### 分歧 2: 缺失处理

- **我的立场**: 对于临床实践导致的系统缺失 (PSA 2018年前大部分缺失)，MICE 填补应在 era 分层下进行。Era 1 和 Era 2 的 PSA 缺失机制完全不同。
- **建议**: MICE 在 era 层内分别运行，或在 MICE 预测矩阵中包含 `era × year` 交互项。

---

## 6. 亚组分析建议

以下亚组具有明确的临床先验假设，建议纳入 SAP:

| 亚组 | 假设 | 分析类型 |
|------|------|---------|
| Age <70 vs ≥70 | 老年 M1 患者生存更差 | 分层 Cox |
| NHB vs NHW | NHB 可能在相同转移模式下生存更差 | 分层 Cox + 交互 |
| Era 1 vs Era 2 | Era 2 中内脏转移的惩罚效应减弱 | 交互检验 |
| ISUP 1-2 vs 3-5 | 高 ISUP 放大内脏转移的负面效应 | 交互检验 |
| Income Q1 vs Q4 | 低收入放大转移模式差异 (access to care) | 分层分析 |

---

*clinical-researcher (urology) — Phase 2 Round 1 独立意见*

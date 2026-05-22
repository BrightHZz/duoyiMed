---
type: methods
topic: 泌尿外科 ML 建模特殊考量
created: 2026-05-22
aliases: [Urology ML, 泌尿ML建模]
---

# 泌尿外科 ML 建模特殊考量

## 1. 生存分析（泌尿外科的最重要方法）

泌尿外科肿瘤研究中，**时间-to-event 结局**比二分类更常见和更有临床意义。

| 疾病场景 | 生存结局 | 推荐方法 | 竞争风险 |
|----------|---------|---------|----------|
| 前列腺癌根治术后 | BCR (Biochemical Recurrence) | Cox PH / RSF / DeepSurv | 非癌死亡 (老年患者) |
| 前列腺癌 | 癌症特异性生存 (CSS) | Cause-specific Cox / Fine-Gray | 其他原因死亡 |
| NMIBC | 首次复发时间 | Cox PH + Frailty (多次复发) | 进展为 MIBC / 死亡 |
| NMIBC | 进展至 MIBC | Fine-Gray (死亡为竞争事件) | 死亡 |
| 膀胱癌根治术后 | 总生存 (OS) | Cox PH / RSF | |
| 肾癌术后 | 无复发生存 (RFS) | Cox PH + 时变系数 | 非癌死亡 |
| 结石复发 | 首次/多次复发时间 | Cox PH + Frailty / AG model | 死亡 |
| BPH | 需要手术的时间 | Cox PH | 死亡 |

**方法选择指南**:
- 竞争风险存在且重要时 (>10% 竞争事件) → Fine-Gray subdistribution hazard 或 Cause-specific hazard
- 多次复发事件 → Frailty model / AG model (Andersen-Gill)
- 时变效应需检测 (Schoenfeld residuals)

## 2. 类别不平衡（泌尿肿瘤常见）

| 疾病 | 结局 | 典型不平衡比 | 策略 |
|------|------|------------|------|
| 前列腺癌 | BCR (根治术后) | 1:3 - 1:5 | class_weight + tuned threshold |
| 前列腺癌 | 淋巴结转移 | 1:5 - 1:10 | SMOTE (Pipeline 外!) + PR-AUC |
| NMIBC | 进展为 MIBC | 1:5 - 1:10 | PR-AUC 为主指标 |
| 结石 | RIRS 术后清石失败 | 1:3 - 1:5 | class_weight |
| 前列腺活检 | 阳性 vs 阴性 | 1:2 - 1:3 | 校准度尤其重要 |

**泌尿外科特殊考量**: 
- 假阴性代价高 (漏诊前列腺癌 → 延迟治疗)
- 假阳性代价：不必要的穿刺 → 感染、出血（但可控）
- 因此阈值选择倾向灵敏度

## 3. 影像特征融合

泌尿外科是影像学依赖度极高的学科。

| 影像学 | 应用场景 | 特征提取 | 融合方式 |
|--------|---------|---------|----------|
| CT (平扫) | 肾结石检测、成分预判 | PyRadiomics (纹理/形状) | Late fusion stacking |
| CT (增强) | 肾癌分期、膀胱癌分期 | 同上 + 增强特征 | Multimodal MLP |
| mpMRI | 前列腺癌 (PI-RADS) | 放射组学 + 深度学习 | 早期或晚期融合 |
| 超声 | 前列腺体积、肾积水 | 手工测量为主 | 作为临床变量 |
| IVP/CTU | 上尿路解剖 | 影像组学 | |

**PI-RADS (Prostate Imaging Reporting and Data System)**:
- v2.1 (2019) 标准：1-5 分级
- PI-RADS ≥ 3 → 建议穿刺
- ML 可辅助：PI-RADS 3 的升级/降级判断

## 4. 时间依赖性问题

| 问题 | 影响 | 处理 |
|------|------|------|
| PSA 筛查引入 (1980s 末) | 前列腺癌发病率"暴增" (lead time + overdiagnosis) | 控制诊断年份 |
| Gleason 分级更新 (2005/2014 ISUP) | 病理报告不可比 | 统一转换为 ISUP Grade Group |
| TNM 版本更迭 (AJCC 7th → 8th) | T 分期定义变化 | 使用统一版本或做 stage migration 分析 |
| 碎石技术演变 (ESWL→URS→PCNL→mini-PCNL) | 手术方式选择变化 | 分层分析或倾向评分 |
| BCG 短缺 (2019-) | 治疗模式被迫改变 | 控制治疗年代 |

## 5. 竞争风险 (Competing Risks)

老年泌尿患者（尤其前列腺癌/膀胱癌）的非癌死亡率高。

**判断是否需要竞争风险分析**:
```
死亡原因中非癌死亡占比
  < 10% → 传统 Cox PH 即可 (偏差 <5%)
  10-25% → Fine-Gray 或 Cause-specific Cox
  > 25% → 必须做竞争风险分析，否则 HR 严重偏倚
```

**典型场景**: 老年前列腺癌患者 (如 CHARLS 高龄队列)，10 年随访中非癌死亡 > 癌症死亡。

## 6. SEER 数据的特殊考量

- **Grace period 偏差**: SEER 中从诊断到治疗的信息不完整
- **分期信息**: SEER 使用 Collaborative Staging (2004-2017) 或 Derived AJCC
- **无生化复发 (BCR)**: SEER 没有 PSA 值，无法定义 BCR → 只能用 OS/CSS
- **无合并症**: 无 Charlson score → 无法调整基础疾病
- **2000-2018**: 足够长时间跨度，但需控制年代效应

---
type: concept
topic: 衰老生物标志物
created: 2026-05-22
aliases: [Aging Biomarkers, 衰老标志, Epigenetic Clocks, 生物年龄]
---

# 衰老生物标志物与衰老时钟

老年医学的核心问题：同年同月生的两个人，为什么一个"老得慢"、一个"老得快"？生物年龄 (Biological Age) 旨在捕捉这种差异。

## 衰老标志物分类 (Lopez-Otin 2013/2023 Hallmarks)

| 标志 | 测量方法 | ML 可用性 |
|------|---------|----------|
| 基因组不稳定性 | 突变负荷 | 少（需测序） |
| 端粒损耗 | qPCR (端粒长度) | CHARLS 部分 wave 有 |
| 表观遗传改变 | DNA 甲基化阵列 | 需要 Illumina 450K/EPIC |
| 蛋白质稳态丧失 | 蛋白质组 | 少（高端） |
| 线粒体功能障碍 | mtDNA 拷贝数 | 少 |
| 细胞衰老 | p16INK4a, SA-β-gal | 少 |
| 干细胞耗竭 | | 研究用 |
| 细胞间通讯改变 | 炎症因子 (IL-6/TNF-α/CRP) | **CHARLS 有血样** |
| 营养感应失调 | IGF-1, 胰岛素, 血糖 | **CHARLS 有** |
| 慢性炎症 (Inflammaging) | CRP, IL-6, WBC | **CHARLS 有** |
| 微生态失调 | 肠道菌群 | 少（队列中） |

## 主要衰老时钟

### 1. DNA 甲基化时钟 (Epigenetic Clocks)

| 时钟 | 年份 | CpG 数 | 训练组织 | 预测目标 |
|------|------|--------|---------|----------|
| Horvath Clock | 2013 | 353 | 51 种组织 | 实足年龄 |
| Hannum Clock | 2013 | 71 | 全血 | 实足年龄 |
| PhenoAge (Levine) | 2018 | 513 | 全血 | 表型年龄 (含临床变量) |
| GrimAge (Lu) | 2019 | 1030 | 全血 | 寿命/健康寿命 |
| DunedinPACE | 2022 | 173 | 全血 | 衰老速率 (纵向) |

**关键概念**:
- **AgeAccel** (年龄加速度) = 预测年龄 - 实足年龄
  - 正值 = "表观遗传学上比同龄人老"
  - 与全因死亡率、心血管、癌症、认知下降均独立相关
- **CHARLS 可用性**: CHARLS 2015 wave 有 DNA 甲基化数据 (~2000 人, EPIC 阵列)
- **局限性**: 中国人少 → 需要中国人群特异性时钟；费用高 → 不适合大规模临床使用

### 2. 基于临床变量的衰老时钟 (Phenotypic Clocks)

利用常规体检/血检变量预测生物年龄，无需表观遗传数据。

| 方法 | 变量 | 说明 |
|------|------|------|
| Klemera-Doubal Method (KDM) | 血压, 肺功能, 肌酐, CRP, Alb... | 经典方法，MLR 框架 |
| Homeostatic Dysregulation (HD) | 同上 | Mahalanobis 距离法 |
| ML-based Age Clocks | ~30-50 血液+体检 | XGBoost/NN 预测实足年龄 |

**CHARLS 可用变量** (构建表型时钟):
- 血液: CRP, Hb, WBC, PLT, 血糖, HbA1c, 总胆固醇, HDL, LDL, TG, 肌酐, BUN, 白蛋白
- 体检: SBP, DBP, 脉搏, BMI, 腰围, 肺功能 (PEAK flow)
- 功能: 握力, 步速, 椅子站立

### 3. 复合生物年龄 (Composite Biomarkers)

| 算法 | 输入 | 说明 |
|------|------|------|
| PhenoAge | 9 血液 + 实足年龄 | 死亡率预测优于甲基化 PhenoAge |
| BioAge (Belsky) | 18 生物标志物 | Dunedin 队列, 纵向校准 |
| FI (Frailty Index) | 30+ 缺陷 | 生物年龄的缺陷累积角度 |

## 衰老时钟在 ML 研究中的应用

1. **生物年龄作为结局变量**: X → predict → ΔAge (AgeAccel) → 识别加速衰老的风险因素
2. **生物年龄作为预测因子**: ΔAge → predict → 死亡率/发病/失能 (独立于实足年龄)
3. **衰老时钟作为 baseline**: ML 模型 vs 传统衰老时钟预测性能对比
4. **干预效果评估**: 干预前后 ΔAge 变化作为 surrogate endpoint

## CHARLS 构建生物年龄的实用方案

```
CHARLS 可用变量构建 KDM 生物年龄:
  Step 1: 选择参考群体 (健康子样本: 无慢性病, 无失能, 非吸烟)
  Step 2: 对每个生物标志物回归实足年龄 → 残差 = 该标志物偏离同龄健康的程度
  Step 3: 加权组合残差 → KDM 生物年龄
  Step 4: ΔAge = KDM 生物年龄 - 实足年龄
  Step 5: 用 ΔAge 预测死亡率/衰弱/失能 (外部验证)
```

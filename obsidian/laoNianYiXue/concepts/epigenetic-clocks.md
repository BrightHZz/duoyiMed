---
type: concept
topic: epigenetic_clocks
status: reference
last_updated: 2026-05-04
tags:
  - aging
  - epigenetics
  - biomarker
  - biological_age
---

# 表观遗传时钟 (Epigenetic Clocks)

## 定义
基于 DNA 甲基化水平预测生物年龄的算法模型。DNAm 年龄与实际年龄的差值称为**年龄加速 (Age Acceleration)**。

## 三代时钟

### 第一代：预测实际年龄
| 时钟 | 作者/年份 | CpG 数 | 组织 | 特点 |
|------|----------|--------|------|------|
| Horvath Clock | Horvath 2013 | 353 | 多组织 | 泛组织 (pan-tissue) |
| Hannum Clock | Hannum 2013 | 71 | 血液 | 血液专用 |

### 第二代：预测健康寿命/死亡率
整合了临床生物标志物，更关注生理衰老而非时序年龄：

| 时钟 | 作者/年份 | 特点 |
|------|----------|------|
| PhenoAge | Levine 2018 | 513 CpG + 9 临床变量，预测死亡率 |
| GrimAge | Lu 2019 | 1030 CpG + 7 血浆蛋白 + 吸烟包年，预测寿命 |
| GrimAge2 | Lu 2022 | GrimAge 的改进版 |

### 第三代：系统/器官特异性时钟
| 时钟 | 特点 |
|------|------|
| DunedinPACE | 衰老速率 (rate of aging)，非年龄预测 |
| 器官特异性时钟 | 心脏年龄、大脑年龄、肝脏年龄等 |

## 年龄加速 (Age Acceleration) 的计算
```
AgeAccel = DNAm_Age - Chronological_Age

正值 = 表观遗传年龄 > 实际年龄 = "加速衰老"
负值 = 表观遗传年龄 < 实际年龄 = "延缓衰老"

通常回归掉实际年龄:
AgeAccel_residual = residuals(lm(DNAm_Age ~ Chronological_Age))
```

## 临床应用潜力
- 死亡风险预测（GrimAge 表现最好）
- 衰弱/功能衰退预测
- 干预效果评估（如热量限制、运动对衰老速度的影响）
- 疾病风险分层

## 计算建模中的要点

### 构建新时钟的标准流程
1. 特征选择: Elastic Net / Boruta 对 CpG 位点降维（450K/850K → 100-500）
2. 模型训练: 5-fold nested CV（外环模型选择，内环超参调优）
3. 泛化验证: 外部独立队列 + 跨组织 + 跨人群
4. 生物学解释: GSEA/KEGG 通路富集 + Hallmarks of Aging 关联

### 关键陷阱
- **特征选择必须在 CV 内部进行**，否则信息泄露导致性能高估
- **批次效应**: 不同 450K/850K 芯片平台可能有系统偏差
- **细胞组分混杂**: 血液 DNAm 反映的是混合细胞信号，需调整细胞比例
- **性别差异**: DNAm 年龄的性别差异可能源于 X 染色体 CpG

## 可用数据源
- UK Biobank (部分样本有 850K 甲基化数据)
- GEO 公共数据库 (大量衰老相关甲基化数据集)
- CLHLS (部分样本有甲基化数据)

## 相关资源
- [[datasets/uk-biobank|UK Biobank]]
- [[methods/model-selection-guide|ML 模型选型]]
- [[concepts/frailty|衰弱]]

## 关键文献
- Horvath S. Genome Biology. 2013;14(10):R115.
- Levine ME et al. Aging. 2018;10(4):573-591.
- Lu AT et al. Aging. 2019;11(2):303-327.
- Belsky DW et al. eLife. 2022;11:e73420. (DunedinPACE)

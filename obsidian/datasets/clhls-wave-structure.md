---
type: reference
name: CLHLS Wave Structure
parent: clhls
tags:
  - longitudinal
  - wave_structure
  - clhls
---

# CLHLS 纵向 Wave 结构

## 设计概述

CLHLS 采用**入组队列 + 追踪至固定终点**的纵向设计。每个基线 wave 对应一个独立的 .sav 文件，其中包含该队列从基线到 2018 年的所有随访记录。数据为宽格式（wide format），不同 wave 的同一变量通过后缀/前缀区分。

## Wave 清单

| Wave | 基线入组 | 追踪终点 | .sav 文件大小 | 变量数 (估计) | 队列特征 |
|:---:|------|:---:|:---:|:---:|------|
| 1998 | 1998 | 2018 | 58.5 MB | ~2,000+ | 初始基线队列，追踪最长 |
| 2000 | 2000 | 2018 | 68.1 MB | ~2,000+ | 补充入组 |
| 2002 | 2002 | 2018 | 93.9 MB | ~2,000+ | 最大文件，含较多补充 |
| 2005 | 2005 | 2018 | 82.3 MB | ~1,800+ | |
| 2008 | 2008 | 2018 | 76.4 MB | ~1,500+ | 与 2008-2018 子集分开存储 |
| 2011 | 2011 | 2018 | 34.2 MB | ~1,000+ | |
| 2014 | 2014 | 2018 | 15.5 MB | ~800+ | 随访次数最少 |

## 纵向合并策略

### 方法 1: 按 ID 横向合并 (推荐)

```
ID (key) → 跨 wave 追踪同一受访者
```

每个 .sav 文件中有相同 ID 的受访者是同一个人。可提取各文件中的基线变量 + 各 wave 随访变量进行横向拼接。

### 方法 2: 使用 2018 横截面 + 回顾基线

2018 横截面数据集 (n=15,874) 包含了 2018 年存活的所有受访者，可通过 ID 回连纵向数据获取基线信息。

## 数据文件目录映射

```
D:\database\datasets\clhls\
├── CLHLS_dataset_1998-2005_SPSS/
│   ├── clhls_1998_2018_longitudinal_dataset_released_version1.sav
│   ├── clhls_2000_2018_longitudinal_dataset_released_version1.sav
│   ├── clhls_2002_2018_longitudinal_dataset_released_version1.sav
│   └── clhls_2005_2018_longitudinal_dataset_released_version1.sav
├── CLHLS_dataset_2008-2018_SPSS/
│   ├── clhls_2008_2018_longitudinal_dataset_released_version1.sav
│   ├── clhls_2011_2018_longitudinal_dataset_released_version1.sav
│   └── clhls_2014_2018_longitudinal_dataset_released_version1.sav
└── CLHLS_2018_cross_sectional_dataset_15874/
    └── clhls_2018_cross_sectional_dataset_15874.sav
```

## 分析注意事项

### 样本流失
- 高龄队列自然减员率高（死亡 + 失访）
- 1998 基线队列到 2018 仅少数存活（多为百岁老人）
- 建议分析时报告各 wave 的 at-risk 人数

### 代访问题
- 认知障碍或体弱受访者允许代访
- 代访变量需注意: 功能评估 (ADL/IADL) 可能来自代访人
- 建议敏感性分析中排除代访样本或进行分层

### 死亡竞争风险
- 高龄研究中死亡是主要竞争事件
- 分析功能衰退时应考虑死亡竞争风险（Fine-Gray / joint model）
- 逝者问卷（Deceased questionnaire）记录临终信息

### 时代效应
- 1998-2018 跨越 20 年，医疗条件和社会环境变化显著
- 不同 cohort 的可比性需关注时代效应
- 建议按 birth cohort (出生年代) 分层分析

## 推荐分析软件

| 语言 | 读取 .sav 的方式 |
|------|------|
| R | `haven::read_sav()` |
| Python | `pyreadstat.read_sav()` |
| Stata | `import spss` |
| SPSS | 直接打开 |

## 相关文档
- [[clhls|CLHLS 主页]]
- [[clhls-2018-analysis|2018 分析报告]]
- [[clhls-codebook|Codebook 使用说明]]
- [[clhls-questionnaires|2018 问卷]]

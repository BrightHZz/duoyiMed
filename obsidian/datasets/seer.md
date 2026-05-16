---
type: data_source
name: SEER
full_name: Surveillance, Epidemiology, and End Results Program
country: United States
age_range: all ages
sample_size: ~1,334,775 (prostate subset, 2000-2023)
time_range: 2000 - 2023
access: seer.cancer.gov 申请
url: https://seer.cancer.gov
status: available
local_path: D:\database\datasets\seer\openSave
data_format:
  raw: CSV (SEER*Stat export)
  dic: SEER*Stat dictionary (.dic)
last_updated: 2026-05-14
tags:
  - data_source
  - us
  - cancer
  - registry
  - oncology
  - prostate
---

# SEER — 美国癌症登记数据库

## 概述

美国 NCI 的 Surveillance, Epidemiology, and End Results (SEER) 数据库，覆盖约 48% 美国人口的癌症登记数据。本数据集聚焦 **前列腺癌 (Prostate Gland)**。

## 数据概况

| 属性 | 值 |
|------|-----|
| 数据库 | Incidence - SEER Research Data, 17 Registries, Nov 2025 Sub (2000-2023) |
| 关联数据 | County Attributes - Time Dependent (1990-2024) Income/Rurality, 1969-2024 Counties |
| 癌症部位 | Prostate gland（前列腺） |
| 记录数 | 1,334,775 |
| 变量数 | 247 (269 列含派生) |
| 文件格式 | CSV (逗号分隔，双引号包裹) |
| 主数据 | `export0514.csv` (3.7 GB, 1,334,775 行) |
| 变量字典 | `export0514.dic` (247 变量定义) |
| 测试子集 | `export0514_test.csv` (前50行) |
| 会话文件 | `Prostate gland.txt` (SEER*Stat 查询参数) |

## 核心优势（肿瘤学研究）

- **超大样本量**: 133万前列腺癌病例，统计效力极强
- **长期随访**: 2000-2023 诊断，中位生存 85 个月
- **多维度分期**: AJCC 3rd/6th/7th/8th 版 TNM、SEER 分期、EOD 分期全有
- **治疗信息完整**: 手术、放疗、化疗及治疗时间线
- **Gleason 评分**: 临床 + 病理 Gleason 评分（前列腺癌核心预后指标）
- **社会经济链接**: 收入中位数（通胀调整至2024）、城乡编码
- **生存数据**: 精确到天的生存时间 + 死因分类
- **多种族覆盖**: NHW/NHB/Hispanic/API/AIAN 分层

## 📁 本地文件结构

```
seer/
├── openSave/
│   ├── export0514.csv              # 主数据文件 (3.7 GB, 1,334,775 rows × 269 cols)
│   ├── export0514.dic              # SEER*Stat 字典文件 (变量定义)
│   ├── export0514_test.csv         # 测试子集 (前50行)
│   ├── export.dic                  # 早期导出字典
│   └── Prostate gland.txt          # SEER*Stat 会话文件 (查询参数)
├── tmpFile/                        # SEER*Stat 内部缓存 (312M)
└── userVari/                       # 用户自定义变量 (空)
```

## 变量分类

### 人口学 (Demographics)
| 变量 | 说明 |
|------|------|
| Age recode | 年龄段分组 (5岁一组) |
| Sex | 性别 (全部 Male) |
| Race recode | 种族 (White/Black/AI/API) |
| Origin recode NHIA | 西班牙裔来源 |
| Race and origin recode | 综合种族/来源 (NHW/NHB/NHAIAN/NHAPI/Hispanic) |
| Marital status at diagnosis | 诊断时婚姻状态 |
| Median household income | 家庭收入中位数 (通胀调整至2024) |
| Rural-Urban Continuum Code | 城乡连续编码 |

### 肿瘤特征 (Tumor Characteristics)
| 变量 | 说明 |
|------|------|
| Primary Site | 原发部位 (ICD-O-3) |
| Histologic Type | 组织学类型 |
| Behavior code | 行为编码 (恶性/原位/良性) |
| Grade | 分级 (包括 Gleason 评分) |
| PSA Lab Value | 前列腺特异性抗原 |
| Tumor Size | 肿瘤大小 |

### 分期系统 (Staging)
| 变量 | 说明 | 时间范围 |
|------|------|---------|
| Combined Summary Stage | 综合分期 | 2004+ |
| Summary stage 2000 | SEER 分期 | 1998-2017 |
| AJCC Stage Group 6th ed | AJCC 第6版 | 2004-2015 |
| AJCC Stage Group 7th ed | AJCC 第7版 | 2010-2015 |
| Derived EOD 2018 Stage | EOD 2018 分期 | 2018+ |
| SEER Cmb Stg Grp | SEER 综合分期 | 2016-2017 |

### 治疗 (Treatment)
| 变量 | 说明 | 时间范围 |
|------|------|---------|
| Surgery Primary Site | 原发灶手术 | 1998-2022 |
| Radiation recode | 放疗 | - |
| Chemotherapy recode | 化疗 (yes/no/unk) | - |
| Time to treatment (days) | 诊断到治疗天数 | - |

### 生存与死因 (Survival & Cause of Death)
| 变量 | 说明 |
|------|------|
| Survival months | 生存月数 (0-287) |
| Survival Days | 生存天数 |
| Vital status recode | 生命状态 |
| SEER cause-specific death | SEER 癌症特异性死亡分类 |
| COD to site recode | 死因部位编码 |

## 数据分布摘要

### 人口学分布
| 维度 | 分布 |
|------|------|
| **年龄** | Peak: 65-69 (21.6%), 60-64 (17.8%), 70-74 (17.6%); 中位 ~65-69 |
| **种族** | NHW 68.6%, NHB 14.2%, Hispanic 9.8%, NHAPI 5.2%, NHAIAN 0.4% |
| **婚姻** | Married 64.4%, Unknown 12.8%, Single 10.2%, Divorced 6.4%, Widowed 5.1% |

### 肿瘤特征
| 维度 | 分布 |
|------|------|
| **分期** | Localized 62.9%, Regional 10.5%, Distant 5.8%, Unknown/Unstaged 5.1% |
| **Gleason** | 6 (28.8%), 7 (33.9%), 8 (9.5%), 9-10 (9.2%), Unknown 10.4% |
| **PSA** | 大部分记录为 Blank (2018年之前不常规收集) |

### 治疗模式
| 治疗 | 比例 |
|------|------|
| **无手术/未知** | 59.2% (主动监测或非手术管理) |
| **根治性前列腺切除** | 27.3% (36.4万例) |
| **放疗** | 33.7% (含外照射 23.1%、近距离 5.6%、联合 3.8%) |
| **化疗** | 仅 1.2% (16,436例) |

### 生存分析
| 分期 | N | 中位生存(月) | P25 | P75 |
|------|---|-------------|-----|-----|
| Localized | 839,749 | 85 | 38 | 148 |
| Regional - direct extension | 115,773 | 89 | 41 | 151 |
| Regional - LN only | 8,971 | 42 | 17 | 86 |
| Regional - both | 15,118 | 56 | 26 | 97 |
| Distant | 76,732 | 21 | 8 | 42 |
| Unknown/Unstaged | 59,275 | 50 | 15 | 93 |

### 生命状态
| 状态 | 数量 | 比例 |
|------|------|------|
| Alive | 831,032 | 62.3% |
| Dead | 503,743 | 37.7% |
| — 死于前列腺癌 | 140,814 | 10.6% |
| — 死于其他原因 | 351,256 | 26.3% |
| — COD 未知 | 11,673 | 0.9% |

## 年份趋势

| 年份 | 病例数 | 年份 | 病例数 |
|------|--------|------|--------|
| 2000 | 51,365 | 2012 | 49,130 |
| 2001 | 53,382 | 2013 | 48,339 |
| 2002 | 54,990 | 2014 | 45,625 |
| 2003 | 50,970 | 2015 | 48,998 |
| 2004 | 51,932 | 2016 | 52,211 |
| 2005 | 50,433 | 2017 | 56,336 |
| 2006 | 55,750 | 2018 | 58,352 |
| 2007 | 59,277 | 2019 | 62,447 |
| 2008 | 56,325 | 2020 | 56,258 |
| 2009 | 56,998 | 2021 | 66,479 |
| 2010 | 55,914 | 2022 | 68,232 |
| 2011 | 56,779 | 2023 | 68,253 |

> 趋势：2000-2014 基本稳定 (45K-59K)，2014 后持续上升至 68K (2023)

## 使用注意事项

- **前列腺癌特异**: 本数据集仅含前列腺癌，其他癌种需另外导出
- **治疗编码复杂**: 手术/放疗编码值需对照 SEER 编码手册解读
- **版本差异**: 分期系统、分级系统随年份变化（2004/2010/2016/2018 多个断点）
- **PSA 数据**: 2018 年前大部分为 Blank
- **Gleason 评分**: 临床和病理评分分别存储，部分记录只有活检无手术病理
- **生存右删失**: Alive 患者生存时间为删失数据
- **健康志愿者偏倚**: 登记数据基于诊断，不代表一般人群发病率

## 相关资源

- SEER*Stat 软件: https://seer.cancer.gov/seerstat/
- SEER 变量文档: https://seer.cancer.gov/data-software/documentation/

## 关联

- [[datasets/seer-prostate|SEER 前列腺癌详细分析]]
- [[datasets/uk-biobank|UK Biobank]]
- [[datasets/charls|CHARLS]]

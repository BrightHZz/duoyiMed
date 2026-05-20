---
type: data_source
name: CLHLS
full_name: Chinese Longitudinal Healthy Longevity Survey
country: China
age_range: "≥65 (百岁老人超采样)"
sample_size: "~15,000+ (per wave)"
waves: "1998, 2000, 2002, 2005, 2008, 2011, 2014, 2018"
access: "官网申请 + DUA"
url: "https://opendata.pku.edu.cn"
status: available
last_updated: 2026-05-20
tags:
  - data_source
  - china
  - longevity
  - oldest_old
---

# CLHLS — 中国老年健康影响因素跟踪调查

## 概述
全球规模最大的高龄老人纵向调查，聚焦健康长寿的决定因素。百岁老人超采样，年龄跨度极大（65-120+）。1998年基线启动，至今已覆盖8个waves，20+年随访。

## 核心优势（老年医学研究）
- **高龄老人优势**: CHARLS 以 45-80 为主，CLHLS 补足了 80+ 尤其是百岁老人的数据缺口
- **长寿研究**: 独特的健康长寿表型数据
- **长期随访**: 1998 开始，已有 20+ 年跨度
- **临终数据**: 收集去世前信息（通过亲属）
- **基因数据**: 部分样本有 SNP 数据

## 关键变量
| 类别 | 内容 |
|------|------|
| 功能 | ADL (6项)、IADL (8项)、功能受限 |
| 认知 | MMSE（30项完整版） |
| 心理 | 自评健康、生活满意度、乐观 |
| 生活方式 | 吸烟、饮酒、饮食（频率）、体力活动 |
| 社会 | 婚姻、居住安排、社会参与 |
| 疾病 | 自报慢性病、用药 |
| 体格 | 血压（部分 waves） |
| 生物样本 | 血液/尿液（部分 waves，部分受访者） |

## 研究设计要点
- 基线: 1998
- 随访频率: 不固定（约 2-3 年间隔）
- 百岁老人超采样: 所有愿意参与的百岁老人均被纳入
- 失访追踪: 记录死亡日期和死因（通过家属/村医）
- 代访: 认知障碍或身体虚弱者可接受代访（需标注）

## 与 CHARLS 的互补
| 维度    | CHARLS             | CLHLS       |
| ----- | ------------------ | ----------- |
| 年龄    | 45+                | 65+ (百岁老人多) |
| 衰弱变量  | Fried phenotype 各项 | 功能、疾病、自评为主  |
| 体格检查  | 握力、步速、肺功能          | 有限（血压）      |
| 生物标志物 | 较丰富                | 有限          |
| MMSE  | 简化版                | 完整 30 项版    |
| 高龄代表  | 一般                 | 极佳          |

---

## 本地数据文件清单

> 数据根目录: `D:\database\datasets\clhls\`

### 纵向数据集 (SPSS .sav 格式)

| 基线 Wave | 文件名 | 大小 | 说明 |
|:---|------|:---:|------|
| 1998 | `CLHLS_dataset_1998-2005_SPSS/clhls_1998_2018_longitudinal_dataset_released_version1.sav` | 58.5 MB | 1998年入组，随访至2018 |
| 2000 | `CLHLS_dataset_1998-2005_SPSS/clhls_2000_2018_longitudinal_dataset_released_version1.sav` | 68.1 MB | 2000年入组，随访至2018 |
| 2002 | `CLHLS_dataset_1998-2005_SPSS/clhls_2002_2018_longitudinal_dataset_released_version1.sav` | 93.9 MB | 2002年入组，随访至2018 |
| 2005 | `CLHLS_dataset_1998-2005_SPSS/clhls_2005_2018_longitudinal_dataset_released_version1.sav` | 82.3 MB | 2005年入组，随访至2018 |
| 2008 | `CLHLS_dataset_2008-2018_SPSS/clhls_2008_2018_longitudinal_dataset_released_version1.sav` | 76.4 MB | 2008年入组，随访至2018 |
| 2011 | `CLHLS_dataset_2008-2018_SPSS/clhls_2011_2018_longitudinal_dataset_released_version1.sav` | 34.2 MB | 2011年入组，随访至2018 |
| 2014 | `CLHLS_dataset_2008-2018_SPSS/clhls_2014_2018_longitudinal_dataset_released_version1.sav` | 15.5 MB | 2014年入组，随访至2018 |

> 纵向数据设计: 每个 .sav 文件以对应年份为基线，包含该队列的纵向追踪数据直至 2018。使用 `ID` 变量进行跨 wave 合并。详见 [[clhls-wave-structure|Wave 结构文档]]。

### 横截面数据集

| 数据 | 文件名 | 大小 | 说明 |
|------|------|:---:|------|
| 2018 Cross-sectional | `CLHLS_2018_cross_sectional_dataset_15874/clhls_2018_cross_sectional_dataset_15874.sav` | 14.2 MB | 2018年横截面快照，n=15,874，761变量 |

> 详见 [[clhls-2018-analysis|CLHLS 2018 分析报告]]

### Codebook

| 文件 | 大小 | 对应数据 |
|------|:---:|------|
| `CLHLS_codebook 1998-2018/codebook_for_1998_2018_longitudinal_dataset.docx` | 1.13 MB | 1998 纵向队列 |
| `CLHLS_codebook 1998-2018/codebook_for_2000_2018_longitudinal_dataset.docx` | 1.11 MB | 2000 纵向队列 |
| `CLHLS_codebook 1998-2018/codebook_for_2002_2018_longitudinal_dataset.docx` | 1.02 MB | 2002 纵向队列 |
| `CLHLS_codebook 1998-2018/codebook_for_2005_2018_longitudinal_dataset.docx` | 0.87 MB | 2005 纵向队列 |
| `CLHLS_codebook 1998-2018/codebook_for_2008_2018_longitudinal_dataset.docx` | 0.69 MB | 2008 纵向队列 |
| `CLHLS_codebook 1998-2018/codebook_for_2011_2018_longitudinal_dataset.docx` | 0.50 MB | 2011 纵向队列 |
| `CLHLS_codebook 1998-2018/codebook_for_2014_2018_longitudinal_dataset.docx` | 0.42 MB | 2014 纵向队列 |
| `CLHLS_codebook 1998-2018/codebook_for_2018_cross_sectional_elderly.docx` | 0.24 MB | 2018 横截面 |

> 详见 [[clhls-codebook|Codebook 使用说明]]

### 问卷

| 文件 | 大小 | 语言 |
|------|:---:|:---:|
| `CLHLS_questionnaires2018/CLHLS-2017-2018_survivors_questionnaire.pdf` | 1.24 MB | English |
| `CLHLS_questionnaires2018/CLHLS-2017-2018_存活老人调查问卷.pdf` | 2.04 MB | 中文 |
| `CLHLS_questionnaires2018/CLHLS-2017-2018_Deceased questionnaire.pdf` | 0.42 MB | English |
| `CLHLS_questionnaires2018/CLHLS-2017-2018_死亡老人调查问卷.pdf` | 0.64 MB | 中文 |

> 详见 [[clhls-questionnaires|问卷文档]]

### 参考文档

| 文件 | 说明 |
|------|------|
| `CLHLS数据集简介 1998-2018.pdf` | 数据集简介（中文） |
| `中国老年健康调查及交叉学科研究简介 2020年3月.pdf` | 交叉学科研究介绍 2020 |
| `dataverse_files_bakj.zip` | 原始下载备份 (44.1 MB) |
| `MANIFEST.TXT` | 原始文件清单 |

### 总数据规模

| 维度 | 数值 |
|------|------|
| 总数据量 | ~455 MB (不含zip) |
| 纵向 .sav 文件 | 7 个 |
| 横截面 .sav 文件 | 1 个 |
| Codebook .docx | 8 个 |
| 问卷 PDF | 4 个 |

---

## 2018 Wave 实测数据 (n=15,874)

> 详见 [[clhls-2018-analysis|完整分析报告]]

| 指标 | 统计值 |
|------|--------|
| 年龄 | 85.5 ± 11.7 (50-117) |
| 女性 | 56.4% |
| 农村 | 44.7% |
| 文盲 | 50.4% |
| 高血压 | 42.9% |
| 多重共病 (≥2) | 33.6% |
| ADL 失能 | 25.1% |
| 吸烟 | 14.8% |
| BMI < 18.5 | 17.0% |
| SBP ≥ 140 | 44.5% |
| 过去一年跌倒 | 22.5% |

---

## 技术规格

| 项目 | 详情 |
|------|------|
| 数据格式 | SPSS .sav (可经 pyreadstat / haven 读取) |
| 编码 | 999/998/99 系列为缺失值 |
| 变量命名 | a1-a2 (人口), b (心理), c (认知), d (生活方式), e (功能), f (社会/经济), g (健康/体格) |
| 纵向合并键 | `ID` (受访者唯一标识) |
| Wave 标识 | 纵向数据以 `TRUEAGE`（实际年龄）和变量后缀区分 wave |

## 相关资源
- [[datasets/charls|CHARLS]]
- [[clhls-2018-analysis|CLHLS 2018 分析报告]]
- [[clhls-wave-structure|纵向 Wave 结构]]
- [[clhls-codebook|Codebook 使用说明]]
- [[clhls-questionnaires|2018 问卷文档]]
- [[concepts/frailty|衰弱]]

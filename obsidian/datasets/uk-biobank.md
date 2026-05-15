---
type: data_source
name: UK Biobank
full_name: UK Biobank
country: United Kingdom
age_range: "40-69 (baseline)"
sample_size: "~500,000"
waves: "Baseline 2006-2010, 持续随访"
access: "研究申请 (ukbiobank.ac.uk)"
url: "https://www.ukbiobank.ac.uk"
status: external
last_updated: 2026-05-04
tags:
  - data_source
  - uk
  - genetics
  - imaging
---

# UK Biobank

## 概述
全球最大的生物医学数据库之一，约 50 万英国参与者，含基因、影像、EHR 链接。

## 核心优势（老年医学研究）
- 极大样本量，适合开发与验证衰老时钟
- 基因组数据 (SNP array + WES/WGS 部分)
- 多模态影像 (脑 MRI、心脏 MRI、腹部 MRI、DEXA)
- 与 NHS EHR 链接（HES、GP、死亡登记、癌症登记）
- 丰富的生物标志物（血液生化、代谢组、蛋白质组部分）
- 表观遗传数据 (DNA 甲基化，部分样本)

## 关键变量
| 类别 | 内容 |
|------|------|
| 人口学 | 年龄、性别、种族、教育、TDI (社会经济剥夺) |
| 生活方式 | 吸烟、饮酒、饮食、体力活动（加速度计） |
| 体格 | BMI、腰臀比、血压、握力（部分）、肺功能 |
| 认知 | 反应时间、配对匹配、数字记忆等（有限） |
| 疾病 | 自报 + EHR 链接 (ICD-10) |
| 实验室 | 血常规、生化、HbA1c |
| 基因 | 全基因组 SNP + 部分 WES/WGS |
| 影像 | 多模态（脑/心/腹/DEXA/颈动脉） |
| 蛋白质组 | Olink (~3000 proteins, 部分样本) |
| 代谢组 | NMR (~250 metabolites, 大部分样本) |
| 甲基化 | 850K array (部分样本) |

## 使用注意事项
- **健康志愿者偏倚**: UKB 参与者比英国一般人群更健康（healthy volunteer bias）
- **年龄限制**: 基线 40-69，适合研究早期衰老，但 80+ 代表性不足
- **老年综合征**: 衰弱、功能评估的变量有限（非专门的老年队列）
- **费用**: 申请需付费（根据数据量和类型）
- **计算资源**: 数据量大，需充足的计算和存储资源

## 与 CHARLS/CLHLS 的互补
- UKB: 生物机制深度（基因+影像+组学）
- CHARLS/CLHLS: 老年表型丰富（衰弱、功能、认知评估全面）

## 关联
- [[datasets/charls|CHARLS]]
- [[datasets/clhls|CLHLS]]
- [[concepts/epigenetic-clocks|表观遗传时钟]]

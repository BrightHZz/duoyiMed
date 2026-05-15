---
type: data_source
name: CHARLS
full_name: China Health and Retirement Longitudinal Study
country: China
age_range: "≥45"
sample_size: "~17,000 (baseline)"
waves: "2011, 2013, 2015, 2018, 2020"
access: "官网申请 + DUA"
url: "https://charls.pku.edu.cn"
status: available
local_path: "/Users/wuyouhang/Documents/trae_projects/related to Sarcopenia/charls"
data_format: 
  raw: "Stata .dta (原始)"
  analysis: "CSV (analysis/ 目录下)"
codebook_path: "/Users/wuyouhang/Documents/trae_projects/related to Sarcopenia/charls/CHARLS_codebook"
last_updated: 2026-05-11
tags:
  - data_source
  - china
  - longitudinal
---

# CHARLS — 中国健康与养老追踪调查

## 概述
全国代表性的中老年纵向调查，覆盖 28 个省/自治区/直辖市，采用多阶段分层 PPS 抽样。

## 核心优势（老年医学研究）
- 全国代表性，可推广到中国中老年人群
- 丰富的老龄化相关变量：衰弱、认知、功能、经济
- 体格检查数据：握力、步速、血压、肺功能
- 生物标志物：血液样本（部分 waves）
- 与国际队列（HRS/ELSA）可联合分析

## 📁 本地文件结构

```
charls/
├── CHARLS_codebook/                  # 各波次问卷编码手册 (PDF)
│   ├── 2011_CHARLS_codebook.pdf
│   ├── 2013_CHARLS_Wave2_CodeBook.pdf
│   ├── 2015_CHARLS_2015_Codebook.pdf
│   ├── 2018_CHARLS_2018_Codebook.pdf
│   └── 2020_CHARLS_2020_Codebook.pdf
│
├── *.dta                             # 原始 Stata 数据文件 (5 waves)
│   ├── 2011_*.dta                    # Wave 1 (17 files)
│   ├── 2013_*.dta                    # Wave 2 (15 files)
│   ├── 2015_*.dta                    # Wave 3 (12 files)
│   ├── 2018_*.dta                    # Wave 4 (14 files)
│   └── 2020_*.dta                    # Wave 5 (9 files)
│
└── analysis/                         # 分析就绪数据 (CSV 格式)
    ├── *.csv                         # 77 个 CSV 文件 (含所有 waves)
    ├── charls_data_processor.py      # 数据预处理脚本
    └── inspect_headers.py            # 数据探查脚本
```

### 各 Wave 核心数据文件

#### Wave 1 — 2011 (基线)
| 文件 | 变量数 | 内容 |
|------|--------|------|
| `2011_demographic_background.dta` | | 人口学背景 |
| `2011_health_status_and_functioning.dta` | | **健康状态与功能** (核心) |
| `2011_health_care_and_insurance.dta` | | 医疗与保险 |
| `2011_biomarkers.dta` | | 体格检查 + 血压 |
| `2011_Blood_20140429.dta` | | 血液检测 |
| `2011_household_income.dta` | | 家庭收入 |
| `2011_family_information.dta` | | 家庭信息 |
| `2011_work_retirement_and_pension.dta` | | 工作与退休 |
| `2011_weight.dta` | | 抽样权重 |
| `2011_PSU.dta` | | 初级抽样单元 |

#### Wave 2 — 2013
| 文件 | 内容 |
|------|------|
| `2013_Demographic_Background.dta` | 人口学背景 |
| `2013_Health_Status_and_Functioning.dta` | **健康状态与功能** ← 含握力、步速 |
| `2013_Biomarker.dta` | 体格检查 + 血压 |
| `2013_Health_Care_and_Insurance.dta` | 医疗与保险 |
| `2013_Exit_Interview.dta` | 死亡退出访谈 |
| `2013_Weights.dta` | 抽样权重 |

#### Wave 3 — 2015
| 文件 | 内容 |
|------|------|
| `2015_Demographic_Background.dta` | 人口学背景 |
| `2015_Health_Status_and_Functioning.dta` | **健康状态与功能** |
| `2015_Biomarker.dta` | 体格检查 |
| `2015_Blood.dta` | 血液检测 |
| `2015_Weights.dta` | 抽样权重 |

#### Wave 4 — 2018
| 文件 | 内容 |
|------|------|
| `2018_Demographic_Background.dta` | 人口学背景 |
| `2018_Health_Status_and_Functioning.dta` | **健康状态与功能** |
| `2018_Cognition.dta` | 认知评估（独立文件） |
| `2018_Weights.dta` | 抽样权重 |

#### Wave 5 — 2020
| 文件 | 内容 |
|------|------|
| `2020_Demographic_Background.dta` | 人口学背景 |
| `2020_Health_Status_and_Functioning.dta` | **健康状态与功能** |
| `2020_COVID_Module.dta` | COVID 模块 |
| `2020_Exit_Module.dta` | 死亡退出 |
| `2020_Weights.dta` | 抽样权重 |

### Analysis 目录
- **77 个 CSV 文件**: 已从原始 .dta 转换为 CSV，可直接用 Python/R 读取
- `charls_data_processor.py`: 数据预处理脚本
- `inspect_headers.py`: 查看各文件表头/变量名

### 分析入口
对衰弱相关研究，核心文件是各 wave 的 **Health_Status_and_Functioning**：
- 2011: `2011_health_status_and_functioning.dta/csv`
- 2013: `2013_Health_Status_and_Functioning.dta/csv` ← 首次含握力、步速
- 2015: `2015_Health_Status_and_Functioning.dta/csv`
- 2018: `2018_Health_Status_and_Functioning.dta/csv`
- 2020: `2020_Health_Status_and_Functioning.dta/csv`

体格检查数据在 Biomarker 文件中，血液检测在 Blood 文件中。

## 关键变量（衰弱/功能相关）
| 变量类别 | 具体变量 |
|----------|----------|
| 衰弱 (Fried) | 体重下降、疲乏（CES-D）、握力、步速、体力活动 |
| 功能 | ADL (6项)、IADL (5项)、SPPB 相关、平衡测试 |
| 认知 | MMSE 类认知评估、词语回忆、画图 |
| 抑郁 | CES-D-10 |
| 社会 | 社会参与、社会支持、居住安排 |
| 生活方式 | 吸烟、饮酒、体力活动 |
| 慢病 | 14 种自报慢性病 |
| 体格 | BMI、血压、握力（测力计）、步速（计时行走）、肺功能 |
| 实验室 | 血红蛋白、CRP、HbA1c、总胆固醇、HDL、LDL、肌酐、胱抑素 C 等 |

## 研究设计要点
- 基线: 2011 (Wave 1)
- 随访频率: 每 2 年
- 代理受访: 认知障碍者可代理，需标注
- 失访: 追踪死亡信息（通过家属/村医）

## 跨 Wave ID 编码规则

CHARLS 的个人 ID 在不同 wave 之间遵循稳定的编码转换规则。

### 核心规则：末位前插 0

**2011 → 2013/2015/2018/2020 的 ID 转换：在末位数字前插入 `0`**

| Wave | ID 位数 | 示例 |
|------|--------|------|
| 2011 | 10 或 11 位 | `1010410101` (10位)、`10179110101` (11位) |
| 2013 | 11 或 12 位 | `10104101001` (11位)、`101791101001` (12位) |

转换公式（Python）:
```python
def convert_2011_to_2013(id_2011):
    """CHARLS 2011 ID → 2013 ID: 末位数字前插入 '0'"""
    return id_2011[:-1] + '0' + id_2011[-1:]

def convert_2013_to_2011(id_2013):
    """反向: 2013 ID → 2011 ID: 去掉倒数第二位 (即去掉插入的 '0')"""
    return id_2013[:-2] + id_2013[-1:]
```

### 匹配验证 (2011 ↔ 2013)

验证数据源: `2011_demographic_background.csv` × `2013_Demographic_Background.csv`

| 指标 | 数值 |
|------|------|
| 2011 总人数 | 17,705 (10位: 5,087 / 11位: 12,618) |
| 2013 总人数 | 18,605 (11位: 5,381 / 12位: 13,224) |
| 2011→2013 匹配成功 | **15,179 (85.7%)** |
| 2011 未匹配 (失访) | 2,526 (14.3%) — 死亡/拒绝/搬迁 |
| 2013 新增 (追访补充) | 3,426 (18.4%) — refresh sample |

#### 按 ID 长度分层

| 2011 ID 长度 | 匹配至 2013 对应长度 | 匹配率 |
|-------------|-------------------|--------|
| 10 位 | 11 位 | 4,391/5,087 (**86.3%**) |
| 11 位 | 12 位 | 10,788/12,618 (**85.5%**) |

### ID 结构解读

CHARLS 个人 ID 由以下层级编码组成：

```
[省] [社区] [家户] [个人]
 2位   3位    2-3位  1-2位
```

- 末位是家户内个人编号 (1=本人, 2=配偶, 3=父母等)
- 2011 部分省份样本量小, 只用 10 位 (家户号 2 位)
- 2013 统一在个人编号前补 `0` (实际效果是家户号从 2 位扩展为 3 位)

### 跨 Wave 纵向合并

```python
# 构建跨 wave 链接
df11['link_id'] = df11['ID'].astype(str).str[:-1] + '0' + df11['ID'].astype(str).str[-1]
df13['link_id'] = df13['ID'].astype(str)
merged = df11.merge(df13, left_on='link_id', right_on='link_id', suffixes=('_2011', '_2013'))
# 预期匹配: ~15,179 人
```

> 验证日期: 2026-05-11，基于本地 analysis/ 目录 CSV 文件分析

## 使用注意事项
- 握力测量从 2013 年开始，2011 无握力数据
- 步速测量在特定 waves 中
- 血液样本非全部受访者
- 代理受访者的认知数据不可直接与自报数据混合
- **跨 wave 合并时注意 ID 位数差异**，使用上述转换规则

## 相关文献
- [[literature/literature-dashboard|文献库]]

## 关联
- [[datasets/charls-variable-map|CHARLS 变量映射速查]]
- [[datasets/charls-ses-variables|CHARLS 社会经济变量映射]]
- [[datasets/clhls|CLHLS]]
- [[datasets/uk-biobank|UK Biobank]]
- [[concepts/frailty|衰弱]]

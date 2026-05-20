---
type: reference
name: CLHLS Codebook
parent: clhls
tags:
  - codebook
  - metadata
  - clhls
---

# CLHLS Codebook 使用说明

## 文件清单

> 路径: `D:\database\datasets\clhls\CLHLS_codebook 1998-2018\`

| 序号 | 文件名 | 大小 | 对应数据集 |
|:---:|------|:---:|------|
| 1 | `codebook_for_1998_2018_longitudinal_dataset.docx` | 1.13 MB | 1998 纵向队列 |
| 2 | `codebook_for_2000_2018_longitudinal_dataset.docx` | 1.11 MB | 2000 纵向队列 |
| 3 | `codebook_for_2002_2018_longitudinal_dataset.docx` | 1.02 MB | 2002 纵向队列 |
| 4 | `codebook_for_2005_2018_longitudinal_dataset.docx` | 0.87 MB | 2005 纵向队列 |
| 5 | `codebook_for_2008_2018_longitudinal_dataset.docx` | 0.69 MB | 2008 纵向队列 |
| 6 | `codebook_for_2011_2018_longitudinal_dataset.docx` | 0.50 MB | 2011 纵向队列 |
| 7 | `codebook_for_2014_2018_longitudinal_dataset.docx` | 0.42 MB | 2014 纵向队列 |
| 8 | `codebook_for_2018_cross_sectional_elderly.docx` | 0.24 MB | 2018 横截面 |

## 变量命名规则

CLHLS 变量按功能区组划分，前缀标识所属模块:

| 前缀 | 模块 | 示例变量 |
|:---:|------|------|
| `a` | 基本信息 (人口学) | `a1` 性别, `a2` 年龄, `a3` 民族 |
| `b` | 心理/自评 | `b1-1` 自评健康, `b31-b39` 情绪/抑郁, `b41-b48` 焦虑 |
| `c` | 认知功能 (MMSE) | `c11-c67` 30项 MMSE 完整版 |
| `d` | 生活方式 | `d1-d92` 吸烟/饮酒/饮食/锻炼 |
| `e` | 功能状态 | `e1-e14` ADL (6项) + IADL (8项) |
| `f` | 社会/经济/照护 | `f1-f2` 教育, `f5` 居住, `f141-f149` 社区服务 |
| `g` | 健康/体格/疾病 | `g15a1-g15t1` 15种慢性病, `g20-g123` 体格测量, `g511` 血压 |

## 缺失值编码

CLHLS 使用系列编码标记不同原因的缺失:

| 编码 | 含义 |
|:---:|------|
| `99` / `999` | 不适用 / 未知 |
| `998` | 拒绝回答 |
| `88` / `888` | 跳转 (skip pattern) |
| `9` | 缺失 |

> 分析前务必检查各变量的缺失值编码，尤其是条件跳转产生的结构缺失（非信息缺失）。

## Codebook 文档结构 (DOCX)

每个 codebook 文件包含:

1. **变量列表** — 变量名、标签、值标签
2. **频率分布** — 各变量的频数和百分比
3. **缺失值说明** — 各编码的含义
4. **跳转逻辑** — 条件跳转的规则说明（部分 waves）

## 跨 Wave 变量对应

同一变量在不同 wave 中可能通过以下方式区分:
- 变量后缀 (如 `_1998`, `_2000` 等)
- 在纵向 .sav 中以独立列出现
- 参考各 wave 的 codebook 确认具体命名

## 使用建议

1. **先查 2018 横截面 codebook** (`codebook_for_2018_cross_sectional_elderly.docx`) — 变量最全、最规范
2. **纵向分析时匹配对应 wave 的 codebook** — 早期 wave 可能缺少后期新增变量
3. **变量名可能随 wave 变化** — 同一概念在不同 wave 可能使用不同变量名
4. **Codebook 中标注的频率分布是原始数据** — 未排除缺失值

## 关键变量区组速查

| 研究主题 | 变量区组 | Wave 可用性 |
|------|------|:---:|
| 人口学 | a1-a2 | 全部 |
| MMSE 认知 | c11-c67 | 全部 (CLHLS 特色) |
| ADL | e1-e6 | 全部 |
| IADL | e7-e14 | 全部 |
| 慢性病 (15种) | g15a1-g15t1 | 全部 |
| 生活方式 (吸烟/饮酒) | d1-d92 | 全部 |
| 饮食频率 | d71-d91 | 2005+ |
| 血压 | g511-g123 | 部分 waves |
| 自评健康 | b1-1 | 全部 |
| 抑郁/情绪 | b31-b39 | 全部 |
| 社会参与 | f141-f149 | 2008+ |
| 跌倒 | g4c1-g4c3 | 2011+ |

## 相关文档
- [[clhls|CLHLS 主页]]
- [[clhls-wave-structure|纵向 Wave 结构]]
- [[clhls-2018-analysis|2018 分析报告]]

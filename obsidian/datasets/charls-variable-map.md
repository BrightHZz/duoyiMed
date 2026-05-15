---
type: data_source
name: CHARLS Variable Mapping
topic: charls_variable_reference
status: reference
last_updated: 2026-05-05
---

# CHARLS 变量映射速查

每个 wave 的 CSV 文件名和关键变量名。CSV 文件在 `analysis/` 目录下。

## 文件说明

每个 wave 的核心文件:
- `{wave}_Health_Status_and_Functioning.csv` — 健康状态与功能 (最常用, ~1220列)
- `{wave}_Biomarker.csv` — 体格检查: 握力、步速、血压、肺功能等 (~239列)
- `{wave}_Demographic_Background.csv` — 人口学
- `{wave}_Weights.csv` — 抽样权重

## Fried Phenotype 五项 — 变量名 (所有 wave)

| Fried 标准 | 变量名 | 所在文件 | 编码说明 |
|-----------|--------|----------|---------|
| 1. 体重下降 | `da049` | Health_Status_and_Functioning | 1=增加 2=下降 3=不变 |
| 2. 疲乏 | `dc011`, `dc012` | Health_Status_and_Functioning | CES-D: 1=很少 4=大部分时间 |
| 3. 握力下降 | `qc003`, `qc004`, `qc005`, `qc006` (4次握力测量) | **Biomarker** | 单位: kg, 取最大值。≥900=缺失码 |
| 4. 步速减慢 | `qg003` | **Biomarker** | 3m 步行时间(秒), 步速=3.0/qg003 |
| 5. 体力活动低 | `da050` (简化) 或 `da051_1_`, `da051_2_`, `da051_3_` | Health_Status_and_Functioning | da050=有/无活动(缺失<5%); da051=详细活动(67%跳题缺失) |

## 关键协变量

| 变量类别 | 变量名 | 所在文件 |
|----------|--------|----------|
| 年龄 | `da003` (出生年份推算) | Demographic_Background |
| 性别 | `xrgender` (或 `da002`) | Health_Status_and_Functioning |
| 身高(cm) | `qi002` | Biomarker |
| 体重(kg) | `ql002` | Biomarker |
| 腰围(cm) | `qm002` | Biomarker |
| ADL | `da005_*` 系列 | Health_Status_and_Functioning |
| 慢性病 | `da007_*` 系列 | Health_Status_and_Functioning |
| CES-D总分 | `dc009`~`dc018` | Health_Status_and_Functioning |
| 椅子站立 | `qh003` (5次站坐时间,秒) | Biomarker |
| 平衡测试 | `da013s1`, `da013s2`, `da013s3` | Health_Status_and_Functioning |

## ⚠️ 常见变量混淆

| 错误认知 | 正确含义 |
|----------|----------|
| `pg002`/`pl001` = 握力值 | ❌ 这些是测量完成状态标记 (1=完成) |
| `ql002` = 步速 | ❌ `ql002`=体重(kg), 步速变量是 `qg003` |
| `ql003` = 步速第2次 | ❌ 这是其他变量, 非步速 |

## 抽样权重

| 文件 | 关键变量 |
|------|----------|
| `{wave}_Weights.csv` | `INDV_weight` (个体权重) |

## 使用注意事项

1. **变量名编码**: CHARLS 使用字母+数字编码 (如 da049, dc011)
2. **跨 wave 变量名一致**: CHARLS 同一变量在不同 wave 中名称基本一致, 可直接复用映射
3. **后缀含义**: `_1_`, `_2_` 等后缀表示多选题的选项或重复测量
4. **缺失编码**: CHARLS 中缺失值通常为空字符串或特殊编码(.r/.d/.n等), CSV转换后通常为空
5. **Biomarker 数据量较少**: 体格检查仅对同意并能够完成的受访者测量, 缺失率约20-30%

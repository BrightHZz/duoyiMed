# 泌尿外科事业部 (Division of Urology)

## 事业部范围

负责泌尿外科领域的计算医学研究，聚焦泌尿系统疾病的预测、诊断和治疗决策支持。

核心研究方向：
- 肾结石/尿石症 (Kidney Stone/Urolithiasis) — 复发预测、成分分析、治疗决策
- 良性前列腺增生 (BPH/LUTS) — 进展预测、手术时机、IPSS 评分轨迹
- 前列腺癌 (Prostate Cancer) — 风险分层、生化复发预测、主动监测决策
- 膀胱癌 (Bladder Cancer) — NMIBC 复发预测、进展至 MIBC 风险
- 尿路感染 (UTI/Pyelonephritis) — 复杂 UTI 风险、抗生素耐药预测
- 肾上腺肿瘤 (Adrenal Tumor) — 功能性/恶性预测
- 肾癌 (Renal Cell Carcinoma) — 术后复发与生存预测

常用数据源：MIMIC-IV、SEER、NHANES (urology module)、Institutional EHR（所有公司数据源均可使用，不限事业部）

## Agent 列表

| Agent ID | 角色 | 核心职责 |
|----------|------|----------|
| `urology/pi` | 泌尿外科首席研究员 | FRAME 评估、期刊策略、质量终审 |
| `urology/clinical-researcher` | 泌尿临床研究员 | 临床问题操作化、泌尿疾病表型库、临床审查 |
| `urology/computational-biologist` | 泌尿计算生物学家 | Urology PICO-ML 映射、影像组学、风险预测方案 |

## 目标期刊矩阵

| 级别 | IF | 期刊 |
|------|-----|------|
| Tier 1 | >10 | European Urology, Lancet Oncology (urological cancers), JAMA Surgery |
| Tier 2 | 5-10 | Journal of Urology, BJU International, Prostate Cancer and Prostatic Diseases, World Journal of Urology |
| Tier 3 | 2-5 | Urology, International Urology and Nephrology, BMC Urology |

## 路由关键词

编排器根据用户输入中的关键词自动路由到本事业部:

- 肾结石, 尿石症, 输尿管结石, 膀胱结石, 肾结石复发
- kidney stone, urolithiasis, stone recurrence
- 前列腺, 前列腺增生, 前列腺癌, PSA, BPH, prostat*, TURP
- 膀胱癌, 膀胱肿瘤, NMIBC, MIBC, bladder cancer, cystectomy
- 泌尿, 尿道, 尿路, urology, urological
- 尿路感染, UTI, 肾盂肾炎, pyelonephritis, 尿脓毒症
- 肾上腺, 肾癌, 睾丸癌, 阴茎癌
- MIMIC-IV, SEER

## 知识库

Obsidian Vault: `{OBSIDIAN_HOME}/miNiaoWaiKe/`

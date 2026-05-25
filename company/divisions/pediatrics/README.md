# 儿科事业部 (Division of Pediatrics)

## 事业部范围

负责儿科领域的计算医学研究，聚焦儿童疾病的预测、诊断和治疗决策支持。

核心研究方向：
- 新生儿疾病 (Neonatal Diseases) — 早产儿并发症预测、新生儿败血症早期识别、NICU 死亡风险评估
- PICU 危重症 (Pediatric Critical Care) — 死亡率预测、机械通气撤机时机、脓毒症进展风险
- 儿童常见病 (Common Pediatric Diseases) — 肺炎严重度预测、哮喘急性加重风险、川崎病 IVIG 耐药预测
- 生长发育 (Growth & Development) — 生长迟缓早期筛查、肥胖代谢风险评估、青春期发育异常预测
- 先天性疾病 (Congenital Diseases) — 先天性心脏病筛查与预后、遗传代谢病早期识别
- 儿童感染性疾病 (Pediatric Infectious Diseases) — 手足口病重症化预测、脑膜炎病原学预测

常用数据源：PIC（浙江大学医学院附属儿童医院 PICU/NICU/CCU）、MIMIC-IV（儿科亚组）、NHANES（儿科模块）（所有公司数据源均可使用，不限事业部）

## Agent 列表

| Agent ID | 角色 | 核心职责 |
|----------|------|----------|
| `pediatrics/pi` | 儿科首席研究员 | FRAME 评估、期刊策略、质量终审 |
| `pediatrics/clinical-researcher` | 儿科临床研究员 | 临床问题操作化、儿科疾病表型库、年龄分层临床审查 |
| `pediatrics/computational-biologist` | 儿科计算生物学家 | Pediatrics PICO-ML 映射、时序模型、小样本学习方法 |

## 目标期刊矩阵

| 级别 | IF | 期刊 |
|------|-----|------|
| Tier 1 | >10 | JAMA Pediatrics, The Lancet Child & Adolescent Health |
| Tier 2 | 5-10 | Pediatrics, The Journal of Pediatrics, Archives of Disease in Childhood, Pediatric Critical Care Medicine |
| Tier 3 | 2-5 | European Journal of Pediatrics, BMC Pediatrics, Frontiers in Pediatrics |

## 路由关键词

编排器根据用户输入中的关键词自动路由到本事业部:

- 儿科, 儿童, 小儿, 新生儿, 婴幼儿, infant, child, pediatric
- PICU, NICU, 儿童重症, pediatric intensive care
- 早产儿, preterm, premature, neonatal
- PIC (浙江大学医学院附属儿童医院 PICU/NICU/CCU 数据库)
- 生长发育, growth, development, 儿童保健
- 先天性疾病, congenital, 出生缺陷
- 川崎病, Kawasaki, 手足口病, HFMD
- 儿童肺炎, pediatric pneumonia, 儿童哮喘, pediatric asthma
- 儿童感染, pediatric infection

## 知识库

Obsidian Vault: `{OBSIDIAN_HOME}/erKe/`

---
type: concept
topic: 泌尿外科评分系统
created: 2026-05-22
aliases: [Urology Scores, 泌尿评分, Nomograms]
---

# 泌尿外科常用评分与列线图

泌尿外科是医学中使用风险评分和列线图最广泛的学科之一。ML 模型必须与这些经典评分对比。

## 1. 肾结石相关

### STONE Score
- **用途**: 输尿管结石自行排出概率
- **5 变量**: Sex, Timing (onset), Origin (race), Nausea/vomiting, Erythrocytes (urine)
- **每项 0-3 分，总分 0-13**
- **AUC ~0.70-0.75**

### RUSS (Renal Urinary Stone Score)
- **用途**: 结石复杂程度量化
- **基于 CT**: 结石数量、位置、梗阻程度、解剖异常
- **用于预测 PCNL/URS 术后清石率**

### Guy's Stone Score
- **用途**: PCNL 术后结石清除率预测
- **Grade I-IV**，基于 CT 结石特征
- **Grade IV 清石率 ~30-40%；Grade I ~90%**

### S.T.O.N.E. Nephrolithometry
- **5 变量**: Stone size, Tract length, Obstruction, Number of calyces, Essence (density, HU)
- **用于 PCNL 术前规划**

## 2. 前列腺癌相关

### CAPRA Score (UCSF)
- **用途**: 前列腺癌根治术后生化复发 (BCR) 风险
- **变量**: PSA (0-4), Gleason (0-3), T stage (0-3), % positive biopsies (0-2), Age (0-1)
- **总分 0-10**: 0-2 低危 / 3-5 中危 / 6-10 高危
- **5 年 BCR**: 低危 ~10%, 高危 ~60%
- **AUC ~0.75-0.80**

### MSKCC Nomogram (Kattan Nomogram)
- **用途**: 前列腺癌根治术后 5/7/10 年 BCR 概率
- **经典列线图基准**，ML 模型必须对比

### Partin Tables
- **用途**: 术前预测病理分期 (器官局限/包膜外/精囊侵犯/淋巴结转移)
- **基于 PSA + Gleason + 临床 T 分期**

### PCPT (Prostate Cancer Prevention Trial) Risk Calculator
- **用途**: 前列腺活检阳性概率
- **变量**: PSA, DRE, Age, Race, Family history, Prior biopsy

## 3. BPH/LUTS

### IPSS (International Prostate Symptom Score)
- **用途**: LUTS 严重度量化 (金标准)
- **7 项症状 + 1 项生活质量**
- **分级**: 0-7 轻度 / 8-19 中度 / 20-35 重度

### BPH Impact Index (BII)
- **用途**: BPH 症状对生活质量的影响

## 4. 膀胱癌

### EORTC Risk Tables (NMIBC)
- **用途**: NMIBC 复发与进展风险
- **变量**: 肿瘤数量、大小、既往复发率、T 分期、CIS、Grade
- **1 年/5 年复发和进展概率**
- **AUC ~0.65-0.75** (ML 有机会超越)

### CUETO Scoring Model
- **用途**: BCG 灌注后 NMIBC 复发/进展 (补充 EORTC)

## 5. 肾癌

### SSIGN Score (Mayo Clinic)
- **用途**: 肾癌根治术后生存预测
- **变量**: TNM, tumor size, nuclear grade, necrosis
- **1/3/5/7/10 年 CSS (癌症特异生存)**

### UISS (UCLA Integrated Staging System)
- **用途**: RCC 风险分层
- **结合 TNM + Fuhrman Grade + ECOG PS**

### MSKCC/Motzer Criteria
- **用途**: 转移性 RCC 预后分层 (靶向治疗时代)
- **5 变量**: KPS, LDH, Hb, Ca, 确诊到治疗时间
- **低危/中危/高危** 三组

## ML 研究中的使用策略

1. **评分系统变量作为特征**: 评分中的组成变量经过大样本验证，直接纳入 ML 模型可提升性能
2. **Baseline 对比**: 新模型必须与经典评分/列线图对比 AUC（如 CAPRA/MSKCC/EORTC）
3. **NRI (Net Reclassification Improvement)**: 证明 ML 模型相比经典评分重新分类了多少患者
4. **决策曲线分析 (DCA)**: 证明 ML 模型能否在临床相关阈值范围内提供 Net Benefit 优于经典评分

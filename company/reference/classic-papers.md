# Classic Methodological Papers Registry

**用途**: 参考文献时效性检查时，此注册表中的论文自动豁免"近 5 年"要求。
**管理**: 新增经典论文需经 PI 审批后加入。每篇需注明豁免理由。

---

## 豁免规则

1. 被引论文在此注册表中 → `check_ref_recency` 自动从时效性计算中排除
2. 不在注册表中的旧文献 (>5年) → 必须在引用处标注 `[Classic — <理由>]` 或 `[Foundational — <理由>]`
3. 缺标注的旧文献 → Gate FAIL (需补充标注或替换为近5年文献)

---

## 预测模型与报告指南

| 论文 | 年份 | 豁免理由 |
|------|------|---------|
| TRIPOD Statement — Collins et al., BMJ 2015 | 2015 | 预测模型报告标准，不可替代 |
| TRIPOD+AI — Collins et al., BMJ 2024 | 2024 | (近5年内，天然达标) |
| PROBAST — Wolff et al., Ann Intern Med 2019 | 2019 | 预测模型偏倚风险评估工具 |
| STROBE Statement — von Elm et al., Lancet 2007 | 2007 | 观察性研究报告标准 |
| PRISMA 2020 — Page et al., BMJ 2021 | 2021 | 系统综述报告标准 |
| CONSORT 2010 — Schulz et al., BMJ 2010 | 2010 | RCT 报告标准 |
| REMARK Guidelines — McShane et al., JNCI 2005 | 2005 | 肿瘤标志物预后研究报告指南 |

## 流行病学与统计方法

| 论文 | 年份 | 豁免理由 |
|------|------|---------|
| Charlson Comorbidity Index — Charlson et al., J Chronic Dis 1987 | 1987 | 合并症指数原始论文 |
| CCI ICD-10 adaptation — Quan et al., Med Care 2005 | 2005 | CCI 的 ICD-10 编码适配 |
| CCI ICD-9-CM adaptation — Deyo et al., J Clin Epidemiol 1992 | 1992 | CCI 的 ICD-9 编码适配 |
| LASSO — Tibshirani, JRSSB 1996 | 1996 | 方法学奠基论文 |
| XGBoost — Chen & Guestrin, KDD 2016 | 2016 | XGBoost 原始论文 |
| Random Forest — Breiman, Machine Learning 2001 | 2001 | 随机森林原始论文 |
| SHAP — Lundberg & Lee, NeurIPS 2017 | 2017 | SHAP 可解释性原始论文 |
| MICE — van Buuren & Groothuis-Oudshoorn, J Stat Soft 2011 | 2011 | 多重插补方法论文 |
| DeLong test — DeLong et al., Biometrics 1988 | 1988 | AUC 比较统计检验 |
| Hosmer-Lemeshow — Hosmer et al., 1980/2013 | 1980 | 校准度检验（注意局限性） |
| Fine-Gray model — Fine & Gray, JASA 1999 | 1999 | 竞争风险模型 |
| Net Reclassification — Pencina et al., Stat Med 2008 | 2008 | NRI 方法论文 |
| Decision Curve Analysis — Vickers & Elkin, Med Decis Making 2006 | 2006 | DCA 方法论文 |

## 老年医学 / 衰弱

| 论文 | 年份 | 豁免理由 |
|------|------|---------|
| Fried Frailty Phenotype — Fried et al., J Gerontol A 2001 | 2001 | 衰弱表型定义原始论文，不可替代 |
| Rockwood Frailty Index — Mitnitski et al., 2001 / Rockwood et al., 2005 | 2001-2005 | 衰弱指数定义 |
| SARC-F — Malmstrom et al., JAMDA 2013 | 2013 | 肌少症筛查工具原始论文 |
| EWGSOP Sarcopenia — Cruz-Jentoft et al., Age Ageing 2010/2019 | 2010 | 肌少症诊断共识 |
| AWGS Sarcopenia — Chen et al., JAMDA 2014/2020 | 2014 | 亚洲肌少症共识 |
| MMSE — Folstein et al., J Psychiatr Res 1975 | 1975 | 认知筛查量表原始论文 |
| GDS-15 — Sheikh & Yesavage, 1986 | 1986 | 老年抑郁量表原始论文 |
| Katz ADL — Katz et al., JAMA 1963 | 1963 | ADL 量表原始论文 |
| Lawton IADL — Lawton & Brody, Gerontologist 1969 | 1969 | IADL 量表原始论文 |

## 泌尿外科

| 论文 | 年份 | 豁免理由 |
|------|------|---------|
| D'Amico Risk Classification — D'Amico et al., JAMA 1998 | 1998 | 前列腺癌风险分层原始定义 |
| CAPRA Score — Cooperberg et al., J Urol 2005 | 2005 | 前列腺癌术前风险评估 |
| Gleason Grading — Gleason, 1966 / Epstein et al., 2016 | 1966-2016 | 前列腺癌病理分级 |
| AJCC Staging 8th Ed — Amin et al., CA Cancer J Clin 2017 | 2017 | 癌症分期标准 |
| EAU Guidelines Prostate Cancer — Mottet et al., 2021+ | 2021+ | 欧洲泌尿外科学会指南 |
| Clavien-Dindo Classification — Dindo et al., Ann Surg 2004 | 2004 | 手术并发症分级 |

## 数据库 / 数据源

| 论文 | 年份 | 豁免理由 |
|------|------|---------|
| MIMIC-IV — Johnson et al., Sci Data 2023 | 2023 | 数据库原始论文 (近5年内) |
| MIMIC-III — Johnson et al., Sci Data 2016 | 2016 | 数据库原始论文 |
| CHARLS — Zhao et al., Int J Epidemiol 2014 | 2014 | 中国健康与养老追踪调查基线论文 |
| SEER Program — Hankey et al., 1999 / NCI ongoing | 1999+ | 癌症登记项目描述 |
| GLOBOCAN — Sung et al., CA Cancer J Clin 2021 | 2021 | 全球癌症统计 |

## 数据库实现

| 论文 | 年份 | 豁免理由 |
|------|------|---------|
| scikit-learn — Pedregosa et al., JMLR 2011 | 2011 | 机器学习库原始论文 |
| pandas — McKinney, 2010 | 2010 | 数据处理库 |
| Python — van Rossum, 1991+ | 1991+ | 编程语言 |
| R — R Core Team, annual | ongoing | 统计计算环境 |

---

## 标注格式 (不在注册表中的旧文献)

引用不在本注册表中的 >5 年文献时，必须在 References 章节使用以下标注格式：

```
[Classic — <领域>: <豁免理由>]

例:
1. Author A, et al. Title. Journal. 2018.
   [Classic — epidemiology: first population-based prevalence estimate of X in China]

2. Author B, et al. Title. Journal. 2015.
   [Foundational — statistics: introduced the weighted estimator used in primary analysis]
```

标注必须包含:
- **领域标签**: epidemiology / statistics / clinical / methodology / database
- **具体理由**: 为什么这篇旧文献不可替代（如：original definition / first estimate / method introduction）

禁止的模糊理由: "important paper" / "well-known" / "seminal work" / "widely cited"

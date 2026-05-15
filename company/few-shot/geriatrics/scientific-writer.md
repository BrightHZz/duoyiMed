# Few-Shot 示例 — Scientific Writer Agent

## Example 1: DOI 验证

### Input
```
参考文献列表已定稿 (35条)。投稿前请验证所有 DOI。
```

### Reasoning
```
1. 从参考文献中提取所有 DOI
2. 调用 verify_all_dois 批量验证
3. 分类处理: valid 保留, fake 标注, 书籍标注 no-DOI
4. 生成验证报告
```

### Output
```markdown
## DOI 验证 — 执行中

→ 调用 verify_all_dois({"dois": ["10.1093/gerona/56.3.M146", ...35条]})

结果:
  31/32 verified real ✅
  1 FAKE ⚠️ — Zhang 2025 doi:10.1007/s11357-025-xxxxx (占位DOI)
  3 no DOI — 会议论文/书籍

处理:
- Zhang 2025 → 标记 [DOI pending verification]
- Chen 2016 (XGBoost) → 标注 [Conference paper, no DOI]
- Steyerberg 2019 → 标注 [Book, no DOI]

验证报告已保存至 checklists/doi-verification.md
通过: 31 条确认实存, 1 条待补, 3 条合理无DOI
```

---

## Example 2: 将分析结果写成 Results 初稿

### Input

```
任务: 基于以下分析结果, 撰写 Results 和 Discussion 初稿

研究: CHARLS 衰弱转换预测, 目标期刊 GeroScience

数据:
  - N=5,432 (60+, 基线非衰弱) 
  - 2年衰弱恶化率: 26.3% (1,428/5,432)
  - 平均年龄 68.4±6.2, 女性 52.1%

模型结果:
  - XGBoost AUC=0.84 (95% CI 0.82-0.86), Brier=0.14
  - LASSO AUC=0.79 (95% CI 0.77-0.81), Brier=0.17
  - LogReg (age+sex) AUC=0.68

Top 5 SHAP: 步速(0.32), 年龄(0.29), 慢性病数(0.21), 
握力(0.19), 白蛋白(0.15)

亚组: 性别差异不显著 (交互p=0.34)
      年龄组: AUC 60-69: 0.83, 70-79: 0.85, 80+: 0.81
  
时间验证 (2015→2018): AUC=0.82

校准: calibration slope 0.92, 高风险区间 slight underestimation

请撰写 Results + Discussion + 确定论文 Title。
```

### Reasoning (Chain of Thought)

```
1. Title: 遵循"方法 + 预测什么 + 数据 + 研究类型"公式
2. Results: 按 TEXT-TABLE-FIGURE 原则组织
   - 先人群描述
   - 再主要发现 (给 AUC + CI)
   - 再特征重要性
   - 再亚组/敏感性
3. Discussion: 七段式 (默认无小标题, 空行分隔, JAMA+BMJ 对齐)
   - 核心发现 → 机制解释 → 文献一致 → 文献不一致 → 临床含义 → 优势 → 局限+未来方向
4. Conclusion: 独立章节, 与 Introduction ¶3 镜像呼应
```

### Output

```markdown
## Title

**Machine Learning Predicts 2-Year Frailty Worsening in Community-Dwelling 
Older Adults: A Prospective Study in the CHARLS Cohort**

备选:
- "XGBoost Outperforms Logistic Regression for Predicting Frailty 
   Transitions in CHARLS" (更强的方法学重点)

---

## Results

### Study Population
After excluding 973 participants with baseline frailty (Fried score ≥3), 
312 with severe cognitive impairment (MMSE <18), and 1,486 lost to follow-up, 
5,432 participants (mean age 68.4 ± 6.2 years, 52.1% female) were included 
in the primary analysis. During the 2-year follow-up, 1,428 participants 
(26.3%) experienced frailty worsening (Table 1). Compared with participants 
who remained stable, those who worsened were older (70.1 vs 67.3 years, 
SMD=0.32), had lower gait speed (0.72 vs 0.89 m/s, SMD=0.41), and had 
more chronic conditions (2.8 vs 1.9, SMD=0.35).

### Model Performance
The XGBoost model achieved an AUC of 0.84 (95% CI 0.82–0.86) for 
predicting 2-year frailty worsening, significantly outperforming both 
LASSO logistic regression (AUC 0.79, 95% CI 0.77–0.81; DeLong test 
p=0.002) and the baseline age-and-sex model (AUC 0.68) (Figure 1). 
The XGBoost model demonstrated good calibration (Brier score 0.14, 
calibration slope 0.92), with slight risk underestimation in the 
highest predicted probability range (predicted risk >0.6) (Figure 2).

### Feature Importance
SHAP analysis identified gait speed (mean |SHAP| = 0.32), age (0.29), 
number of chronic conditions (0.21), grip strength (0.19), and serum 
albumin (0.15) as the five most important predictors (Figure 3). 
Functional measures (gait speed and grip strength) collectively 
accounted for 31% of the model's predictive power, followed by 
demographic (24%), clinical (22%), and laboratory (12%) features.

### Subgroup and Sensitivity Analyses
Model performance was consistent across age subgroups (AUC 60–69: 0.83, 
70–79: 0.85, ≥80: 0.81) and between sexes (male: 0.83, female: 0.84; 
interaction p=0.34). In temporal validation (2015→2018 wave), the model 
maintained robust discrimination (AUC 0.82, 95% CI 0.80–0.84). Sensitivity 
analyses using complete-case analysis (AUC 0.83), Frailty Index as an 
alternative outcome (AUC 0.81), and including death as a competing risk 
(subdistribution AUC 0.82) yielded consistent results (Supplementary Table S3).

---

## Discussion

In this prospective study of 5,432 community-dwelling Chinese older adults, 
we developed and validated a machine learning model that predicted 2-year 
frailty worsening with good discrimination. Functional measures—particularly 
gait speed and grip strength—were the dominant predictors, contributing 
nearly one-third of the model's total predictive power.

The strong predictive contribution of physical performance measures likely 
reflects their role as integrative markers of multiple physiological systems. 
Gait speed, in particular, captures neuromuscular, cardiorespiratory, and 
sensory function simultaneously. An alternative explanation is that self-
reported chronic conditions—the other major predictor category—may be 
under-measured in CHARLS, inflating the relative importance of objective 
physical measures.

Our finding that functional measures dominate frailty prediction is consistent 
with Fried et al. [1], who identified gait speed and grip strength as core 
components of the frailty phenotype, and with Hoogendijk et al. [5], who 
reported similar SHAP rankings in a Dutch cohort. The moderate discrimination 
(AUC ~0.84) also aligns with the range reported in a recent meta-analysis [12].

However, in contrast to Chen et al. [8], who found that laboratory biomarkers 
(albumin, CRP) contributed more than physical measures, our model assigned 
substantially less weight to laboratory features. This discrepancy may reflect 
differences in variable availability—CHARLS lacks inflammatory markers like 
IL-6 that might capture systemic processes more directly than albumin alone. 
Population differences (Chinese vs. European) in the prevalence of 
inflammation-driven frailty may also contribute.

If externally validated, gait-speed-based risk stratification could help 
clinicians in community health settings identify older adults who may benefit 
from targeted preventive interventions, because gait speed was the single 
strongest predictor (SHAP = 0.32) and is measurable without specialized 
equipment, supported by Studenski et al. [15] who demonstrated gait speed 
as a robust predictor of adverse outcomes in pooled cohort data. However, 
this model predicts risk—it does not identify causal intervention targets—
and functional measures may be markers of underlying processes rather than 
modifiable risk factors themselves.

Strengths of this study include the use of a nationally representative Chinese 
cohort with complete 2-year follow-up, rigorous nested cross-validation with 
temporal validation, and comprehensive SHAP-based interpretability analysis.

This study has limitations. First, the observational design precludes causal 
inference—the associations identified may reflect confounding rather than 
etiologic relationships, although we adjusted for measured confounders and 
results were consistent across sensitivity analyses. Second, the model lacks 
external validation in independent cohorts, which limits assessment of 
transportability to other populations or healthcare settings. Third, 
grip strength was unavailable in the 2011 CHARLS wave for sensitivity 
analysis, potentially overestimating gait speed's relative importance. 
External validation in an independent Chinese cohort and in non-Chinese 
populations is needed to confirm these findings and assess transportability 
before clinical implementation.

## Conclusion

A machine learning model incorporating routinely available clinical and 
functional measures predicted 2-year frailty worsening with good 
discrimination in community-dwelling Chinese older adults. Functional 
performance emerged as the dominant predictor, supporting the central 
role of physical assessment in frailty risk stratification.
```

---

## Example 3: 从 SAP 和上游数据撰写 Methods

### Input

```
任务: 基于以下上游产出, 撰写 Methods 章节

上游 SAP (biostatistician 产出, 内部工作文档):
### 1. 研究设计概览
- 设计类型: 前瞻性队列
- 数据来源: CHARLS 2011-2018
### 2. 样本量与功效
- 目标功效: 0.80, 最终 N=5,432
### 3. 基线特征描述
- 正态性检验: Shapiro-Wilk
### 4. 主要分析
- 模型: XGBoost, LASSO, Logistic Regression
- 缺失处理: MICE (m=10, 假设 MAR)
### 5. 模型评估
- AUC-ROC, Brier Score, Calibration
### 6. 亚组分析
- 年龄组, 性别, 交互检验
### 7. 敏感性分析
- CCA, Frailty Index 替代结局, 竞争风险
### 8. 软件
- Python 3.12, scikit-learn 1.5

⚠️ 注意: 上游 SAP 有 8 个 ### 标题, 但这是内部工作文档结构,
不代表论文 Methods 的章节组织。
论文 Methods 应只有 5 个 ### 子标题。
```

### Reasoning (Chain of Thought)

```
1. SAP 的 8 个 ### 标题是工作文档结构, 不能直接映射为论文 Methods 子标题
2. 论文 Methods 标准 5 个子标题:
   - Study Design and Setting ← 合并 SAP §1 (设计类型+数据来源+报告指南)
   - Study Population ← 合并 SAP §2 (纳入排除+样本量+流程图)
   - Outcomes and Predictors ← 结局定义+预测因子+CHARLS 变量名
   - Statistical Analysis ← 合并 SAP §3/4/5/8 (正态性+缺失+模型+评估+软件)
   - Sensitivity Analysis ← 对应 SAP §7
3. SAP §6 (亚组) 属于 Statistical Analysis 的二级内容, 不独立成节
4. 不写 "### 1. 研究设计概览" / "### 2. 样本量" / "### 3. 基线特征" 等 SAP 标题
```

### Output

```markdown
## Methods

### Study Design and Setting
This was a prospective cohort study using data from the China Health and 
Retirement Longitudinal Study (CHARLS) waves 2011–2018. CHARLS is a nationally 
representative longitudinal survey of Chinese adults aged ≥45 years. The study 
followed the TRIPOD+AI reporting guideline for prediction model development.

### Study Population
We included participants aged ≥60 years at baseline (2011 wave) who were 
non-frail (Fried frailty phenotype score <3). Exclusion criteria were: 
severe cognitive impairment (MMSE <18), missing frailty assessment at baseline, 
and loss to follow-up at the 2013 wave. After applying these criteria, 
5,432 participants were included in the primary analysis (Figure 1).

### Outcomes and Predictors
The primary outcome was 2-year frailty worsening, defined as an increase in 
Fried frailty phenotype score between the 2011 and 2013 waves. Candidate 
predictors included demographics (age, sex), functional measures (gait speed 
[CHARLS variable da049], grip strength), clinical variables (number of chronic 
conditions, depressive symptoms [CES-D]), and laboratory measures (serum albumin).

### Statistical Analysis
Normality of continuous variables was assessed using the Shapiro-Wilk test. 
Missing data (8.2% of observations) were handled using multiple imputation by 
chained equations (MICE) with m=10 imputations under the missing-at-random 
(MAR) assumption. We trained three models: XGBoost, LASSO logistic regression, 
and a baseline age-and-sex logistic regression model. Feature selection was 
performed using LASSO with 5-fold cross-validation. Hyperparameters were tuned 
via Bayesian optimization within nested cross-validation. Model performance 
was assessed via 5-fold cross-validation, reporting AUC-ROC (with 95% CI 
via DeLong's method), Brier score, and calibration slope. Subgroup analyses 
were conducted by age group (60–69, 70–79, ≥80) and sex, with interaction 
terms tested for significance. All analyses were performed using Python 3.12 
with scikit-learn 1.5 and XGBoost 2.0.

### Sensitivity Analysis
We conducted three pre-specified sensitivity analyses: (1) complete-case 
analysis to assess the impact of missing data assumptions; (2) using the 
Frailty Index as an alternative outcome definition; and (3) Fine-Gray 
competing risk regression treating death as a competing event.
```

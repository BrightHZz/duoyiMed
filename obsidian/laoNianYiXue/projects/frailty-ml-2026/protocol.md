---
type: protocol
project: "[[project-brief|衰弱预测项目]]"
status: draft
last_updated: 2026-05-04
---

# 研究方案: ML 预测 CHARLS 衰弱转换

## 1. 研究设计与数据

### 设计
前瞻性队列研究，使用 CHARLS 2011-2018 纵向数据。

### 数据源
[[../../datasets/charls|CHARLS]] — China Health and Retirement Longitudinal Study

### 预测窗口
基线评估 → 2 年后的随访评估
- 训练: Wave1 (2011) → Wave2 (2013)
- 时间验证: Wave3 (2015) → Wave4 (2018)

## 2. 研究人群

### 纳入标准
- CHARLS Wave 1 参与者
- 年龄 ≥ 60 岁（基线）
- Fried Phenotype 各组成项数据完整（或可接受缺失）
- 2 年后完成衰弱评估

### 排除标准
- 基线已衰弱（Fried ≥3）— 仅研究衰弱恶化，不研究衰弱改善
- 基线严重认知障碍（MMSE <18，代理受访）
- 基线 ADL 严重依赖（≥3 项需要帮助）
- 2 年内失访且无死亡信息（注：死亡患者暂排除，后续作为敏感性分析）

### 预期样本量
CHARLS Wave1 约 17,000 → 60+ 岁约 8,000-9,000 → 数据完整约 5,000-7,000

## 3. 结局变量

### 主要结局
2 年衰弱状态恶化（Fried Phenotype 总分增加 ≥1）
- 编码: 1 = 恶化, 0 = 稳定/改善

### 次要结局
- 衰弱发病率（基线健壮 → 2 年后衰弱）
- 衰弱转换的多分类（改善/稳定/恶化）

## 4. 预测因子（~80 个候选）

| 类别 | 变量数 | 具体变量 |
|------|--------|----------|
| 人口学 | 6 | 年龄、性别、教育、婚姻、居住地（城乡）、独居 |
| 临床 | 15 | 高血压、糖尿病、心脏病、卒中、COPD、关节炎、肾病、癌症、消化疾病、哮喘、血脂异常、肝病、抑郁史、多重用药(≥5)、自评健康 |
| 功能 | 8 | ADL 依赖项数、IADL 依赖项数、步速(m/s)、握力(kg)、SPPB 相关、平衡、坐站 |
| 认知 | 5 | MMSE 总分、时间定向、词语即时回忆、词语延迟回忆、画图 |
| 心理 | 5 | CES-D-10 总分、抑郁情绪、积极情绪、生活满意度、孤独 |
| 社会 | 5 | 社会参与频率、社会支持、婚姻满意度、经济满意度、医疗保险 |
| 生活方式 | 5 | 吸烟、饮酒、体力活动频率、睡眠时长、BMI |
| 实验室(子集) | 10 | Hb、CRP、HbA1c、总胆固醇、HDL、LDL、TG、肌酐、胱抑素C、白蛋白 |
| 其他 | ~20 | 疼痛、视力、听力、跌倒史、住院史、门诊次数等 |

## 5. 统计方法

### 缺失数据处理
- 主分析: MICE (m=10, 假设 MAR)
- 敏感性: 完整案例分析

### 模型开发
- 基线: Logistic Regression + LASSO
- 主模型: XGBoost (超参: Bayesian Optimization)
- 特征选择: Elastic Net (在 CV 内执行)

### 验证
- 内部: 10-fold nested CV (外环评估，内环调参)
- 时间验证: Wave1→2 训练，Wave3→4 评估

### 评估指标
- 区分度: AUC-ROC, AUC-PR
- 校准度: Calibration plot, Brier Score
- 临床效用: Decision Curve Analysis

### 可解释性
- SHAP 全局重要性 + Dependence Plot
- SHAP 交互值 (top 10 交互对)
- 个体 waterfall plot (抽样 20 例)

### 敏感性分析
1. 不同缺失处理 (MICE vs CCA)
2. 排除极端预测值 (bootstrap)
3. 加入死亡作为结局 (Fine-Gray 竞争风险)
4. 不同衰弱定义 (FI vs Fried)
5. 不同年龄分层

## 6. 分析工具
- Python 3.x: scikit-learn, XGBoost, SHAP, MLflow
- R 4.x: MICE, tableone, pROC, rms

## 7. 时间线
| 阶段 | 时间 | 产出 |
|------|------|------|
| 方案确定 | Week 1 | 本协议 + SAP |
| 数据准备 | Week 1-2 | 分析就绪数据集 |
| 建模 | Week 2-4 | 训练好的模型 + 评估报告 |
| 可解释性 | Week 4-5 | SHAP 报告 |
| 撰写 | Week 5-8 | 初稿 |
| 审查 | Week 8-10 | 终稿 |
| 投稿 | Week 10-12 | 提交 |

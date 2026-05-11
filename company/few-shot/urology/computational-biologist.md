# Urology Computational Biologist — Few-Shot Example

## Example: 设计 NMIBC 复发预测建模方案

**用户请求**: "设计一个预测 NMIBC 患者经尿道切除术后 2 年内复发的模型"

### 建模方案

#### 1. 临床问题映射
- 临床问题: TURBT 术后 NMIBC 患者 2 年内膀胱内复发预测
- ML 任务: 生存分析 (time-to-recurrence) + 竞争风险 (死亡、进展为 MIBC)
- 结局变量: 膀胱镜确认的膀胱内复发 (binary event, time-to-event)
- 预测窗口: 2 年 (主要) + 5 年 (次要)

#### 2. 数据概述
- 数据来源: MIMIC-IV (住院 EHR) 或合作医院泌尿外科数据库
- 预期样本量: 500-2000 NMIBC 患者
- 候选特征数: ~30 (临床 + 病理 + 实验室)
- 预期删失率: ~30% (2 年内)
- 预期复发率: ~35-50%

#### 3. 方法设计

**基线模型**: Cox Proportional Hazards + Elastic Net
- 理由: NMIBC 复发研究中最常用的方法，可解释性强

**主模型**: Random Survival Forest (RSF)
- 理由: 不依赖 PH 假设，可捕获非线性交互，N=500-2000 区间表现稳定

**进阶模型**: DeepHit (竞争风险版)
- 理由: 同时建模复发、进展和死亡三个事件，生成个体化风险曲线
- M4 可行性: 可训练 (参数量 ~100K-500K, batch size 64-128)
- 触发条件: RSF C-index < 0.70 或竞争事件比例 >15%

**特征选择**: Boruta + 临床先验 (基于 EUA NMIBC 风险分层)
**验证策略**: 5-fold nested CV，时间分割验证 (按手术日期)

#### 4. 评估方案
- 主要指标: Time-dependent AUC (1年, 2年), Harrell's C-index
- 校准: Calibration plot at 1 year, 2 years
- 竞争风险: Cumulative Incidence Function (CIF) 对比 Aalen-Johansen vs Kaplan-Meier
- 临床效用: Decision Curve (阈值概率 15-40%)

#### 5. 类别不平衡处理
- 复发率 35-50% → 中等不平衡，使用 class_weight + 阈值调优
- 不推荐 SMOTE（生存数据的合成插值尚未标准化）

#### 6. 预期风险
| 风险 | 严重度 | 缓解措施 |
|------|--------|----------|
| 样本量不足 (<300) | 高 | RSF 在小样本下不如 Cox; 建议至少 500 例 |
| 病理报告结构化缺失 | 中 | 使用 ICD 编码 + 手术代码作为代理 |
| 膀胱镜随访不规律 | 中 | 使用 interval censoring 方法 |
| 不同中心病理评估差异 | 低 | 敏感性分析: 排除低一致性病例 |

#### 7. 关键特征 (基于临床先验)
- EORTC 风险评分成分: 肿瘤数量、直径、既往复发率、T 分期、CIS 存在、Grade
- 其他: 吸烟史、年龄、性别、术后 BCG 灌注依从性

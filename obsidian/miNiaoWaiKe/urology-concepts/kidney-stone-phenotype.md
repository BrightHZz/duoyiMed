---
type: concept
status: validated
topics: [kidney_stone, phenotype, computable_definition, MIMIC, MIMIC-IV, DuckDB, CPT, ICD]
last_updated: 2026-05-09
---

# 肾结石可计算表型 (Kidney Stone Computable Phenotype)

## 诊断定义

### ICD-10
- N20.0 — Calculus of kidney
- N20.1 — Calculus of ureter
- N20.2 — Calculus of kidney with calculus of ureter
- N20.9 — Calculus of urinary tract, unspecified

### ICD-9
- 592.0 — Calculus of kidney
- 592.1 — Calculus of ureter

## 外科干预定义

### ICD-10-PCS (已实现)
| 编码模式 | 描述 | 映射 |
|---------|------|------|
| 0T7x8DZ | Dilation of ureter, via endo, w/ intraluminal device | URS + 支架 |
| 0T7x8ZZ | Dilation of ureter, via endo | URS |
| 0TCx8ZZ | Extirpation of ureter, via endo | 取石 |
| 0TFx8ZZ | Fragmentation of ureter, via endo | 碎石 |
| 0TCx3ZZ | Extirpation via percutaneous | PCNL |
| 0TCx4ZZ | Extirpation via percutaneous endoscopic | PCNL |

### CPT (hcpcsevents, 已实现 ✓)
| CPT | 描述 | 映射 |
|-----|------|------|
| 52356 | URS w/ lithotripsy | URS |
| 52352 | URS w/ stone removal | URS |
| 52353 | URS w/ lithotripsy + stent | URS |
| 52351 | URS diagnostic | URS |
| 52332 | URS w/ stent insertion | URS |
| 50080 | PCNL | PCNL |
| 50081 | PCNL, second stage | PCNL |
| 50590 | ESWL | ESWL |
| 50432 | Nephrostomy + dilation | PCNL |
| 50945 | Lap ureterolithotomy | URS |

## 临床特征定义

### 结石相关
- 结石位置: 肾 (N20.0) / 输尿管 (N20.1) / 两者 (N20.2)
- 结石大小: CT 报告 (需影像文本提取, 暂未实现)
- 结石负荷: 多发/双侧/鹿角形 (ICD 编码推断)

### 代谢相关
- 24h 尿代谢: MIMIC 中不可用
- 血清: Calcium, Uric Acid (labevents)
- 尿液: pH, Specific Gravity (labevents)

### 感染相关
- UTI 证据: 尿培养阳性 + 尿 WBC > 10/HPF
- Sepsis: ICD 编码 + qSOFA
- 常见病原: E. coli (最多), P. aeruginosa, K. pneumoniae, P. mirabilis

## 结局定义

**已实现**: 急诊就诊后 90 天内首次外科干预 (binary)
- 阳性率: 6.0% (118/1979)
- 手术类型: URS 110 (93.2%), PCNL 8 (6.8%)
- 中位手术时间: 2.5 天
- 数据源: ICD-10-PCS + CPT (hcpcsevents) 双编码

备选方案 (未实现):
1. 缩短窗口至 30 天 (增加临床相关性)
2. 扩展至任何结石相关再入院 (不限于手术)
3. Time-to-event (生存分析) 而非 binary

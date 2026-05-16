---
type: dashboard
topic: literature
---

# 📚 文献库

## 按主题浏览

### 衰弱预测
```dataview
TABLE 
  first_author as "作者", 
  year as "年", 
  journal as "期刊",
  relevance_score as "相关度"
FROM "literature"
WHERE contains(topics, "frailty_prediction") AND status != "unread"
SORT year DESC
```

### 衰老时钟
```dataview
TABLE 
  first_author as "作者", 
  year as "年", 
  journal as "期刊",
  relevance_score as "相关度"
FROM "literature"
WHERE contains(topics, "aging_clocks") AND status != "unread"
SORT year DESC
```

### 多病共存聚类
```dataview
TABLE 
  first_author as "作者", 
  year as "年", 
  journal as "期刊"
FROM "literature"
WHERE contains(topics, "multimorbidity") AND status != "unread"
SORT year DESC
```

### 方法学
```dataview
TABLE 
  first_author as "作者", 
  year as "年", 
  journal as "期刊"
FROM "literature"
WHERE contains(topics, "methodology") AND status != "unread"
SORT year DESC
```

## 全部已读文献（按相关度排序）
```dataview
TABLE 
  first_author as "作者",
  year as "年", 
  journal as "期刊",
  relevance_score as "相关度",
  dateformat(date_read, "yyyy-MM-dd") as "阅读日期"
FROM "literature"
WHERE type = "literature" AND status = "read"
SORT relevance_score DESC
```

## 待读队列
```dataview
TABLE 
  first_author as "作者",
  year as "年",
  relevance_score as "相关度"
FROM "literature"
WHERE status = "unread"
SORT relevance_score DESC
```

---

## PubMed Alerts 检索式

**Alert 1 — 老年 + ML**:
```
("frailty"[MeSH] OR "frail elderly"[MeSH] OR "sarcopenia"[MeSH]) 
AND ("machine learning" OR "deep learning" OR "xgboost")
```

**Alert 2 — 衰老时钟**:
```
("epigenetic clock" OR "biological age" OR "DNA methylation age") 
AND ("aging"[MeSH] OR "mortality")
```

**Alert 3 — 预测模型 + 老年**:
```
("geriatric assessment"[MeSH]) 
AND ("prediction model" OR "risk prediction" OR "prognostic model")
```

## 核心期刊监控
- Lancet Healthy Longevity
- Nature Aging
- GeroScience
- Aging Cell
- J Gerontol A Biol Sci Med Sci
- J Am Geriatr Soc (JAGS)
- J Am Med Dir Assoc (JAMDA)
- BMC Geriatrics

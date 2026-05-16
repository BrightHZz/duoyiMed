---
type: dashboard
---

# 🏠 计算老年医学研究知识库

## 活跃项目

```dataview
TABLE 
  status as "状态", 
  priority as "优先级", 
  target_journal as "目标期刊",
  dateformat(start_date, "yyyy-MM") as "启动"
FROM "projects"
WHERE type = "project" AND status != "completed"
SORT priority DESC
```

## 文献库 (按主题)

```dataview
TABLE 
  first_author as "第一作者", 
  journal as "期刊", 
  relevance_score as "相关度",
  dateformat(date_read, "yyyy-MM-dd") as "阅读日期"
FROM "literature"
WHERE type = "literature" AND status = "read"
SORT relevance_score DESC
```

## 待读文献

```dataview
TABLE 
  first_author as "第一作者", 
  journal as "期刊", 
  relevance_score as "相关度"
FROM "literature"
WHERE status = "unread" OR status = "skimmed"
SORT relevance_score DESC
```

## 数据源

```dataview
TABLE 
  country as "国家", 
  age_range as "年龄", 
  sample_size as "样本量",
  access as "获取方式"
FROM "datasets"
SORT country ASC
```

## 方法库

```dataview
LIST 
FROM "methods"
```

## 老年医学概念

```dataview
LIST 
FROM "concepts"
```

---

## 快捷操作

- 新建文献笔记: 使用模板 `t-literature-note`
- 新建项目: 使用模板 `t-project-brief`
- 记录实验: 使用模板 `t-experiment-log`
- [[literature/literature-dashboard|文献库总览]]

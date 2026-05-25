---
type: dashboard
---

# 🏠 计算儿科研究知识库

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

- [[../datasets/pic/PIC|PIC — 儿科重症监护数据库]]
- [[../datasets/mimic-iv|MIMIC-IV]] (儿科亚组)
- [[../datasets/nhanes|NHANES]] (儿科模块)

## 儿科疾病概念

```dataview
LIST 
FROM "concepts"
```

---

## 快捷操作

- 新建文献笔记: 使用模板 `t-literature-note`
- 新建项目: 使用模板 `t-project-brief`
- 记录实验: 使用模板 `t-experiment-log`

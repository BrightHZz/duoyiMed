# 规则变更传播清单 (Rule Propagation Checklist)

> **用途**: 任何参考文献规则的变更, 必须按此清单同步更新所有相关文件。
> **原则**: 标准文件是唯一真相源。规则变更必须五层同步。

---

## 变更登记

| 日期 | 变更人 | 规则 | 变更摘要 | 清单状态 |
|------|--------|------|---------|:--:|
| 2026-05-27 | wangduoduo | 参考文献 A/B 环统一改造 | P0-P2 全量修复 | ✅ 完成 |
| 2026-05-27 | wangduoduo | 经典文献占比 ≤5% | 新增 check_classic_ratio + B环#18 | ✅ 完成 |

---

## 变更时必须检查的 5 层 12 文件

执行变更时, 复制以下清单并在每个项目后标注 ✅:

### 第 1 层: 标准定义 (权威真相源)

```
☐ company/reference/reference-quality-standard.md       — 规则定义 + 违规处理表
☐ company/reference/classic-papers.md                   — 经典豁免注册表 (如涉及)
```

### 第 2 层: Gate 强制执行 (B环)

```
☐ engine/core/gate_checks.py                            — auto check 函数 + GATE_DEFINITIONS 注册
☐ .claude/skills/duoyi/SKILL.md                         — 编排原则 + B环触发规则 (如涉及新触发规则)
```

### 第 3 层: Agent 行为指引 (A环)

```
☐ company/shared-services/scientific-writer-agent.md     — 写作前置检查 + Quality Checklist
☐ company/shared-services/research-assistant-agent.md    — 文献检索筛选规范
☐ company/divisions/urology/pi-agent.md                  — PI 终审清单
☐ company/divisions/geriatrics/pi-agent.md               — PI 终审清单
☐ company/divisions/pediatrics/pi-agent.md               — PI 终审清单 (如存在)
```

### 第 4 层: 运营文档

```
☐ company/company-sop.md                                 — Gate 检查清单
☐ company/management/pi-signoff-template.md              — PI 终审标准模板
```

### 第 5 层: 覆盖验证

```
☐ company/management/agent-gate-coverage-audit.md        — 覆盖审计 (更新检查项计数 + 矛盾记录)
```

---

## 变更模板

```
## [YYYY-MM-DD] 规则变更: [简短描述]

### 变更内容
- 规则名称: [如: 参考文献时效性双重门槛]
- 变更前: [旧规则]
- 变更后: [新规则]
- 影响项目类型: [论著 / 综述 / 通用]

### 同步状态

#### 第 1 层: 标准定义
- [ ] reference-quality-standard.md — 已更新规则定义
- [ ] classic-papers.md — [N/A / 已更新]

#### 第 2 层: Gate 强制执行
- [ ] gate_checks.py — [新增函数 / 修改函数 check_xxx]
- [ ] SKILL.md — [已更新编排原则 / 已更新 B环触发规则 / N/A]

#### 第 3 层: Agent 行为指引
- [ ] scientific-writer-agent.md — [已更新 Quality Checklist / N/A]
- [ ] research-assistant-agent.md — [已更新筛选规范 / N/A]
- [ ] urology/pi-agent.md — [已更新终审清单 / N/A]
- [ ] geriatrics/pi-agent.md — [已更新终审清单 / N/A]

#### 第 4 层: 运营文档
- [ ] company-sop.md — [已更新 Gate 检查清单 / N/A]
- [ ] pi-signoff-template.md — [已更新 / N/A]

#### 第 5 层: 覆盖验证
- [ ] agent-gate-coverage-audit.md — [已更新检查项 / 新增矛盾记录]

### Gate 6 自动验证
PASS 条件: 第 2 层 Gate 检查函数已注册 + 第 4 层 SOP 清单已更新 + 至少 2/5 Agent prompt 已同步
```

---

## 反模式警示

以下行为被视为违规, Gate 6 的 `check_lesson_rules_compliance` 会检测:

1. ❌ **异步更新**: 只修改 Gate 函数, 不更新 Agent prompt → Agent 盲飞, Gate 意外 FAIL
2. ❌ **标准文件滞后**: 在 Agent prompt 新增规则, 但标准文件无对应条目 → 规则无权威来源
3. ❌ **SOP 遗漏**: 新增 Gate 检查但 SOP 清单未更新 → Gate 6 checklist 与实际执行不一致
4. ❌ **覆盖审计腐败**: 修改 Gate 后不更新 coverage-audit.md → 审计基线失真

---

*此清单为全公司强制执行。规则变更未打满勾 → Gate 变更审批不予通过。*

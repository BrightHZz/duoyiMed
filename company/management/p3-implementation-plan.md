# P3 实现方案：季度运行报告 + FRAME 定量化 + 知识库备份

> 对应钱学森工程控制论 §系统辨识(§四) + §综合集成研讨厅(§六) + §可靠性(§五)，2026-05-10

---

## 一、P3-1：季度运行状态报告

### 1.1 目标

读取 `outputs/run_logs/*.jsonl` 累积的运行数据，自动生成《公司运行状态报告》Markdown 文件。

### 1.2 需要修改/新增的文件

| 文件 | 改动 | 行数 |
|------|------|------|
| `engine/core/run_analyzer.py` | **新文件** — RunAnalyzer 类：读取 JSONL → 聚合统计 → 生成 Markdown 报告 | ~150 |
| `run_research.py` | 新增 `--analyze` CLI 参数 + `--analyze-days` 指定分析天数 | ~30 |

### 1.3 报告输出

```
## Q2 2026 公司运行状态报告
*数据范围: 2026-04-01 至 2026-06-30 | 生成时间: 2026-07-01*

### Phase 耗时分布
| Phase | 平均耗时 | P50 | P95 | 目标 | 达标率 | 状态 |
|-------|---------|-----|-----|------|-------|------|
| problem_definition | 4.2h | 3.8h | 8.1h | 4h | 62% | ⚠️ 瓶颈 |
| execution | 5.5h | 5.1h | 10.2h | 5h | 78% | ✓ |

### Agent 一次通过率 (Gate 首次=PASS)
| Agent | 调用次数 | 一次通过率 | 降级率 | 主要失败原因 |
|-------|---------|----------|-------|------------|
| scientific-writer | 12 | 62% | 8% | Conclusion 层级 + DOI 未验证 |
| ml-engineer | 15 | 75% | 5% | n_jobs 不安全 + AUC 不达标 |

### 返工分析
| Phase | 返工率 | 平均返工次数 | 最常见原因 |
|-------|-------|------------|----------|
| writing | 38% | 1.8 | Conclusion 层级错误 |
| execution | 25% | 1.3 | AUC < 0.70 |

### 资源消耗
| 指标 | 值 |
|------|-----|
| 总 LLM 调用次数 | 87 |
| 总 Token 消耗 (in/out) | 2.1M / 1.4M |
| 估计 API 费用 | ~$35 |
| 降级模型使用次数 | 3 |
| 系统完全不可用次数 | 0 |

### 改进建议 (auto-generated)
1. writing Phase 一次通过率最低 (62%) → 建议强化 scientific-writer prompt
2. problem_definition 耗时超标 → 考虑增加并行度
3. ...
```

---

## 二、P3-2：FRAME 定量化改造

### 2.1 目标

PI 做 FRAME 评估不再靠记忆——Phase 1 先并行产出 5 份机器预检报告，PI 在定量数据基础上完成五维评估。

### 2.2 Phase 1 当前流程

```
Phase 1 agents: [clinical-researcher, data-engineer, research-assistant, pi]
全部并行调用，pi 自己凭记忆做 FRAME。
```

### 2.3 改造后流程

```
Phase 1 拆为两步:

Step 1a (并行 — 机器体系): 
  research-assistant → 选题文献预检报告 (F 维度数据源)
  data-engineer      → 数据可用性报告 (R 维度数据源)  
  research-assistant → 期刊趋势分析报告 (M 维度数据源)
  computational-biologist → 建模可行性报告 (技术可行性)
  编排器             → 当前资源负载报告 (E 维度数据源)

Step 1b (串行 — 专家体系):
  clinical-researcher → 临床问题操作化 + 表型定义
  pi                  → 接收 5 份预检报告 → FRAME 评估 (每个维度必须有定量支撑)
```

### 2.4 对 Phase 1 编排的改动

本质是对 `build_agent_input()` 中 PI 的 prompt 改造：当 PI 被调用时，已经有 5 份预检报告作为上下文注入，PI 的 system prompt 要求每个 FRAME 维度引用具体的报告数据。

**需要修改的文件**：

| 文件 | 改动 | 行数 |
|------|------|------|
| `engine/core/orchestrator_graph.py` | Phase 1 拆分 Step 1a/1b；新增 `_build_frame_precheck_prompt()`；修改 PI prompt 强制引用报告 | ~60 |
| `company/few-shot/geriatrics/pi.md` | 更新 FRAME 评估 few-shot 示例，展示引用预检报告的方式 | ~30 |
| `agents/few-shot/pi.md` | 同上 (旧版同步) | ~30 |

### 2.5 实现方式

不改 PROJECT_PHASES 的配置结构，而是在 `_execute_phase` 中识别 `problem_definition` Phase，分两轮执行:

```
Round 1 (并行): research-assistant + data-engineer + computational-biologist
  → 产出: 文献预检报告 + 数据可用性报告 + 建模可行性报告

Round 2 (串行): clinical-researcher + pi
  → pi 的 task_input 中包含 Round 1 的 3 份报告 + 编排器负载报告 + 期刊趋势报告
  → pi prompt 强制要求每个 FRAME 维度引用具体的报告数据
```

---

## 三、P3-3：知识库 Git 备份

### 3.1 目标

Obsidian vault 自动定期 git 备份，防止知识丢失。

### 3.2 实现方式

创建独立脚本 `scripts/backup_knowledge.sh`，手动执行或集成到 launchd/cron。

```bash
#!/bin/bash
# 备份 Obsidian 知识库到 git

VAULTS=(
  "$HOME/Documents/trae_projects/obsidian/laoNianYiXue"
  "$HOME/Documents/trae_projects/obsidian/miNiaoWaiKe"
)

for vault in "${VAULTS[@]}"; do
  cd "$vault" || continue
  if [ -d .git ]; then
    git add -A
    git commit -m "auto-backup: $(date '+%Y-%m-%d %H:%M')" 2>/dev/null
    echo "✓ $vault backed up"
  fi
done
```

**需要修改/新增的文件**：

| 文件 | 改动 | 行数 |
|------|------|------|
| `scripts/backup_knowledge.sh` | **新文件** — Git 备份脚本 | ~20 |
| `scripts/setup_backup_cron.sh` | **新文件** — 设置 launchd 定时任务的辅助脚本 + 说明 | ~40 |

---

## 四、实现优先级

```
P3-1 (季度报告)
  │  独立模块，只读 JSONL 文件，不影响主流程
  │  文件: run_analyzer.py (新) + run_research.py (小改)
  │  时间: ~1 小时
  │
  ├─→ P3-2 (FRAME 定量化)
  │     依赖: Phase 1 编排逻辑改动，需谨慎
  │     文件: orchestrator_graph.py + pi.md few-shot
  │     时间: ~1.5 小时
  │
  └─→ P3-3 (知识库备份)
        最独立, 纯 shell 脚本
        文件: scripts/backup_knowledge.sh (新)
        时间: ~20 分钟
```

## 五、验证方案

### P3-1
- 提前准备 2-3 天的 `.jsonl` 文件 (或手工造几条) → 跑 `python run_research.py --analyze --analyze-days 30` → 验证生成的 Markdown 报告

### P3-2
- 启动新项目 → 观察 Phase 1 log → 确认 Round 1 先并行出 3+ 报告 → Round 2 PI 输入中包含报告引用

### P3-3
- 手动执行 `scripts/backup_knowledge.sh` → 检查 git log 确认有 auto-backup commit

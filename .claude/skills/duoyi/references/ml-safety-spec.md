# ML 工程内存安全规范 (跨平台)

多进程/多线程 ML 训练在统一的资源约束下需防止内存溢出和系统崩溃。以下规范适用于 macOS / Windows / Linux。

## 规则 1 — n_jobs 动态上限
- 默认值: 2, 上限为 `min(4, os.cpu_count() // 2)`
- 绝对禁止 `n_jobs=-1` (使用所有核心)
- sklearn / XGBoost / LightGBM / CatBoost 所有 `n_jobs` / `nthread` 统一约束
- 交叉验证的 `n_jobs` 同样限制
- 大内存机器 (>32GB 可用) 可放宽至 4-6

## 规则 2 — SMOTE + 多进程 = 危险组合
- SMOTE 在 worker 内分配内存生成合成样本 → CoW 或内存复制爆炸
- 安全方案: (A) 训练循环外提前做 SMOTE (推荐) / (B) Pipeline 内 SMOTE 时 n_jobs=1 / (C) RandomUnderSampler 替代
- 禁止 Pipeline 内 SMOTE + 并行 CV

## 规则 3 — 启动方式 (平台适配)
- macOS / Linux: `os.environ["JOBLIB_START_METHOD"] = "forkserver"`
- Windows: 无需设置 (默认 spawn 等效)

## 规则 4 — 限制底层线程库
所有脚本顶部必须设置:
```python
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"
```

## 规则 5 — 运行前预估内存
- 预计峰值 = 数据内存 × n_jobs × SMOTE系数(1.5) + 模型内存 + 2GB
- 预计峰值 > 可用 RAM × 0.7 → 降 n_jobs
- 训练中系统无响应 → 立即终止进程

## 规则 6 — pickle 加载后覆盖 n_jobs
- `pickle.load` / `joblib.load` 加载的任何 sklearn/XGBoost/LightGBM 模型, 必须在加载后立即覆盖内部 `n_jobs` / `nthread` 属性
- `model = pickle.load(f); if hasattr(model, 'n_jobs'): model.n_jobs = 1`
- 原因: pickled 模型保留训练时的 n_jobs 值, `cross_val_predict` clone 后仍会使用该值

## 规则 7 — cross_val_predict / cross_val_score 必须显式传 n_jobs
- `cross_val_predict(model, X, y, cv=cv, n_jobs=1)` — 不可依赖默认值
- `cross_val_score(model, X, y, cv=cv, n_jobs=N_JOBS)` — N_JOBS 使用全局安全值
- 原因: sklearn 不同版本 `n_jobs=None` 默认行为不一致

## 规则 8 — 多模型串行加载时必须显式 gc
- 加载多个 pickled 模型时, 每个模型处理完后立即 `del data; gc.collect()`
- 原因: unpickled RF 模型内存占用可达 pickle 文件的 10-20 倍

## 规则 9 — 关键步骤前后打印内存使用
- 脚本启动时、每个耗时步骤前后调用 `psutil.virtual_memory()` 输出内存使用率
- 原因: 无监控 = 盲飞

## 规则 10 — 禁止嵌套并行: cross_val 与模型 n_jobs 互斥
- **禁止**: `cross_val_predict(..., n_jobs=N)` + 模型内部 `n_jobs=N` (N > 1)
- **方案 A** (推荐小模型): 模型 `n_jobs=1` + `cross_val_score(..., n_jobs=2)`
- **方案 B** (推荐树模型): 模型 `n_jobs=2` + `cross_val_score(..., n_jobs=1)`
- **选择指南**: N > 10,000 → 方案 B; 多模型 (≥3) → 方案 A; N < 5,000 → `n_jobs=1` 最安全

```python
# ✅ 正确
model = XGBClassifier(n_jobs=2)
scores = cross_val_score(model, X, y, cv=5, n_jobs=1)  # 模型内并行, CV 串行

# ❌ 灾难: 嵌套并行
model = XGBClassifier(n_jobs=2)
scores = cross_val_predict(model, X, y, cv=5, n_jobs=2)  # 8 线程抢 CPU
```

## 代码样板 (所有 import 之前)

```python
import os
import platform

# 线程限制 (全平台)
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

# Unix 平台: forkserver 减少内存继承
if platform.system() != "Windows":
    os.environ["JOBLIB_START_METHOD"] = "forkserver"

import numpy as np
import pandas as pd

N_JOBS = 2
RANDOM_SEED = 42
```

---

## 执行前安全扫描 (Pre-flight Safety Scan)

**实现文件**: `engine/core/preflight_scanner.py` → `PreflightScanner.scan()`

Phase 3/4/6 执行任何 Python 脚本前, 编排器必须先运行 `preflight_safety_scan`。扫描 FAIL 时禁止执行, 输出具体修复项清单。

### 扫描步骤

```
preflight_safety_scan(project_dir, target_scripts):
    for each script in target_scripts:
        # 1. n_jobs / nthread 审计
        grep 所有 n_jobs / nthread 赋值
        → 任何值 > 4 或 == -1 → FAIL
        → cross_val_score / cross_val_predict / cross_validate 调用未显式传 n_jobs → FAIL
        → RandomizedSearchCV / GridSearchCV 未显式传 n_jobs → FAIL

        # 2. pickle.load 后 n_jobs 覆盖检查
        grep "pickle.load\|joblib.load" 后续 8 行
        → 加载的是 sklearn/XGBoost/LightGBM 模型 AND 未覆盖 model.n_jobs=1 → FAIL
        → 加载后缺少 gc.collect() → WARN

        # 3. 线程限制环境变量检查
        required_vars = ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                         "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
                         "NUMEXPR_NUM_THREADS"]
        → 任何一项缺失 → FAIL
        → 任何一项值 > 2 → WARN

        # 4. 启动方式检查
        → Unix 平台缺少 JOBLIB_START_METHOD=forkserver → FAIL
        → 设置位置必须在 import numpy/pandas 之前 → WARN

        # 5. 跨脚本安全配置一致性
        → 同项目的 .py 脚本间 N_JOBS 值不一致 → WARN
        → 同项目的 .py 脚本间 thread_limits 不一致 → WARN
        → 任一脚本缺少安全样板 → FAIL

        # 6. 内存峰值预估
        data_size_mb = estimate_parquet_memory(data_dir)
        n_jobs_max = max(all n_jobs values found)
        has_smote = grep "SMOTE" in script
        smote_factor = 1.5 if has_smote else 1.0
        peak_est_gb = data_size_mb / 1024 * n_jobs_max * smote_factor * 20 + 4
        available_gb = psutil.virtual_memory().available / (1024**3)
        → peak_est_gb > available_gb * 0.7 → FAIL
        → 无法获取可用内存 → WARN
```

### 执行时机与阻断规则

| Phase | 触发时机 | 扫描目标 | FAIL 行为 |
|-------|---------|---------|----------|
| Phase 3 | train_model.py / tune_model.py 执行前 | 项目所有 .py | 拒绝执行, 输出修复清单 |
| Phase 4 | external_validation.py 执行前 | external_validation.py | 拒绝执行 |
| Phase 6 | regenerate_figures_tables.py 执行前 | regenerate_figures_tables.py + generate_figures.py | 拒绝执行 |

### 编排器指令

调度 ml-engineer 时, 必须在任务上下文中同时注入:
1. ML 内存安全规范全部 10 条规则
2. preflight_safety_scan 的检查结果 (若之前已扫描)
3. 当前可用内存值

---

## 脚本风险评级因子

**风险因子权重表**:

| 风险因子 | 权重 | 级别 | 说明 |
|----------|------|------|------|
| `n_jobs=-1` 或 `n_jobs > 4` | 8 | Critical | 必杀: kernel panic 根因 |
| SMOTE + 并行 CV (Pipeline 内) | 8 | Critical | 合成样本 CoW 爆炸 |
| `cross_val_predict` 未显式传 `n_jobs` | 5 | High | 默认值行为不确定 |
| `pickle.load` 后未覆盖 `model.n_jobs` | 5 | High | 训练时 n_jobs 逃逸到推理时 |
| `cross_val_score` 未显式传 `n_jobs` | 4 | High | 同上 |
| 缺少 OMP/MKL/OPENBLAS thread limits | 4 | High | worker × threads 乘积效应 |
| 缺少 JOBLIB_START_METHOD=forkserver | 3 | Medium | CoW 内存继承风险 |
| ≥2 个模型串行加载无 `gc.collect()` | 3 | Medium | 内存累积效应 |
| 无内存监控日志 | 1 | Low | 可观测性缺失 |
| SMOTE (Pipeline 外) | 1 | Low | 安全实践 |
| `n_jobs=2` on ≤24GB RAM + SMOTE | 3 | Medium | 边界风险 |

**评级公式**:
```
risk_score = Σ(factor_weight × count_of_occurrences)
risk_level = Critical if any(Critical_factor_present) or score ≥ 8
             High     if score ≥ 5
             Medium   if score ≥ 3
             Low      otherwise
```

编排器在 Phase 0 (SDS) 阶段生成项目风险评估时扫描项目所有 .py 脚本。风险等级 ≥ High 时 SDS 必须包含降风险方案。Phase 3/6 执行前 re-scan 确认风险已降低。

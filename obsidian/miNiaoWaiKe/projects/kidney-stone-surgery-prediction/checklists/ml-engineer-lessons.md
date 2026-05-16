# ML Engineer 经验总结 — scikit-learn 多进程内存管理

## 事故回顾

**日期:** 2026-05-09, 2026-05-10  
**机器:** MacBook Pro M4, 24 GB RAM, macOS 15.7.3  
**现象:** 运行 `tune_model.py` 时系统两次 watchdog timeout → kernel panic → 强制重启

## 根因

```
N_JOBS = 8  # ← 这一行导致系统崩溃
```

`cross_val_score(..., n_jobs=8)` 一次性 fork 8 个子进程，每个子进程通过 Copy-on-Write 继承父进程地址空间。

当 worker 内执行 SMOTE（合成少数类样本）+ RF 训练时：
- 每个 worker 产生 200 万+ page fault
- 临时 numpy 数组、RF 树结构触发大量 CoW 页面复制
- 8 worker 并发 → 物理内存瞬间耗尽
- macOS watchdogd 僵死 >90 秒 → kernel panic

**关键教训:** 即使你的数据集只有 1.5 MB / 1979 行，fork + SMOTE + N_JOBS=8 的组合也可以打爆 24 GB 内存。

## 多进程并行安全配置

### 规则 1: `n_jobs` 别超过物理核心数的一半

```python
# ❌ 危险
N_JOBS = 8   # 或 n_jobs=-1

# ✅ 安全
N_JOBS = 2   # 24GB RAM 的数据科学任务
N_JOBS = 4   # 32GB+ RAM 时可尝试

# ✅ 更好的写法：根据可用内存动态设置
import os, psutil
available_gb = psutil.virtual_memory().available / (1024**3)
N_JOBS = max(1, min(4, int(available_gb / 8)))  # 每 8 GB 分配 1 个 worker
```

### 规则 2: 设置 joblib 启动方式

```python
# fork (默认) — 继承父进程全部内存, CoW 风险最高
# forkserver — 轻量 fork，减少共享内存
# spawn — 全新进程，无 CoW 风险，但启动慢

os.environ['JOBLIB_START_METHOD'] = 'forkserver'  # 推荐
```

### 规则 3: SMOTE + 多进程是危险组合

SMOTE 会在每个 worker 内生成合成样本（大量内存分配），加上多进程 fork，CoW 页面复制会爆炸。

```python
# ✅ 安全做法
N_JOBS = 1   # SMOTE + RF 用单进程
# 或
N_JOBS = 2   # 确认可用内存 > 数据集大小 × 20 再开多进程
```

### 规则 4: 限制底层线程库

```python
# 防止 numpy/scipy 内部也开多线程
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
```

如果不设置，每个 worker 的 numpy 操作还会内部多线程，N_JOBS × OMP_THREADS = 线程爆炸。

### 规则 5: 运行前检查内存

```bash
# 跑 ML 脚本前
vm_stat | head -10           # 查看内存压力
memory_pressure              # 查看当前压力级别
sudo fs_usage | grep python  # 查看磁盘 I/O（swap 迹象）
```

## 按 RAM 大小的推荐配置

| 内存 | n_jobs | 注意事项 |
|---|---|---|
| 8 GB | 1 | 关掉 IDE、浏览器再跑 |
| 16 GB | 1-2 | 谨慎开 2 |
| 24 GB | 2 | 关闭不必要的应用 |
| 32 GB | 2-4 | 可以同时开发 |
| 64 GB+ | 4-8 | 相对自由 |

## 代码模板

```python
import os
import psutil

# --- 并行安全配置 ---
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
os.environ.setdefault('JOBLIB_START_METHOD', 'forkserver')

def safe_n_jobs(max_jobs=4, min_ram_per_job_gb=8):
    """根据当前可用内存计算安全的 n_jobs 值"""
    avail = psutil.virtual_memory().available / (1024**3)
    return max(1, min(max_jobs, int(avail / min_ram_per_job_gb)))

N_JOBS = safe_n_jobs()
print(f"[MEM] {psutil.virtual_memory().available/1024**3:.1f} GB available → n_jobs={N_JOBS}")

# --- 主流程 ---
cross_val_score(model, X, y, cv=cv, n_jobs=N_JOBS)
```

## 复盘检查清单

跑 ML pipeline 之前确认：

- [ ] `n_jobs` 是否 ≤ 4？
- [ ] 是否设置了 `JOBLIB_START_METHOD=forkserver`？
- [ ] 是否限制了 `OMP/MKL_NUM_THREADS`？
- [ ] IDE + 浏览器 + 其他应用占了多少内存？（活动监视器）
- [ ] 数据集 × n_jobs × 临时分配倍数 是否会超出可用 RAM？
- [ ] 如果用 SMOTE，是否需要额外降低 n_jobs？

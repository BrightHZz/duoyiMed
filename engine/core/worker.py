"""
Worker 守护进程 — Worker Daemon

多进程并发 Worker, 轮询项目队列, 竞争执行项目。
每个 Worker 拥有独立的 ResearchOrchestrator 实例, 项目间完全隔离。

用法:
    python run_research.py --worker              # 单 Worker
    python run_research.py --worker --workers 3  # 3 个 Worker

生命周期:
    while running:
        scan_and_claim()     → 寻找 status=pending 的项目, 原子抢占
        execute_project()    → 实例化 Orchestrator, 调用 run_resume
        release_lock()       → 释放 .lock, 标记完成/失败
"""

import os
import sys
import time
import signal
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional


class WorkerDaemon:
    """Worker 守护进程。

    特性:
    - 优雅关闭: SIGTERM/SIGINT 触发 _graceful_shutdown, 完成当前 Phase 后退出
    - 死锁恢复: 被抢占的项目自动由其他 Worker 接管 (ProjectLock.lock_timeout)
    - 速率限制: 可选 RateLimiter 集成, 保护 LLM API
    - 错误隔离: 单个项目崩溃不影响 Worker 继续处理下一个
    """

    def __init__(self, config, worker_id: int = 0):
        """
        Args:
            config: EngineConfig 实例
            worker_id: Worker 编号 (多 Worker 时用于日志)
        """
        self.config = config
        self.worker_id = worker_id
        self.running = True
        self._current_project_id: Optional[str] = None
        self._current_lock = None

        # 懒加载 (避免导入时触发 pandas 等重依赖)
        self._project_manager = None
        self._rate_limiter = None

    @property
    def project_manager(self):
        if self._project_manager is None:
            from .project_manager import ProjectManager
            self._project_manager = ProjectManager(self.config)
        return self._project_manager

    @property
    def rate_limiter(self):
        if self._rate_limiter is None:
            from .rate_limiter import RateLimiter
            shared_dir = self.config.projects_output_dir / "_shared"
            self._rate_limiter = RateLimiter(shared_dir)
        return self._rate_limiter

    # ================================================================
    # 主循环
    # ================================================================

    def run_forever(self):
        """主循环: 轮询 → 抢项目 → 执行 → 循环。优雅关闭由信号处理。"""
        signal.signal(signal.SIGTERM, self._graceful_shutdown)
        signal.signal(signal.SIGINT, self._graceful_shutdown)

        self._log("Worker 启动")
        poll_interval = 5  # 无项目时的轮询间隔(秒)

        while self.running:
            pid = self.scan_and_claim()
            if pid:
                try:
                    self.execute_project(pid)
                except Exception:
                    self._log(f"项目 {pid} 执行异常:\n{traceback.format_exc()}")
                finally:
                    self.release_project()
            else:
                time.sleep(poll_interval)

        self._log("Worker 已停止")

    # ================================================================
    # 项目扫描与抢占
    # ================================================================

    def scan_and_claim(self) -> Optional[str]:
        """扫描 pending 项目, 通过 ProjectLock 原子抢占。

        策略:
        1. 先检查 running 项目是否有死锁 (可抢占的过期锁)
        2. 扫描 pending 项目, 尝试原子加锁

        Returns:
            抢占成功的 project_id, 或 None
        """
        from .project_lock import ProjectLock

        try:
            # 1. 扫描 running 项目中的死锁
            running = self.project_manager.list_projects(status_filter="running")
            for p in running:
                lock = ProjectLock(self.config.projects_output_dir, p["project_id"])
                if lock.acquire():
                    lock.release()  # 清理死锁, 让项目回到 pending 状态
                    # 将状态重置为 pending
                    self.project_manager.save_state(p["project_id"], status="pending")
                    self._log(f"恢复死锁项目: {p['project_id']}")

            # 2. 扫描 pending 项目, 原子抢占
            pending = self.project_manager.list_projects(status_filter="pending")
            for p in pending:
                lock = ProjectLock(self.config.projects_output_dir, p["project_id"])
                if lock.acquire():
                    self._current_lock = lock
                    self._current_project_id = p["project_id"]
                    # 标记为 running
                    self.project_manager.save_state(
                        p["project_id"],
                        status="running",
                        worker_pid=os.getpid(),
                        worker_id=self.worker_id,
                    )
                    self._log(f"抢占项目: {p['project_id']} ({p.get('user_request', '')[:60]})")
                    return p["project_id"]
        except Exception:
            self._log(f"扫描异常: {traceback.format_exc()}")

        return None

    # ================================================================
    # 项目执行
    # ================================================================

    def execute_project(self, project_id: str):
        """实例化独立的 Orchestrator 并续传项目。"""
        from .orchestrator_graph import ResearchOrchestrator

        self._log(f"开始执行: {project_id}")

        # 独立的 Orchestrator 实例 — 项目间完全隔离
        orchestrator = ResearchOrchestrator(self.config)

        # 注入速率限制器 (可选 — 保护 LLM API)
        orchestrator.rate_limiter = self.rate_limiter

        # 续传 (内部已有断点续传逻辑)
        result = orchestrator.run_resume(project_id)

        self._log(f"执行完成: {project_id}")
        return result

    def release_project(self):
        """释放当前项目的锁, 标记 Worker 空闲。"""
        if self._current_lock:
            try:
                self._current_lock.release()
            except Exception:
                pass
            self._current_lock = None
        self._current_project_id = None

    # ================================================================
    # 辅助
    # ================================================================

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = f"[W{self.worker_id}]" if self.worker_id else "[Worker]"
        print(f"{ts} {prefix} {msg}")

    def _graceful_shutdown(self, signum=None, frame=None):
        """优雅关闭: 完成当前 Phase 后退出, 不中途杀 Agent 调用。"""
        sig_name = signal.Signals(signum).name if signum else "UNKNOWN"
        self._log(f"收到 {sig_name} 信号, 优雅关闭中...")
        self.running = False
        # 不强制释放锁 — 让 heartbeat 超时后自动过期。
        # 如果当前正在执行 Phase, Orchestrator 会完成当前 Phase 再退出。

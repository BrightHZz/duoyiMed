"""
进程间项目锁 — Project Lock

基于 O_CREAT|O_EXCL 原子操作实现跨进程互斥锁, 防止多个 Worker
同时执行同一项目。支持心跳检测和死锁抢占(Worker 崩溃恢复)。

用法:
    lock = ProjectLock(projects_dir, project_id)
    if lock.acquire():
        try:
            # 执行项目
            lock.heartbeat()  # 定期心跳
        finally:
            lock.release()
"""

import os
import time
from pathlib import Path


class ProjectLock:
    """跨进程项目互斥锁。

    机制:
    1. O_CREAT|O_EXCL 原子创建 .lock 文件 → 只有一个 Worker 能成功
    2. .lock 内写入 PID + 心跳时间戳
    3. 定期 heartbeat() 更新心跳, 证明 Worker 存活
    4. 其他 Worker 发现 lock_timeout 秒无心跳 → 可抢占(死锁恢复)
    """

    def __init__(self, projects_dir: Path, project_id: str,
                 lock_timeout: float = 300.0, heartbeat_interval: float = 30.0):
        """
        Args:
            projects_dir: outputs/projects/ 根目录
            project_id: 项目 ID
            lock_timeout: 锁过期时间(秒), 超时无心跳视为死锁, 默认 300s
            heartbeat_interval: 心跳间隔, 建议取 lock_timeout / 10
        """
        self.lock_file = projects_dir / project_id / ".lock"
        self.pid = os.getpid()
        self.lock_timeout = lock_timeout
        self.heartbeat_interval = heartbeat_interval
        self._owned = False

    def acquire(self) -> bool:
        """尝试原子获取锁。返回 True 表示抢到项目, False 表示已被占用。

        如果锁过期(持有者崩溃), 自动抢占并覆盖旧锁。
        """
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 原子创建: 仅当文件不存在时成功
            fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            self._write_lock(fd)
            os.close(fd)
            self._owned = True
            return True
        except FileExistsError:
            return self._try_steal_stale_lock()

    def heartbeat(self):
        """更新心跳时间戳。Worker 应在执行循环中定期调用。"""
        if not self._owned:
            return
        try:
            with open(self.lock_file, "w") as f:
                f.write(f"{self.pid}\n{time.time()}\n")
        except Exception:
            pass  # 心跳失败不阻塞

    def release(self):
        """释放锁, 删除 .lock 文件。"""
        if not self._owned:
            return
        try:
            self.lock_file.unlink(missing_ok=True)
        except Exception:
            pass
        self._owned = False

    @property
    def is_owned(self) -> bool:
        return self._owned

    # ================================================================
    # 内部
    # ================================================================

    def _write_lock(self, fd: int):
        """写入 PID + 时间戳到锁文件"""
        os.write(fd, f"{self.pid}\n{time.time()}\n".encode())

    def _try_steal_stale_lock(self) -> bool:
        """检查现有锁是否过期, 过期则抢占。"""
        try:
            content = self.lock_file.read_text().strip()
            lines = content.splitlines()
            if len(lines) >= 2:
                last_heartbeat = float(lines[1])
            else:
                last_heartbeat = 0.0

            age = time.time() - last_heartbeat
            if age > self.lock_timeout:
                # 死锁: 删除旧锁, 重新获取
                old_pid = lines[0] if lines else "?"
                self.lock_file.unlink()
                try:
                    fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    self._write_lock(fd)
                    os.close(fd)
                    self._owned = True
                    print(f"  🔓 抢占过期锁 (原 PID={old_pid}, 失联 {age:.0f}s)")
                    return True
                except FileExistsError:
                    # 竞态: 其他 Worker 抢先了
                    return False
        except Exception:
            pass
        return False


def cleanup_stale_locks(projects_dir: Path, max_age: float = 600.0) -> int:
    """清理所有过期锁文件。用于手动恢复 (--cleanup-locks)。

    Returns:
        清理的锁文件数量
    """
    count = 0
    if not projects_dir.exists():
        return 0

    for proj_dir in projects_dir.iterdir():
        if not proj_dir.is_dir() or proj_dir.name.startswith("_"):
            continue
        lock_file = proj_dir / ".lock"
        if not lock_file.exists():
            continue
        try:
            content = lock_file.read_text().strip()
            lines = content.splitlines()
            if len(lines) >= 2:
                age = time.time() - float(lines[1])
                if age > max_age:
                    lock_file.unlink()
                    count += 1
                    print(f"  🧹 清理过期锁: {proj_dir.name} (失联 {age:.0f}s)")
        except Exception:
            # 损坏的锁文件也清理
            lock_file.unlink(missing_ok=True)
            count += 1
    return count

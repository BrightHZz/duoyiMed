"""
跨进程 LLM 速率限制器 — Rate Limiter

基于令牌桶算法, 使用共享状态文件 + fcntl.flock 在多 Worker 进程间
协调 LLM API 调用速率, 防止触发 API provider 的速率限制 (429)。

用法:
    limiter = RateLimiter(shared_dir, config=RateLimitConfig(rpm=30))
    wait = limiter.acquire()  # 阻塞直到获取令牌, 返回等待秒数
"""

import json
import fcntl
import time
import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    """速率限制配置 — 按 LLM provider 的默认限制设置。"""
    requests_per_minute: int = 30       # 每分钟最大请求数
    max_burst: int = 5                  # 突发容量(令牌桶最大容量)
    refill_rate: float = 0.0            # 令牌补充速率 (tokens/s), 0=从 rpm 推导

    def __post_init__(self):
        if self.refill_rate <= 0:
            self.refill_rate = self.requests_per_minute / 60.0


# 不同 provider 的默认限制
PROVIDER_LIMITS = {
    "deepseek": RateLimitConfig(requests_per_minute=30, max_burst=5),
    "anthropic": RateLimitConfig(requests_per_minute=50, max_burst=10),
    "openai": RateLimitConfig(requests_per_minute=60, max_burst=10),
}


class RateLimiter:
    """跨进程令牌桶速率限制器。

    使用 outputs/_shared/rate_limit_state.json 作为共享状态,
    fcntl.flock 提供进程间互斥, 确保多 Worker 安全。

    Usage:
        limiter = RateLimiter(shared_dir)
        wait = limiter.acquire()  # 阻塞, 返回等待秒数
    """

    def __init__(self, shared_dir: Path, config: RateLimitConfig = None):
        self.state_file = shared_dir / "rate_limit_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = config or RateLimitConfig()
        self.max_tokens = float(self.config.max_burst)
        self.refill_rate = self.config.refill_rate

    def acquire(self, timeout: float = 120.0) -> float:
        """获取 1 个令牌。如果令牌不足则阻塞等待, 超时后强制放行。

        Returns:
            实际等待的秒数 (0 = 立即获取, 无等待)
        """
        start = time.time()
        while True:
            tokens, slept = self._try_acquire()
            if tokens:
                return time.time() - start
            if time.time() - start > timeout:
                # 超时强制放行 — 避免锁争用导致永久阻塞
                return time.time() - start
            time.sleep(0.5)

    def try_acquire(self) -> bool:
        """非阻塞获取令牌。成功返回 True, 失败返回 False。"""
        got, _ = self._try_acquire()
        return got

    # ================================================================
    # 内部
    # ================================================================

    def _try_acquire(self) -> tuple[bool, float]:
        """尝试获取令牌: 读状态 → 补充令牌 → 消费 1 个 → 写状态。
        整个过程在 fcntl.flock 下执行, 保证原子性。

        Returns:
            (got_token, slept_seconds)
        """
        try:
            with open(self.state_file, "a+") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    # 读取当前状态
                    state = self._read_state(f)
                    now = time.time()

                    # 补充令牌 (基于流逝时间)
                    elapsed = now - state["last_refill"]
                    refill = elapsed * self.refill_rate
                    state["tokens"] = min(self.max_tokens, state["tokens"] + refill)
                    state["last_refill"] = now

                    # 消费 1 个令牌
                    if state["tokens"] >= 1.0:
                        state["tokens"] -= 1.0
                        state["total_requests"] += 1
                        self._write_state(f, state)
                        return True, 0.0

                    # 令牌不足, 保存状态后返回 False
                    self._write_state(f, state)
                    # 计算需要等待的时间
                    wait_needed = (1.0 - state["tokens"]) / self.refill_rate
                    return False, wait_needed
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except Exception:
            # 任何错误都放行 — 速率限制失败不应阻断业务
            return True, 0.0

    def _read_state(self, f) -> dict:
        """从文件读取令牌桶状态。文件为空或损坏时返回初始状态。"""
        f.seek(0)
        content = f.read().strip()
        if not content:
            return {"tokens": self.max_tokens, "last_refill": time.time(),
                    "total_requests": 0}
        try:
            return json.loads(content)
        except Exception:
            return {"tokens": self.max_tokens, "last_refill": time.time(),
                    "total_requests": 0}

    def _write_state(self, f, state: dict):
        """原子写入状态 (flock 已持锁, 截断+写入即可)"""
        f.seek(0)
        f.truncate()
        f.write(json.dumps(state))
        f.flush()
        os.fsync(f.fileno())

    def stats(self) -> dict:
        """返回当前速率限制统计 (非阻塞, 读快照)"""
        try:
            if self.state_file.exists():
                with open(self.state_file) as f:
                    fcntl.flock(f, fcntl.LOCK_SH)
                    try:
                        state = self._read_state(f)
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
                    return {
                        "tokens_available": round(state.get("tokens", 0), 2),
                        "total_requests": state.get("total_requests", 0),
                        "max_burst": self.max_tokens,
                        "rpm_limit": self.config.requests_per_minute,
                    }
        except Exception:
            pass
        return {"error": "无法读取速率限制状态"}

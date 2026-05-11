"""LLM 客户端 — 统一的 LLM 调用接口, 支持 tool calling + 容错 (retry + fallback)"""

import json
import os
import time
import random
from typing import Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path


# 可重试的错误类型 (按类名匹配)
_RETRYABLE_ERROR_NAMES = (
    "RateLimitError",
    "APITimeoutError",
    "APIConnectionError",
    "InternalServerError",
    "ServiceUnavailableError",
    "ReadTimeout",
    "ConnectTimeout",
    "ConnectionError",
    "RemoteDisconnected",
    "Timeout",
)

# 错误消息中的可重试关键词
_RETRYABLE_MSG_KEYWORDS = (
    "timeout", "rate limit", "server error", "connection",
    "service unavailable", "too many requests", "overloaded",
    "timed out", "reset by peer", "internal error",
)


class LLMCallFailedError(Exception):
    """LLM 调用最终失败 (所有重试 + 降级均未成功)"""
    pass


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict
    tool_calls: list[dict] = field(default_factory=list)
    degraded: bool = False  # 是否使用了降级模型

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


class LLMClient:
    """
    统一的 LLM 客户端, 支持 Anthropic / OpenAI / DeepSeek。
    优先使用 Anthropic SDK, 回退到 requests (适用于 DeepSeek 等兼容 API)。

    容错能力:
    - 指数退避重试 (最多 3 次, 1s→2s→4s)
    - 模型降级 (primary → fallback model)
    - 错误分类 (可重试 vs 不可重试)
    - 断点保存 (tool-calling 中断后恢复)
    """

    def __init__(self, provider: str = "anthropic", model: str = "claude-sonnet-4-6",
                 max_tokens: int = 8192, temperature: float = 0.1, verbose: bool = True,
                 fallback_model: str = "claude-haiku-4-5-20251001",
                 max_retries: int = 3, retry_base_delay: float = 1.0,
                 retry_max_delay: float = 8.0, request_timeout: int = 300,
                 checkpoint_dir: Optional[Path] = None):
        self.provider = provider
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.verbose = verbose

        # 容错配置
        self.fallback_model = fallback_model
        self.max_retries = max_retries            # 不含首次, 即最多 1+3=4 次尝试
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay
        self.request_timeout = request_timeout
        self.checkpoint_dir = checkpoint_dir

    # ================================================================
    # 核心容错逻辑
    # ================================================================

    def _call_with_retry(self, call_fn: Callable, call_name: str = "chat") -> LLMResponse:
        """
        容错包装: 指数退避重试 + 模型降级。

        重试序列 (最多 4 次尝试):
          Attempt 0: primary model
          Attempt 1: primary model, delay=1s+jitter
          Attempt 2: fallback model, delay=2s+jitter
          Attempt 3: fallback model, delay=4s+jitter → 最终失败

        Returns:
            LLMResponse (degraded=True 表示用了降级模型)

        Raises:
            LLMCallFailedError: 所有尝试均失败
        """
        last_error = None
        total_attempts = self.max_retries + 1  # 首次 + 重试

        for attempt in range(total_attempts):
            # 第 3 次尝试起降级到 fallback model
            if attempt >= 2 and self.model != self.fallback_model:
                degraded_model = self.fallback_model
                if self.verbose:
                    print(f"  🔄 LLM 降级: {self.model} → {degraded_model}")
                self._swap_model(degraded_model)

            try:
                result = call_fn()
                if self.verbose and attempt > 0:
                    print(f"  ✅ LLM 恢复 (attempt {attempt+1}/{total_attempts})")
                return result

            except Exception as e:
                last_error = e

                # 不可重试的错误 → 直接失败
                if not self._is_retryable(e):
                    if self.verbose:
                        print(f"  ✗ LLM 不可重试错误: {type(e).__name__}")
                    raise

                # 已达最大重试次数
                if attempt >= total_attempts - 1:
                    break

                # 计算退避延迟
                delay = min(
                    self.retry_base_delay * (2 ** attempt) + random.uniform(0, 0.5),
                    self.retry_max_delay,
                )

                if self.verbose:
                    print(f"  ⚠️ LLM {type(e).__name__} (attempt {attempt+1}/{total_attempts}), "
                          f"{delay:.1f}s 后重试...")

                time.sleep(delay)

        # 全部重试失败
        raise LLMCallFailedError(
            f"LLM 调用失败 (共 {total_attempts} 次尝试): {type(last_error).__name__}: {last_error}"
        ) from last_error

    def _is_retryable(self, error: Exception) -> bool:
        """判断错误是否可重试。基于错误类名 + 错误消息关键词。"""
        error_name = type(error).__name__

        # 检查类名
        for name in _RETRYABLE_ERROR_NAMES:
            if name in error_name:
                return True

        # 检查错误消息
        error_msg = str(error).lower()
        for kw in _RETRYABLE_MSG_KEYWORDS:
            if kw in error_msg:
                return True

        return False

    def _swap_model(self, model_name: str):
        """临时切换模型 (用于降级/恢复)"""
        self.model = model_name

    # ================================================================
    # 公开接口
    # ================================================================

    def chat(self, system_prompt: str, user_message: str,
             tools: Optional[list[dict]] = None,
             tool_choice: Optional[str] = None) -> LLMResponse:
        """
        发送消息到 LLM (带容错)。

        Args:
            system_prompt: 系统提示
            user_message: 用户消息
            tools: 可选的 tool definitions (Anthropic 格式)
            tool_choice: tool choice 策略

        Returns:
            LLMResponse (检查 degraded 字段判断是否用了降级模型)

        Raises:
            LLMCallFailedError: 所有重试 + 降级均失败
        """
        primary_model = self.model

        def _do_chat():
            if self.provider == "anthropic":
                return self._chat_anthropic(system_prompt, user_message, tools, tool_choice)
            elif self.provider == "deepseek":
                return self._chat_deepseek(system_prompt, user_message)
            elif self.provider == "openai":
                return self._chat_openai(system_prompt, user_message, tools)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        try:
            result = self._call_with_retry(_do_chat, "chat")
            result.degraded = (self.model != primary_model)
            return result
        finally:
            # 恢复主模型 (为下次调用准备)
            self._swap_model(primary_model)

    def chat_with_tools(self, system_prompt: str, user_message: str,
                         tools: list[dict], execute_tool: Callable,
                         max_tool_rounds: int = 8) -> LLMResponse:
        """
        带工具调用的 chat 循环 (带容错 + checkpoint)。

        LLM 可以多次调用工具, 直到给出最终文本响应。
        每轮 tool-calling 都经过容错包装, 中断时保存 checkpoint。
        """
        primary_model = self.model
        all_tool_calls = []
        messages = [{"role": "user", "content": user_message}]
        round_num = 0

        try:
            for round_num in range(max_tool_rounds):
                # 每轮 tool calling 带容错 (返回原始 dict)
                response = self._call_with_retry_raw(
                    lambda: self._chat_anthropic_with_history(system_prompt, messages, tools)
                )

                # 解析 tool_use 和 text
                tool_uses = []
                text_parts = []
                resp_content = response.get("content", [])
                for block in resp_content:
                    if hasattr(block, 'type'):
                        if block.type == "text":
                            text_parts.append(block.text)
                        elif block.type == "tool_use":
                            tool_uses.append({"id": block.id, "name": block.name, "input": block.input})

                if not tool_uses:
                    return LLMResponse(
                        content="\n".join(text_parts),
                        model=response.get("model", ""),
                        usage=response.get("usage", {}),
                        tool_calls=all_tool_calls,
                        degraded=(self.model != primary_model),
                    )

                # 执行工具调用
                tool_results = []
                for tu in tool_uses:
                    if self.verbose:
                        print(f"  🔧 {tu['name']}({json.dumps(tu['input'], ensure_ascii=False)[:100]})")
                    result = execute_tool(tu["name"], tu["input"])
                    all_tool_calls.append({
                        "tool": tu["name"],
                        "input": tu["input"],
                        "result": result[:500] + "..." if len(result) > 500 else result,
                    })
                    tool_results.append({
                        "tool_use_id": tu["id"],
                        "content": result[:8000],
                    })

                # 将助手响应 + 工具结果加入消息历史
                messages.append({
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "id": tu["id"], "name": tu["name"], "input": tu["input"]}
                        for tu in tool_uses
                    ],
                })
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": tr["tool_use_id"], "content": tr["content"]}
                        for tr in tool_results
                    ],
                })

            # 超过最大轮次
            return LLMResponse(
                content="[Max tool rounds exceeded]",
                model="",
                usage={},
                tool_calls=all_tool_calls,
                degraded=(self.model != primary_model),
            )
        except LLMCallFailedError:
            self._save_checkpoint(all_tool_calls, round_num)
            raise
        finally:
            self._swap_model(primary_model)

    def _call_with_retry_raw(self, call_fn: Callable) -> dict:
        """
        容错包装 (raw 版本): 返回原始 dict, 用于 tool-calling 循环内部。

        与 _call_with_retry 相同的重试逻辑, 但返回类型为 dict 而非 LLMResponse。
        """
        last_error = None
        total_attempts = self.max_retries + 1

        for attempt in range(total_attempts):
            if attempt >= 2 and self.model != self.fallback_model:
                degraded_model = self.fallback_model
                if self.verbose:
                    print(f"  🔄 LLM 降级: {self.model} → {degraded_model}")
                self._swap_model(degraded_model)

            try:
                result = call_fn()
                if self.verbose and attempt > 0:
                    print(f"  ✅ LLM 恢复 (attempt {attempt+1}/{total_attempts})")
                return result
            except Exception as e:
                last_error = e
                if not self._is_retryable(e):
                    raise
                if attempt >= total_attempts - 1:
                    break
                delay = min(
                    self.retry_base_delay * (2 ** attempt) + random.uniform(0, 0.5),
                    self.retry_max_delay,
                )
                if self.verbose:
                    print(f"  ⚠️ LLM {type(e).__name__} (attempt {attempt+1}/{total_attempts}), "
                          f"{delay:.1f}s 后重试...")
                time.sleep(delay)

        raise LLMCallFailedError(
            f"LLM 调用失败 (共 {total_attempts} 次尝试): {type(last_error).__name__}: {last_error}"
        ) from last_error

    # ================================================================
    # Checkpoint (断点保存)
    # ================================================================

    def _save_checkpoint(self, tool_calls: list, round_num: int):
        """保存断点，中断后可从此恢复 tool-calling 进度"""
        if not self.checkpoint_dir:
            return
        try:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            checkpoint = {
                "tool_calls": tool_calls,
                "round": round_num,
                "timestamp": time.time(),
                "model": self.model,
            }
            path = self.checkpoint_dir / f"checkpoint_{hash(str(tool_calls))[:8]}.json"
            path.write_text(json.dumps(checkpoint, ensure_ascii=False))
            if self.verbose:
                print(f"  💾 Checkpoint 已保存: {path.name}")
        except Exception:
            pass  # checkpoint 保存失败不应影响主流程

    # ================================================================
    # 底层 API 调用 (不变)
    # ================================================================

    def _chat_anthropic_with_history(self, system_prompt: str, messages: list[dict],
                                      tools: list[dict]) -> dict:
        """Anthropic API 调用 (支持消息历史 + 工具)"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("请安装 anthropic SDK: pip install anthropic")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("请设置 ANTHROPIC_API_KEY 环境变量")

        client = anthropic.Anthropic(api_key=api_key)

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": messages,
            "tools": tools,
        }

        response = client.messages.create(**kwargs)
        return {
            "content": response.content,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }

    def _chat_anthropic(self, system_prompt: str, user_message: str,
                        tools: Optional[list[dict]] = None,
                        tool_choice: Optional[str] = None) -> LLMResponse:
        try:
            import anthropic
        except ImportError:
            raise ImportError("请安装 anthropic SDK: pip install anthropic")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("请设置 ANTHROPIC_API_KEY 环境变量")

        client = anthropic.Anthropic(api_key=api_key)

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = {"type": "auto"}

        if self.verbose:
            print(f"[LLM] Calling {self.model}...")

        response = client.messages.create(**kwargs)

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                content += f"\n[TOOL USE: {block.name}]\n{json.dumps(block.input, indent=2)}"

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    def _chat_deepseek(self, system_prompt: str, user_message: str) -> LLMResponse:
        """DeepSeek API (OpenAI 兼容格式)"""
        import requests

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
            timeout=self.request_timeout,
        )
        data = response.json()
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            usage=data.get("usage", {}),
        )

    def _chat_openai(self, system_prompt: str, user_message: str,
                     tools: Optional[list[dict]] = None) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("请安装 openai SDK: pip install openai")

        client = OpenAI()
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
        )

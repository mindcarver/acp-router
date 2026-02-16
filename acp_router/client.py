"""ACP Router 主客户端

提供统一的接口来调用多个 ACP 后端。
"""

from __future__ import annotations

import os
from typing import Any, Optional
from dataclasses import dataclass, field

from acp_router.backends.base import BackendBase, ChatResponse
from acp_router.backends import OpenCodeBackend, ClaudeBackend
from acp_router.config import get_config, Config


@dataclass
class CompletionChoice:
    """OpenAI 风格的 Choice"""
    message: "CompletionMessage"
    finish_reason: str | None = None
    index: int = 0


@dataclass
class CompletionMessage:
    """OpenAI 风格的 Message"""
    role: str = "assistant"
    content: str = ""


@dataclass
class CompletionResponse:
    """OpenAI 风格的响应"""
    choices: list[CompletionChoice] = field(default_factory=list)
    model: str | None = None
    usage: dict | None = None


@dataclass
class CompletionUsage:
    """Token 使用情况"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ACPRouter:
    """统一的 ACP 后端路由器

    通过统一接口调用多个 AI 编码 Agent：
    - OpenCode (原生 ACP)
    - Claude Code (ACP 适配器)

    示例:
        router = ACPRouter(backend="opencode")
        response = router.chat([{"role": "user", "content": "写一个快排"}])
    """

    # 后端注册表
    _backends = {
        "opencode": OpenCodeBackend,
        "claude": ClaudeBackend,
        "claude-code": ClaudeBackend,
    }

    def __init__(
        self,
        backend: str | None = None,
        config: Config | None = None,
    ):
        """
        初始化 ACP Router

        Args:
            backend: 后端名称 ("opencode", "claude")
                     默认从环境变量 ACP_BACKEND 读取
            config: 配置对象，默认使用 get_config()
        """
        self.config = config or get_config()
        # 如果没有指定 backend，优先从环境变量读取（而不是从已创建的 config）
        if backend is None:
            backend = os.environ.get("ACP_BACKEND")
            if backend is None:
                backend = self.config.backend
        self.backend_name = backend

        if self.backend_name not in self._backends:
            available = list(self._backends.keys())
            raise ValueError(
                f"未知后端: {self.backend_name}. "
                f"可用后端: {available}"
            )

        self._backend_instance: Optional[BackendBase] = None

    @property
    def backend(self) -> BackendBase:
        """获取后端实例（懒加载）"""
        if self._backend_instance is None:
            backend_class = self._backends[self.backend_name]
            self._backend_instance = backend_class()
        return self._backend_instance

    def start(self) -> None:
        """启动后端进程"""
        if not self.backend.is_started():
            self.backend.start()

    def stop(self) -> None:
        """停止后端进程"""
        if self._backend_instance and self._backend_instance.is_started():
            self._backend_instance.stop()
            self._backend_instance = None

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称（可选）
            temperature: 温度参数 (0.0-1.0)
            max_tokens: 最大 tokens
            **kwargs: 其他参数

        Returns:
            str: 生成的文本内容
        """
        self.start()
        response = self.backend.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.content

    # OpenAI 兼容接口
    class ChatCompletions:
        """OpenAI 风格的 chat.completions 接口"""

        def __init__(self, router: ACPRouter):
            self.router = router

        def create(
            self,
            messages: list[dict],
            model: str | None = None,
            temperature: float = 0.7,
            max_tokens: int = 4096,
            **kwargs: Any,
        ) -> CompletionResponse:
            """
            OpenAI 风格的 chat.completions.create

            Args:
                messages: 消息列表
                model: 模型名称
                temperature: 温度
                max_tokens: 最大 tokens
                **kwargs: 其他参数

            Returns:
                CompletionResponse: OpenAI 风格的响应
            """
            self.router.start()
            backend_response = self.router.backend.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # 构造 OpenAI 风格的响应
            choice = CompletionChoice(
                message=CompletionMessage(
                    role="assistant",
                    content=backend_response.content,
                ),
                finish_reason=backend_response.finish_reason,
            )

            usage = None
            if backend_response.usage:
                usage = CompletionUsage(
                    prompt_tokens=backend_response.usage.get("prompt_tokens", 0),
                    completion_tokens=backend_response.usage.get("completion_tokens", 0),
                    total_tokens=backend_response.usage.get("total_tokens", 0),
                )

            return CompletionResponse(
                choices=[choice],
                model=backend_response.model,
                usage=usage,
            )

    @property
    def chat_completions(self) -> ChatCompletions:
        """OpenAI 风格的 chat.completions 属性"""
        return ACPRouter.ChatCompletions(self)

    def completions(self) -> "Completions":
        """OpenAI 风格的 completions 属性"""
        return Completions(self)

    @property
    def capabilities(self):
        """获取当前后端的能力"""
        return self.backend.capabilities

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


class Completions:
    """OpenAI 风格的 completions 接口"""

    def __init__(self, router: ACPRouter):
        self.router = router

    def create(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> CompletionResponse:
        """completion.create (实际上是 chat.completions)"""
        return self.router.chat.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

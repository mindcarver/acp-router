"""后端基类

定义所有后端必须实现的接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    model: str | None = None
    finish_reason: str | None = None
    usage: dict | None = None


@dataclass
class BackendCapabilities:
    """后端能力声明"""
    chat: bool = True
    streaming: bool = False
    function_calling: bool = False
    max_tokens: int = 4096


class BackendBase(ABC):
    """后端抽象基类

    所有 ACP 后端必须实现此接口。
    """

    def __init__(self):
        self._started = False

    @abstractmethod
    def start(self) -> None:
        """启动后端进程"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止后端进程"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ChatResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称（可选）
            temperature: 温度参数
            max_tokens: 最大 tokens
            **kwargs: 其他参数

        Returns:
            ChatResponse: 聊天响应
        """
        pass

    @property
    @abstractmethod
    def capabilities(self) -> BackendCapabilities:
        """返回后端支持的能力"""
        pass

    def is_started(self) -> bool:
        """检查后端是否已启动"""
        return self._started

    def __enter__(self):
        self.start()
        self._started = True
        return self

    def __exit__(self, *args):
        self.stop()
        self._started = False

"""Claude Code SDK 后端实现

通过 claude-code-sdk 与本地 Claude Code CLI 通信。
使用 ANTHROPIC_AUTH_TOKEN 认证，无需 API key。
"""

import asyncio
import os
from typing import Any

from acp_router.backends.base import BackendBase, ChatResponse, BackendCapabilities
from acp_router.config import get_config


class ClaudeSDKBackend(BackendBase):
    """Claude Code SDK 后端

    使用 claude-code-sdk 与本地 Claude Code 通信。
    支持 ANTHROPIC_AUTH_TOKEN 认证方式。

    环境变量:
        ANTHROPIC_AUTH_TOKEN: 认证 token (必需)
        ANTHROPIC_BASE_URL: API 端点 (可选，用于自定义后端)
    """

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self._model: str | None = None
        self._last_session_id: str | None = None

    def start(self) -> None:
        """启动后端（SDK 模式无需预启动进程）"""
        if self._started:
            return

        # 验证环境变量
        auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not auth_token and not api_key:
            raise RuntimeError(
                "Claude Code SDK 需要认证。请设置环境变量:\n"
                "  ANTHROPIC_AUTH_TOKEN=xxx (推荐，使用 Claude 订阅)\n"
                "  或 ANTHROPIC_API_KEY=xxx (使用 API key)"
            )

        self._started = True

    def stop(self) -> None:
        """停止后端（SDK 模式无需清理）"""
        self._started = False
        self._last_session_id = None

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ChatResponse:
        """通过 SDK 发送聊天请求"""
        if not self._started:
            raise RuntimeError("Claude Code SDK 后端未启动")

        # 提取最后一条用户消息作为 prompt
        prompt = self._extract_prompt(messages)

        # 运行异步查询
        return asyncio.run(self._async_chat(prompt, model, kwargs))

    async def _async_chat(
        self,
        prompt: str,
        model: str | None,
        options: dict[str, Any],
    ) -> ChatResponse:
        """异步聊天实现"""
        try:
            from claude_code_sdk import query, ClaudeCodeOptions
        except ImportError:
            raise ImportError("claude-code-sdk 未安装。请运行: pip install claude-code-sdk")

        # 构建 SDK 选项
        sdk_options = ClaudeCodeOptions(
            max_turns=options.get("max_turns", 1),
            model=model,
        )

        # 支持会话继续
        if options.get("continue_conversation") and self._last_session_id:
            sdk_options.resume = self._last_session_id

        # 收集响应
        content = ""
        result_msg = None

        async for msg in query(prompt=prompt, options=sdk_options):
            if hasattr(msg, "content") and hasattr(msg.content, "__iter__"):
                # AssistantMessage with content blocks
                for block in msg.content:
                    if hasattr(block, "text"):
                        content += block.text
            elif hasattr(msg, "result"):
                # ResultMessage
                result_msg = msg
                if hasattr(msg, "session_id"):
                    self._last_session_id = msg.session_id

        return ChatResponse(
            content=content,
            model=model,
            finish_reason="stop" if result_msg else None,
            usage={"cost_usd": getattr(result_msg, "cost_usd", None)} if result_msg else None,
        )

    def _extract_prompt(self, messages: list[dict]) -> str:
        """从消息列表提取 prompt"""
        # 优先使用最后一条用户消息
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")

        # 如果没有用户消息，拼接所有内容
        return "\n".join(m.get("content", "") for m in messages)

    @property
    def capabilities(self) -> BackendCapabilities:
        """Claude Code SDK 能力声明"""
        return BackendCapabilities(
            chat=True,
            streaming=False,  # SDK 模式下流式需要额外处理
            function_calling=True,
            max_tokens=200000,
        )

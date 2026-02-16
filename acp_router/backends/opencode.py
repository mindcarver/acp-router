"""OpenCode 后端实现

通过 ACP 协议与 OpenCode 通信。
"""

from acp_router.backends.base import BackendBase, ChatResponse, BackendCapabilities
from acp_router.transport import ACPTransport
from acp_router.config import get_config


class OpenCodeBackend(BackendBase):
    """OpenCode 后端

    使用原生 ACP 协议与 OpenCode 通信。
    启动命令: `opencode acp`
    """

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.transport: ACPTransport | None = None

    def start(self) -> None:
        """启动 OpenCode 子进程"""
        if self._started:
            return

        self.transport = ACPTransport(
            command=self.config.opencode_command,
            args=self.config.opencode_args,
            client_info={"name": "acp-router", "version": "0.1.0"},
            timeout=self.config.request_timeout,
        )
        self.transport.start()
        self._started = True

    def stop(self) -> None:
        """停止 OpenCode 子进程"""
        if self.transport:
            self.transport.stop()
            self.transport = None
        self._started = False

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ChatResponse:
        """通过 ACP 发送聊天请求

        使用 ACP 协议的 session/new 和 session/prompt 方法
        """
        if not self._started or not self.transport:
            raise RuntimeError("OpenCode 后端未启动")

        # 创建会话 (需要 cwd 和 mcpServers 参数)
        import os
        cwd = os.getcwd()
        session_result = self.transport.send_request(
            "session/new",
            {
                "cwd": cwd,
                "mcpServers": [],  # 暂时不使用 MCP
            }
        )

        session_id = session_result.get("sessionId") or session_result.get("id")
        if not session_id:
            raise RuntimeError(f"无法创建会话: {session_result}")

        # 发送 prompt (使用 ACP ContentBlock 格式)
        # ACP 要求每个消息块有 type 和 text 字段
        messages_for_acp = []
        for msg in messages:
            messages_for_acp.append({
                "type": "text",
                "text": msg.get("content", "")
            })

        # 发送请求并收集通知（用于获取流式响应）
        prompt_result, notifications = self.transport.send_request(
            "session/prompt",
            {
                "sessionId": session_id,
                "prompt": messages_for_acp,
            },
            collect_notifications=True,
        )

        # 解析响应 - 从通知中提取文本内容
        return self._parse_response_with_notifications(prompt_result, notifications)

    def _parse_response_with_notifications(self, result: dict, notifications: list) -> ChatResponse:
        """解析 ACP session/prompt 响应和通知为 ChatResponse"""
        content = ""
        model = None
        finish_reason = None
        usage = None

        # 从通知中提取 agent_message_chunk 内容
        for notification in notifications:
            params = notification.get("params", {})
            update = params.get("update", {})

            # 检查是否是 agent_message_chunk 类型
            if update.get("sessionUpdate") == "agent_message_chunk":
                content_block = update.get("content", {})
                if content_block.get("type") == "text":
                    text = content_block.get("text", "")
                    content += text

        # 检查最终响应中的 stopReason
        if isinstance(result, dict):
            finish_reason = result.get("stopReason")

        # 如果没有从通知中获取到内容，尝试从 result 中获取
        if not content and isinstance(result, dict):
            if "content" in result:
                content = result["content"]
            elif "message" in result:
                msg = result["message"]
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                else:
                    content = str(msg)
            elif "text" in result:
                content = result["text"]
            elif "completion" in result:
                content = result["completion"]

            model = result.get("model")
            usage = result.get("usage")

        if not isinstance(content, str):
            content = str(content)

        return ChatResponse(
            content=content,
            model=model,
            finish_reason=finish_reason,
            usage=usage,
        )

    def _parse_response(self, result: dict) -> ChatResponse:
        """解析 ACP session/prompt 响应为 ChatResponse"""
        content = ""
        model = None
        finish_reason = None
        usage = None

        if isinstance(result, dict):
            # session/prompt 响应格式
            if "content" in result:
                content = result["content"]
            elif "message" in result:
                msg = result["message"]
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                else:
                    content = str(msg)
            elif "text" in result:
                content = result["text"]
            elif "completion" in result:
                content = result["completion"]

            model = result.get("model")
            usage = result.get("usage")

        if not isinstance(content, str):
            content = str(content)

        return ChatResponse(
            content=content,
            model=model,
            finish_reason=finish_reason,
            usage=usage,
        )

    @property
    def capabilities(self) -> BackendCapabilities:
        """OpenCode 能力声明"""
        return BackendCapabilities(
            chat=True,
            streaming=True,
            function_calling=True,
            max_tokens=128000,
        )

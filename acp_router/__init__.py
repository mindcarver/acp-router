"""ACP Router - 统一的 ACP 后端路由器

支持通过统一的接口调用多个 AI 编码 Agent:
- OpenCode (原生 ACP)
- Claude Code (ACP 适配器)
"""

from acp_router.client import ACPRouter
from acp_router.config import Config, get_config
from acp_router.backends import (
    BackendBase,
    OpenCodeBackend,
    ClaudeBackend,
)

__version__ = "0.1.0"
__all__ = [
    "ACPRouter",
    "Config",
    "get_config",
    "BackendBase",
    "OpenCodeBackend",
    "ClaudeBackend",
]

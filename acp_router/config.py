"""配置管理模块

从环境变量加载配置，提供默认值。
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Config:
    """ACP Router 配置

    通过环境变量配置，支持合理的默认值。
    """

    # 后端选择
    backend: str = field(default_factory=lambda: os.environ.get("ACP_BACKEND", "opencode"))

    # 命令路径
    opencode_command: str = field(default_factory=lambda: os.environ.get("OPENCODE_CMD", "opencode"))
    claude_command: str = field(default_factory=lambda: os.environ.get("CLAUDE_CMD", "claude"))
    gemini_command: str = field(default_factory=lambda: os.environ.get("GEMINI_CMD", "gemini-cli"))

    # ACP 配置
    acp_protocol_version: str = "2024-11-05"
    request_timeout: int = field(default_factory=lambda: int(os.environ.get("ACP_TIMEOUT", "120")))

    # 启动参数
    opencode_args: list[str] = field(default_factory=lambda:
        os.environ.get("OPENCODE_ARGS", "acp").split()
    )
    claude_args: list[str] = field(default_factory=lambda:
        os.environ.get("CLAUDE_ARGS", "--acp").split()
    )
    gemini_args: list[str] = field(default_factory=lambda:
        os.environ.get("GEMINI_ARGS", "acp").split()
    )

    # 客户端信息
    client_name: str = "acp-router"
    client_version: str = "0.1.0"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "backend": self.backend,
            "opencode_command": self.opencode_command,
            "claude_command": self.claude_command,
            "gemini_command": self.gemini_command,
            "acp_protocol_version": self.acp_protocol_version,
            "request_timeout": self.request_timeout,
        }


# 全局配置实例
_config: Config | None = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config) -> None:
    """设置全局配置"""
    global _config
    _config = config

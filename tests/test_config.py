"""配置模块测试"""

import os
import pytest

from acp_router.config import Config, get_config, set_config


def test_default_config():
    """测试默认配置"""
    config = Config()
    assert config.backend == "opencode"
    assert config.opencode_command == "opencode"
    assert config.claude_command == "claude"
    assert config.request_timeout == 120


def test_config_from_env():
    """测试从环境变量加载配置"""
    os.environ["ACP_BACKEND"] = "claude"
    os.environ["CLAUDE_CMD"] = "custom-claude"
    os.environ["ACP_TIMEOUT"] = "60"

    config = Config()
    assert config.backend == "claude"
    assert config.claude_command == "custom-claude"
    assert config.request_timeout == 60

    # 清理
    del os.environ["ACP_BACKEND"]
    del os.environ["CLAUDE_CMD"]
    del os.environ["ACP_TIMEOUT"]


def test_get_config_singleton():
    """测试配置单例"""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2


def test_set_config():
    """测试设置配置"""
    new_config = Config(backend="claude")
    set_config(new_config)

    assert get_config().backend == "claude"

    # 恢复默认
    set_config(Config())

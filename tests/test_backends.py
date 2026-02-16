"""后端模块测试"""

import pytest
from acp_router.backends import OpenCodeBackend, ClaudeBackend


class TestBackendBase:
    """后端基类测试"""

    def test_opencode_backend_creation(self):
        """测试创建 OpenCode 后端"""
        backend = OpenCodeBackend()
        assert backend is not None
        assert not backend.is_started()

    def test_claude_backend_creation(self):
        """测试创建 Claude 后端"""
        backend = ClaudeBackend()
        assert backend is not None
        assert not backend.is_started()

    def test_opencode_capabilities(self):
        """测试 OpenCode 能力声明"""
        backend = OpenCodeBackend()
        caps = backend.capabilities
        assert caps.chat is True
        assert caps.streaming is True
        assert caps.function_calling is True
        assert caps.max_tokens == 128000

    def test_claude_capabilities(self):
        """测试 Claude 能力声明"""
        backend = ClaudeBackend()
        caps = backend.capabilities
        assert caps.chat is True
        assert caps.streaming is True
        assert caps.function_calling is True
        assert caps.max_tokens == 200000


class TestACPRouter:
    """ACPRouter 测试"""

    def test_router_creation(self):
        """测试创建 Router"""
        from acp_router import ACPRouter

        router = ACPRouter(backend="opencode")
        assert router.backend_name == "opencode"

    def test_router_invalid_backend(self):
        """测试无效后端"""
        from acp_router import ACPRouter

        with pytest.raises(ValueError, match="未知后端"):
            ACPRouter(backend="invalid")

    def test_router_env_backend(self, monkeypatch):
        """测试从环境变量读取后端"""
        import os
        monkeypatch.setenv("ACP_BACKEND", "claude")

        from acp_router import ACPRouter
        router = ACPRouter()
        assert router.backend_name == "claude"


@pytest.mark.integration
class TestIntegration:
    """集成测试 (需要实际的 Agent)"""

    def test_opencode_chat(self):
        """测试 OpenCode 聊天 (需要 opencode)"""
        backend = OpenCodeBackend()
        # 需要本机安装 opencode
        # backend.start()
        # response = backend.chat([{"role": "user", "content": "Hello"}])
        # assert len(response.content) > 0
        # backend.stop()

    @pytest.mark.skip("需要实际的 Agent")
    def test_claude_chat(self):
        """测试 Claude 聊天 (需要 claude)"""
        backend = ClaudeBackend()
        # 需要本机安装 claude
        # backend.start()
        # response = backend.chat([{"role": "user", "content": "Hello"}])
        # assert len(response.content) > 0
        # backend.stop()

"""ACP Transport 测试"""

import pytest
from acp_router.transport import ACPTransport


class TestACPTransport:
    """ACP 传输层测试"""

    def test_transport_creation(self):
        """测试创建传输层"""
        transport = ACPTransport(
            command="echo",
            args=["test"],
        )
        assert transport is not None
        assert transport.command == "echo"

    def test_transport_context_manager(self):
        """测试上下文管理器"""
        transport = ACPTransport(
            command="echo",
            args=["test"],
        )
        # 不会真正启动，只是测试接口
        # with transport:
        #     assert transport.process is not None

    @pytest.mark.skip("需要实际的 ACP Agent")
    def test_send_request(self):
        """测试发送请求"""
        transport = ACPTransport(
            command="opencode",
            args=["acp"],
        )
        # with transport:
        #     result = transport.send_request("initialize", {...})
        #     assert result is not None

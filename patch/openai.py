"""OpenAI 模块运行时补丁

替换 openai 模块的调用，使用 ACP Router 作为后端。
"""

import os
from typing import Any

# 全局补丁状态
_original_openai_methods = {}
_patched = False
_router_instance = None


def patch_openai(backend: str | None = None) -> None:
    """
    补丁 openai 模块

    将 openai.OpenAI().chat.completions.create 的调用替换为 ACP Router

    Args:
        backend: 要使用的后端 ("opencode", "claude")
                 默认从环境变量 ACP_BACKEND 读取

    示例:
        import acp_router.patch
        acp_router.patch.patch_openai(backend="opencode")

        import openai
        client = openai.OpenAI()
        response = client.chat.completions.create(...)  # 实际调用 OpenCode
    """
    global _patched, _router_instance

    if _patched:
        return

    try:
        import openai
    except ImportError:
        raise ImportError("openai 模块未安装，无法补丁")

    # 保存原始方法
    original_create = openai.OpenAI().chat.completions.create
    _original_openai_methods["create"] = original_create

    # 导入 ACPRouter（延迟导入避免循环依赖）
    from acp_router import ACPRouter

    # 创建补丁函数
    def patched_create(self, *args, **kwargs):
        # 检查是否启用 ACP
        if not os.environ.get("ACP_BACKEND") and backend is None:
            return original_create(self, *args, **kwargs)

        # 获取或创建 router 实例
        global _router_instance
        if _router_instance is None:
            _router_instance = ACPRouter(backend=backend)
            _router_instance.start()

        # 提取参数
        messages = kwargs.get("messages")
        if messages is None and args:
            messages = args[0]

        if messages is None:
            return original_create(self, *args, **kwargs)

        # 调用 ACP Router
        model = kwargs.get("model")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)

        response = _router_instance.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 构造 OpenAI 风格的响应
        return _wrap_openai_response(response)

    # 应用补丁
    openai.OpenAI().chat.completions.create = patched_create
    _patched = True


def unpatch_openai() -> None:
    """恢复 openai 模块的原始方法"""
    global _patched, _router_instance

    if not _patched:
        return

    try:
        import openai
    except ImportError:
        return

    # 恢复原始方法
    if "create" in _original_openai_methods:
        openai.OpenAI().chat.completions.create = _original_openai_methods["create"]

    # 清理 router
    if _router_instance:
        _router_instance.stop()
        _router_instance = None

    _original_openai_methods.clear()
    _patched = False


def _wrap_openai_response(content: str) -> Any:
    """将 ACP 响应包装为 OpenAI 风格"""
    # 创建一个简单的 OpenAI 风格响应对象
    class OpenAIResponse:
        def __init__(self, content: str):
            self.choices = [OpenAIChoice(content)]

    class OpenAIChoice:
        def __init__(self, content: str):
            self.message = OpenAIMessage(content)

    class OpenAIMessage:
        def __init__(self, content: str):
            self.content = content

    return OpenAIResponse(content)


def is_patched() -> bool:
    """检查 openai 模块是否已被补丁"""
    return _patched

"""运行时补丁模块

提供运行时补丁功能，将 openai 模块的调用替换为 ACP Router。
"""

from acp_router.patch.openai import patch_openai, unpatch_openai

__all__ = ["patch_openai", "unpatch_openai"]

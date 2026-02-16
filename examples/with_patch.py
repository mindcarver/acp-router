"""运行时补丁使用示例

展示如何使用运行时补丁替换 openai 模块。
"""

import os

# 设置 ACP 后端
os.environ["ACP_BACKEND"] = "opencode"

# 应用补丁（必须在导入 openai 之前）
import acp_router.patch
acp_router.patch.patch_openai()

# 现在可以正常使用 openai 模块
import openai


def example_with_patching():
    """使用补丁后的 openai 模块"""
    print("=== 运行时补丁示例 ===")
    print("注意: 实际调用的是 OpenCode (通过 ACP)")

    # 创建 OpenAI 客户端
    client = openai.OpenAI()

    # 这个调用实际上会路由到 OpenCode
    response = client.chat.completions.create(
        model="gpt-4",  # model 参数会被忽略
        messages=[
            {"role": "system", "content": "你是一个简洁的编程助手"},
            {"role": "user", "content": "用一句话解释什么是递归"}
        ],
        temperature=0.7,
    )

    print(f"\n响应:\n{response.choices[0].message.content}")


def example_unpatch():
    """恢复补丁"""
    print("\n\n=== 恢复补丁示例 ===")

    acp_router.patch.unpatch_openai()
    print("openai 模块已恢复正常")

    # 现在会使用真正的 OpenAI API
    # response = openai.OpenAI().chat.completions.create(...)


if __name__ == "__main__":
    # 检查是否启用 ACP
    if not os.environ.get("ACP_BACKEND"):
        print("请设置 ACP_BACKEND 环境变量")
        print("例如: export ACP_BACKEND=opencode")
    else:
        example_with_patching()
        # example_unpatch()  # 取消注释以测试恢复功能

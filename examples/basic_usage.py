"""基础使用示例

展示如何使用 ACP Router 调用不同的后端。
"""

import os
from acp_router import ACPRouter


def example_opencode():
    """使用 OpenCode 后端"""
    print("=== OpenCode 示例 ===")

    with ACPRouter(backend="opencode") as router:
        response = router.chat([
            {"role": "user", "content": "用 Python 写一个快速排序算法"}
        ])
        print(response)


def example_claude():
    """使用 Claude Code 后端"""
    print("\n=== Claude Code 示例 ===")

    # 设置环境变量
    os.environ["ACP_BACKEND"] = "claude"

    router = ACPRouter()
    response = router.chat([
        {"role": "user", "content": "解释一下什么是快速排序"}
    ])
    print(response)
    router.stop()


def example_openai_compatible():
    """OpenAI 兼容接口"""
    print("\n=== OpenAI 兼容接口示例 ===")

    router = ACPRouter(backend="opencode")

    # 使用 OpenAI 风格的 API
    response = router.chat.completions.create(
        messages=[
            {"role": "system", "content": "你是一个编程助手"},
            {"role": "user", "content": "写一个冒泡排序"}
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    print(f"Model: {response.model}")
    print(f"Content: {response.choices[0].message.content}")

    router.stop()


def example_with_environment():
    """通过环境变量控制后端"""
    print("\n=== 环境变量控制示例 ===")

    # 设置环境变量
    os.environ["ACP_BACKEND"] = "opencode"
    os.environ["OPENCODE_CMD"] = "opencode"

    router = ACPRouter()  # 自动从环境变量读取
    print(f"当前后端: {router.backend_name}")
    print(f"后端能力: {router.capabilities}")

    router.stop()


if __name__ == "__main__":
    # 根据环境选择运行哪个示例
    backend = os.environ.get("ACP_BACKEND", "opencode")

    if backend == "opencode":
        example_opencode()
    elif backend == "claude":
        example_claude()
    else:
        print(f"请设置 ACP_BACKEND 环境变量 (opencode/claude)")

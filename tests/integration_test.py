"""集成测试 - 直接测试 ACP Router

测试 ACP Router 与实际后端 (OpenCode/Claude Code) 的集成。
"""

import os
import sys
import time

# 添加项目路径
sys.path.insert(0, "/Users/mac08/workspace/acp-router")

from acp_router import ACPRouter


def test_backend_availability(backend: str, command: str) -> bool:
    """检查后端是否可用"""
    import shutil

    return shutil.which(command) is not None


def test_opencode_integration():
    """测试 OpenCode 集成"""
    print("\n=== OpenCode 集成测试 ===")

    if not test_backend_availability("opencode", "opencode"):
        print("⚠️  OpenCode 未安装，跳过测试")
        return

    os.environ["ACP_BACKEND"] = "opencode"

    try:
        router = ACPRouter()
        print(f"后端: {router.backend_name}")
        print(f"能力: {router.capabilities}")

        # 测试简单对话
        print("\n发送: 你好")
        response = router.chat([{"role": "user", "content": "你好，请用一句话介绍你自己"}])
        print(f"响应: {response[:100]}...")

        router.stop()
        print("✅ OpenCode 集成测试通过")
        return True

    except Exception as e:
        print(f"❌ OpenCode 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_claude_integration():
    """测试 Claude Code 集成（SDK 模式）"""
    print("\n=== Claude Code 集成测试 (SDK 模式) ===")

    # 检查认证环境变量
    import os

    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not auth_token and not api_key:
        print("⚠️  Claude Code 未配置认证，跳过测试")
        print("    请设置 ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY")
        return

    os.environ["ACP_BACKEND"] = "claude"

    try:
        router = ACPRouter()
        print(f"后端: {router.backend_name}")
        print(f"能力: {router.capabilities}")

        # 测试简单对话
        print("\n发送: Hello")
        response = router.chat([{"role": "user", "content": "Hello, please say hi back"}])
        print(f"响应: {response[:100]}...")

        router.stop()
        print("✅ Claude Code 集成测试通过")
        return True

    except Exception as e:
        print(f"❌ Claude Code 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_openai_compatible_api():
    """测试 OpenAI 兼容 API"""
    print("\n=== OpenAI 兼容 API 测试 ===")

    if not test_backend_availability("opencode", "opencode"):
        print("⚠️  OpenCode 未安装，跳过测试")
        return

    os.environ["ACP_BACKEND"] = "opencode"

    try:
        router = ACPRouter()

        # 使用 OpenAI 风格的 API
        response = router.chat_completions.create(
            messages=[
                {"role": "system", "content": "你是一个简洁的助手"},
                {"role": "user", "content": "说 '测试成功'"},
            ],
            temperature=0.7,
        )

        print(f"Model: {response.model}")
        print(f"Content: {response.choices[0].message.content}")

        router.stop()
        print("✅ OpenAI 兼容 API 测试通过")
        return True

    except Exception as e:
        print(f"❌ OpenAI 兼容 API 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_code_generation():
    """测试代码生成"""
    print("\n=== 代码生成测试 ===")

    if not test_backend_availability("opencode", "opencode"):
        print("⚠️  OpenCode 未安装，跳过测试")
        return

    os.environ["ACP_BACKEND"] = "opencode"

    try:
        router = ACPRouter()

        print("请求: 写一个 Python 快速排序")
        response = router.chat(
            [{"role": "user", "content": "用 Python 写一个快速排序函数，要简洁"}]
        )

        # 检查响应是否包含代码
        has_code = "def " in response or "quick_sort" in response.lower() or "快速排序" in response
        print(f"响应长度: {len(response)} 字符")
        print(f"包含代码: {has_code}")

        router.stop()

        if has_code:
            print("✅ 代码生成测试通过")
            return True
        else:
            print("⚠️  响应可能不包含代码")
            return False

    except Exception as e:
        print(f"❌ 代码生成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有集成测试"""
    print("=" * 60)
    print("ACP Router 集成测试")
    print("=" * 60)

    # 检查可用后端
    import shutil

    available = []
    if shutil.which("opencode"):
        available.append("OpenCode")
    if shutil.which("claude"):
        available.append("Claude Code")

    print(f"\n可用后端: {', '.join(available) if available else '无'}")

    if not available:
        print("\n❌ 没有可用的后端，请安装:")
        print("  - OpenCode: https://github.com/axter/opencode")
        print("  - Claude Code: https://claude.ai/code")
        return

    # 运行测试
    results = []
    results.append(("OpenCode", test_opencode_integration()))
    results.append(("Claude Code", test_claude_integration()))
    results.append(("OpenAI API", test_openai_compatible_api()))
    results.append(("代码生成", test_code_generation()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(p for _, p in results)
    if all_passed:
        print("\n🎉 所有集成测试通过!")
    else:
        print("\n⚠️  部分测试失败")


if __name__ == "__main__":
    main()

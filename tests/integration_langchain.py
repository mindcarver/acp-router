"""集成测试 - 使用 LangChain Agent 测试 ACP Router

这个测试创建一个简单的 LangChain Agent，通过 ACP Router 调用后端。
"""

import os
from typing import Type

# 设置后端
os.environ["ACP_BACKEND"] = "opencode"

from langchain.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.outputs import LLMResult


class ACPRouterLLM(BaseLanguageModel):
    """ACP Router LLM - LangChain 兼容接口

    将 ACP Router 包装为 LangChain 的 BaseLanguageModel
    """

    @property
    def _llm_type(self) -> str:
        return "acp-router"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> LLMResult:
        """生成响应"""
        from acp_router import ACPRouter

        # 转换消息格式
        acp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                acp_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                acp_messages.append({"role": "assistant", "content": msg.content})

        # 调用 ACP Router
        router = ACPRouter()
        response = router.chat(acp_messages, **kwargs)

        # 构造 LangChain 响应
        generation = LLMResult(
            generations=[[AIMessage(content=response)]],
            llm_output={"model": "acp-router"},
        )
        return generation

    @property
    def IdentifyingParams(self):
        return {"model_name": "acp-router"}


# 定义工具
@tool
def calculator(expression: str) -> str:
    """执行数学计算

    Args:
        expression: 数学表达式，例如 "2 + 2"
    """
    try:
        result = eval(expression)
        return f"结果: {result}"
    except Exception as e:
        return f"错误: {e}"


@tool
def get_word_length(word: str) -> str:
    """获取单词的长度

    Args:
        word: 要计算长度的单词
    """
    return f"'{word}' 的长度是 {len(word)}"


def test_simple_chat():
    """测试简单对话"""
    print("\n=== 测试简单对话 ===")

    llm = ACPRouterLLM()

    response = llm.invoke("什么是 Python?")
    print(f"响应: {response.content[:100]}...")


def test_react_agent():
    """测试 ReAct Agent"""
    print("\n=== 测试 ReAct Agent ===")

    llm = ACPRouterLLM()

    # 定义 prompt 模板
    prompt = PromptTemplate.from_template(
        "回答以下问题。你有以下工具可用:\n"
        "{tools}\n"
        "使用以下格式:\n"
        "问题: {input}\n"
        "思考: {{思考过程}}\n"
        "操作: {{工具名称}}{{输入}}\n"
        "观察: {{结果}}\n"
        "... (重复思考/操作/观察)\n"
        "答案: {{最终答案}}\n"
    )

    # 创建 agent
    agent = create_react_agent(
        llm=llm,
        tools=[calculator, get_word_length],
        prompt=prompt,
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=[calculator, get_word_length],
        verbose=True,
        handle_parsing_errors=True,
    )

    # 测试问题
    questions = [
        "2 + 2 等于多少?",
        "'hello' 有几个字母?",
    ]

    for question in questions:
        print(f"\n问题: {question}")
        try:
            result = agent_executor.invoke({"input": question})
            print(f"答案: {result.get('output', '无答案')}")
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    # 检查后端是否可用
    backend = os.environ.get("ACP_BACKEND", "opencode")
    print(f"使用后端: {backend}")
    print(f"后端命令: {os.environ.get('OPENCODE_CMD', 'opencode')}")

    try:
        test_simple_chat()
        test_react_agent()
        print("\n✅ 集成测试完成!")
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()

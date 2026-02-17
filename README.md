<div align="center">

# ACP Router

**统一的 AI 编码 Agent 路由器**

一个简单的 Python 库，通过统一接口无缝调用多个 AI 编码 Agent

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ACP](https://img.shields.io/badge/ACP-2.0-purple.svg)](https://github.com/agentclientprotocol/agent-client-protocol)

</div>

---

## 📖 简介

**ACP Router** 是一个统一的接口层，让你通过一套 API 调用多个 AI 编码 Agent。无需修改现有代码，即可在 OpenCode、Claude Code 等后端之间自由切换。

### 为什么选择 ACP Router？

| 特性 | 说明 |
|------|------|
| 🔄 **统一接口** | 一套 API，支持多个后端 |
| 🚀 **多模式支持** | ACP 原生协议 + SDK 模式 |
| 🔌 **OpenAI 兼容** | 兼容 OpenAI SDK 风格的 API |
| 💰 **零费用** | 本地运行，无额外 API 调用费用 |
| 🔒 **数据安全** | 所有数据处理都在本地 |
| 🎨 **运行时补丁** | 无需修改现有代码即可迁移 |

---

## 🎯 支持的后端

| 后端 | 模式 | 认证方式 | 推荐用途 |
|------|------|----------|----------|
| **OpenCode** | ACP 原生 | 本地 CLI | 通用代码生成 |
| **Claude Code** | SDK | AUTH_TOKEN / API Key | 代码理解与重构 |

> 💡 **提示**: 更多后端支持正在开发中...

---

## 🚀 快速开始

### 安装

```bash
pip install acp-router
```

或从源码安装：

```bash
git clone https://github.com/your-org/acp-router.git
cd acp-router
pip install -e .
```

### 基础用法

#### OpenCode 后端

```python
from acp_router import ACPRouter

# 使用 OpenCode 后端（ACP 原生模式）
router = ACPRouter(backend="opencode")
response = router.chat([
    {"role": "user", "content": "写一个 Python 快速排序"}
])
print(response)
router.stop()
```

#### Claude Code 后端

```python
import os
from acp_router import ACPRouter

# 设置认证（使用 Claude 订阅的 auth token）
os.environ["ANTHROPIC_AUTH_TOKEN"] = "your-auth-token"
# 可选：自定义 API 端点
os.environ["ANTHROPIC_BASE_URL"] = "https://api.anthropic.com"

router = ACPRouter(backend="claude")
response = router.chat([
    {"role": "user", "content": "解释这段代码..."}
])
print(response)
router.stop()
```

### 上下文管理器（推荐）

```python
from acp_router import ACPRouter

# 自动管理后端生命周期
with ACPRouter(backend="opencode") as router:
    response = router.chat([
        {"role": "user", "content": "解释这段代码..."}
    ])
    print(response)
```

### OpenAI 兼容接口

```python
from acp_router import ACPRouter

router = ACPRouter(backend="opencode")

# 使用 OpenAI 风格的 API
response = router.chat_completions.create(
    messages=[
        {"role": "system", "content": "你是一个简洁的助手"},
        {"role": "user", "content": "用一句话解释递归"}
    ],
    temperature=0.7,
)

print(response.choices[0].message.content)
router.stop()
```

---

## ⚙️ 配置

### 环境变量

```bash
# 选择默认后端 (opencode / claude)
export ACP_BACKEND=opencode

# Claude Code 认证（二选一）
export ANTHROPIC_AUTH_TOKEN=your-auth-token  # 推荐：使用 Claude 订阅
export ANTHROPIC_API_KEY=your-api-key        # 或使用 API key

# 可选：自定义 API 端点
export ANTHROPIC_BASE_URL=https://api.anthropic.com

# 请求超时（秒）
export ACP_TIMEOUT=120
```

### 代码配置

```python
from acp_router import ACPRouter, Config

config = Config(
    backend="opencode",
    opencode_command="/usr/local/bin/opencode",
    opencode_args=["acp"],
    request_timeout=180,
)

router = ACPRouter(config=config)
```

---

## 📁 项目架构

```
acp-router/
├── acp_router/
│   ├── __init__.py           # 包入口
│   ├── client.py             # ACPRouter 主类
│   ├── config.py             # 配置管理
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── base.py            # BackendBase 抽象类
│   │   ├── opencode.py        # OpenCode 后端 (ACP 原生)
│   │   ├── claude.py          # Claude Code 后端 (ACP 模式)
│   │   └── claude_sdk.py      # Claude Code 后端 (SDK 模式)
│   └── transport/
│       ├── __init__.py
│       └── acp.py             # ACP JSON-RPC 传输层
├── examples/
│   ├── basic_usage.py         # 基础用法示例
│   └── with_langchain.py      # LangChain 集成
├── tests/
│   ├── test_backends.py       # 后端测试
│   ├── test_config.py         # 配置测试
│   └── integration_test.py    # 集成测试
├── pyproject.toml
└── README.md
```

### 核心组件

| 组件 | 职责 |
|------|------|
| **ACPRouter** | 统一的路由器接口，管理后端选择和生命周期 |
| **BackendBase** | 后端抽象类，定义统一的聊天接口 |
| **ACPTransport** | ACP JSON-RPC 2.0 传输层，处理进程通信 |
| **ClaudeSDKBackend** | Claude Code SDK 后端，支持 auth token 认证 |
| **Config** | 配置管理，支持环境变量和代码配置 |

---

## 🔌 高级用法

### 运行时补丁

无需修改现有代码，将 OpenAI 调用替换为本地后端：

```python
import acp_router.patch
acp_router.patch.openai()

# 现有代码无需修改
import openai
client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4",  # 会被忽略
    messages=[{"role": "user", "content": "Hello"}],
)
# 实际调用的是 OpenCode！
```

### 多轮对话

```python
from acp_router import ACPRouter

router = ACPRouter(backend="opencode")
router.start()

messages = [
    {"role": "user", "content": "什么是快速排序？"},
]

# 第一轮
response1 = router.chat(messages)
print(response1)

# 添加助手回复到上下文
messages.append({"role": "assistant", "content": response1})

# 第二轮
messages.append({"role": "user", "content": "给我一个 Python 实现"})
response2 = router.chat(messages)
print(response2)

router.stop()
```

### 与 LangChain 集成

```python
from langchain.llms.base import LLM
from acp_router import ACPRouter

class ACPRouterLLM(LLM):
    router: ACPRouter = None

    def __init__(self, backend: str = "opencode"):
        self.router = ACPRouter(backend=backend)
        self.router.start()

    def _call(self, prompt: str, stop=None) -> str:
        return self.router.chat([{"role": "user", "content": prompt}])

    @property
    def _llm_type(self) -> str:
        return "acp-router"

# 使用
llm = ACPRouterLLM(backend="opencode")
response = llm("写一个 Python 函数来计算斐波那契数列")
```

---

## 🧪 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行集成测试（需要配置后端）
# OpenCode: 确保 opencode CLI 已安装
# Claude Code: 设置 ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY
pytest tests/integration_test.py

# 查看测试覆盖率
pytest --cov=acp_router
```

### 代码格式化

```bash
# 使用 Black 格式化
black acp_router/

# 使用 Ruff 检查
ruff check acp_router/
```

---

## 📋 ACP 协议说明

ACP (Agent Client Protocol) 是一个标准化的通信协议，用于编辑器和 AI 编码 Agent 之间的通信。

### 关键概念

| 概念 | 说明 |
|------|------|
| **session/new** | 创建新的会话上下文 |
| **session/prompt** | 发送用户消息 |
| **session/update** | 接收流式响应（通知） |
| **ContentBlock** | 内容块，格式为 `{"type": "text", "text": "..."}` |

### 消息格式

```json
// session/prompt 请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "session/prompt",
  "params": {
    "sessionId": "sess_abc123",
    "prompt": [
      {"type": "text", "text": "解释这段代码..."}
    ]
  }
}

// session/update 响应（流式）
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "sessionId": "sess_abc123",
    "update": {
      "sessionUpdate": "agent_message_chunk",
      "content": {
        "type": "text",
        "text": "这段代码的功能是..."
      }
    }
  }
}
```

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [Agent Client Protocol](https://github.com/agentclientprotocol/agent-client-protocol) - ACP 协议规范
- [OpenCode](https://github.com/anomaly/opencode) - 开源的 AI 编码 Agent
- [Claude Code](https://claude.ai/code) - Anthropic 的 AI 编码助手
- [claude-code-sdk](https://github.com/anthropics/claude-code-sdk-python) - Claude Code Python SDK

---

<div align="center">

**Made with ❤️ by the ACP Router community**

</div>


# Neo: 本地自进化智能助手

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/Platform-macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</div>

**Neo** 是一个运行在本地 macOS 上的智能助手框架。与传统 AI 助手不同，Neo 具备**规划式任务执行**、**长期记忆**以及**自我编程进化**的能力。

它不仅仅是一个聊天机器人，更是一个能够通过编写代码来扩展自身能力的数字生命。

## ✨ 核心特性

- **🧠 规划式架构**: 
  Neo 在执行复杂任务前会先生成计划，能够拆解任务、评估工具可用性，而不是简单的“提示-响应”模式。
  
- **🛠️ 动态技能生成**: 
  当发现自身能力不足时（如“无法查询实时天气”），Neo 会自动编写 Python 代码、保存并在无需重启的情况下加载新技能，实现自我进化。

- **🧬 双子星记忆系统**: 
  - **Memory (对他人的认知)**: 记录用户偏好、历史对话摘要，通过“记忆蒸馏”压缩上下文。
  - **Soul (对自我的认知)**: 独立的“灵魂”模块，记录 Neo 的性格特质、价值观演变，使其具备稳定且独特的人格。

- **🔒 本地优先**: 
  数据存储在本地文件系统（`memory/`, `soul/`, `agent_skills/`），保护隐私，无需联网即可使用核心能力（LLM API 除外）。

- **🖥️ 双模式交互**: 
  提供强大的命令行界面 和 简洁的 Web 界面，均支持 Markdown 渲染与工具调用可视化。

## 📁 项目结构

```
Neo/
├── chat_cli.py           # 主入口：命令行交互模式
├── app.py                # Web UI 模式
├── llm_client.py         # LLM 统一调用客户端 (支持 OpenAI 兼容接口)
├── core/
│   └── skill_manager.py  # 核心引擎：技能加载、动态注册、生命周期管理
├── tools/                # 系统级内置技能
│   ├── __init__.py
│   ├── notes_skill.py    # 备忘录操作 (读写追加)
│   ├── memory_skill.py   # 记忆管理 (存储与蒸馏)
│   └── soul_skill.py     # 灵魂管理 (人格进化)
├── agent_skills/         # 【自动生成】Neo 自行编写的技能存放目录
├── memory/               # 【数据】用户记忆存储目录
└── soul/                 # 【数据】Neo 人格数据目录
```

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装 Python 3.10+。

```bash
# 克隆项目
git clone <your-repo-url>
cd Neo

# 安装依赖
pip install -r requirements.txt
```

依赖列表 (`requirements.txt`):
```text
openai
rich
streamlit
python-dotenv
watchdog
pyyaml
```

### 2. 配置 API Key

Neo 需要一个大模型作为“大脑”。你可以使用 OpenAI 或任何兼容 OpenAI 接口的服务（如 DeepSeek, QNAIGC 等）。

创建 `.env` 文件或在终端中设置环境变量：

```bash
export LLM_API_KEY="your-api-key-here"
export LLM_BASE_URL="https://api.openai.com/v1/chat/completions" # 可选，默认为 OpenAI
export LLM_MODEL="gpt-4o" # 推荐 gpt-4o 或 deepseek-chat
```

### 3. 启动 Neo

**命令行模式 (推荐开发调试):**
```bash
python chat_cli.py
```

**Web 模式 (推荐日常使用):**
```bash
streamlit run app.py
```

## 💡 使用指南

### 闲聊与任务分流
Neo 具备意图识别能力。对于简单的问候（“你好”），它会直接回复，不消耗规划算力；对于复杂任务，它会进入**任务模式**。

### 示例：自我进化演示

1.  **用户**: "帮我查一下北京明天的天气。"
2.  **Neo (规划)**: "我发现我没有天气查询工具。"
3.  **Neo (行动)**: "是否尝试自动编写该技能？"
4.  **用户**: "y"
5.  **Neo (编程)**: 生成 `auto_skill_xxxx.py`，自动安装并加载。
6.  **Neo (反馈)**: "我已经学会了查天气，请再试一次。"
7.  **用户**: "查北京天气。"
8.  **Neo (执行)**: 调用新技能，返回结果。

### 记忆与人格

*   **记忆积累**: 与 Neo 聊得越多，它越了解你。当对话积累到一定程度，它会自动提炼关键信息存入长期记忆。
*   **人格进化**: 每 10 轮对话，Neo 会进行一次“灵魂内省”，反思自己的说话风格和价值观，可能会变得更加幽默或严谨。

## 🛠️ 开发新技能

你可以手动为 Neo 编写技能，只需遵循以下规范：

1.  在 `tools/` 目录下创建 `my_skill.py`。
2.  实现 `run(arguments: dict)` 函数。
3.  实现 `get_tool_definition()` 函数，返回 OpenAI Tool Schema。
4.  重启 Neo，技能将自动加载。

**示例 Schema:**
```python
def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "my_skill",
            "description": "这是一个示例技能",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "输入文本"}
                },
                "required": ["input"]
            }
        }
    }
```

## ⚠️ 注意事项

*   **权限**: 操作备忘录和读取 iMessage 数据库需要 macOS 的“完全磁盘访问”权限。如果功能异常，请在 `系统设置 -> 隐私与安全性` 中为 Terminal 或 Python 解释器授权。
*   **Token 消耗**: 规划模式和记忆压缩会额外消耗 Token，建议使用成本较低的强力模型（如 GPT-4o-mini 或 DeepSeek）。

## 📜 License

MIT License
```

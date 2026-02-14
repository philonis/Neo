
# Neo: 本地自进化智能助手 / Local Self-Evolving AI Assistant

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/Platform-macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Architecture-ReAct-orange" alt="Architecture">
  <img src="https://img.shields.io/badge/AI-Agentic-purple" alt="Agentic AI">
</div>

[中文](#中文) | [English](#english)

---

<a name="中文"></a>
## 🇨🇳 中文

**Neo** 是一个基于 ReAct 架构的本地智能助手框架。与传统 AI 助手不同，Neo 具备**思考-行动-观察循环**、**原生 Function Calling**、**向量记忆系统**以及**自主编程进化**的能力。

它不仅仅是一个聊天机器人，更是一个能够自主规划、执行、反思并**编写代码扩展自身能力**的数字生命。

### ✨ 核心特性

#### 🧠 ReAct 架构
Neo 采用 ReAct (Reasoning + Acting) 模式工作：
- **Thought**: 分析当前状态，思考下一步
- **Action**: 选择并执行工具
- **Observation**: 观察执行结果
- **Loop**: 循环直到任务完成

这种架构使 Neo 能够自我修正、动态调整策略，而不是盲目执行预设计划。

#### 🌐 Browser Agent
Neo 具备**像真人一样使用浏览器**的能力：
- 自动导航、点击、填表、登录
- 处理动态渲染的页面
- 提取页面内容
- 安全护栏保护敏感操作
- 支持凭证加密存储

#### 💻 Desktop Agent
Neo 可以**像真人一样操作macOS应用**：
- 启动和激活本地应用（豆包、微信、Safari等）
- 在应用中输入文本、点击按钮
- 发送快捷键、读取窗口内容
- 支持40+常用应用

#### 🔧 自主编程能力
Neo 具备**自我编程进化**的能力：
- 当发现现有工具无法完成任务时，自动编写新技能
- 新技能创建后立即可用，无需重启
- 支持链式调用：搜索 → 获取数据 → 解析 → 返回结果
- 不会轻易说"无法完成"，而是主动尝试解决问题

#### ⚡ 原生 Function Calling
- 直接利用 LLM 的工具调用能力
- 无需手动解析 JSON 格式
- 更可靠的工具调用体验
- 支持多工具并行调用

#### 🛠️ 丰富的内置工具
| 工具 | 功能 |
|-----|------|
| `browser_agent` | 🌐 像真人一样使用浏览器 |
| `browser_agent_save_credentials` | 🔐 保存网站登录凭证 |
| `desktop_agent` | 💻 像真人一样操作macOS应用 |
| `desktop_list_common_apps` | 📱 列出支持的常用应用 |
| `notes_operator` | 📝 macOS 备忘录操作 |
| `web_search` | 🔍 网络搜索 |
| `http_request` | 🌍 HTTP 请求，获取网页/API 数据 |
| `rss_fetcher` | 📡 RSS/Atom 订阅解析 |
| `web_scraper` | 📄 网页内容提取 |
| `chat` | 💬 通用聊天 |
| `create_skill` | 🔧 动态创建新技能 |

#### 💾 向量记忆系统
- **短期记忆**: 最近对话，快速访问
- **长期记忆**: 重要信息，持久存储
- **语义检索**: 基于关键词的相关性搜索
- **自动压缩**: 定期总结和精简记忆

#### 🎵 富媒体渲染
- 自动检测并渲染图片
- 音频播放器（支持 MP3、播客、Spotify、Apple Podcasts 等）
- 地图显示
- 数据可视化图表

#### 🔒 本地优先
数据存储在本地文件系统，保护隐私，无需联网即可使用核心能力。

### 📁 项目结构

```
Neo/
├── app.py                  # Streamlit Web 界面
├── chat_cli.py             # 命令行交互模式
├── llm_client.py           # LLM 客户端 (支持原生 Function Calling)
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── react_agent.py      # ReAct Agent 核心 (含自主编程能力)
│   ├── planner.py          # 智能任务规划器
│   ├── memory.py           # 向量记忆系统
│   ├── skill_manager.py    # 增强型技能管理器
│   └── skill_generator.py  # 动态技能生成器
├── browser_agent/          # 🌐 浏览器自动化模块
│   ├── __init__.py
│   ├── browser_skill.py    # 主技能入口
│   ├── browser_controller.py # Playwright浏览器控制
│   ├── safety_guard.py     # 安全护栏系统
│   └── session_manager.py  # 会话和凭证管理
├── desktop_agent/          # 💻 macOS应用自动化模块
│   ├── __init__.py
│   ├── desktop_skill.py    # 主技能入口
│   ├── app_launcher.py     # 应用启动器
│   └── ui_agent.py         # UI操作代理
├── tools/                  # 系统级内置技能
│   ├── notes_skill.py      # 备忘录操作
│   ├── chat_skill.py       # 通用聊天工具
│   ├── search_skill.py     # 网络搜索工具
│   ├── http_skill.py       # HTTP/RSS/网页提取工具
│   ├── memory_skill.py     # 记忆管理
│   └── soul_skill.py       # 人格进化
├── agent_skills/           # 动态生成的技能
├── memory/                 # 记忆数据存储
├── soul/                   # 人格数据存储
└── test_system.py          # 系统测试脚本
```

### 🚀 快速开始

#### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd Neo

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（用于 Browser Agent）
pip install playwright
playwright install chromium
```

依赖列表 (`requirements.txt`):
```text
openai
streamlit
requests
numpy
playwright>=1.40.0
beautifulsoup4
```

#### 2. 配置 API Key

创建 `.env` 文件：

```bash
LLM_API_KEY="your-api-key-here"
LLM_BASE_URL="https://api.openai.com/v1/chat/completions"
LLM_MODEL="gpt-4o"
```

支持任何兼容 OpenAI 接口的服务（DeepSeek, QNAIGC 等）。

#### 3. 启动 Neo

**Web 模式 (推荐):**
```bash
streamlit run app.py
```

**命令行模式:**
```bash
python chat_cli.py
```

**运行测试:**
```bash
python test_system.py
```

### 💡 使用指南

#### Browser Agent 示例

**场景：访问需要登录的网站**
```
用户: 帮我看看某论坛的最新帖子

Neo:
  🧠 Thought: 需要访问网站获取信息...
  ⚡ Action: browser_agent(action="navigate", url="https://example.com")
  👁️ Observation: 页面加载成功，检测到需要登录
  🧠 Thought: 需要用户确认是否登录
  ❓ 询问: 检测到需要登录，是否继续？
  [用户确认]
  ⚡ Action: browser_agent(action="login")
  👁️ Observation: 登录成功
  ⚡ Action: browser_agent(action="extract")
  ✅ 回复: 最新帖子列表如下...
```

#### Desktop Agent 示例

**场景：打开豆包并对话**
```
用户: 帮我打开豆包，问它今天天气怎么样

Neo:
  🧠 Thought: 需要启动豆包应用...
  ⚡ Action: desktop_agent(action="launch", app_name="豆包")
  👁️ Observation: 豆包已启动
  ⚡ Action: desktop_agent(action="type", text="今天天气怎么样")
  👁️ Observation: 已输入文本
  ⚡ Action: desktop_agent(action="hotkey", key="enter")
  ✅ 回复: 豆包回复：今天天气...
```

#### 自主编程示例

**场景：需要创建新技能**
```
用户: 帮我查询比特币当前价格

Neo:
  🧠 Thought: 我没有比特币价格查询工具，需要创建一个...
  ⚡ Action: create_skill(
      skill_name="bitcoin_price",
      skill_description="查询比特币实时价格",
      skill_code="..."
    )
  👁️ Observation: 技能创建成功！
  ⚡ Action: bitcoin_price()
  👁️ Observation: 当前价格 $67,234
  ✅ 回复: 比特币当前价格是 $67,234
```

### 🛡️ 安全护栏

Browser Agent 和 Desktop Agent 都内置了安全护栏：

```
操作分级：
├── ✅ 安全操作（自动执行）
│   └── navigate, read, scroll, screenshot, launch
├── ⚠️ 需确认操作
│   └── click, fill, login, type, hotkey
└── ❌ 禁止操作
    └── payment, delete, publish, modify_settings
```

### 🛠️ 开发新技能

在 `tools/` 目录下创建技能文件：

```python
class MySkill:
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "my_skill",
                "description": "技能描述",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "输入参数"}
                    },
                    "required": ["input"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict):
        return {"status": "success", "message": "执行结果"}
```

### ⚠️ 注意事项

- **权限**: 
  - 操作备忘录需要 macOS 的"完全磁盘访问"权限
  - Desktop Agent 需要"辅助功能"权限
  - Browser Agent 需要安装 Playwright
- **Token 消耗**: ReAct 循环可能多次调用 LLM，建议使用性价比高的模型
- **迭代限制**: 默认最多 15 次迭代，防止无限循环

## 🔒 代码保护系统

Neo 具备自我编程能力，但为了安全，我们实现了代码保护系统：

### 保护级别

| 级别 | 说明 | 风险 |
|------|------|------|
| `none` | 禁止所有代码修改 | 无 |
| `skills_only` | 只能创建新技能（默认） | 低 |
| `extensions` | 可以创建扩展模块 | 中 |
| `full_with_approval` | 可以修改任何文件，需确认 | 高 |

### 核心文件保护

以下文件被标记为**只读**，默认不可修改：
- `core/react_agent.py` - Agent核心
- `browser_agent/safety_guard.py` - 安全护栏
- `code_guard.py` - 代码保护系统
- 其他核心模块...

### 沙盒区域

Neo 可以在以下目录自由创建新功能：
- `agent_skills/` - 动态技能
- `extensions/` - 扩展模块

### 危险代码检测

系统会自动检测并阻止：
- `os.system()`、`subprocess` 等系统调用
- `eval()`、`exec()` 等动态执行
- 修改安全配置的代码
- 可疑的网络请求

### 相关命令

```
用户: 查看代码保护状态
Neo: [调用 code_guard_status]

用户: 设置保护级别为 extensions
Neo: [调用 code_guard_set_level]

用户: 查看修改历史
Neo: [调用 code_guard_history]

用户: 回滚最近的修改
Neo: [调用 code_guard_rollback]
```

---

<a name="english"></a>
## 🇺🇸 English

**Neo** is a local AI assistant framework based on the ReAct architecture. Unlike traditional AI assistants, Neo features a **Think-Act-Observe loop**, **native Function Calling**, **vector memory system**, and **self-programming evolution** capabilities.

It's not just a chatbot, but a digital life form capable of autonomous planning, execution, reflection, and **writing code to extend its own abilities**.

### ✨ Core Features

#### 🧠 ReAct Architecture
Neo works using the ReAct (Reasoning + Acting) pattern:
- **Thought**: Analyze current state, think about next steps
- **Action**: Select and execute tools
- **Observation**: Observe execution results
- **Loop**: Continue until task completion

This architecture enables Neo to self-correct and dynamically adjust strategies rather than blindly executing pre-designed plans.

#### 🌐 Browser Agent
Neo can **use browsers like a real human**:
- Automatic navigation, clicking, form filling, login
- Handle dynamically rendered pages
- Extract page content
- Safety guardrails for sensitive operations
- Encrypted credential storage

#### 💻 Desktop Agent
Neo can **operate macOS applications like a real human**:
- Launch and activate local apps (Doubao, WeChat, Safari, etc.)
- Input text, click buttons in applications
- Send hotkeys, read window content
- Support for 40+ common applications

#### 🔧 Self-Programming Capability
Neo has the ability to **self-program and evolve**:
- Automatically writes new skills when existing tools are insufficient
- New skills are immediately available without restart
- Supports chain calls: search → fetch data → parse → return results
- Won't easily say "cannot complete", actively tries to solve problems

#### ⚡ Native Function Calling
- Directly utilizes LLM's tool calling capability
- No manual JSON parsing required
- More reliable tool calling experience
- Supports parallel multi-tool calls

#### 🛠️ Rich Built-in Tools
| Tool | Function |
|-----|----------|
| `browser_agent` | 🌐 Use browsers like a human |
| `browser_agent_save_credentials` | 🔐 Save website login credentials |
| `desktop_agent` | 💻 Operate macOS apps like a human |
| `desktop_list_common_apps` | 📱 List supported common apps |
| `notes_operator` | 📝 macOS Notes operations |
| `web_search` | 🔍 Web search |
| `http_request` | 🌍 HTTP requests, fetch web/API data |
| `rss_fetcher` | 📡 RSS/Atom feed parsing |
| `web_scraper` | 📄 Web content extraction |
| `chat` | 💬 General chat |
| `create_skill` | 🔧 Dynamically create new skills |

#### 💾 Vector Memory System
- **Short-term Memory**: Recent conversations, quick access
- **Long-term Memory**: Important information, persistent storage
- **Semantic Retrieval**: Keyword-based relevance search
- **Auto Compression**: Periodic summarization and memory refinement

#### 🎵 Rich Media Rendering
- Auto-detect and render images
- Audio players (supports MP3, podcasts, Spotify, Apple Podcasts, etc.)
- Map display
- Data visualization charts

#### 🔒 Local-First
Data stored in local file system, protecting privacy, core capabilities work offline.

### 🚀 Quick Start

#### 1. Environment Setup

```bash
# Clone the project
git clone <your-repo-url>
cd Neo

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser (for Browser Agent)
pip install playwright
playwright install chromium
```

Dependencies (`requirements.txt`):
```text
openai
streamlit
requests
numpy
playwright>=1.40.0
beautifulsoup4
```

#### 2. Configure API Key

Create a `.env` file:

```bash
LLM_API_KEY="your-api-key-here"
LLM_BASE_URL="https://api.openai.com/v1/chat/completions"
LLM_MODEL="gpt-4o"
```

Supports any OpenAI-compatible service (DeepSeek, QNAIGC, etc.).

#### 3. Start Neo

**Web Mode (Recommended):**
```bash
streamlit run app.py
```

**CLI Mode:**
```bash
python chat_cli.py
```

**Run Tests:**
```bash
python test_system.py
```

### 💡 Usage Guide

#### Browser Agent Example

**Scenario: Access a website requiring login**
```
User: Check the latest posts on a forum

Neo:
  🧠 Thought: Need to access the website...
  ⚡ Action: browser_agent(action="navigate", url="https://example.com")
  👁️ Observation: Page loaded, login required
  🧠 Thought: Need user confirmation
  ❓ Ask: Login required, continue?
  [User confirms]
  ⚡ Action: browser_agent(action="login")
  👁️ Observation: Login successful
  ⚡ Action: browser_agent(action="extract")
  ✅ Response: Latest posts are...
```

#### Desktop Agent Example

**Scenario: Open an app and interact**
```
User: Open Notes and create a shopping list

Neo:
  🧠 Thought: Need to launch Notes...
  ⚡ Action: desktop_agent(action="launch", app_name="Notes")
  👁️ Observation: Notes launched
  ⚡ Action: desktop_agent(action="type", text="Shopping List")
  ⚡ Action: desktop_agent(action="hotkey", key="enter")
  ✅ Response: Shopping list created
```

#### Self-Programming Example

**Scenario: Need to create a new skill**
```
User: Check the current Bitcoin price

Neo:
  🧠 Thought: I don't have a Bitcoin price tool, need to create one...
  ⚡ Action: create_skill(
      skill_name="bitcoin_price",
      skill_description="Query real-time Bitcoin price",
      skill_code="..."
    )
  👁️ Observation: Skill created successfully!
  ⚡ Action: bitcoin_price()
  👁️ Observation: Current price $67,234
  ✅ Response: Bitcoin current price is $67,234
```

### 🛡️ Safety Guardrails

Both Browser Agent and Desktop Agent have built-in safety guardrails:

```
Operation Levels:
├── ✅ Safe Operations (Auto-execute)
│   └── navigate, read, scroll, screenshot, launch
├── ⚠️ Confirmation Required
│   └── click, fill, login, type, hotkey
└── ❌ Prohibited Operations
    └── payment, delete, publish, modify_settings
```

### 🛠️ Developing New Skills

Create a skill file in the `tools/` directory:

```python
class MySkill:
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "my_skill",
                "description": "Skill description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Input parameter"}
                    },
                    "required": ["input"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict):
        return {"status": "success", "message": "Result"}
```

### ⚠️ Notes

- **Permissions**: 
  - Notes operations require "Full Disk Access" on macOS
  - Desktop Agent requires "Accessibility" permission
  - Browser Agent requires Playwright installation
- **Token Consumption**: ReAct loop may call LLM multiple times, recommend cost-effective models
- **Iteration Limit**: Default max 15 iterations to prevent infinite loops

---

## 📊 Architecture Comparison

| Feature | Old Neo | New Neo |
|---------|---------|---------|
| Execution Mode | Single plan execution | ReAct Loop |
| Tool Calling | Manual JSON parsing | Native Function Calling |
| Error Handling | Simple retry | Observe-Adjust-Retry |
| Memory System | File storage | Vector retrieval + Compression |
| Skill Search | Keyword matching | Semantic similarity |
| Self-Programming | ❌ | ✅ Dynamic skill creation |
| Browser Automation | ❌ | ✅ Browser Agent |
| App Automation | ❌ | ✅ Desktop Agent |
| Safety Guardrails | ❌ | ✅ Operation-level protection |

## 📜 License

MIT License

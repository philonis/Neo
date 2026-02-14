
# Neo: 本地自进化智能助手

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/Platform-macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Architecture-ReAct-orange" alt="Architecture">
  <img src="https://img.shields.io/badge/AI-Agentic-purple" alt="Agentic AI">
</div>

**Neo** 是一个基于 ReAct 架构的本地智能助手框架。与传统 AI 助手不同，Neo 具备**思考-行动-观察循环**、**原生 Function Calling**、**向量记忆系统**以及**自主编程进化**的能力。

它不仅仅是一个聊天机器人，更是一个能够自主规划、执行、反思并**编写代码扩展自身能力**的数字生命。

## ✨ 核心特性

### 🧠 ReAct 架构
Neo 采用 ReAct (Reasoning + Acting) 模式工作：
- **Thought**: 分析当前状态，思考下一步
- **Action**: 选择并执行工具
- **Observation**: 观察执行结果
- **Loop**: 循环直到任务完成

这种架构使 Neo 能够自我修正、动态调整策略，而不是盲目执行预设计划。

### 🌐 Browser Agent ⭐ NEW
Neo 具备**像真人一样使用浏览器**的能力：
- 自动导航、点击、填表、登录
- 处理动态渲染的页面
- 提取页面内容
- 安全护栏保护敏感操作
- 支持凭证加密存储

### 💻 Desktop Agent ⭐ NEW
Neo 可以**像真人一样操作macOS应用**：
- 启动和激活本地应用（豆包、微信、Safari等）
- 在应用中输入文本、点击按钮
- 发送快捷键、读取窗口内容
- 支持40+常用应用

### 🔧 自主编程能力
Neo 具备**自我编程进化**的能力：
- 当发现现有工具无法完成任务时，自动编写新技能
- 新技能创建后立即可用，无需重启
- 支持链式调用：搜索 → 获取数据 → 解析 → 返回结果
- 不会轻易说"无法完成"，而是主动尝试解决问题

### ⚡ 原生 Function Calling
- 直接利用 LLM 的工具调用能力
- 无需手动解析 JSON 格式
- 更可靠的工具调用体验
- 支持多工具并行调用

### 🛠️ 丰富的内置工具
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

### 💾 向量记忆系统
- **短期记忆**: 最近对话，快速访问
- **长期记忆**: 重要信息，持久存储
- **语义检索**: 基于关键词的相关性搜索
- **自动压缩**: 定期总结和精简记忆

### 🔒 本地优先
数据存储在本地文件系统，保护隐私，无需联网即可使用核心能力。

## 📁 项目结构

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

## 🚀 快速开始

### 1. 环境准备

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
```

### 2. 配置 API Key

创建 `.env` 文件：

```bash
LLM_API_KEY="your-api-key-here"
LLM_BASE_URL="https://api.openai.com/v1/chat/completions"
LLM_MODEL="gpt-4o"
```

支持任何兼容 OpenAI 接口的服务（DeepSeek, QNAIGC 等）。

### 3. 启动 Neo

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

## 💡 使用指南

### Browser Agent 示例 ⭐ NEW

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

**保存凭证供自动登录：**
```
用户: 保存这个网站的登录凭证

Neo:
  ⚡ Action: browser_agent_save_credentials(
      site_url="https://example.com",
      username="my_username",
      password="my_password"
    )
  ✅ 回复: 凭证已加密保存，下次访问时自动登录
```

### Desktop Agent 示例 ⭐ NEW

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
  👁️ Observation: 已发送
  ⚡ Action: desktop_agent(action="read")
  ✅ 回复: 豆包回复：今天天气...
```

**支持的常用应用：**
```
豆包、微信、Safari、Chrome、音乐、备忘录、日历、
访达、终端、计算器、邮件、地图、飞书、钉钉...
```

### 自主编程示例

**场景：查询播客最新一期**
```
用户: 津津乐道的最新单集是什么？

Neo:
  🧠 Thought: 我需要获取播客信息，但没有现成的工具...
  ⚡ Action: web_search(query="津津乐道播客 RSS")
  👁️ Observation: 找到 RSS 地址
  ⚡ Action: rss_fetcher(url="https://...")
  👁️ Observation: 获取到最新一期信息
  ✅ 回复: 津津乐道最新一期是"xxx"，发布于...
```

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

### ReAct 执行流程

```
用户输入: "帮我创建一个购物清单备忘录"
    ↓
🧠 Thought: 用户想要创建备忘录，我需要使用 notes_operator 工具
    ↓
⚡ Action: 调用 notes_operator(action="create", title="购物清单")
    ↓
👁️ Observation: 备忘录创建成功
    ↓
🧠 Thought: 任务完成，向用户确认
    ↓
✅ 回复: "已为您创建购物清单备忘录"
```

## 🛡️ 安全护栏

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

- 敏感操作需要用户确认
- 行为审计日志记录所有操作
- 凭证加密存储

## 🛠️ 开发新技能

### 手动创建技能

在 `tools/` 目录下创建技能文件：

```python
class MySkill:
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "my_skill",
                "description": "技能描述，用于语义搜索匹配",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "输入参数描述"
                        }
                    },
                    "required": ["input"]
                }
            }
        }

    @staticmethod
    def run(arguments: dict):
        input_value = arguments.get("input", "")
        # 实现技能逻辑
        return {
            "status": "success",
            "message": "执行结果"
        }
```

### Neo 自动创建技能

Neo 会在运行时自动创建技能，保存在 `agent_skills/` 目录。

## 📊 架构对比

| 特性 | 旧版 Neo | 新版 Neo |
|-----|---------|---------|
| 执行模式 | 单次规划执行 | ReAct 循环 |
| 工具调用 | 手动解析 JSON | 原生 Function Calling |
| 错误处理 | 简单重试 | 观察-调整-重试 |
| 记忆系统 | 文件存储 | 向量检索 + 压缩 |
| 技能搜索 | 关键词匹配 | 语义相似度 |
| 自主编程 | ❌ | ✅ 动态创建技能 |
| 浏览器自动化 | ❌ | ✅ Browser Agent |
| 应用自动化 | ❌ | ✅ Desktop Agent |
| 安全护栏 | ❌ | ✅ 操作分级保护 |

## ⚠️ 注意事项

- **权限**: 
  - 操作备忘录需要 macOS 的"完全磁盘访问"权限
  - Desktop Agent 需要"辅助功能"权限
  - Browser Agent 需要安装 Playwright
- **Token 消耗**: ReAct 循环可能多次调用 LLM，建议使用性价比高的模型
- **迭代限制**: 默认最多 15 次迭代，防止无限循环
- **技能验证**: 动态创建的技能会经过语法检查，但请谨慎执行

## 📜 License

MIT License

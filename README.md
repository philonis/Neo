
# Neo: 本地自进化智能助手

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/Platform-macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Architecture-ReAct-orange" alt="Architecture">
</div>

**Neo** 是一个基于 ReAct 架构的本地智能助手框架。与传统 AI 助手不同，Neo 具备**思考-行动-观察循环**、**原生 Function Calling**、**向量记忆系统**以及**自我编程进化**的能力。

它不仅仅是一个聊天机器人，更是一个能够自主规划、执行、反思并扩展自身能力的数字生命。

## ✨ 核心特性

### 🧠 ReAct 架构
Neo 采用 ReAct (Reasoning + Acting) 模式工作：
- **Thought**: 分析当前状态，思考下一步
- **Action**: 选择并执行工具
- **Observation**: 观察执行结果
- **Loop**: 循环直到任务完成

这种架构使 Neo 能够自我修正、动态调整策略，而不是盲目执行预设计划。

### ⚡ 原生 Function Calling
- 直接利用 LLM 的工具调用能力
- 无需手动解析 JSON 格式
- 更可靠的工具调用体验
- 支持多工具并行调用

### 🎯 智能任务规划
- **任务复杂度分析**: 自动判断任务是否需要分解
- **子任务拆分**: 将复杂任务分解为可执行步骤
- **动态调整**: 根据执行结果实时调整计划

### 💾 向量记忆系统
- **短期记忆**: 最近对话，快速访问
- **长期记忆**: 重要信息，持久存储
- **语义检索**: 基于关键词的相关性搜索
- **自动压缩**: 定期总结和精简记忆

### 🛠️ 动态技能生成
当发现自身能力不足时，Neo 会自动编写 Python 代码、保存并加载新技能，实现自我进化。

### 🔍 语义技能搜索
基于语义相似度匹配技能，"写笔记" 和 "记录备忘录" 能够正确匹配。

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
│   ├── react_agent.py      # ReAct Agent 核心
│   ├── planner.py          # 智能任务规划器
│   ├── memory.py           # 向量记忆系统
│   └── skill_manager.py    # 增强型技能管理器
├── tools/                  # 系统级内置技能
│   ├── notes_skill.py      # 备忘录操作
│   ├── chat_skill.py       # 通用聊天工具
│   ├── search_skill.py     # 网络搜索工具
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
```

依赖列表 (`requirements.txt`):
```text
openai
rich
streamlit
python-dotenv
watchdog
pyyaml
beautifulsoup4
requests
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

### 示例对话

**简单任务:**
```
用户: 你好
Neo: 你好！我是 Neo，有什么可以帮助你的吗？
```

**工具调用:**
```
用户: 帮我创建一个叫"今日待办"的备忘录
Neo: [调用 notes_operator 工具]
    已为您创建备忘录"今日待办"，您可以开始添加内容了。
```

**复杂任务 (自动分解):**
```
用户: 帮我创建一个购物清单，然后搜索一下附近的超市
Neo: [分析任务复杂度: medium]
    [分解为子任务]
    1. 创建购物清单备忘录 ✓
    2. 搜索附近超市信息 ✓
    已完成两项任务...
```

### 记忆系统

Neo 会记住与你的对话：

```
用户: 我喜欢喝咖啡
Neo: 好的，我记住了。

[10轮对话后]

用户: 给我推荐点喝的
Neo: 根据您的偏好，我推荐您尝试...
```

## 🛠️ 开发新技能

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

## 📊 架构对比

| 特性 | 旧版 Neo | 新版 Neo |
|-----|---------|---------|
| 执行模式 | 单次规划执行 | ReAct 循环 |
| 工具调用 | 手动解析 JSON | 原生 Function Calling |
| 错误处理 | 简单重试 | 观察-调整-重试 |
| 记忆系统 | 文件存储 | 向量检索 + 压缩 |
| 技能搜索 | 关键词匹配 | 语义相似度 |

## ⚠️ 注意事项

- **权限**: 操作备忘录需要 macOS 的"完全磁盘访问"权限
- **Token 消耗**: ReAct 循环可能多次调用 LLM，建议使用性价比高的模型
- **迭代限制**: 默认最多 15 次迭代，防止无限循环

## 📜 License

MIT License

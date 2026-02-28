# Neo 智能助手架构设计文档

## 概述

Neo 是一个基于 ReAct 架构的 AI 智能助手，具有自主编程、浏览器自动化、桌面操作等能力。本文档面向开发人员，帮助快速理解系统架构。

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Streamlit  │  │  Telegram   │  │    CLI      │             │
│  │    Web UI   │  │    Bot      │  │   Chat      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       核心代理层                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ReActAgent                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │  Thought │→ │  Action  │→ │Observation│ → 循环       │   │
│  │  └──────────┘  └──────────┘  └──────────┘               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ TaskPlanner   │  │ SkillComposer │  │  SoulSkill    │       │
│  │ 任务规划器     │  │ 技能组合器     │  │  人格系统     │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       技能管理层                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   SkillManager                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ SkillIndex  │  │ SkillLoader │  │CodeGuard    │      │   │
│  │  │ 技能索引     │  │ 技能加载器   │  │代码保护     │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     技能类型                              │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ 元技能    │  │ Python   │  │ Markdown │  │ 动态创建  │ │   │
│  │  │ MetaSkill│  │ Skills   │  │ Skills   │  │ Skills   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       能力执行层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ BrowserAgent│  │DesktopAgent │  │  LLMClient  │             │
│  │ 浏览器自动化 │  │ 桌面自动化   │  │  LLM 客户端  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ SafetyGuard │  │SessionMgr   │  │ Memory      │             │
│  │ 安全护栏     │  │ 会话管理    │  │ 记忆系统    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 核心模块说明

### 1. ReActAgent (core/react_agent.py)

核心推理引擎，实现 ReAct (Reasoning + Acting) 循环：

```python
# 执行流程
for iteration in range(max_iterations):
    1. Thought  - LLM 分析当前状态，决定下一步
    2. Action   - 选择并执行工具/技能
    3. Observation - 观察执行结果
    4. 循环直到任务完成或达到最大迭代次数
```

**关键特性**：
- 自主编程能力：当现有工具不足时，可创建新技能
- 链式调用：支持多步骤任务
- 错误恢复：失败时尝试其他方法

### 2. SkillManager (core/skill_manager.py)

技能管理中枢，支持多种技能格式：

| 技能类型 | 存储位置 | 加载方式 |
|----------|----------|----------|
| Python 技能 | `tools/*.py` | 模块导入 |
| Markdown 技能 | `skills/*/SKILL.md` | 渐进式加载 |
| 动态技能 | `agent_skills/*.py` | 运行时创建 |

**新增功能**：
- `SkillIndex` - 技能索引，防止重复创建
- `find_similar_skill()` - 查找相似技能
- `suggest_skills_for_task()` - 为任务建议技能

### 3. SkillIndex (core/skill_index.py)

技能索引服务，核心功能：

```python
# 检查是否已存在相似技能
match = skill_index.check_duplicate(description, threshold=0.7)

# 搜索相关技能
skills = skill_index.search_similar(query, top_k=5)

# 获取技能组合建议
composition = skill_index.suggest_composition(task_description)
```

### 4. VectorMemory (core/memory.py)

智能记忆系统：

```
┌─────────────────────────────────────┐
│           记忆分层                   │
├─────────────────────────────────────┤
│ 短期记忆 (Short-term)               │
│ - 最近 20 条对话                    │
│ - 快速访问                          │
│ - 自动压缩                          │
├─────────────────────────────────────┤
│ 长期记忆 (Long-term)                │
│ - 重要性 >= 0.7 的记忆              │
│ - 持久存储                          │
│ - 语义检索                          │
├─────────────────────────────────────┤
│ 记忆索引 (Index)                    │
│ - 关键词索引                        │
│ - 相关性匹配                        │
└─────────────────────────────────────┘
```

### 5. BrowserAgent (browser_agent/)

浏览器自动化模块：

```
browser_agent/
├── browser_skill.py      # 技能入口
├── browser_controller.py # 浏览器控制
├── safety_guard.py       # 安全护栏
└── session_manager.py    # 会话管理
```

**安全分级**：
- `SAFE` - 自动执行（导航、读取、截图）
- `CONFIRM_REQUIRED` - 需确认（点击、填写）
- `FORBIDDEN` - 禁止执行（支付、删除）

### 6. CodeGuard (code_guard.py)

代码保护系统：

```
┌─────────────────────────────────────┐
│          保护级别                    │
├─────────────────────────────────────┤
│ NONE           - 禁止所有修改        │
│ SKILLS_ONLY    - 只允许修改技能目录  │
│ EXTENSIONS     - 允许修改扩展目录    │
│ FULL_WITH_APPROVAL - 全部修改需确认  │
└─────────────────────────────────────┘
```

## 数据流向

```
用户输入
    │
    ▼
┌─────────────┐
│ ReActAgent  │ ←── 记忆上下文
└─────────────┘
    │
    ▼
┌─────────────┐
│  LLM 推理   │ ←── 技能列表
└─────────────┘
    │
    ├──→ 直接回答 ──→ 输出
    │
    └──→ 工具调用
            │
            ▼
        ┌─────────────┐
        │ SkillManager │
        └─────────────┘
            │
            ├──→ 元技能组合
            │
            ├──→ 现有技能执行
            │
            └──→ 创建新技能
                    │
                    ▼
                ┌─────────────┐
                │  CodeGuard  │ ← 安全检查
                └─────────────┘
                    │
                    ▼
                执行结果 ──→ 输出
```

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| LLM | OpenAI API 兼容 | 支持 DeepSeek、Qwen 等 |
| Web UI | Streamlit | 响应式界面 |
| 浏览器自动化 | Playwright | 跨浏览器支持 |
| 桌面自动化 | pyautogui | Linux/macOS 通用 |
| 向量存储 | NumPy | 轻量级向量计算 |
| 日志 | logging | 结构化日志 |

## 目录结构

```
Neo/
├── app.py                 # Streamlit 主应用
├── llm_client.py          # LLM 客户端
├── code_guard.py          # 代码保护系统
│
├── core/                  # 核心模块
│   ├── react_agent.py     # ReAct 代理
│   ├── skill_manager.py   # 技能管理
│   ├── skill_index.py     # 技能索引
│   ├── skill_loader.py    # 技能加载
│   ├── skill_composer.py  # 技能组合
│   ├── memory.py          # 记忆系统
│   ├── planner.py         # 任务规划
│   └── logger.py          # 日志模块
│
├── tools/                 # Python 技能
│   ├── meta_skills.py     # 元技能
│   ├── search_skill.py    # 搜索技能
│   ├── http_skill.py      # HTTP 技能
│   ├── notes_skill.py     # 笔记技能
│   └── ...
│
├── skills/                # Markdown 技能
│   ├── browser-agent/
│   ├── desktop-agent/
│   └── ...
│
├── browser_agent/         # 浏览器自动化
│   ├── browser_skill.py
│   ├── browser_controller.py
│   ├── safety_guard.py
│   └── session_manager.py
│
├── desktop_agent/         # 桌面自动化
│   ├── desktop_skill.py
│   ├── app_launcher.py
│   └── ui_agent.py
│
├── soul/                  # 人格系统
│   ├── core.md
│   └── evolution.md
│
├── docs/                  # 文档
│   ├── ARCHITECTURE.md    # 本文档
│   ├── SKILL_SYSTEM.md    # 技能系统
│   └── DEVELOPMENT.md     # 开发指南
│
└── agent_skills/          # 动态创建的技能
```

## 设计哲学

借鉴 OpenClaw 项目的设计原则：

### 1. 上下文效率优先

```
上下文窗口是公共资源。技能共享上下文窗口与：
- 系统提示词
- 对话历史
- 其他技能元数据
- 用户实际请求

默认假设：AI 已经非常智能。只添加 AI 不具备的上下文。
```

### 2. 渐进式披露架构

```
第1层：元数据层 [始终在上下文中，约100词]
第2层：指令主体 [触发后加载，<5000词]
第3层：捆绑资源 [按需加载，无限制]
```

### 3. 自由度匹配原则

| 自由度 | 适用场景 | 形式 |
|--------|----------|------|
| 高自由度 | 多种方法有效 | 文本指令 |
| 中自由度 | 存在首选模式 | 伪代码/脚本 |
| 低自由度 | 操作脆弱易错 | 具体脚本 |

### 4. SOUL.md 人格定义

```markdown
**Be genuinely helpful, not performatively helpful.**
**Have opinions.**
**Be resourceful before asking.**
**Earn trust through competence.**
```

## 快速开始

### 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install

# 配置环境变量
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.example.com/v1/chat/completions"
export LLM_MODEL="deepseek/deepseek-v3"
```

### 启动服务

```bash
# Web UI
streamlit run app.py

# CLI 模式
python chat_cli.py
```

### 添加新技能

1. **Python 技能**：在 `tools/` 创建新文件

```python
class MySkill:
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "my_skill",
                "description": "技能描述",
                "parameters": {...}
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        # 实现逻辑
        return {"success": True, "result": "..."}
```

2. **Markdown 技能**：在 `skills/` 创建目录

```markdown
---
name: my-skill
description: |
  技能描述，包含触发场景
---

# 技能名称

## 快速开始
...

## 工作流程
...
```

## 扩展阅读

- [技能系统详解](./SKILL_SYSTEM.md)
- [开发指南](./DEVELOPMENT.md)
- [安全机制](./SECURITY.md)

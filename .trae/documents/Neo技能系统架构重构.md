## 重构目标

按照"AI助手技能扩展架构设计"重构Neo技能系统，实现：

* 渐进式披露架构

* 上下文效率优先

* 动态技能创建

* 资源捆绑机制

***

## 新目录结构

```
Neo/
├── skills/                      # 新技能目录
│   ├── web-search/             # 网络搜索技能
│   │   ├── SKILL.md            # 技能定义（必需）
│   │   └── scripts/            # 可执行脚本
│   │       └── search.py
│   ├── browser-agent/          # 浏览器自动化
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   └── references/
│   │       └── safety-rules.md
│   ├── desktop-agent/          # 桌面应用操作
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── notes-operator/         # 备忘录操作
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── http-request/           # HTTP请求
│       ├── SKILL.md
│       └── scripts/
├── core/
│   ├── skill_loader.py         # 新：渐进式技能加载器
│   ├── skill_manager.py        # 更新：支持新架构
│   └── skill_creator.py        # 新：技能创建工具
└── tools/
    └── init_skill.py           # 新：技能初始化CLI
```

***

## 实现步骤

### Step 1: 创建核心组件

1. **skill\_loader.py** - 渐进式技能加载器

   * `load_metadata()` - 加载SKILL.md元数据（\~100词）

   * `load_body()` - 加载指令主体（<5000词）

   * `load_resources()` - 按需加载资源文件

2. **skill\_manager.py** - 更新支持新架构

   * 兼容旧Python技能和新SKILL.md技能

   * 语义搜索基于description字段

   * 按需加载技能详情

### Step 2: 创建技能模板

**SKILL.md模板**:

```markdown
---
name: skill-name
description: |
  技能功能描述。
  触发场景：(1) 场景一 (2) 场景二
---

# 技能名称

## 快速开始
[核心操作示例]

## 工作流程
[详细指令]
```

### Step 3: 迁移现有技能

将现有Python技能迁移到新架构：

* `web_search` → `skills/web-search/SKILL.md`

* `browser_agent` → `skills/browser-agent/SKILL.md`

* `desktop_agent` → `skills/desktop-agent/SKILL.md`

* `notes_operator` → `skills/notes-operator/SKILL.md`

* `http_request` → `skills/http-request/SKILL.md`

### Step 4: 创建技能初始化工具

**init\_skill.py** - CLI工具

```bash
python tools/init_skill.py <skill-name> --resources scripts,references
```

### Step 5: 更新ReAct Agent

* 更新系统提示，支持新技能架构

* 技能决策时只加载元数据

* 执行时按需加载完整指令

***

## 关键设计

### 渐进式披露

```
第1层：元数据（始终加载）
├── name: 技能名称
└── description: 触发描述

第2层：指令主体（触发后加载）
└── 工作流程、操作指令

第3层：捆绑资源（按需加载）
├── scripts/ 可执行代码
├── references/ 参考文档
└── assets/ 模板资源
```

### 自由度匹配

| 技能类型   | 自由度 | 形式    |
| ------ | --- | ----- |
| 网络搜索   | 高   | 文本指令  |
| HTTP请求 | 中   | 参数化脚本 |
| 浏览器操作  | 低   | 具体脚本  |

***

## 文件清单

新增文件：

1. `core/skill_loader.py` - 渐进式加载器
2. `core/skill_creator.py` - 技能创建工具
3. `tools/init_skill.py` - CLI初始化工具
4. `skills/web-search/SKILL.md` - 搜索技能
5. `skills/browser-agent/SKILL.md` - 浏览器技能
6. `skills/desktop-agent/SKILL.md` - 桌面技能
7. `skills/notes-operator/SKILL.md` - 备忘录技能
8. `skills/http-request/SKILL.md` - HTTP技能

更新文件：

1. `core/skill_manager.py` - 支持新架构
2. `core/react_agent.py` - 更新技能加载逻辑


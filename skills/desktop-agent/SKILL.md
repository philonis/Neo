---
name: desktop-agent
description: |
  桌面应用自动化技能。像真人一样操作macOS应用（豆包、微信、Safari等）。
  触发场景：(1) 操作本地应用 (2) 需要与应用交互 (3) 应用没有API可用
---

# 桌面应用自动化

## 快速开始

```python
# 启动应用
desktop_agent(action="launch", app_name="豆包")

# 输入文本
desktop_agent(action="type", text="你好")

# 发送快捷键
desktop_agent(action="hotkey", key="enter")
```

## 工作流程

### 操作列表

| 操作 | 说明 | 安全级别 |
|------|------|---------|
| launch | 启动应用 | ✅ 安全 |
| activate | 激活窗口 | ✅ 安全 |
| type | 输入文本 | ⚠️ 需确认 |
| click | 点击元素 | ⚠️ 需确认 |
| hotkey | 发送快捷键 | ⚠️ 需确认 |
| read | 读取窗口内容 | ✅ 安全 |

### 详细步骤

1. **启动应用**: 使用 AppleScript 启动
2. **激活窗口**: 将应用置于前台
3. **执行操作**: 输入、点击、快捷键
4. **读取结果**: 获取窗口内容

## 支持的应用

| 应用 | 名称 | 别名 |
|------|------|------|
| 豆包 | Doubao | 豆包, doubao |
| 微信 | WeChat | 微信, wechat |
| Safari | Safari | safari |
| Chrome | Google Chrome | chrome |
| 音乐 | Music | 音乐, music |
| 备忘录 | Notes | 备忘录, notes |

## 使用原则

- **特定场景**: 仅用于操作本地应用
- **权限要求**: 需要辅助功能权限
- **效率考虑**: 适合没有API的应用

## 注意事项

- 需要macOS辅助功能权限
- 部分应用可能有权限限制
- 操作可能需要等待应用响应

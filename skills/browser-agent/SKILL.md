---
name: browser-agent
description: |
  浏览器自动化技能。像真人一样使用浏览器访问网站、填写表单、点击按钮。
  触发场景：(1) 网站需要登录才能查看内容 (2) 动态渲染的复杂页面 (3) 需要交互操作（点击、填表）
---

# 浏览器自动化

## 快速开始

```python
# 导航到网站
browser_agent(action="navigate", url="https://example.com")

# 读取页面内容
browser_agent(action="read")

# 点击元素
browser_agent(action="click", element="登录按钮")
```

## 工作流程

### 操作列表

| 操作 | 说明 | 安全级别 |
|------|------|---------|
| navigate | 导航到URL | ✅ 安全 |
| read | 读取页面内容 | ✅ 安全 |
| click | 点击元素 | ⚠️ 需确认 |
| fill | 填写输入框 | ⚠️ 需确认 |
| login | 登录网站 | ⚠️ 需确认 |
| scroll | 滚动页面 | ✅ 安全 |
| screenshot | 截图 | ✅ 安全 |

### 详细步骤

1. **启动浏览器**: 初始化 Playwright
2. **导航**: 访问目标URL
3. **等待加载**: 等待页面完全加载
4. **执行操作**: 点击、填写、读取
5. **返回结果**: 提取页面内容

## 安全护栏

### 安全操作（自动执行）
- navigate, read, scroll, screenshot

### 需确认操作
- click, fill, login, type

### 禁止操作（需用户授权）
- payment, delete, publish

## 使用原则

- **必要时使用**: 仅在需要登录或交互时使用
- **优先轻量工具**: 公开信息优先使用 web_search 或 http_request
- **效率考虑**: 浏览器消耗更多资源

## 高级功能

- **凭证管理**: 见 [credentials.md](references/credentials.md)
- **安全规则**: 见 [safety-rules.md](references/safety-rules.md)

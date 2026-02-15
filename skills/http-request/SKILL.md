---
name: http-request
description: |
  HTTP请求技能。用于获取网页内容、调用API、发送HTTP请求。
  触发场景：(1) 获取公开网页内容 (2) 调用REST API (3) 获取RSS/Atom订阅
---

# HTTP请求

## 快速开始

```python
# GET请求
http_request(url="https://api.example.com/data")

# POST请求
http_request(method="POST", url="https://api.example.com/submit", data={"key": "value"})

# 获取网页
web_scraper(url="https://example.com")
```

## 工作流程

### 操作列表

| 操作 | 说明 | 参数 |
|------|------|------|
| GET | 获取数据 | url, headers |
| POST | 提交数据 | url, data, headers |
| scrape | 提取网页 | url, selector |
| rss | 获取RSS | url, count |

### 详细步骤

1. **构建请求**: 设置URL、方法、头信息
2. **发送请求**: 执行HTTP请求
3. **解析响应**: 处理JSON或HTML
4. **返回结果**: 格式化输出

## 使用原则

- **优先使用**: 公开网页内容优先使用此工具
- **轻量高效**: 比浏览器更轻量
- **格式支持**: 自动处理JSON、HTML、RSS

## 高级功能

- **RSS解析**: 见 [rss-fetcher](references/rss-fetcher.md)
- **网页提取**: 见 [web-scraper](references/web-scraper.md)

## 注意事项

- 部分网站可能有反爬机制
- 动态渲染页面需要使用 browser_agent
- 需要登录的网站使用 browser_agent

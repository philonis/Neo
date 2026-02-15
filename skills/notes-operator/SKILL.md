---
name: notes-operator
description: |
  备忘录操作技能。用于创建、读取、修改macOS备忘录。
  触发场景：(1) 用户要求创建备忘录 (2) 查看备忘录内容 (3) 添加内容到备忘录
---

# 备忘录操作

## 快速开始

```python
# 创建备忘录
notes_operator(action="create", title="购物清单", body="牛奶\n面包")

# 读取备忘录
notes_operator(action="read", note_name="购物清单")

# 添加内容
notes_operator(action="append", note_name="购物清单", content="鸡蛋")
```

## 工作流程

### 操作列表

| 操作 | 说明 | 参数 |
|------|------|------|
| create | 创建备忘录 | title, body |
| read | 读取备忘录 | note_name |
| append | 追加内容 | note_name, content |
| list | 列出备忘录 | - |
| search | 搜索备忘录 | query |

### 详细步骤

1. **连接备忘录**: 使用 AppleScript 连接
2. **执行操作**: 创建、读取、修改
3. **返回结果**: 操作状态和内容

## 使用原则

- **本地存储**: 备忘录存储在本地
- **隐私安全**: 内容不会上传
- **格式支持**: 支持纯文本和简单格式

## 注意事项

- 需要macOS备忘录权限
- 文件名不能包含特殊字符
- 大量内容可能影响性能

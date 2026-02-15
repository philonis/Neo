#!/usr/bin/env python3
"""
技能初始化工具 - Skill Initialization CLI

创建新的SKILL.md格式技能骨架

用法:
    python tools/init_skill.py <skill-name> [--resources scripts,references,assets]
"""

import os
import sys
import argparse
from pathlib import Path


SKILL_TEMPLATE = '''---
name: {skill_name}
description: |
  {description}
  触发场景：(1) 场景一 (2) 场景二 (3) 场景三
metadata:
  openclaw:
    requires:
      bins: []
      env: []
    install: []
---

# {skill_title}

## 快速开始

[核心操作示例]

```python
# 示例代码
result = skill.run(action="example", params={{"key": "value"}})
```

## 工作流程

### 操作列表

| 操作 | 说明 | 参数 |
|------|------|------|
| action1 | 操作说明 | param1, param2 |
| action2 | 操作说明 | param1 |

### 详细步骤

1. **步骤一**: 描述
2. **步骤二**: 描述
3. **步骤三**: 描述

## 高级功能

- **功能A**: 见 [references/feature-a.md](references/feature-a.md)
- **功能B**: 见 [references/feature-b.md](references/feature-b.md)

## 注意事项

- 注意事项一
- 注意事项二
'''

SCRIPT_TEMPLATE = '''"""
{script_name} - {description}

参数:
    params: dict - 操作参数

返回:
    result: dict - 执行结果
"""

def main(params: dict) -> dict:
    # TODO: 实现具体逻辑
    
    return {{
        "success": True,
        "message": "操作完成",
        "data": None
    }}

result = main(params)
'''

REFERENCE_TEMPLATE = '''# {title}

{description}

## 详细说明

[内容]

## 示例

```
示例代码
```
'''

ASSET_TEMPLATE = '''# {title}

{description}
'''


def create_skill(skill_name: str, output_dir: str, resources: list = None):
    """
    创建技能骨架
    
    :param skill_name: 技能名称（小写，连字符分隔）
    :param output_dir: 输出目录
    :param resources: 资源类型列表
    """
    resources = resources or []
    
    if not validate_skill_name(skill_name):
        print(f"❌ 技能名称格式错误: {skill_name}")
        print("   规则: 仅使用小写字母、数字、连字符，最大64字符")
        return False
    
    skill_dir = Path(output_dir) / skill_name
    if skill_dir.exists():
        print(f"❌ 技能目录已存在: {skill_dir}")
        return False
    
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    skill_title = skill_name.replace('-', ' ').title()
    description = f"{skill_title} 技能。用于执行{skill_title}相关操作。"
    
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title,
        description=description
    )
    
    skill_md_path = skill_dir / "SKILL.md"
    with open(skill_md_path, 'w', encoding='utf-8') as f:
        f.write(skill_content)
    
    print(f"✅ 创建 SKILL.md: {skill_md_path}")
    
    for resource_type in resources:
        resource_dir = skill_dir / resource_type
        resource_dir.mkdir(exist_ok=True)
        
        if resource_type == "scripts":
            script_path = resource_dir / "main.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(SCRIPT_TEMPLATE.format(
                    script_name="main",
                    description=f"{skill_title} 主脚本"
                ))
            print(f"✅ 创建脚本: {script_path}")
        
        elif resource_type == "references":
            ref_path = resource_dir / "guide.md"
            with open(ref_path, 'w', encoding='utf-8') as f:
                f.write(REFERENCE_TEMPLATE.format(
                    title=f"{skill_title} 指南",
                    description=f"{skill_title} 的详细使用指南"
                ))
            print(f"✅ 创建参考文档: {ref_path}")
        
        elif resource_type == "assets":
            asset_path = resource_dir / "template.md"
            with open(asset_path, 'w', encoding='utf-8') as f:
                f.write(ASSET_TEMPLATE.format(
                    title=f"{skill_title} 模板",
                    description=f"{skill_title} 的输出模板"
                ))
            print(f"✅ 创建资源文件: {asset_path}")
    
    print(f"\n🎉 技能 '{skill_name}' 创建成功!")
    print(f"   目录: {skill_dir}")
    print(f"\n下一步:")
    print(f"   1. 编辑 {skill_md_path}")
    print(f"   2. 添加触发场景到 description")
    print(f"   3. 完善工作流程和操作说明")
    
    return True


def validate_skill_name(name: str) -> bool:
    """
    验证技能名称格式
    
    规则:
    - 仅使用小写字母、数字、连字符
    - 最大 64 字符
    - 优先使用动词短语
    """
    if len(name) > 64:
        return False
    
    import re
    if not re.match(r'^[a-z0-9-]+$', name):
        return False
    
    if name.startswith('-') or name.endswith('-'):
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="技能初始化工具 - 创建新的SKILL.md格式技能"
    )
    parser.add_argument(
        "skill_name",
        help="技能名称（小写，连字符分隔，如: web-search）"
    )
    parser.add_argument(
        "--path",
        default="skills",
        help="输出目录，默认为 skills/"
    )
    parser.add_argument(
        "--resources",
        help="资源类型，逗号分隔（scripts,references,assets）"
    )
    
    args = parser.parse_args()
    
    resources = []
    if args.resources:
        resources = [r.strip() for r in args.resources.split(',')]
    
    create_skill(args.skill_name, args.path, resources)


if __name__ == "__main__":
    main()

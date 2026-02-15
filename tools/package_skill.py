#!/usr/bin/env python3
"""
技能打包工具 - Skill Packaging CLI

验证并打包技能为 skill-name.skill 文件（zip 格式）

用法:
    python tools/package_skill.py <skill-folder> [output-dir]
"""

import os
import sys
import argparse
import zipfile
import json
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skill_loader import SkillLoader


def validate_skill(skill_path: Path) -> dict:
    """
    验证技能格式
    
    :param skill_path: 技能目录路径
    :return: 验证结果
    """
    loader = SkillLoader(str(skill_path.parent))
    skill_name = skill_path.name
    
    validation = loader.validate_skill(skill_name)
    
    # 额外验证
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        validation["valid"] = False
        validation["errors"].append("SKILL.md 文件不存在")
    
    # 验证目录结构
    for dir_name in ["scripts", "references", "assets"]:
        dir_path = skill_path / dir_name
        if dir_path.exists() and not dir_path.is_dir():
            validation["errors"].append(f"{dir_name} 应是目录")
    
    return validation


def package_skill(skill_path: Path, output_dir: Path) -> bool:
    """
    打包技能为 zip 文件
    
    :param skill_path: 技能目录路径
    :param output_dir: 输出目录
    :return: 是否成功
    """
    skill_name = skill_path.name
    output_file = output_dir / f"{skill_name}.skill"
    
    # 验证技能
    validation = validate_skill(skill_path)
    if not validation.get("valid"):
        print(f"❌ 技能验证失败: {skill_name}")
        for error in validation.get("errors", []):
            print(f"   - {error}")
        return False
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 zip 文件
    print(f"📦 打包技能: {skill_name}")
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 添加 SKILL.md
        skill_file = skill_path / "SKILL.md"
        if skill_file.exists():
            zf.write(skill_file, f"SKILL.md")
            print(f"   ✅ 添加: SKILL.md")
        
        # 添加资源目录
        for dir_name in ["scripts", "references", "assets"]:
            dir_path = skill_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = str(file_path.relative_to(skill_path))
                        zf.write(file_path, arcname)
                        print(f"   ✅ 添加: {arcname}")
    
    # 生成验证报告
    report_file = output_dir / f"{skill_name}.report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(validation, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 技能打包成功!")
    print(f"   输出文件: {output_file}")
    print(f"   验证报告: {report_file}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="技能打包工具 - 验证并打包技能为 zip 格式"
    )
    parser.add_argument(
        "skill_folder",
        help="技能目录路径"
    )
    parser.add_argument(
        "output_dir",
        nargs='?',
        default="dist",
        help="输出目录，默认为 dist/"
    )
    
    args = parser.parse_args()
    
    skill_path = Path(args.skill_folder)
    if not skill_path.exists() or not skill_path.is_dir():
        print(f"❌ 技能目录不存在: {skill_path}")
        return 1
    
    output_dir = Path(args.output_dir)
    
    success = package_skill(skill_path, output_dir)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

"""
AI 助手技能扩展架构设计 - Progressive Skill Loader

核心设计:
1. 元数据层: 始终在上下文中（约100词）
2. 指令主体: 触发后加载（<5000词）
3. 捆绑资源: 按需加载（无限制）

遵循原则:
- 上下文效率优先
- 渐进式披露架构
- 自由度匹配原则
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class SkillMetadata:
    """技能元数据 - 第1层"""
    name: str  # 技能名称
    description: str  # 触发描述（包含所有"何时使用"信息）
    triggers: List[str] = field(default_factory=list)  # 触发场景
    requires: Dict[str, List[str]] = field(default_factory=dict)  # 依赖声明
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据


@dataclass
class SkillBody:
    """技能主体 - 第2层"""
    content: str  # 完整内容
    quick_start: str = ""  # 快速开始
    workflow: str = ""  # 工作流程
    references: List[str] = field(default_factory=list)  # 参考文档
    resources: List[str] = field(default_factory=list)  # 捆绑资源


@dataclass
class SkillResource:
    """技能资源 - 第3层"""
    path: str  # 资源路径
    resource_type: str  # 资源类型
    content: Optional[str] = None  # 资源内容


class SkillLoader:
    """
    渐进式技能加载器
    
    分层加载技能，优化上下文使用效率
    """
    
    SKILL_FILE = "SKILL.md"
    RESOURCE_DIRS = ["scripts", "references", "assets"]
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self._metadata_cache: Dict[str, SkillMetadata] = {}
        self._body_cache: Dict[str, SkillBody] = {}
        self._resource_cache: Dict[str, Dict[str, SkillResource]] = {}
    
    def list_skills(self) -> List[str]:
        """列出所有技能"""
        skills = []
        if not self.skills_dir.exists():
            return skills
        
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / self.SKILL_FILE).exists():
                skills.append(item.name)
        
        return skills
    
    def load_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """加载技能元数据（第1层）"""
        if skill_name in self._metadata_cache:
            return self._metadata_cache[skill_name]
        
        skill_path = self.skills_dir / skill_name
        skill_file = skill_path / self.SKILL_FILE
        
        if not skill_file.exists():
            return None
        
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata = self._parse_frontmatter(content, skill_name)
            
            self._metadata_cache[skill_name] = metadata
            return metadata
            
        except Exception as e:
            print(f"[SkillLoader] 加载技能元数据失败: {skill_name} - {e}")
            return None
    
    def load_body(self, skill_name: str) -> Optional[SkillBody]:
        """加载技能主体（第2层）"""
        if skill_name in self._body_cache:
            return self._body_cache[skill_name]
        
        skill_path = self.skills_dir / skill_name
        skill_file = skill_path / self.SKILL_FILE
        
        if not skill_file.exists():
            return None
        
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            body = self._parse_body(content)
            
            # 加载捆绑资源列表
            body.resources = self.list_resources(skill_name)
            
            self._body_cache[skill_name] = body
            return body
            
        except Exception as e:
            print(f"[SkillLoader] 加载技能主体失败: {skill_name} - {e}")
            return None
    
    def load_resource(
        self, 
        skill_name: str, 
        resource_path: str
    ) -> Optional[SkillResource]:
        """加载技能资源（第3层，按需加载）"""
        cache_key = f"{skill_name}:{resource_path}"
        if cache_key in self._resource_cache:
            return self._resource_cache[cache_key]
        
        skill_path = self.skills_dir / skill_name
        full_path = skill_path / resource_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            resource_type = self._get_resource_type(resource_path)
            
            resource = SkillResource(
                path=str(full_path),
                resource_type=resource_type,
                content=content
            )
            
            self._resource_cache[cache_key] = resource
            return resource
            
        except Exception as e:
            print(f"[SkillLoader] 加载资源失败: {resource_path} - {e}")
            return None
    
    def load_script(self, skill_name: str, script_name: str) -> Optional[str]:
        """加载脚本资源"""
        script_path = f"scripts/{script_name}"
        resource = self.load_resource(skill_name, script_path)
        return resource.content if resource else None
    
    def list_resources(self, skill_name: str, resource_type: str = None) -> List[str]:
        """列出技能的所有资源"""
        skill_path = self.skills_dir / skill_name
        resources = []
        
        for res_dir in self.RESOURCE_DIRS:
            res_path = skill_path / res_dir
            if res_path.exists() and res_path.is_dir():
                if resource_type and res_dir != resource_type:
                    continue
                for item in res_path.iterdir():
                    if item.is_file():
                        resources.append(f"{res_dir}/{item.name}")
        
        return resources
    
    def _parse_frontmatter(self, content: str, skill_name: str) -> SkillMetadata:
        """解析 YAML frontmatter"""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            fm_content = match.group(1)
            
            if HAS_YAML:
                try:
                    fm_data = yaml.safe_load(fm_content)
                    
                    name = fm_data.get('name', skill_name)
                    description = fm_data.get('description', '')
                    
                    # 提取触发场景
                    triggers = []
                    if isinstance(description, str):
                        # 支持多种格式的触发场景
                        lines = description.split('\n')
                        for line in lines:
                            if '场景' in line:
                                scene_match = re.findall(r'\((\d+)\)\s*([^()]+)', line)
                                if scene_match:
                                    triggers.extend([sm[1].strip() for sm in scene_match])
                                else:
                                    # 简单格式: "场景一、场景二"
                                    scene_text = line
                                    triggers.extend([s.strip() for s in scene_text.split('、') if s.strip()])
                    
                    # 解析依赖声明
                    requires = {
                        'bins': [],
                        'env': []
                    }
                    metadata = fm_data.get('metadata', {})
                    if isinstance(metadata, dict):
                        openclaw = metadata.get('openclaw', {})
                        req = openclaw.get('requires', {})
                        if isinstance(req, dict):
                            requires['bins'] = req.get('bins', [])
                            requires['env'] = req.get('env', [])
                    
                    version = fm_data.get('version', '1.0.0')
                    
                    return SkillMetadata(
                        name=name,
                        description=description,
                        triggers=triggers,
                        requires=requires,
                        version=version,
                        metadata=metadata
                    )
                except yaml.YAMLError:
                    pass
            
            # 兼容纯文本解析
            name_match = re.search(r'^name:\s*(.+)', fm_content, re.MULTILINE)
            desc_match = re.search(r'^description:\s*\|?\s*\n((?:[ \t]+.+\n?)+)', fm_content, re.MULTILINE)
            
            name = name_match.group(1).strip() if name_match else skill_name
            description = desc_match.group(1).strip() if desc_match else ""
            
            return SkillMetadata(
                name=name,
                description=description,
                triggers=[],
                requires={'bins': [], 'env': []},
                version="1.0.0"
            )
        
        return SkillMetadata(
            name=skill_name,
            description=content[:200],
            requires={'bins': [], 'env': []}
        )
    
    def _parse_body(self, content: str) -> SkillBody:
        """解析技能主体"""
        frontmatter_pattern = r'^---\s*\n.*?\n---\s*\n'
        body_content = re.sub(frontmatter_pattern, '', content, count=1, flags=re.DOTALL)
        
        quick_start = ""
        workflow = ""
        references = []
        
        # 解析快速开始
        quick_start_match = re.search(
            r'##\s*快速开始\s*\n(.*?)(?=\n##|\Z)', 
            body_content, 
            re.DOTALL | re.IGNORECASE
        )
        if quick_start_match:
            quick_start = quick_start_match.group(1).strip()
        
        # 解析工作流程
        workflow_match = re.search(
            r'##\s*工作流程\s*\n(.*?)(?=\n##|\Z)', 
            body_content, 
            re.DOTALL | re.IGNORECASE
        )
        if workflow_match:
            workflow = workflow_match.group(1).strip()
        
        # 解析参考文档
        ref_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        for match in re.finditer(ref_pattern, body_content):
            ref_path = match.group(2)
            if any(ref_path.startswith(d) for d in self.RESOURCE_DIRS):
                references.append(ref_path)
        
        return SkillBody(
            content=body_content,
            quick_start=quick_start,
            workflow=workflow,
            references=references
        )
    
    def _get_resource_type(self, path: str) -> str:
        """获取资源类型"""
        for res_type in self.RESOURCE_DIRS:
            if path.startswith(res_type):
                return res_type
        return "unknown"
    
    def get_tool_schema(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取工具 schema"""
        metadata = self.load_metadata(skill_name)
        if not metadata:
            return None
        
        return {
            "type": "function",
            "function": {
                "name": metadata.name,
                "description": metadata.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "要执行的操作"
                        },
                        "params": {
                            "type": "object",
                            "description": "操作参数"
                        }
                    },
                    "required": ["action"]
                }
            }
        }
    
    def search_skills(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        """搜索技能"""
        query_lower = query.lower()
        results = []
        
        for skill_name in self.list_skills():
            metadata = self.load_metadata(skill_name)
            if not metadata:
                continue
            
            score = 0.0
            
            # 名称匹配
            if query_lower in metadata.name.lower():
                score += 0.5
            
            # 描述匹配
            if query_lower in metadata.description.lower():
                score += 0.3
            
            # 触发场景匹配
            for trigger in metadata.triggers:
                if query_lower in trigger.lower():
                    score += 0.2
                    break
            
            if score > 0:
                results.append((skill_name, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def validate_skill(self, skill_name: str) -> Dict[str, Any]:
        """验证技能格式"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        skill_path = self.skills_dir / skill_name
        skill_file = skill_path / self.SKILL_FILE
        
        if not skill_file.exists():
            validation["valid"] = False
            validation["errors"].append("SKILL.md 文件不存在")
            return validation
        
        # 验证命名规范
        if not re.match(r'^[a-z0-9-]{1,64}$', skill_name):
            validation["warnings"].append("技能名称应仅使用小写字母、数字、连字符，最大64字符")
        
        # 验证元数据
        metadata = self.load_metadata(skill_name)
        if not metadata:
            validation["valid"] = False
            validation["errors"].append("无法加载技能元数据")
        else:
            if not metadata.description:
                validation["errors"].append("缺少技能描述")
            if len(metadata.description) < 20:
                validation["warnings"].append("技能描述过短，应包含触发场景")
        
        # 验证目录结构
        for res_dir in self.RESOURCE_DIRS:
            res_path = skill_path / res_dir
            if res_path.exists() and not res_path.is_dir():
                validation["errors"].append(f"{res_dir} 应是目录")
        
        return validation
    
    def clear_cache(self):
        """清除缓存"""
        self._metadata_cache.clear()
        self._body_cache.clear()
        self._resource_cache.clear()
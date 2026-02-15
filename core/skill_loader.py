"""
渐进式技能加载器 - Progressive Skill Loader

核心设计:
1. 元数据层: 始终加载（~100词）
2. 指令主体: 触发后加载（<5000词）
3. 捆绑资源: 按需加载（无限制）

遵循原则:
- 上下文效率优先
- 渐进式披露
- 自由度匹配
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
    name: str
    description: str
    triggers: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass
class SkillBody:
    content: str
    quick_start: str = ""
    workflow: str = ""
    references: List[str] = field(default_factory=list)


@dataclass
class SkillResource:
    path: str
    resource_type: str
    content: Optional[str] = None


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
        skills = []
        if not self.skills_dir.exists():
            return skills
        
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / self.SKILL_FILE).exists():
                skills.append(item.name)
        
        return skills
    
    def load_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
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
        script_path = f"scripts/{script_name}"
        resource = self.load_resource(skill_name, script_path)
        return resource.content if resource else None
    
    def list_resources(self, skill_name: str, resource_type: str = None) -> List[str]:
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
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            fm_content = match.group(1)
            
            if HAS_YAML:
                try:
                    fm_data = yaml.safe_load(fm_content)
                    
                    name = fm_data.get('name', skill_name)
                    description = fm_data.get('description', '')
                    
                    triggers = []
                    if isinstance(description, str):
                        trigger_match = re.search(r'触发场景[：:]\s*(.+?)(?:\n|$)', description)
                        if trigger_match:
                            triggers_text = trigger_match.group(1)
                            triggers = [t.strip() for t in re.findall(r'\((\d+)\)\s*([^()]+)', triggers_text)]
                            if not triggers:
                                triggers = [t.strip() for t in triggers_text.split('、') if t.strip()]
                    
                    requires = fm_data.get('metadata', {}).get('requires', [])
                    if isinstance(requires, dict):
                        requires = requires.get('bins', []) + requires.get('env', [])
                    
                    version = fm_data.get('version', '1.0.0')
                    
                    return SkillMetadata(
                        name=name,
                        description=description,
                        triggers=triggers,
                        requires=requires if isinstance(requires, list) else [],
                        version=version
                    )
                except yaml.YAMLError:
                    pass
            
            name_match = re.search(r'^name:\s*(.+)$', fm_content, re.MULTILINE)
            desc_match = re.search(r'^description:\s*\|?\s*\n((?:[ \t]+.+\n?)+)', fm_content, re.MULTILINE)
            
            name = name_match.group(1).strip() if name_match else skill_name
            description = desc_match.group(1).strip() if desc_match else ""
            
            return SkillMetadata(
                name=name,
                description=description,
                triggers=[],
                requires=[],
                version="1.0.0"
            )
        
        return SkillMetadata(
            name=skill_name,
            description=content[:200]
        )
    
    def _parse_body(self, content: str) -> SkillBody:
        frontmatter_pattern = r'^---\s*\n.*?\n---\s*\n'
        body_content = re.sub(frontmatter_pattern, '', content, count=1, flags=re.DOTALL)
        
        quick_start = ""
        workflow = ""
        references = []
        
        quick_start_match = re.search(
            r'##\s*快速开始\s*\n(.*?)(?=\n##|\Z)', 
            body_content, 
            re.DOTALL | re.IGNORECASE
        )
        if quick_start_match:
            quick_start = quick_start_match.group(1).strip()
        
        workflow_match = re.search(
            r'##\s*工作流程\s*\n(.*?)(?=\n##|\Z)', 
            body_content, 
            re.DOTALL | re.IGNORECASE
        )
        if workflow_match:
            workflow = workflow_match.group(1).strip()
        
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
        for res_type in self.RESOURCE_DIRS:
            if path.startswith(res_type):
                return res_type
        return "unknown"
    
    def get_tool_schema(self, skill_name: str) -> Optional[Dict[str, Any]]:
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
        query_lower = query.lower()
        results = []
        
        for skill_name in self.list_skills():
            metadata = self.load_metadata(skill_name)
            if not metadata:
                continue
            
            score = 0.0
            
            if query_lower in metadata.name.lower():
                score += 0.5
            
            if query_lower in metadata.description.lower():
                score += 0.3
            
            for trigger in metadata.triggers:
                if query_lower in trigger.lower():
                    score += 0.2
                    break
            
            if score > 0:
                results.append((skill_name, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def clear_cache(self):
        self._metadata_cache.clear()
        self._body_cache.clear()
        self._resource_cache.clear()

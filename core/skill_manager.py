"""
增强型技能管理器 - 支持渐进式披露架构

特性:
1. 双模式支持: Python技能 + SKILL.md技能
2. 渐进式加载: 元数据优先，按需加载详情
3. 语义搜索: 基于描述匹配技能
4. 动态创建: 支持运行时创建新技能
"""

import os
import importlib.util
import sys
import json
import re
from typing import List, Dict, Any, Optional, Callable

from .skill_loader import SkillLoader


class SkillManager:
    """
    增强型技能管理器
    
    支持两种技能格式:
    1. Python技能 (tools/*.py) - 传统格式
    2. SKILL.md技能 (skills/*/SKILL.md) - 渐进式披露格式
    """
    
    def __init__(
        self, 
        static_skills_dir: str = "tools", 
        dynamic_skills_dir: str = "agent_skills",
        md_skills_dir: str = "skills"
    ):
        self.static_dir = static_skills_dir
        self.dynamic_dir = dynamic_skills_dir
        self.md_skills_dir = md_skills_dir
        
        self.skills: Dict[str, Dict] = {}
        self.skill_embeddings: Dict[str, List[str]] = {}
        
        self.md_loader = SkillLoader(md_skills_dir)
        
        if not os.path.exists(self.dynamic_dir):
            os.makedirs(self.dynamic_dir)
            with open(os.path.join(self.dynamic_dir, "__init__.py"), "w") as f:
                f.write("# Agent generated skills\n")
        
        self._load_all_skills()
    
    def _load_all_skills(self):
        self._load_static_skills()
        self._load_dynamic_skills()
        self._load_md_skills()
        self._build_skill_index()
    
    def _load_static_skills(self):
        static_skills = [
            ("tools.notes_skill", "NotesSkill", "notes_operator"),
            ("tools.chat_skill", "ChatSkill", "chat"),
            ("tools.search_skill", "SearchSkill", "web_search"),
            ("tools.http_skill", "HttpSkill", "http_request"),
            ("tools.http_skill", "RssSkill", "rss_fetcher"),
            ("tools.http_skill", "WebScraperSkill", "web_scraper"),
            ("browser_agent.browser_skill", "BrowserSkill", "browser_agent"),
            ("browser_agent.browser_skill", "BrowserCredentialSkill", "browser_agent_save_credentials"),
            ("browser_agent.browser_skill", "BrowserListSitesSkill", "browser_agent_list_sites"),
            ("desktop_agent.desktop_skill", "DesktopSkill", "desktop_agent"),
            ("desktop_agent.desktop_skill", "DesktopAppListSkill", "desktop_list_common_apps"),
            ("tools.code_guard_skill", "CodeGuardSkill", "code_guard_status"),
            ("tools.code_guard_skill", "CodeGuardSetLevelSkill", "code_guard_set_level"),
            ("tools.code_guard_skill", "CodeGuardHistorySkill", "code_guard_history"),
            ("tools.code_guard_skill", "CodeGuardRollbackSkill", "code_guard_rollback"),
        ]
        
        for module_path, class_name, default_name in static_skills:
            try:
                module = __import__(module_path, fromlist=[class_name])
                skill_class = getattr(module, class_name)
                
                if hasattr(skill_class, 'get_tool_definition') and hasattr(skill_class, 'run'):
                    schema = skill_class.get_tool_definition()
                    self.register_skill(default_name, skill_class.run, schema, source_type="python")
            except (ImportError, AttributeError) as e:
                pass
    
    def _load_dynamic_skills(self):
        if not os.path.exists(self.dynamic_dir):
            return
        
        for filename in os.listdir(self.dynamic_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(self.dynamic_dir, filename)
                module_name = filename[:-3]
                self._load_skill_from_file(filepath, module_name)
    
    def _load_md_skills(self):
        for skill_name in self.md_loader.list_skills():
            self._load_md_skill(skill_name)
    
    def _load_md_skill(self, skill_name: str):
        metadata = self.md_loader.load_metadata(skill_name)
        if not metadata:
            return
        
        schema = self.md_loader.get_tool_schema(skill_name)
        if not schema:
            return
        
        def md_skill_runner(arguments: dict) -> dict:
            return self._execute_md_skill(skill_name, arguments)
        
        self.register_skill(
            metadata.name, 
            md_skill_runner, 
            schema, 
            source_type="md",
            source_path=skill_name
        )
    
    def _execute_md_skill(self, skill_name: str, arguments: dict) -> dict:
        body = self.md_loader.load_body(skill_name)
        if not body:
            return {"success": False, "error": f"无法加载技能主体: {skill_name}"}
        
        action = arguments.get("action", "")
        params = arguments.get("params", {})
        
        script_path = f"scripts/{action}.py"
        script_content = self.md_loader.load_script(skill_name, f"{action}.py")
        
        if script_content:
            try:
                result = self._execute_script(script_content, params)
                return result
            except Exception as e:
                return {"success": False, "error": f"脚本执行失败: {e}"}
        
        return {
            "success": True,
            "message": f"技能 {skill_name} 已触发",
            "action": action,
            "params": params,
            "workflow": body.workflow[:500] if body.workflow else ""
        }
    
    def _execute_script(self, script_content: str, params: dict) -> dict:
        local_vars = {"params": params, "result": None}
        
        try:
            exec(script_content, {"__builtins__": __builtins__}, local_vars)
            return local_vars.get("result", {"success": True})
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _load_skill_from_file(self, filepath: str, module_name: str):
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if not spec or not spec.loader:
                return
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, 'run') and hasattr(module, 'get_tool_definition'):
                schema = module.get_tool_definition()
                self.register_skill(module_name, module.run, schema, source_type="python")
        except Exception as e:
            print(f"[SkillManager] 加载 {filepath} 失败: {e}")
    
    def register_skill(
        self, 
        name: str, 
        func: Callable, 
        schema: Dict, 
        source_type: str = "python",
        source_path: str = None
    ) -> bool:
        if "function" not in schema and "name" in schema:
            schema = {
                "type": "function",
                "function": schema
            }
        
        if "function" not in schema:
            print(f"[SkillManager] ⚠️ 技能 {name} 的 Schema 格式错误")
            return False
        
        real_name = schema["function"]["name"]
        
        self.skills[real_name] = {
            "func": func,
            "schema": schema,
            "source": name,
            "source_type": source_type,
            "source_path": source_path or name
        }
        
        return True
    
    def _build_skill_index(self):
        self.skill_embeddings = {}
        
        for skill_name, skill_info in self.skills.items():
            schema = skill_info.get("schema", {})
            func = schema.get("function", {})
            
            keywords = []
            
            description = func.get("description", "")
            keywords.extend(self._extract_keywords(description))
            
            name_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', skill_name)
            keywords.extend([p.lower() for p in name_parts])
            
            params = func.get("parameters", {}).get("properties", {})
            for param_name, param_info in params.items():
                keywords.append(param_name.lower())
                if "description" in param_info:
                    keywords.extend(self._extract_keywords(param_info["description"]))
            
            self.skill_embeddings[skill_name] = list(set(keywords))
    
    def _extract_keywords(self, text: str) -> List[str]:
        stop_words = {"的", "是", "在", "了", "和", "与", "或", "有", "这", "那", "一个", "可以", "用于", "支持"}
        
        words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text)
        
        keywords = []
        for word in words:
            if len(word) > 1 and word.lower() not in stop_words:
                keywords.append(word.lower())
        
        return keywords
    
    def get_all_tools_schema(self) -> List[Dict]:
        return [info["schema"] for info in self.skills.values()]
    
    def get_skill(self, name: str) -> Optional[Callable]:
        return self.skills.get(name, {}).get("func")
    
    def get_skill_info(self, name: str) -> Optional[Dict]:
        skill = self.skills.get(name)
        if skill:
            return {
                "name": name,
                "schema": skill["schema"],
                "source": skill["source"],
                "source_type": skill.get("source_type", "python"),
                "source_path": skill.get("source_path", name)
            }
        return None
    
    def get_skill_body(self, name: str) -> Optional[str]:
        skill_info = self.skills.get(name)
        if not skill_info:
            return None
        
        if skill_info.get("source_type") == "md":
            source_path = skill_info.get("source_path", name)
            body = self.md_loader.load_body(source_path)
            return body.content if body else None
        
        return None
    
    def search_skills(self, query: str, top_k: int = 5) -> List[Dict]:
        query_keywords = self._extract_keywords(query)
        
        scores = {}
        for skill_name, skill_keywords in self.skill_embeddings.items():
            score = self._calculate_similarity(query_keywords, skill_keywords)
            scores[skill_name] = score
        
        sorted_skills = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
        
        results = []
        for skill_name in sorted_skills:
            if scores[skill_name] > 0:
                skill_info = self.skills[skill_name]
                func_info = skill_info["schema"].get("function", {})
                results.append({
                    "name": skill_name,
                    "description": func_info.get("description", ""),
                    "score": scores[skill_name],
                    "source": skill_info["source"],
                    "source_type": skill_info.get("source_type", "python")
                })
        
        return results
    
    def _calculate_similarity(self, query_keywords: List[str], skill_keywords: List[str]) -> float:
        if not query_keywords or not skill_keywords:
            return 0.0
        
        query_set = set(query_keywords)
        skill_set = set(skill_keywords)
        
        intersection = query_set & skill_set
        
        base_score = len(intersection) / max(len(query_set), 1)
        
        bonus = 0.0
        for qk in query_keywords:
            for sk in skill_keywords:
                if qk in sk or sk in qk:
                    bonus += 0.1
        
        return min(base_score + bonus, 1.0)
    
    def create_skill_file(self, skill_name: str, code_content: str) -> Optional[str]:
        code_content = self._clean_code_content(code_content)
        
        if not self._validate_skill_code(code_content):
            print(f"[SkillManager] ⚠️ 技能代码验证失败")
            return None
        
        try:
            from code_guard import get_code_guard
            guard = get_code_guard()
            
            is_dangerous, dangers = guard.check_dangerous_code(code_content)
            if is_dangerous:
                print(f"[SkillManager] ❌ 代码包含危险模式: {dangers}")
                return None
            
            is_suspicious, warnings = guard.check_suspicious_code(code_content)
            if is_suspicious:
                print(f"[SkillManager] ⚠️ 代码包含可疑模式: {warnings}")
        except ImportError:
            pass
        
        filename = f"{skill_name}.py"
        filepath = os.path.join(self.dynamic_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_content)
        
        print(f"[SkillManager] ✅ 新技能已保存: {filepath}")
        
        self._load_skill_from_file(filepath, skill_name)
        self._build_skill_index()
        
        return filepath
    
    def create_md_skill(
        self, 
        skill_name: str, 
        description: str, 
        body_content: str,
        resources: Dict[str, str] = None
    ) -> Optional[str]:
        skill_dir = os.path.join(self.md_skills_dir, skill_name)
        os.makedirs(skill_dir, exist_ok=True)
        
        skill_md_content = f"""---
name: {skill_name}
description: |
  {description}
---

{body_content}
"""
        
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(skill_md_content)
        
        if resources:
            for res_type, res_files in resources.items():
                res_dir = os.path.join(skill_dir, res_type)
                os.makedirs(res_dir, exist_ok=True)
                
                for filename, content in res_files.items():
                    filepath = os.path.join(res_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
        
        self._load_md_skill(skill_name)
        self._build_skill_index()
        
        return skill_dir
    
    def _clean_code_content(self, code: str) -> str:
        code = re.sub(r'```python\s*', '', code, flags=re.IGNORECASE)
        code = re.sub(r'```\s*', '', code)
        return code.strip()
    
    def _validate_skill_code(self, code: str) -> bool:
        required_elements = ['def run(', 'def get_tool_definition(']
        
        for element in required_elements:
            if element not in code:
                return False
        
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False
    
    def list_skills(self) -> List[str]:
        return list(self.skills.keys())
    
    def list_skills_by_type(self, source_type: str = None) -> List[str]:
        if not source_type:
            return list(self.skills.keys())
        
        return [
            name for name, info in self.skills.items() 
            if info.get("source_type") == source_type
        ]
    
    def get_skills_summary(self) -> str:
        lines = ["## 已加载技能"]
        for name, info in self.skills.items():
            func = info["schema"].get("function", {})
            desc = func.get("description", "无描述")[:50]
            source_type = info.get("source_type", "python")
            type_icon = "📄" if source_type == "md" else "🐍"
            lines.append(f"- {type_icon} **{name}**: {desc}")
        return "\n".join(lines)
    
    def reload_skills(self):
        self.skills.clear()
        self.skill_embeddings.clear()
        self.md_loader.clear_cache()
        self._load_all_skills()

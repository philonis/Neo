# core/skill_manager.py
import os
import importlib.util
import sys
import json

class SkillManager:
    def __init__(self, static_skills_dir="tools", dynamic_skills_dir="agent_skills"):
        self.static_dir = static_skills_dir
        self.dynamic_dir = dynamic_skills_dir
        self.skills = {} # name -> function
        
        # 确保动态技能目录存在
        if not os.path.exists(self.dynamic_dir):
            os.makedirs(self.dynamic_dir)
            # 创建 __init__.py 使其成为一个包
            with open(os.path.join(self.dynamic_dir, "__init__.py"), "w") as f:
                f.write("# Agent generated skills")

        self.load_static_skills()
        self.load_dynamic_skills()

    def load_static_skills(self):
        """加载系统级工具（如 NotesSkill）"""
        # 这里硬编码导入，确保系统核心稳定
        # 实际生产中可以自动扫描 tools 目录，但为了安全，建议显式注册
        try:
            from tools.notes_skill import NotesSkill
            self.register_skill("notes_operator", NotesSkill.run, NotesSkill.get_tool_definition())
        except ImportError:
            pass # 忽略未安装的模块
        
        try:
            from tools.chat_skill import ChatSkill
            self.register_skill("chat", ChatSkill.run, ChatSkill.get_tool_definition())
        except ImportError:
            pass # 忽略未安装的模块
        
        try:
            from tools.search_skill import SearchSkill
            self.register_skill("web_search", SearchSkill.run, SearchSkill.get_tool_definition())
        except ImportError:
            pass # 忽略未安装的模块

    def load_dynamic_skills(self):
        """动态加载 agent_skills 目录下的 .py 文件"""
        for filename in os.listdir(self.dynamic_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(self.dynamic_dir, filename)
                module_name = filename[:-3]
                self._load_skill_from_file(filepath, module_name)

    def _load_skill_from_file(self, filepath, module_name):
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, 'run') and hasattr(module, 'get_tool_definition'):
                # 注意：这里的 module_name 是文件名，传入 register_skill 仅用于错误提示或日志
                # 真正的名字会在 register_skill 内部从 schema 读取
                self.register_skill(module_name, module.run, module.get_tool_definition())
        except Exception as e:
            print(f"[SkillManager] 加载 {filepath} 失败: {e}")
            
    def register_skill(self, name, func, schema):
        # --- 修复格式 ---
        # 如果 schema 里直接有 'name' 但没有 'function' 键，补全格式
        if "function" not in schema and "name" in schema:
            schema = {
                "type": "function",
                "function": schema
            }
        
        if "function" not in schema:
            print(f"[SkillManager] ⚠️ 技能文件 {name} 的 Schema 格式错误，已忽略。")
            return

        # === 核心修正：使用代码内部定义的名字，而不是文件名 ===
        real_name = schema["function"]["name"]
        
        self.skills[real_name] = {  # 这里用 real_name 作为 key
            "func": func,
            "schema": schema
        }
        # 打印日志确认
        # print(f"[SkillManager] 注册技能: {real_name} (文件: {name})")
    def get_all_tools_schema(self):
        return [info["schema"] for info in self.skills.values()]

    def get_skill(self, name):
        return self.skills.get(name, {}).get("func")

    def search_skills(self, description):
        """
        根据功能描述搜索现有技能
        
        :param description: 技能功能描述
        :return: 匹配的技能列表，按相关性排序
        """
        matching_skills = []
        
        for skill_name, skill_info in self.skills.items():
            schema = skill_info.get("schema", {})
            function_info = schema.get("function", {})
            skill_description = function_info.get("description", "")
            
            # 简单的关键词匹配
            if any(keyword in skill_description.lower() for keyword in description.lower().split()):
                matching_skills.append({
                    "name": skill_name,
                    "description": skill_description,
                    "relevance": len(set(description.lower().split()) & set(skill_description.lower().split()))
                })
        
        # 按相关性排序
        matching_skills.sort(key=lambda x: x["relevance"], reverse=True)
        return matching_skills

    def create_skill_file(self, skill_name, code_content):
        """保存新生成的技能代码"""
        filename = f"{skill_name}.py"
        filepath = os.path.join(self.dynamic_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_content)
        print(f"[SkillManager] 新技能已保存: {filepath}")
        
        # 立即加载
        self._load_skill_from_file(filepath, skill_name)
        return filepath

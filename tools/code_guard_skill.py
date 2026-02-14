"""
代码修改管理技能 - 让用户可以安全地管理Neo的自我修改能力

提供：
- 查看当前保护状态
- 设置修改级别
- 查看修改历史
- 回滚修改
"""

from typing import Dict, Any


class CodeGuardSkill:
    """代码保护状态查询"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "code_guard_status",
                "description": "查看代码保护系统的当前状态，包括保护级别、受保护的文件、沙盒目录等信息。",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        try:
            from code_guard import get_code_guard
            guard = get_code_guard()
            return {
                "success": True,
                "status": guard.get_status()
            }
        except ImportError:
            return {
                "success": False,
                "error": "代码保护系统未安装"
            }


class CodeGuardSetLevelSkill:
    """设置代码修改级别"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "code_guard_set_level",
                "description": """设置代码修改保护级别。

级别说明：
- none: 禁止所有代码修改
- skills_only: 只能创建新技能（默认，推荐）
- extensions: 可以创建扩展模块
- full_with_approval: 可以修改任何文件，但需要用户确认

⚠️ 更高级别意味着更高风险！""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": ["none", "skills_only", "extensions", "full_with_approval"],
                            "description": "保护级别"
                        }
                    },
                    "required": ["level"]
                }
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        level = arguments.get("level", "skills_only")
        
        try:
            from code_guard import get_code_guard, ModificationLevel
            
            level_map = {
                "none": ModificationLevel.NONE,
                "skills_only": ModificationLevel.SKILLS_ONLY,
                "extensions": ModificationLevel.EXTENSIONS,
                "full_with_approval": ModificationLevel.FULL_WITH_APPROVAL
            }
            
            if level not in level_map:
                return {
                    "success": False,
                    "error": f"未知级别: {level}"
                }
            
            guard = get_code_guard(level_map[level])
            
            return {
                "success": True,
                "message": f"保护级别已设置为: {level}",
                "level": level,
                "warning": "⚠️ 更高级别意味着更高风险" if level in ["extensions", "full_with_approval"] else None
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "代码保护系统未安装"
            }


class CodeGuardHistorySkill:
    """查看修改历史"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "code_guard_history",
                "description": "查看最近的代码修改历史记录。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "返回的记录数量，默认10",
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": []
                }
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        limit = arguments.get("limit", 10)
        
        try:
            from code_guard import get_code_guard
            guard = get_code_guard()
            history = guard.get_modification_history(limit)
            
            return {
                "success": True,
                "history": history,
                "count": len(history)
            }
        except ImportError:
            return {
                "success": False,
                "error": "代码保护系统未安装"
            }


class CodeGuardRollbackSkill:
    """回滚代码修改"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "code_guard_rollback",
                "description": "回滚最近的代码修改。每次回滚会恢复一个被修改的文件到之前的状态。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "steps": {
                            "type": "integer",
                            "description": "回滚步数，默认1",
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": []
                }
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        steps = arguments.get("steps", 1)
        
        try:
            from code_guard import get_code_guard
            guard = get_code_guard()
            result = guard.rollback(steps)
            
            return result
        except ImportError:
            return {
                "success": False,
                "error": "代码保护系统未安装"
            }

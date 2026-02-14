"""
Desktop Agent Skill - 主技能入口

像真人一样操作macOS应用。

核心能力:
1. 启动和激活应用
2. 操作UI元素（点击、输入、选择）
3. 读取应用内容
4. 发送快捷键
5. 安全护栏保护
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from .app_launcher import AppLauncher
from .ui_agent import UIAgent


class DesktopSkill:
    """
    Desktop Agent 技能
    
    让Neo能够像真人一样操作macOS应用
    """
    
    _instance = None
    _launcher = None
    _ui_agent = None
    _safety_guard = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def _ensure_initialized(cls):
        if cls._launcher is None:
            cls._launcher = AppLauncher()
        if cls._ui_agent is None:
            cls._ui_agent = UIAgent()
        if cls._safety_guard is None:
            from browser_agent.safety_guard import SafetyGuard
            cls._safety_guard = SafetyGuard()
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "desktop_agent",
                "description": """像真人一样操作macOS应用。适用场景：
- 打开并操作本地应用（如豆包、微信、Safari等）
- 在应用中输入文本、点击按钮
- 读取应用窗口内容
- 发送快捷键

支持的操作：
- launch: 启动应用
- activate: 激活应用窗口
- click: 点击UI元素
- type: 输入文本
- hotkey: 发送快捷键
- read: 读取窗口内容
- get_elements: 获取UI元素列表
- screenshot: 截图
- scroll: 滚动
- close: 关闭应用

安全说明：敏感操作需要用户确认。""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "launch", "activate", "click", "type",
                                "hotkey", "read", "get_elements", 
                                "screenshot", "scroll", "close",
                                "is_running", "list_apps", "select_menu",
                                "clear_and_type", "click_at"
                            ],
                            "description": "要执行的操作类型"
                        },
                        "app_name": {
                            "type": "string",
                            "description": "应用名称（如 '豆包', 'Safari', 'WeChat'）"
                        },
                        "element": {
                            "type": "string",
                            "description": "UI元素描述（用于click操作）"
                        },
                        "text": {
                            "type": "string",
                            "description": "要输入的文本（用于type操作）"
                        },
                        "key": {
                            "type": "string",
                            "description": "按键名称（如 'enter', 'tab', 'escape'）"
                        },
                        "modifiers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "修饰键（如 ['command', 'shift']）"
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down"],
                            "description": "滚动方向"
                        },
                        "menu_name": {
                            "type": "string",
                            "description": "菜单名称（用于select_menu操作）"
                        },
                        "menu_item": {
                            "type": "string",
                            "description": "菜单项名称"
                        },
                        "x": {
                            "type": "integer",
                            "description": "X坐标（用于click_at操作）"
                        },
                        "y": {
                            "type": "integer",
                            "description": "Y坐标"
                        },
                        "auto_confirm": {
                            "type": "boolean",
                            "description": "是否自动确认敏感操作，默认false"
                        }
                    },
                    "required": ["action"]
                }
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        DesktopSkill._ensure_initialized()
        
        action = arguments.get("action", "")
        
        if not action:
            return {
                "success": False,
                "error": "缺少action参数",
                "available_actions": [
                    "launch", "activate", "click", "type",
                    "hotkey", "read", "get_elements", 
                    "screenshot", "scroll", "close",
                    "is_running", "list_apps", "select_menu",
                    "clear_and_type", "click_at"
                ]
            }
        
        app_name = arguments.get("app_name", "")
        element = arguments.get("element", "")
        text = arguments.get("text", "")
        key = arguments.get("key", "")
        modifiers = arguments.get("modifiers", [])
        direction = arguments.get("direction", "down")
        menu_name = arguments.get("menu_name", "")
        menu_item = arguments.get("menu_item", "")
        x = arguments.get("x")
        y = arguments.get("y")
        auto_confirm = arguments.get("auto_confirm", False)
        
        safety_check = DesktopSkill._safety_guard.check_operation(
            action=action,
            target=app_name or element,
            value=text or key,
            auto_confirm=auto_confirm
        )
        
        if not safety_check["allowed"]:
            return {
                "success": False,
                "error": safety_check["reason"],
                "level": safety_check["level"],
                "requires_confirmation": safety_check.get("requires_confirmation", False),
                "confirmation_message": safety_check.get("confirmation_message", "")
            }
        
        launcher = DesktopSkill._launcher
        ui_agent = DesktopSkill._ui_agent
        
        if action == "launch":
            if not app_name:
                return {"success": False, "error": "launch操作需要app_name参数"}
            return launcher.launch(app_name)
        
        elif action == "activate":
            if not app_name:
                return {"success": False, "error": "activate操作需要app_name参数"}
            return launcher.activate(app_name)
        
        elif action == "is_running":
            if not app_name:
                return {"success": False, "error": "is_running操作需要app_name参数"}
            return launcher.is_running(app_name)
        
        elif action == "list_apps":
            return launcher.list_running_apps()
        
        elif action == "close":
            if not app_name:
                return {"success": False, "error": "close操作需要app_name参数"}
            return launcher.close(app_name)
        
        elif action == "click":
            if not app_name or not element:
                return {"success": False, "error": "click操作需要app_name和element参数"}
            return ui_agent.click(app_name, element)
        
        elif action == "click_at":
            if x is None or y is None:
                return {"success": False, "error": "click_at操作需要x和y参数"}
            return ui_agent.click_at(app_name, x, y)
        
        elif action == "type":
            if not text:
                return {"success": False, "error": "type操作需要text参数"}
            return ui_agent.type_text(app_name, text)
        
        elif action == "clear_and_type":
            if not text:
                return {"success": False, "error": "clear_and_type操作需要text参数"}
            return ui_agent.clear_and_type(app_name, text)
        
        elif action == "hotkey":
            if not key:
                return {"success": False, "error": "hotkey操作需要key参数"}
            return ui_agent.hotkey(app_name, *modifiers, key)
        
        elif action == "read":
            return ui_agent.get_window_content(app_name)
        
        elif action == "get_elements":
            if not app_name:
                return {"success": False, "error": "get_elements操作需要app_name参数"}
            return ui_agent.get_ui_elements(app_name)
        
        elif action == "screenshot":
            return ui_agent.screenshot(app_name)
        
        elif action == "scroll":
            return ui_agent.scroll(app_name, direction)
        
        elif action == "select_menu":
            if not app_name or not menu_name or not menu_item:
                return {"success": False, "error": "select_menu操作需要app_name、menu_name和menu_item参数"}
            return ui_agent.select_menu(app_name, menu_name, menu_item)
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}


class DesktopAppListSkill:
    """列出常用应用"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "desktop_list_common_apps",
                "description": "列出Desktop Agent支持的常用应用名称",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        from .app_launcher import AppLauncher
        
        launcher = AppLauncher()
        
        apps = []
        for alias, name in launcher.COMMON_APPS.items():
            if alias.lower() == name.lower():
                apps.append(name)
            elif alias not in [a.get("alias") for a in apps]:
                apps.append({
                    "alias": alias,
                    "name": name
                })
        
        return {
            "success": True,
            "common_apps": launcher.COMMON_APPS,
            "hint": "也可以使用应用的完整名称或路径"
        }

"""
Browser Agent Skill - 主技能入口

像真人一样使用浏览器访问网站，获取信息，执行操作。

核心能力:
1. 导航和浏览网页
2. 提取页面内容
3. 自动处理登录
4. 执行交互操作
5. 安全护栏保护
"""

import asyncio
import os
from typing import Dict, Any, Optional, Callable
from .browser_controller import BrowserController
from .safety_guard import SafetyGuard, OperationLevel
from .session_manager import SessionManager


class BrowserSkill:
    """
    Browser Agent 技能
    
    让Neo能够像真人一样使用浏览器
    """
    
    _instance = None
    _controller = None
    _safety_guard = None
    _session_manager = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def _ensure_initialized(cls):
        if cls._safety_guard is None:
            cls._safety_guard = SafetyGuard()
        if cls._session_manager is None:
            cls._session_manager = SessionManager()
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "browser_agent",
                "description": """像真人一样使用浏览器访问网站。适用场景：
- 网站没有API时获取信息
- 需要登录才能查看的内容
- 动态渲染的页面内容
- 复杂的网页交互流程

支持的操作：
- navigate: 导航到URL
- read: 读取页面内容
- click: 点击元素
- fill: 填写输入框
- login: 登录网站
- scroll: 滚动页面
- screenshot: 截图
- extract: 提取特定内容
- get_dom: 获取页面结构

安全说明：敏感操作需要用户确认。""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "navigate", "read", "click", "fill", 
                                "login", "scroll", "screenshot", 
                                "extract", "get_dom", "wait",
                                "check_login", "close"
                            ],
                            "description": "要执行的操作类型"
                        },
                        "url": {
                            "type": "string",
                            "description": "目标URL（用于navigate操作）"
                        },
                        "target": {
                            "type": "string",
                            "description": "目标元素描述（用于click、fill等操作）"
                        },
                        "value": {
                            "type": "string",
                            "description": "输入值（用于fill操作）"
                        },
                        "selector": {
                            "type": "string",
                            "description": "CSS选择器（用于extract操作）"
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down"],
                            "description": "滚动方向（用于scroll操作）"
                        },
                        "headless": {
                            "type": "boolean",
                            "description": "是否无头模式运行，默认true"
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
        BrowserSkill._ensure_initialized()
        
        action = arguments.get("action", "")
        
        if not action:
            return {
                "success": False,
                "error": "缺少action参数",
                "available_actions": [
                    "navigate", "read", "click", "fill", "login",
                    "scroll", "screenshot", "extract", "get_dom", 
                    "wait", "check_login", "close"
                ]
            }
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            BrowserSkill._execute_action_async(arguments)
        )
    
    @staticmethod
    async def _execute_action_async(arguments: dict) -> dict:
        action = arguments.get("action", "")
        
        if action == "close":
            return await BrowserSkill._close_browser()
        
        if BrowserSkill._controller is None or not BrowserSkill._initialized:
            headless = arguments.get("headless", True)
            init_result = await BrowserSkill._initialize_browser(headless=headless)
            if not init_result["success"]:
                return init_result
        
        url = arguments.get("url", "")
        target = arguments.get("target", "")
        value = arguments.get("value", "")
        selector = arguments.get("selector", "")
        direction = arguments.get("direction", "down")
        auto_confirm = arguments.get("auto_confirm", False)
        
        safety_check = BrowserSkill._safety_guard.check_operation(
            action=action,
            target=target or url,
            value=value,
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
        
        controller = BrowserSkill._controller
        
        if action == "navigate":
            if not url:
                return {"success": False, "error": "navigate操作需要url参数"}
            
            result = await controller.navigate(url)
            
            if result["success"]:
                login_check = await controller.check_login_required()
                result["login_required"] = login_check.get("requires_login", False)
                
                if BrowserSkill._session_manager.has_credentials(url):
                    result["has_saved_credentials"] = True
            
            return result
        
        elif action == "read":
            return await controller.get_page_info()
        
        elif action == "get_dom":
            return await controller.get_dom_structure()
        
        elif action == "click":
            if not target:
                return {"success": False, "error": "click操作需要target参数"}
            return await controller.click(target)
        
        elif action == "fill":
            if not target or not value:
                return {"success": False, "error": "fill操作需要target和value参数"}
            return await controller.fill(target, value)
        
        elif action == "login":
            return await BrowserSkill._handle_login(url, target, value)
        
        elif action == "scroll":
            return await controller.scroll(direction)
        
        elif action == "screenshot":
            return await controller.screenshot()
        
        elif action == "extract":
            return await controller.extract_text(selector)
        
        elif action == "wait":
            return await controller.wait_for(selector)
        
        elif action == "check_login":
            return await controller.check_login_required()
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}
    
    @staticmethod
    async def _initialize_browser(headless: bool = True) -> dict:
        BrowserSkill._controller = BrowserController(headless=headless)
        
        success = await BrowserSkill._controller.initialize()
        
        if success:
            BrowserSkill._initialized = True
            return {
                "success": True,
                "message": "浏览器初始化成功",
                "headless": headless
            }
        else:
            BrowserSkill._controller = None
            return {
                "success": False,
                "error": "浏览器初始化失败，请确保已安装Playwright: pip install playwright && playwright install"
            }
    
    @staticmethod
    async def _handle_login(url: str, target: str, value: str) -> dict:
        controller = BrowserSkill._controller
        session_manager = BrowserSkill._session_manager
        
        current_url = controller.current_url or url
        credentials = None
        
        if session_manager.has_credentials(current_url):
            credentials = session_manager.get_credentials(current_url)
        
        if not credentials:
            return {
                "success": False,
                "error": "未找到保存的登录凭证",
                "hint": "请先使用 browser_agent_save_credentials 保存凭证，或在fill操作中手动输入用户名密码"
            }
        
        try:
            dom = await controller.get_dom_structure()
            elements = dom.get("interactive_elements", [])
            
            username_field = None
            password_field = None
            login_button = None
            
            for el in elements:
                el_type = (el.get("type") or "").lower()
                el_tag = el.get("tag", "")
                el_text = (el.get("text") or "").lower()
                el_name = (el.get("name") or "").lower()
                el_placeholder = (el.get("placeholder") or "").lower()
                
                if el_tag == "input":
                    if el_type == "password":
                        password_field = el
                    elif el_type in ["text", "email"] or "user" in el_name or "email" in el_name or "email" in el_placeholder:
                        username_field = el
                
                if el_tag == "button" or el_type == "submit":
                    if "登录" in el_text or "login" in el_text or "sign" in el_text:
                        login_button = el
            
            if username_field:
                username_selector = f"input[name='{username_field.get('name')}']" if username_field.get("name") else f"input[type='{username_field.get('type', 'text')}']"
                await controller.fill(username_selector, credentials["username"])
            
            if password_field:
                password_selector = f"input[type='password']"
                await controller.fill(password_selector, credentials["password"])
            
            if login_button:
                await controller.click(login_button.get("text", "登录"))
            
            await controller.human_like_delay(1, 2)
            
            cookies = await controller.get_cookies()
            
            session = session_manager.get_session_for_site(current_url)
            if session:
                session_manager.update_session(
                    session.session_id,
                    cookies=cookies,
                    is_logged_in=True,
                    username=credentials["username"]
                )
            else:
                session = session_manager.create_session(current_url)
                session_manager.update_session(
                    session.session_id,
                    cookies=cookies,
                    is_logged_in=True,
                    username=credentials["username"]
                )
            
            return {
                "success": True,
                "message": "登录成功",
                "username": credentials["username"],
                "url": controller.current_url
            }
            
        except Exception as e:
            return {"success": False, "error": f"登录失败: {str(e)}"}
    
    @staticmethod
    async def _close_browser() -> dict:
        if BrowserSkill._controller:
            await BrowserSkill._controller.close()
            BrowserSkill._controller = None
            BrowserSkill._initialized = False
        
        audit_path = BrowserSkill._safety_guard.save_audit_logs()
        
        return {
            "success": True,
            "message": "浏览器已关闭",
            "audit_log": audit_path,
            "session_summary": BrowserSkill._safety_guard.get_session_summary()
        }


class BrowserCredentialSkill:
    """凭证管理技能"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "browser_agent_save_credentials",
                "description": "保存网站的登录凭证，供Browser Agent自动登录使用。凭证会被加密存储。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_url": {
                            "type": "string",
                            "description": "网站URL"
                        },
                        "username": {
                            "type": "string",
                            "description": "用户名或邮箱"
                        },
                        "password": {
                            "type": "string",
                            "description": "密码"
                        }
                    },
                    "required": ["site_url", "username", "password"]
                }
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        BrowserSkill._ensure_initialized()
        
        site_url = arguments.get("site_url", "")
        username = arguments.get("username", "")
        password = arguments.get("password", "")
        
        if not all([site_url, username, password]):
            return {"success": False, "error": "缺少必要参数"}
        
        BrowserSkill._session_manager.save_credentials(site_url, username, password)
        
        return {
            "success": True,
            "message": f"凭证已保存: {site_url}",
            "username": username
        }


class BrowserListSitesSkill:
    """列出已保存的网站"""
    
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "browser_agent_list_sites",
                "description": "列出所有已保存登录凭证和会话的网站",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    @staticmethod
    def run(arguments: dict) -> dict:
        BrowserSkill._ensure_initialized()
        
        sites = BrowserSkill._session_manager.list_saved_sites()
        
        return {
            "success": True,
            "sites": sites,
            "count": len(sites)
        }

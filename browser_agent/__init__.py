"""
Browser Agent - 像真人一样使用浏览器

核心组件:
- BrowserSkill: 主技能入口
- BrowserController: Playwright浏览器控制
- SafetyGuard: 安全护栏系统
- SessionManager: 会话和凭证管理
"""

from .browser_skill import BrowserSkill
from .safety_guard import SafetyGuard, OperationLevel
from .session_manager import SessionManager
from .browser_controller import BrowserController

__all__ = [
    'BrowserSkill',
    'SafetyGuard', 
    'OperationLevel',
    'SessionManager',
    'BrowserController'
]

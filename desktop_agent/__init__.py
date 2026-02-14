"""
Desktop Agent - 像真人一样操作macOS应用

核心组件:
- DesktopSkill: 主技能入口
- AppLauncher: 应用启动器
- UIAgent: UI操作代理
- ScreenReader: 屏幕内容读取
"""

from .desktop_skill import DesktopSkill
from .app_launcher import AppLauncher
from .ui_agent import UIAgent

__all__ = [
    'DesktopSkill',
    'AppLauncher',
    'UIAgent'
]

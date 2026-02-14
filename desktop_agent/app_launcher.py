"""
应用启动器 - 使用AppleScript启动和激活macOS应用

核心功能:
1. 启动应用（按名称或路径）
2. 激活应用窗口
3. 检查应用是否运行
4. 关闭应用
"""

import subprocess
import os
from typing import Dict, Any, Optional, List
from datetime import datetime


class AppLauncher:
    """
    macOS应用启动器
    
    使用AppleScript和系统命令控制应用
    """
    
    COMMON_APPS = {
        "豆包": "Doubao",
        "doubao": "Doubao",
        "safari": "Safari",
        "chrome": "Google Chrome",
        "微信": "WeChat",
        "wechat": "WeChat",
        "音乐": "Music",
        "music": "Music",
        "备忘录": "Notes",
        "notes": "Notes",
        "日历": "Calendar",
        "calendar": "Calendar",
        "访达": "Finder",
        "finder": "Finder",
        "终端": "Terminal",
        "terminal": "Terminal",
        "设置": "System Preferences",
        "计算器": "Calculator",
        "calculator": "Calculator",
        "邮件": "Mail",
        "mail": "Mail",
        "地图": "Maps",
        "maps": "Maps",
        "照片": "Photos",
        "photos": "Photos",
        "pages": "Pages",
        "numbers": "Numbers",
        "keynote": "Keynote",
        "xcode": "Xcode",
        "vscode": "Visual Studio Code",
        "pycharm": "PyCharm",
        "飞书": "Feishu",
        "feishu": "Feishu",
        "钉钉": "DingTalk",
        "dingtalk": "DingTalk",
        "腾讯会议": "TencentMeeting",
        "zoom": "zoom.us",
        "spotify": "Spotify",
        "notion": "Notion",
        "obsidian": "Obsidian",
    }
    
    def __init__(self):
        self.running_apps_cache = None
        self.cache_time = None
    
    def _run_applescript(self, script: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "AppleScript执行失败"
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "AppleScript执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _normalize_app_name(self, app_name: str) -> str:
        app_lower = app_name.lower().strip()
        
        if app_lower in self.COMMON_APPS:
            return self.COMMON_APPS[app_lower]
        
        if app_name.endswith('.app'):
            return app_name
        
        return app_name
    
    def launch(self, app_name: str) -> Dict[str, Any]:
        normalized_name = self._normalize_app_name(app_name)
        
        script = f'''
        tell application "{normalized_name}"
            activate
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"已启动应用: {normalized_name}",
                "app_name": normalized_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            try_path = self._try_launch_by_path(app_name)
            if try_path["success"]:
                return try_path
            else:
                return {
                    "success": False,
                    "error": f"无法启动应用 '{app_name}': {result['error']}",
                    "hint": "请确认应用名称正确，或使用应用的完整路径"
                }
    
    def _try_launch_by_path(self, app_name: str) -> Dict[str, Any]:
        possible_paths = [
            f"/Applications/{app_name}.app",
            f"/Applications/{app_name}",
            os.path.expanduser(f"~/Applications/{app_name}.app"),
            os.path.expanduser(f"~/Applications/{app_name}"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                script = f'''
                tell application "{path}"
                    activate
                end tell
                '''
                result = self._run_applescript(script)
                if result["success"]:
                    return {
                        "success": True,
                        "message": f"已启动应用: {path}",
                        "app_path": path
                    }
        
        return {"success": False, "error": "未找到应用"}
    
    def activate(self, app_name: str) -> Dict[str, Any]:
        normalized_name = self._normalize_app_name(app_name)
        
        script = f'''
        tell application "{normalized_name}"
            if it is running then
                activate
                return "activated"
            else
                return "not_running"
            end if
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            if result["output"] == "activated":
                return {
                    "success": True,
                    "message": f"已激活应用: {normalized_name}"
                }
            else:
                return {
                    "success": False,
                    "error": f"应用 {normalized_name} 未运行",
                    "hint": "请先使用 launch 操作启动应用"
                }
        
        return result
    
    def is_running(self, app_name: str) -> Dict[str, Any]:
        normalized_name = self._normalize_app_name(app_name)
        
        script = f'''
        tell application "System Events"
            return name of processes contains "{normalized_name}"
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            running = result["output"].lower() == "true"
            return {
                "success": True,
                "is_running": running,
                "app_name": normalized_name
            }
        
        return result
    
    def list_running_apps(self) -> Dict[str, Any]:
        script = '''
        tell application "System Events"
            return name of every process whose background only is false
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            apps = [app.strip() for app in result["output"].split(",")]
            return {
                "success": True,
                "apps": apps,
                "count": len(apps)
            }
        
        return result
    
    def close(self, app_name: str, force: bool = False) -> Dict[str, Any]:
        normalized_name = self._normalize_app_name(app_name)
        
        if force:
            script = f'''
            tell application "{normalized_name}"
                quit
            end tell
            '''
        else:
            script = f'''
            tell application "{normalized_name}"
                if it is running then
                    quit
                    return "closed"
                else
                    return "not_running"
                end if
            end tell
            '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"已关闭应用: {normalized_name}"
            }
        
        return result
    
    def get_frontmost_app(self) -> Dict[str, Any]:
        script = '''
        tell application "System Events"
            return name of first process whose frontmost is true
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "app_name": result["output"]
            }
        
        return result
    
    def set_frontmost(self, app_name: str) -> Dict[str, Any]:
        normalized_name = self._normalize_app_name(app_name)
        
        script = f'''
        tell application "{normalized_name}"
            activate
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"已将 {normalized_name} 设为前台应用"
            }
        
        return result
    
    def get_app_info(self, app_name: str) -> Dict[str, Any]:
        normalized_name = self._normalize_app_name(app_name)
        
        script = f'''
        tell application "{normalized_name}"
            set appName to name
            set appVersion to version
            set appPath to path
            return appName & "|" & appVersion & "|" & appPath
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            parts = result["output"].split("|")
            if len(parts) >= 3:
                return {
                    "success": True,
                    "name": parts[0],
                    "version": parts[1],
                    "path": parts[2]
                }
        
        return result

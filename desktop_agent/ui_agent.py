"""
UI操作代理 - 操作macOS应用的UI元素

核心功能:
1. 查找UI元素
2. 点击、输入、选择操作
3. 读取UI内容
4. 发送快捷键
5. 截图
"""

import subprocess
import time
import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime


class UIAgent:
    """
    macOS UI操作代理
    
    使用AppleScript和系统命令操作UI
    """
    
    def __init__(self):
        self.current_app = None
    
    def _run_applescript(self, script: str, timeout: int = 30) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=timeout,
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
    
    def _run_system_events(self, script: str) -> Dict[str, Any]:
        full_script = f'''
        tell application "System Events"
            {script}
        end tell
        '''
        return self._run_applescript(full_script)
    
    def click(self, app_name: str, element_description: str) -> Dict[str, Any]:
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        tell application "System Events"
            tell process "{app_name}"
                set frontmost to true
                
                -- 尝试点击按钮
                try
                    click button "{element_description}"
                    return "clicked_button"
                end try
                
                -- 尝试点击菜单项
                try
                    click menu item "{element_description}" of menu bar 1
                    return "clicked_menu"
                end try
                
                -- 尝试点击链接
                try
                    click link "{element_description}"
                    return "clicked_link"
                end try
                
                return "element_not_found"
            end tell
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            if "not_found" in result["output"]:
                return {
                    "success": False,
                    "error": f"未找到元素: {element_description}",
                    "hint": "请使用 get_ui_elements 查看可用的UI元素"
                }
            return {
                "success": True,
                "message": f"已点击: {element_description}",
                "action": result["output"]
            }
        
        return result
    
    def click_at(self, app_name: str, x: int, y: int) -> Dict[str, Any]:
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        delay 0.2
        
        do shell script "cliclick c:{x},{y}"
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"已点击坐标 ({x}, {y})"
            }
        
        return {
            "success": False,
            "error": result.get("error", "点击失败"),
            "hint": "可能需要安装 cliclick: brew install cliclick"
        }
    
    def type_text(self, app_name: str, text: str) -> Dict[str, Any]:
        escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
        
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        delay 0.3
        
        tell application "System Events"
            keystroke "{escaped_text}"
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"已输入文本: {text[:50]}{'...' if len(text) > 50 else ''}"
            }
        
        return result
    
    def type_in_field(self, app_name: str, field_name: str, text: str) -> Dict[str, Any]:
        escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
        
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        tell application "System Events"
            tell process "{app_name}"
                set frontmost to true
                
                -- 尝试找到文本字段
                try
                    set targetField to text field "{field_name}"
                    click targetField
                    delay 0.2
                    keystroke "{escaped_text}"
                    return "typed"
                end try
                
                -- 尝试找到搜索字段
                try
                    set targetField to search field "{field_name}"
                    click targetField
                    delay 0.2
                    keystroke "{escaped_text}"
                    return "typed"
                end try
                
                return "field_not_found"
            end tell
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            if "not_found" in result["output"]:
                return {
                    "success": False,
                    "error": f"未找到输入框: {field_name}"
                }
            return {
                "success": True,
                "message": f"已在 {field_name} 中输入文本"
            }
        
        return result
    
    def press_key(self, app_name: str, key: str, modifiers: List[str] = None) -> Dict[str, Any]:
        modifiers = modifiers or []
        modifier_str = " ".join([f"{m} down" for m in modifiers])
        
        key_mapping = {
            "enter": "return",
            "return": "return",
            "tab": "tab",
            "escape": "escape",
            "esc": "escape",
            "space": "space",
            "delete": "delete",
            "backspace": "delete",
            "arrow_up": "key code 126",
            "arrow_down": "key code 125",
            "arrow_left": "key code 123",
            "arrow_right": "key code 124",
        }
        
        key_code = key_mapping.get(key.lower(), f'keystroke "{key}"')
        
        if modifier_str:
            script = f'''
            tell application "{app_name}"
                activate
            end tell
            
            delay 0.2
            
            tell application "System Events"
                {modifier_str}
                {key_code}
            end tell
            '''
        else:
            script = f'''
            tell application "{app_name}"
                activate
            end tell
            
            delay 0.2
            
            tell application "System Events"
                {key_code}
            end tell
            '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            modifier_desc = f" ({' + '.join(modifiers)})" if modifiers else ""
            return {
                "success": True,
                "message": f"已按键: {key}{modifier_desc}"
            }
        
        return result
    
    def hotkey(self, app_name: str, *keys) -> Dict[str, Any]:
        if len(keys) < 1:
            return {"success": False, "error": "需要至少一个按键"}
        
        main_key = keys[-1]
        modifiers = keys[:-1]
        
        return self.press_key(app_name, main_key, list(modifiers))
    
    def get_ui_elements(self, app_name: str) -> Dict[str, Any]:
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        tell application "System Events"
            tell process "{app_name}"
                set frontmost to true
                
                set elementList to {{}}
                
                -- 获取窗口
                try
                    set windowList to name of every window
                    set end of elementList to "Windows: " & (windowList as string)
                end try
                
                -- 获取按钮
                try
                    set buttonList to name of every button of window 1
                    set end of elementList to "Buttons: " & (buttonList as string)
                end try
                
                -- 获取菜单
                try
                    set menuList to name of every menu item of menu 1 of menu bar 1
                    set end of elementList to "Menu Items: " & (menuList as string)
                end try
                
                -- 获取文本字段
                try
                    set textFields to name of every text field of window 1
                    set end of elementList to "Text Fields: " & (textFields as string)
                end try
                
                return elementList as string
            end tell
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "elements": result["output"],
                "app_name": app_name
            }
        
        return result
    
    def get_window_content(self, app_name: str) -> Dict[str, Any]:
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        tell application "System Events"
            tell process "{app_name}"
                set frontmost to true
                
                set contentList to {{}}
                
                try
                    set staticTexts to value of every static text of window 1
                    set end of contentList to staticTexts as string
                end try
                
                try
                    set textFields to value of every text field of window 1
                    set end of contentList to textFields as string
                end try
                
                return contentList as string
            end tell
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "content": result["output"],
                "app_name": app_name
            }
        
        return result
    
    def select_menu(self, app_name: str, menu_name: str, menu_item: str) -> Dict[str, Any]:
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        tell application "System Events"
            tell process "{app_name}"
                set frontmost to true
                click menu item "{menu_item}" of menu "{menu_name}" of menu bar 1
            end tell
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"已选择菜单: {menu_name} > {menu_item}"
            }
        
        return result
    
    def screenshot(self, app_name: str = None, save_path: str = None) -> Dict[str, Any]:
        if not save_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = f"/tmp/neo_screenshot_{timestamp}.png"
        
        if app_name:
            script = f'''
            tell application "{app_name}"
                activate
            end tell
            
            delay 0.3
            
            do shell script "screencapture -x '{save_path}'"
            '''
        else:
            script = f'''
            do shell script "screencapture -x '{save_path}'"
            '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": "截图成功",
                "path": save_path
            }
        
        return result
    
    def wait_for_element(
        self, 
        app_name: str, 
        element_description: str, 
        timeout: int = 10
    ) -> Dict[str, Any]:
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        tell application "System Events"
            tell process "{app_name}"
                set frontmost to true
                
                set startTime to current date
                set foundElement to false
                
                repeat until foundElement or ((current date) - startTime) > {timeout}
                    try
                        set targetElement to button "{element_description}"
                        set foundElement to true
                    end try
                    
                    try
                        set targetElement to text field "{element_description}"
                        set foundElement to true
                    end try
                    
                    delay 0.5
                end repeat
                
                if foundElement then
                    return "found"
                else
                    return "timeout"
                end if
            end tell
        end tell
        '''
        
        result = self._run_applescript(script, timeout=timeout + 5)
        
        if result["success"]:
            if result["output"] == "found":
                return {
                    "success": True,
                    "message": f"找到元素: {element_description}"
                }
            else:
                return {
                    "success": False,
                    "error": f"等待元素超时: {element_description}"
                }
        
        return result
    
    def scroll(self, app_name: str, direction: str = "down", amount: int = 3) -> Dict[str, Any]:
        direction_code = "125" if direction.lower() == "down" else "126"
        
        scroll_script = "\n".join([f"key code {direction_code}" for _ in range(amount)])
        
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        delay 0.2
        
        tell application "System Events"
            {scroll_script}
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"已向{direction}滚动 {amount} 次"
            }
        
        return result
    
    def clear_and_type(self, app_name: str, text: str) -> Dict[str, Any]:
        escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
        
        script = f'''
        tell application "{app_name}"
            activate
        end tell
        
        delay 0.3
        
        tell application "System Events"
            -- 全选
            keystroke "a" using command down
            delay 0.1
            -- 输入新文本
            keystroke "{escaped_text}"
        end tell
        '''
        
        result = self._run_applescript(script)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"已清空并输入文本: {text[:50]}{'...' if len(text) > 50 else ''}"
            }
        
        return result

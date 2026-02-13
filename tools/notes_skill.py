import subprocess
import json

class NotesSkill:
    @staticmethod
    def _escape_applescript(text: str) -> str:
        """处理 AppleScript 特殊字符转义"""
        if not text: return ""
        # 处理反斜杠和双引号
        return text.replace('\\', '\\\\').replace('"', '\\"')

    # --- 1. 工具说明书 ---
    @staticmethod
    def get_tool_definition():
        return {
            "type": "function",
            "function": {
                "name": "notes_operator",
                "description": "macOS 备忘录操作工具。支持创建、读取和追加备忘录。创建时支持HTML格式（如<b>加粗</b>、<br>换行）来美化排版。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "read", "append"],
                            "description": "操作类型：'create'新建，'read'读取内容，'append'追加内容。"
                        },
                        "title": {
                            "type": "string",
                            "description": "备忘录标题。create时必须提供；read/append时用于查找目标。"
                        },
                        "content": {
                            "type": "string",
                            "description": "备忘录内容。create/append时必须提供。支持HTML标签进行排版美化（例如：<b>标题</b>, <br>换行）。"
                        }
                    },
                    "required": ["action", "title"]
                }
            }
        }

    # --- 2. 统一入口 ---
    @staticmethod
    def run(arguments: dict):
        action = arguments.get("action")
        title = arguments.get("title", "无标题备忘录")
        content = arguments.get("content", "")

        if action == "create":
            # 默认给内容套一个简单的 HTML 结构，确保格式正确
            html_content = f"<div>{content}</div>"
            return NotesSkill._create_note(title, html_content)
        
        elif action == "read":
            return NotesSkill._read_note(title)
            
        elif action == "append":
            if not content:
                return {"status": "error", "message": "追加模式需要提供 content"}
            return NotesSkill._append_note(title, content)
            
        else:
            return {"status": "error", "message": f"未知的操作类型: {action}"}

    # --- 3. 底层实现 ---

    @staticmethod
    def _create_note(title: str, body_html: str):
        script = f'''
        tell application "Notes"
            tell account "iCloud"
                -- 创建备忘录，body 属性直接支持 HTML
                make new note at folder "Notes" with properties {{name:"{NotesSkill._escape_applescript(title)}", body:"{NotesSkill._escape_applescript(body_html)}"}}
            end tell
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
            return {"status": "success", "message": f"已创建备忘录: {title}"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"AppleScript 执行错误: {e.stderr}"}

    @staticmethod
    def _read_note(title_query: str):
        """
        读取备忘录内容。
        如果 title_query 为空或 "list"，则列出最近的备忘录标题。
        否则搜索包含 title_query 的备忘录并返回内容。
        """
        # 如果只是想列出列表
        if not title_query or title_query.lower() == "list":
            script = '''
            tell application "Notes"
                tell account "iCloud"
                    set output to ""
                    -- 获取最近的5条备忘录
                    set theNotes to notes 1 thru 5
                    repeat with n in theNotes
                        set output to output & (name of n) & "|SEPARATOR|"
                    end repeat
                    return output
                end tell
            end tell
            '''
            try:
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                titles = [t.strip() for t in result.stdout.strip().split("|SEPARATOR|") if t.strip()]
                return {"status": "success", "data": titles, "message": "最近的备忘录列表已获取。"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        # 查找特定备忘录
        else:
            script = f'''
            tell application "Notes"
                tell account "iCloud"
                    try
                        -- 查找名称包含关键词的备忘录
                        set foundNote to first note whose name contains "{NotesSkill._escape_applescript(title_query)}"
                        return "TITLE: " & (name of foundNote) & "\nBODY: " & (body of foundNote)
                    on error
                        return "ERROR_NOT_FOUND"
                    end try
                end tell
            end tell
            '''
            try:
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                output = result.stdout.strip()
                
                if "ERROR_NOT_FOUND" in output:
                    return {"status": "error", "message": f"未找到包含 '{title_query}' 的备忘录"}
                
                # 简单解析返回内容
                # 注意：body 返回的是 HTML 源码
                return {"status": "success", "content": output, "message": f"已读取备忘录内容。"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    @staticmethod
    def _append_note(note_name: str, extra_content: str):
        # 追加时，最好也用 HTML 换行隔开
        append_html = f"<br><br>{extra_content}"
        script = f'''
        tell application "Notes"
            tell account "iCloud"
                try
                    set theNote to first note whose name contains "{NotesSkill._escape_applescript(note_name)}"
                    set body of theNote to (body of theNote) & "{NotesSkill._escape_applescript(append_html)}"
                    return "SUCCESS"
                on error
                    return "ERROR_NOT_FOUND"
                end try
            end tell
        end tell
        '''
        try:
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if "SUCCESS" in result.stdout:
                return {"status": "success", "message": f"已向 '{note_name}' 追加内容"}
            else:
                return {"status": "error", "message": "未找到该备忘录"}
        except Exception as e:
             return {"status": "error", "message": str(e)}

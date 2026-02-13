import subprocess
import json

class NotesSkill:
    """
    备忘录工具类 - 适配 LLM Function Calling
    """
    
    @staticmethod
    def _escape_applescript(text: str) -> str:
        """处理 AppleScript 特殊字符转义"""
        if not text: return ""
        return text.replace('\\', '\\\\').replace('"', '\\"')

    # --- 1. 定义工具说明书 ---
    @staticmethod
    def get_tool_definition():
        """
        返回符合 OpenAI Function Calling 格式的定义
        这是告诉大模型怎么用这个工具的关键
        """
        return {
            "type": "function",
            "function": {
                "name": "notes_operator",
                "description": "用于在 macOS 备忘录应用中进行操作。当用户想要记录信息、保存备忘、创建清单时使用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "append"], # 限制动作类型，防止模型瞎编
                            "description": "操作类型。'create'表示新建备忘录，'append'表示在现有备忘录末尾追加内容。"
                        },
                        "title": {
                            "type": "string",
                            "description": "备忘录的标题。仅在 create 模式下必须提供。"
                        },
                        "content": {
                            "type": "string",
                            "description": "备忘录的具体内容。"
                        },
                        "target_note_name": {
                            "type": "string",
                            "description": "目标备忘录的名称。仅在 append 模式下需要，用于查找要追加的备忘录。"
                        }
                    },
                    "required": ["action", "content"] # 必填项
                }
            }
        }

    # --- 2. 执行逻辑 ---
    @staticmethod
    def run(arguments: dict):
        """
        统一入口函数，接收 LLM 传来的 JSON 参数
        """
        action = arguments.get("action")
        content = arguments.get("content", "")
        
        # 为了演示，这里简化了错误处理
        
        if action == "create":
            title = arguments.get("title", "无标题备忘录")
            return NotesSkill._create_note(title, content)
            
        elif action == "append":
            target_name = arguments.get("target_note_name")
            if not target_name:
                return {"status": "error", "message": "追加模式需要提供 target_note_name"}
            return NotesSkill._append_note(target_name, content)
            
        else:
            return {"status": "error", "message": f"未知的操作类型: {action}"}

    @staticmethod
    def _create_note(title: str, body: str):
        script = f'''
        tell application "Notes"
            tell account "iCloud"
                make new note at folder "Notes" with properties {{name:"{NotesSkill._escape_applescript(title)}", body:"{NotesSkill._escape_applescript(body)}"}}
            end tell
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
            return {"status": "success", "message": f"已成功创建备忘录: {title}"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"AppleScript 执行错误: {e.stderr}"}

    @staticmethod
    def _append_note(note_name: str, extra_content: str):
        # 这是一个扩展功能：查找名为 note_name 的备忘录并在后面追加内容
        script = f'''
        tell application "Notes"
            tell account "iCloud"
                set theNote to first note whose name contains "{NotesSkill._escape_applescript(note_name)}"
                set body of theNote to (body of theNote) & "<br>" & "{NotesSkill._escape_applescript(extra_content)}"
            end tell
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)
            return {"status": "success", "message": f"已向备忘录 '{note_name}' 追加内容"}
        except Exception as e:
             return {"status": "error", "message": f"追加失败，可能未找到该备忘录: {str(e)}"}

# --- 测试代码 ---
if __name__ == "__main__":
    # 模拟 LLM 调用的过程
    
    # 1. 打印工具定义（这通常会发给 GPT-4 或本地模型）
    print("=== 工具定义 ===")
    print(json.dumps(NotesSkill.get_tool_definition(), indent=2, ensure_ascii=False))
    
    # 2. 模拟 LLM 返回的参数（LLM 看到用户的提示词“帮我记一下明天开会”，生成的 JSON）
    llm_generated_args = {
        "action": "create",
        "title": "工作提醒",
        "content": "明天上午10点开会"
    }
    
    # 3. 执行工具
    print("\n=== 执行结果 ===")
    result = NotesSkill.run(llm_generated_args)
    print(result)

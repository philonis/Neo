import json
import time
from typing import List, Dict, Any, Optional, Callable

class ReActAgent:
    """
    ReAct Agent: 推理(Reasoning) + 行动(Acting) 循环
    
    核心流程:
    1. Thought: 分析当前状态，决定下一步
    2. Action: 选择并执行工具
    3. Observation: 观察执行结果
    4. 循环直到任务完成
    
    增强功能:
    - 自主编程能力：当现有工具不足时，可创建新技能
    - 链式调用：支持多步骤任务
    - 错误恢复：失败时尝试其他方法
    """
    
    def __init__(self, llm_client, skill_manager, memory_system=None, max_iterations=15):
        self.llm = llm_client
        self.skills = skill_manager
        self.memory = memory_system
        self.max_iterations = max_iterations
        
        self.execution_trace = []
        self.generated_skills = []
        
        self.system_prompt = """你是一个智能助手 Neo，使用 ReAct 模式工作。

## 工作模式
你将通过以下步骤完成任务：
1. **Thought**: 分析当前情况，思考下一步该做什么
2. **Action**: 选择合适的工具并执行
3. **Observation**: 观察执行结果
4. 重复以上步骤直到任务完成

## 核心能力
- 你可以使用 `browser_agent` **访问任何网站**获取信息（小红书、微博、知乎、淘宝等）
- 你可以使用 `desktop_agent` 像真人一样操作macOS应用
- 你可以**自主编写新技能**来解决现有工具无法完成的任务
- 当发现需要新功能时，使用 `create_skill` 工具创建

## 工具选择指南
当用户要求：
- 访问某个网站、获取网页内容 → 使用 `browser_agent`
- 查看某个网站的信息（如小红书热门、微博热搜）→ 使用 `browser_agent`
- 操作本地应用（如打开豆包、微信）→ 使用 `desktop_agent`
- 网络搜索 → 使用 `web_search` 或 `browser_agent`
- 获取RSS/播客内容 → 使用 `rss_fetcher`

**重要：不要说"我没有访问某网站的功能"，你应该使用 browser_agent 访问任何网站！**

## 重要规则
- **优先尝试解决问题**：不要轻易说"无法完成"
- **主动使用工具**：当需要访问网站时，直接使用 browser_agent
- 每次只执行一个工具调用
- 仔细观察工具返回的结果
- 如果工具执行失败，分析原因并尝试其他方法
- 当任务完成时，直接回复用户

## 安全确认机制
当工具返回 `requires_confirmation: true` 时：
1. 向用户展示 `confirmation_message` 的内容
2. 询问用户是否允许此操作
3. 如果用户同意，再次调用**相同的工具**并设置 `auto_confirm: true`
4. 如果用户拒绝，告知用户并停止该操作

示例：
```
工具返回: {{"success": false, "requires_confirmation": true, "confirmation_message": "是否允许点击登录按钮？"}}
你的回复: "我需要点击登录按钮才能继续。请问您允许这个操作吗？"
用户回复: "允许"
你的操作: 再次调用相同工具，添加 auto_confirm: true 参数
```

## 可用工具
{tool_descriptions}

## 输出格式
当你需要调用工具时，直接使用 function calling。
当你认为任务完成时，直接回复用户。
当需要用户确认时，直接向用户询问，等待用户回复后再继续。"""

    def run(self, user_input: str, context: List[Dict] = None, on_progress: Callable = None) -> Dict:
        self.execution_trace = []
        self.generated_skills = []
        
        tool_schemas = self._get_tool_schemas_with_create_skill()
        tool_descriptions = self._format_tool_descriptions(tool_schemas)
        
        messages = self._build_initial_messages(user_input, context, tool_descriptions)
        
        for iteration in range(self.max_iterations):
            if on_progress:
                on_progress("thinking", f"思考中... (步骤 {iteration + 1})")
            
            response = self.llm.chat(messages, tools=tool_schemas)
            
            if not response:
                return self._build_result(False, "LLM 请求失败", messages)
            
            message = response["choices"][0]["message"]
            messages.append(message)
            
            tool_calls = message.get("tool_calls", [])
            
            if not tool_calls:
                final_content = message.get("content", "")
                return self._build_result(True, final_content, messages)
            
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                args_str = tool_call["function"]["arguments"]
                if isinstance(args_str, str):
                    tool_args = json.loads(args_str)
                else:
                    tool_args = args_str if isinstance(args_str, dict) else {}
                tool_id = tool_call["id"]
                
                if on_progress:
                    on_progress("action", f"执行工具: {tool_name}")
                
                if tool_name == "create_skill":
                    result = self._create_skill(tool_args, on_progress)
                else:
                    result = self._execute_tool(tool_name, tool_args)
                
                self.execution_trace.append({
                    "iteration": iteration + 1,
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                })
                
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False)
                }
                messages.append(tool_message)
                
                if tool_name == "create_skill" and result.get("success"):
                    tool_schemas = self._get_tool_schemas_with_create_skill()
                
                if on_progress:
                    on_progress("observation", f"观察结果: {self._summarize_result(result)}")
        
        return self._build_result(False, "达到最大迭代次数，任务未完成", messages)

    def _get_tool_schemas_with_create_skill(self) -> List[Dict]:
        schemas = self.skills.get_all_tools_schema()
        
        create_skill_schema = {
            "type": "function",
            "function": {
                "name": "create_skill",
                "description": "创建新技能。当你发现现有工具无法完成任务时，使用此工具编写新技能。新技能创建后会立即可用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "技能名称，使用下划线命名法，如 podcast_fetcher"
                        },
                        "skill_description": {
                            "type": "string",
                            "description": "技能功能描述，用于语义搜索匹配"
                        },
                        "skill_code": {
                            "type": "string",
                            "description": "完整的 Python 技能代码，必须包含 run() 和 get_tool_definition() 函数"
                        }
                    },
                    "required": ["skill_name", "skill_description", "skill_code"]
                }
            }
        }
        
        schemas.append(create_skill_schema)
        return schemas

    def _create_skill(self, args: Dict, on_progress: Callable = None) -> Dict:
        skill_name = args.get("skill_name", "")
        skill_description = args.get("skill_description", "")
        skill_code = args.get("skill_code", "")
        
        if not skill_name or not skill_code:
            return {"success": False, "error": "缺少技能名称或代码"}
        
        if on_progress:
            on_progress("generating", f"创建技能: {skill_name}")
        
        skill_code = self._clean_code(skill_code)
        
        if not self._validate_skill_code(skill_code):
            return {"success": False, "error": "技能代码验证失败"}
        
        try:
            from code_guard import get_code_guard
            guard = get_code_guard()
            
            is_dangerous, dangers = guard.check_dangerous_code(skill_code)
            if is_dangerous:
                return {
                    "success": False,
                    "error": "代码包含危险模式，禁止创建",
                    "dangers": dangers
                }
            
            is_suspicious, warnings = guard.check_suspicious_code(skill_code)
            if is_suspicious:
                print(f"[ReActAgent] ⚠️ 技能包含可疑代码: {warnings}")
        except ImportError:
            pass
        
        filepath = self.skills.create_skill_file(skill_name, skill_code)
        
        if filepath:
            self.generated_skills.append(skill_name)
            return {
                "success": True,
                "message": f"技能 {skill_name} 创建成功，现在可以使用",
                "skill_name": skill_name
            }
        else:
            return {"success": False, "error": "技能保存失败"}

    def _clean_code(self, code: str) -> str:
        import re
        code = re.sub(r'```python\s*', '', code, flags=re.IGNORECASE)
        code = re.sub(r'```\s*', '', code)
        return code.strip()

    def _validate_skill_code(self, code: str) -> bool:
        required = ['def run(', 'def get_tool_definition(']
        for r in required:
            if r not in code:
                return False
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False

    def _build_initial_messages(self, user_input: str, context: List[Dict], tool_descriptions: str) -> List[Dict]:
        messages = []
        
        system_content = self.system_prompt.format(tool_descriptions=tool_descriptions)
        
        if self.memory:
            relevant_memories = self.memory.retrieve_relevant(user_input, top_k=3)
            if relevant_memories:
                memory_context = "\n\n## 相关记忆\n" + "\n".join(relevant_memories)
                system_content += memory_context
        
        messages.append({"role": "system", "content": system_content})
        
        if context:
            for msg in context[-10:]:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": user_input})
        
        return messages

    def _execute_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        if tool_name not in self.skills.skills:
            return {"error": f"未知工具: {tool_name}，你可以使用 create_skill 创建新技能"}
        
        try:
            func = self.skills.get_skill(tool_name)
            if func:
                result = func(tool_args)
                return result if isinstance(result, dict) else {"result": result}
            return {"error": f"工具 {tool_name} 不可用"}
        except Exception as e:
            return {"error": f"工具执行错误: {str(e)}"}

    def _format_tool_descriptions(self, tool_schemas: List[Dict]) -> str:
        descriptions = []
        for schema in tool_schemas:
            func = schema.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "无描述")
            descriptions.append(f"- **{name}**: {desc}")
        return "\n".join(descriptions)

    def _summarize_result(self, result: Dict, max_length: int = 100) -> str:
        if isinstance(result, dict):
            if "error" in result:
                return f"错误: {result['error']}"
            if "message" in result:
                return result["message"][:max_length]
            if "content" in result:
                return result["content"][:max_length]
        return str(result)[:max_length]

    def _build_result(self, success: bool, response: str, messages: List[Dict]) -> Dict:
        return {
            "success": success,
            "response": response,
            "trace": self.execution_trace,
            "generated_skills": self.generated_skills,
            "message_count": len(messages)
        }

    def get_trace_summary(self) -> str:
        if not self.execution_trace:
            return "无执行记录"
        
        lines = ["## 执行轨迹"]
        for item in self.execution_trace:
            lines.append(f"- 步骤{item['iteration']}: 调用 {item['tool']}")
            if "error" in item.get("result", {}):
                lines.append(f"  - 结果: ❌ {item['result']['error']}")
            else:
                lines.append(f"  - 结果: ✅ 成功")
        
        if self.generated_skills:
            lines.append(f"\n## 新创建的技能: {', '.join(self.generated_skills)}")
        
        return "\n".join(lines)

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
        
        self.system_prompt = """# AI 助手系统提示词

## 核心身份

你不是聊天机器人，你是一个有能力的助手。
你的目标是解决问题，而不是解释为什么不能解决。

## 核心原则

### 1. 先尝试，后询问

大多数任务可以通过基础能力组合完成：
- 文件操作：读取、写入、编辑
- 命令执行：运行脚本、安装工具
- 网络访问：搜索、获取网页
- 代码能力：编写、调试、执行

遇到请求时：
1. 先思考：我能否用现有能力完成？
2. 能完成 → 直接执行
3. 不能完成 → 尝试安装依赖后执行
4. 真正无法完成 → 说明原因，询问用户

### 2. 不要表演性礼貌

跳过：
- "很高兴为您服务"
- "好问题！"
- "我来帮您分析一下"

直接行动，用结果说话。

### 3. 有主见，敢于决策

- 不要列出选项菜单让用户选择
- 不要问"您希望我采用哪种方案？"
- 选择最优方案执行，说明理由

示例：
❌ "有三种方案：A...B...C...，您选择哪个？"
✅ "我选择方案A，因为最快捷。已执行完成。"

### 4. 安全边界

**大胆执行**：
- 读取文件
- 搜索信息
- 组织数据
- 学习新知识

**先确认后执行**：
- 发送消息/邮件
- 发布公开内容
- 删除文件
- 修改重要配置

## 能力边界定义

你的能力不是由工具列表定义的，而是由你的**基础能力组合**定义的：

- 能读文件 → 能分析任何文本内容
- 能写文件 → 能生成任何格式输出
- 能执行命令 → 能使用任何命令行工具
- 能搜索网络 → 能获取任何公开信息
- 能编写代码 → 能解决任何可编程问题

不要说"我没有这个功能"。
要说"我来尝试实现这个功能"。

## 响应格式

1. **能直接完成**：直接执行，简短告知结果
2. **需要探索**：边做边说，展示进展
3. **需要确认**：说明计划，请求确认
4. **无法完成**：说明原因，提供替代方案

永远不要：
- 列出选项让用户选择
- 问"需要我执行吗？"
- 说"我没有这个功能"

# 可用工具
{tool_descriptions}"""

    def run(self, user_input: str, context: List[Dict] = None, on_progress: Callable = None, on_log: Callable = None) -> Dict:
        self.execution_trace = []
        self.generated_skills = []
        self.llm_logs = []
        
        tool_schemas = self._get_tool_schemas_with_create_skill()
        tool_descriptions = self._format_tool_descriptions(tool_schemas)
        
        messages = self._build_initial_messages(user_input, context, tool_descriptions)
        
        for iteration in range(self.max_iterations):
            if on_progress:
                on_progress("thinking", f"思考中... (步骤 {iteration + 1})")
            
            if on_log:
                request_messages = []
                for msg in messages:
                    msg_preview = {
                        "role": msg.get("role", "unknown"),
                    }
                    if msg.get("content"):
                        content = msg.get("content", "")
                        msg_preview["content_preview"] = content[:300] + "..." if len(content) > 300 else content
                    if msg.get("tool_calls"):
                        msg_preview["tool_calls"] = [{"name": tc["function"]["name"]} for tc in msg["tool_calls"]]
                    if msg.get("name"):
                        msg_preview["tool_name"] = msg.get("name")
                    request_messages.append(msg_preview)
                
                on_log("request", {
                    "iteration": iteration + 1,
                    "total_messages": len(messages),
                    "messages": request_messages,
                    "tools_available": [t["function"]["name"] for t in tool_schemas]
                })
            
            response = self.llm.chat(messages, tools=tool_schemas)
            
            
            if not response:
                return self._build_result(False, "LLM 请求失败", messages)
            
            message = response["choices"][0]["message"]
            messages.append(message)
            
            if on_log:
                on_log("response", {
                    "iteration": iteration + 1,
                    "content": message.get("content", "")[:500] if message.get("content") else None,
                    "has_tool_calls": bool(message.get("tool_calls")),
                    "tool_calls_count": len(message.get("tool_calls", []))
                })
            
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
                
                if on_log:
                    on_log("tool_call", {
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "args": tool_args
                    })
                
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
                
                if on_log:
                    on_log("tool_result", {
                        "iteration": iteration + 1,
                        "tool": tool_name,
                        "success": result.get("success", False),
                        "result_preview": str(result)[:300]
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

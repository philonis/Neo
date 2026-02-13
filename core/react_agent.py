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
    """
    
    def __init__(self, llm_client, skill_manager, memory_system=None, max_iterations=15):
        self.llm = llm_client
        self.skills = skill_manager
        self.memory = memory_system
        self.max_iterations = max_iterations
        
        self.execution_trace = []
        self.current_thought = ""
        
        self.system_prompt = """你是一个智能助手 Neo，使用 ReAct 模式工作。

## 工作模式
你将通过以下步骤完成任务：
1. **Thought**: 分析当前情况，思考下一步该做什么
2. **Action**: 选择合适的工具并执行
3. **Observation**: 观察执行结果
4. 重复以上步骤直到任务完成

## 重要规则
- 每次只执行一个工具调用
- 仔细观察工具返回的结果
- 如果工具执行失败，尝试其他方法
- 当任务完成时，直接回复用户，不要继续调用工具
- 保持思考简洁明了

## 可用工具
{tool_descriptions}

## 输出格式
当你需要调用工具时，直接使用 function calling。
当你认为任务完成时，直接回复用户。"""

    def run(self, user_input: str, context: List[Dict] = None, on_progress: Callable = None) -> Dict:
        """
        执行 ReAct 循环
        
        :param user_input: 用户输入
        :param context: 上下文消息
        :param on_progress: 进度回调函数
        :return: {"success": bool, "response": str, "trace": list}
        """
        self.execution_trace = []
        
        tool_schemas = self.skills.get_all_tools_schema()
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
                tool_args = json.loads(tool_call["function"]["arguments"])
                tool_id = tool_call["id"]
                
                if on_progress:
                    on_progress("action", f"执行工具: {tool_name}")
                
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
                
                if on_progress:
                    on_progress("observation", f"观察结果: {self._summarize_result(result)}")
        
        return self._build_result(False, "达到最大迭代次数，任务未完成", messages)

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
            return {"error": f"未知工具: {tool_name}"}
        
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
        return "\n".join(lines)

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Task:
    """任务节点"""
    id: str
    description: str
    status: str = "pending"  # pending, running, completed, failed
    subtasks: List['Task'] = field(default_factory=list)
    result: Optional[Dict] = None
    tool_used: Optional[str] = None

class TaskPlanner:
    """
    智能任务规划器
    
    功能:
    1. 任务分解: 将复杂任务拆分为子任务
    2. 依赖分析: 确定任务执行顺序
    3. 动态调整: 根据执行结果调整计划
    """
    
    def __init__(self, llm_client, skill_manager):
        self.llm = llm_client
        self.skills = skill_manager
        
        self.decomposition_prompt = """你是一个任务规划专家。请分析用户任务并分解为可执行的子任务。

## 用户任务
{task_description}

## 可用工具
{tool_list}

## 规划要求
1. 将复杂任务分解为具体的、可执行的步骤
2. 每个步骤应该明确使用哪个工具
3. 考虑任务之间的依赖关系
4. 如果任务简单，不需要分解

## 输出格式
请以 JSON 格式输出计划:
```json
{{
    "need_decomposition": true/false,
    "reasoning": "简要说明为什么需要/不需要分解",
    "tasks": [
        {{
            "id": "1",
            "description": "步骤描述",
            "tool": "工具名称",
            "args": {{"参数": "值"}},
            "depends_on": []
        }}
    ]
}}
```

只输出 JSON，不要有其他内容。"""

    def plan(self, user_input: str, context: List[Dict] = None) -> Dict:
        """
        生成任务计划
        
        :param user_input: 用户输入
        :param context: 上下文
        :return: 计划结果
        """
        tool_list = self._get_tool_list()
        
        prompt = self.decomposition_prompt.format(
            task_description=user_input,
            tool_list=tool_list
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        if context:
            context_str = "\n".join([
                f"{m['role']}: {m['content']}" 
                for m in context[-5:] 
                if m.get("content")
            ])
            if context_str:
                messages.insert(0, {
                    "role": "system", 
                    "content": f"对话上下文:\n{context_str}"
                })
        
        response = self.llm.simple_chat(prompt)
        
        if not response:
            return self._create_simple_plan(user_input)
        
        plan_data = self._parse_plan_response(response)
        
        if not plan_data:
            return self._create_simple_plan(user_input)
        
        return plan_data

    def _get_tool_list(self) -> str:
        tools = self.skills.get_all_tools_schema()
        lines = []
        for schema in tools:
            func = schema.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "")
            params = func.get("parameters", {}).get("properties", {})
            param_str = ", ".join(params.keys()) if params else "无参数"
            lines.append(f"- {name}({param_str}): {desc}")
        return "\n".join(lines)

    def _parse_plan_response(self, response: str) -> Optional[Dict]:
        try:
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            plan_data = json.loads(json_str.strip())
            
            if "tasks" not in plan_data:
                return None
            
            return plan_data
        except (json.JSONDecodeError, KeyError, IndexError):
            return None

    def _create_simple_plan(self, user_input: str) -> Dict:
        return {
            "need_decomposition": False,
            "reasoning": "简单任务，直接执行",
            "tasks": [{
                "id": "1",
                "description": user_input,
                "tool": "chat",
                "args": {},
                "depends_on": []
            }]
        }

    def analyze_complexity(self, user_input: str) -> Dict:
        """
        分析任务复杂度
        
        :return: {"level": "simple/medium/complex", "factors": [...]}
        """
        factors = []
        score = 0
        
        complex_keywords = ["然后", "接着", "之后", "同时", "并且", "以及", "还要", "再"]
        for kw in complex_keywords:
            if kw in user_input:
                score += 1
                factors.append(f"包含连接词 '{kw}'")
        
        if "和" in user_input or "与" in user_input:
            score += 1
            factors.append("包含并列关系")
        
        if len(user_input) > 100:
            score += 1
            factors.append("输入较长")
        
        questions = user_input.count("？") + user_input.count("?")
        if questions > 1:
            score += 1
            factors.append("包含多个问题")
        
        if score >= 3:
            level = "complex"
        elif score >= 1:
            level = "medium"
        else:
            level = "simple"
        
        return {"level": level, "score": score, "factors": factors}

    def should_decompose(self, user_input: str) -> bool:
        analysis = self.analyze_complexity(user_input)
        return analysis["level"] in ["medium", "complex"]


class DynamicPlanner:
    """
    动态规划器 - 支持运行时调整计划
    """
    
    def __init__(self, llm_client, skill_manager):
        self.llm = llm_client
        self.skills = skill_manager
        self.planner = TaskPlanner(llm_client, skill_manager)
        self.execution_history = []
    
    def execute_with_adaptation(self, user_input: str, context: List[Dict] = None, 
                                  executor: callable = None) -> Dict:
        """
        执行任务，支持动态调整
        
        :param user_input: 用户输入
        :param context: 上下文
        :param executor: 执行函数 (task) -> result
        :return: 执行结果
        """
        plan = self.planner.plan(user_input, context)
        
        if not plan.get("need_decomposition", False):
            if executor:
                return executor({"description": user_input})
            return {"success": False, "message": "无执行器"}
        
        tasks = plan.get("tasks", [])
        results = []
        
        for task in tasks:
            if executor:
                result = executor(task)
                results.append({
                    "task": task,
                    "result": result
                })
                
                if not result.get("success", False):
                    adjustment = self._check_need_adjustment(task, result, tasks)
                    if adjustment:
                        new_plan = self._adjust_plan(task, result, tasks)
                        tasks = new_plan.get("tasks", tasks[len(results):])
        
        return {
            "success": all(r["result"].get("success", True) for r in results),
            "results": results,
            "plan": plan
        }

    def _check_need_adjustment(self, failed_task: Dict, result: Dict, remaining_tasks: List) -> bool:
        return not result.get("success", False)

    def _adjust_plan(self, failed_task: Dict, result: Dict, remaining_tasks: List) -> Dict:
        prompt = f"""任务执行失败，需要调整计划。

失败的任务: {failed_task.get('description')}
失败原因: {result.get('error', '未知')}
剩余任务: {json.dumps([t.get('description') for t in remaining_tasks], ensure_ascii=False)}

请提供调整建议，JSON格式:
{{
    "action": "retry/skip/replan",
    "reason": "原因",
    "new_tasks": [...]
}}"""
        
        response = self.llm.simple_chat(prompt)
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            return json.loads(response.strip())
        except:
            return {"action": "continue", "new_tasks": remaining_tasks}

import json
import os
import re
import time
import uuid
from typing import Dict, List, Optional, Any

class SkillGenerator:
    """
    动态技能生成器
    
    当现有工具无法完成任务时，自动编写新技能
    """
    
    def __init__(self, llm_client, skill_manager):
        self.llm = llm_client
        self.skills = skill_manager
        
        self.generation_prompt = """你是一个 Python 技能开发专家。用户需要一个新技能来完成任务。

## 任务需求
{task_description}

## 已有技能
{existing_skills}

## 技能开发规范
1. 必须包含 `run(arguments: dict)` 函数 - 执行技能逻辑
2. 必须包含 `get_tool_definition()` 函数 - 返回 OpenAI Tool Schema
3. 使用 Python 标准库优先，必要时使用 requests
4. 返回值必须是 dict 格式，包含 status 和 message/data 字段
5. 处理好异常情况，返回友好的错误信息
6. 技能名称使用下划线命名法，如 `podcast_fetcher`

## 代码模板
```python
import requests
import json
from typing import Dict

def get_tool_definition():
    return {{
        "type": "function",
        "function": {{
            "name": "技能名称",
            "description": "详细描述技能功能，用于语义搜索匹配",
            "parameters": {{
                "type": "object",
                "properties": {{
                    "参数名": {{
                        "type": "string",
                        "description": "参数描述"
                    }}
                }},
                "required": ["必需参数"]
            }}
        }}
    }}

def run(arguments: dict) -> dict:
    try:
        # 获取参数
        param = arguments.get("参数名", "")
        
        # 实现技能逻辑
        # ...
        
        return {{
            "status": "success",
            "message": "执行成功",
            "data": {{}}
        }}
    except Exception as e:
        return {{
            "status": "error",
            "message": f"执行失败: {{str(e)}}"
        }}
```

请根据任务需求，编写一个完整的 Python 技能文件。只输出代码，不要有其他内容。"""

    def generate_skill(self, task_description: str) -> Dict:
        """
        生成新技能
        
        :param task_description: 任务描述
        :return: {"success": bool, "skill_name": str, "message": str}
        """
        existing_skills = self._get_existing_skills_summary()
        
        prompt = self.generation_prompt.format(
            task_description=task_description,
            existing_skills=existing_skills
        )
        
        response = self.llm.simple_chat(prompt)
        
        if not response:
            return {"success": False, "message": "技能生成失败：LLM 无响应"}
        
        code = self._clean_code(response)
        
        if not self._validate_code(code):
            return {"success": False, "message": "技能生成失败：代码验证不通过"}
        
        skill_name = self._extract_skill_name(code)
        if not skill_name:
            skill_name = f"auto_skill_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        filepath = self.skills.create_skill_file(skill_name, code)
        
        if filepath:
            return {
                "success": True,
                "skill_name": skill_name,
                "filepath": filepath,
                "message": f"已成功创建技能: {skill_name}"
            }
        else:
            return {"success": False, "message": "技能保存失败"}

    def generate_and_execute(self, task_description: str, arguments: dict = None) -> Dict:
        """
        生成技能并立即执行
        
        :param task_description: 任务描述
        :param arguments: 执行参数
        :return: {"success": bool, "result": dict, "skill_name": str}
        """
        gen_result = self.generate_skill(task_description)
        
        if not gen_result["success"]:
            return gen_result
        
        skill_name = gen_result["skill_name"]
        
        time.sleep(0.5)
        
        func = self.skills.get_skill(skill_name)
        if not func:
            return {
                "success": False,
                "message": f"技能 {skill_name} 加载失败"
            }
        
        try:
            result = func(arguments or {})
            return {
                "success": True,
                "skill_name": skill_name,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "skill_name": skill_name,
                "message": f"技能执行失败: {str(e)}"
            }

    def _get_existing_skills_summary(self) -> str:
        skills = self.skills.list_skills()
        if not skills:
            return "暂无已有技能"
        
        lines = []
        for name in skills:
            info = self.skills.get_skill_info(name)
            if info:
                desc = info["schema"].get("function", {}).get("description", "")
                lines.append(f"- {name}: {desc[:50]}")
        return "\n".join(lines)

    def _clean_code(self, code: str) -> str:
        code = re.sub(r'```python\s*', '', code, flags=re.IGNORECASE)
        code = re.sub(r'```\s*', '', code)
        return code.strip()

    def _validate_code(self, code: str) -> bool:
        required = ['def run(', 'def get_tool_definition(', 'return']
        for r in required:
            if r not in code:
                return False
        
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False

    def _extract_skill_name(self, code: str) -> Optional[str]:
        match = re.search(r'"name":\s*"([a-zA-Z_][a-zA-Z0-9_]*)"', code)
        if match:
            return match.group(1)
        return None


class AutonomousAgent:
    """
    自主智能体 - 具备自我编程能力
    
    工作流程:
    1. 分析任务需求
    2. 检查现有技能是否足够
    3. 如果不足，自动生成新技能
    4. 执行并返回结果
    """
    
    def __init__(self, llm_client, skill_manager, max_skill_generation=3):
        self.llm = llm_client
        self.skills = skill_manager
        self.generator = SkillGenerator(llm_client, skill_manager)
        self.max_skill_generation = max_skill_generation
        
        self.analysis_prompt = """分析以下任务，判断是否需要创建新技能。

## 任务
{task}

## 现有技能
{existing_skills}

## 判断标准
1. 如果现有技能可以完成任务，返回 {"need_new_skill": false, "reason": "..."}
2. 如果需要新技能，返回 {"need_new_skill": true, "skill_description": "详细描述需要什么技能", "skill_args": {"参数名": "值"}}

只返回 JSON，不要有其他内容。"""

    def analyze_and_execute(self, user_input: str, on_progress=None) -> Dict:
        """
        分析任务并执行
        
        :param user_input: 用户输入
        :param on_progress: 进度回调
        :return: 执行结果
        """
        if on_progress:
            on_progress("analyzing", "分析任务需求...")
        
        analysis = self._analyze_task(user_input)
        
        if not analysis.get("need_new_skill", False):
            if on_progress:
                on_progress("executing", "使用现有技能执行...")
            return self._execute_with_existing_skills(user_input)
        
        skill_gen_count = 0
        while skill_gen_count < self.max_skill_generation:
            skill_gen_count += 1
            
            if on_progress:
                on_progress("generating", f"生成新技能 (尝试 {skill_gen_count})...")
            
            skill_desc = analysis.get("skill_description", user_input)
            skill_args = analysis.get("skill_args", {})
            
            gen_result = self.generator.generate_and_execute(skill_desc, skill_args)
            
            if gen_result.get("success"):
                return gen_result
            
            if on_progress:
                on_progress("retrying", f"技能生成失败，重新分析...")
            
            analysis = self._analyze_task(user_input + f"\n\n注意：之前尝试创建技能失败：{gen_result.get('message', '未知错误')}")
            
            if not analysis.get("need_new_skill", False):
                break
        
        return {
            "success": False,
            "message": "无法自动创建合适的技能来完成任务"
        }

    def _analyze_task(self, task: str) -> Dict:
        existing_skills = self._get_skills_summary()
        
        prompt = self.analysis_prompt.format(
            task=task,
            existing_skills=existing_skills
        )
        
        response = self.llm.simple_chat(prompt)
        
        if not response:
            return {"need_new_skill": False, "reason": "分析失败"}
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
        except:
            return {"need_new_skill": False, "reason": "解析失败"}

    def _execute_with_existing_skills(self, user_input: str) -> Dict:
        from core.react_agent import ReActAgent
        
        agent = ReActAgent(self.llm, self.skills)
        result = agent.run(user_input)
        
        return result

    def _get_skills_summary(self) -> str:
        skills = self.skills.list_skills()
        if not skills:
            return "暂无技能"
        
        lines = []
        for name in skills:
            info = self.skills.get_skill_info(name)
            if info:
                desc = info["schema"].get("function", {}).get("description", "")
                lines.append(f"- {name}: {desc[:60]}")
        return "\n".join(lines)

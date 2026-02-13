import sys
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.status import Status

from llm_client import LLMClient
from tools.memory_skill import PersonalMemorySkill
from tools.soul_skill import SoulSkill
from core.skill_manager import SkillManager

console = Console()

def build_context_messages(full_system_prompt, history_messages, current_input):
    """
    构建带有历史上下文的完整消息列表
    为了节省 Token，我们只取最近 5 轮历史
    """
    # 保留 system prompt
    messages = [{"role": "system", "content": full_system_prompt}]
    
    # 截取最近的历史 (保留最近 5 组对话，即 10 条消息)
    # 注意：history_messages 包含了刚才 append 进去的 user_input，所以要去掉最后一条再处理
    recent_history = history_messages[-6:] if len(history_messages) > 6 else history_messages[:-1]
    
    if recent_history:
        messages.extend(recent_history)
        
    # 添加当前最新的输入
    messages.append({"role": "user", "content": current_input})
    return messages

def classify_intent(user_input, tool_names, client, history_context):
    """
    路由器：判断用户意图。
    现在也带入简要历史，防止误判上下文。
    """
    prompt = f"""
    历史对话摘要: {history_context[-1] if history_context else "无"}
    当前用户输入: "{user_input}"
    可用功能: {tool_names}
    
    判断意图：
    1. 如果是简单的问候、闲聊、常识问题 -> 回复 "CHAT"
    2. 如果涉及文件操作、数据查询、系统设置、或者需要调用工具 -> 回复 "TASK"
    
    只能回复 CHAT 或 TASK。
    """
    result = client.simple_chat(prompt)
    return "TASK" if "TASK" in result else "CHAT"

def main():
    # 1. 初始化
    with Status("[bold green]正在初始化核心系统...[/]", spinner="dots") as status:
        client = LLMClient()
        memory = PersonalMemorySkill()
        soul = SoulSkill()
        skill_manager = SkillManager()
        
        available_tools = skill_manager.get_all_tools_schema()
        tool_names = [t['function']['name'] for t in available_tools]

        # 构建系统提示
        base_system_prompt = (
            "你是一个高级本地助手 Neo。你具备规划能力。\n"
            "重要规则：当你需要回答关于用户数据的问题（如总结、查询）时，**必须先调用工具读取数据**，不要预设自己不知道。"
        )
        soul_context = soul.load_soul()
        memory_context = memory.load_context()
        full_system_prompt = base_system_prompt + soul_context + memory_context

    console.print(Panel.fit(
        "🧠 [bold magenta]Neo 助手已启动[/]\n"
        f"已加载技能: [cyan]{', '.join(tool_names)}[/]\n"
        "具备 [yellow]连续对话[/] 与 [green]主动探索[/] 能力",
        border_style="magenta"
    ))

    # 初始化对话历史
    messages = [{"role": "system", "content": full_system_prompt}]
    interaction_counter = 0

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]👤 You[/]")
            if not user_input.strip(): continue
            if user_input.lower() in ["exit", "quit"]: break

            # 先把用户输入加入历史（临时），方便构建上下文
            # 如果后续发现是 TASK，我们会用专门的逻辑处理
            messages.append({"role": "user", "content": user_input})

            # === 第一步：意图路由 ===
            # 传入 history messages 让路由器也知道刚才聊了啥
            with Status("[bold dim]🧐 理解意图...[/]", spinner="point") as status:
                intent = classify_intent(user_input, tool_names, client, messages)
            
            final_reply = ""
            
            # === 第二步：分流执行 ===
            
            # --- 分支 A：闲聊模式 ---
            if intent == "CHAT":
                with Status("[bold green]💬 闲聊模式...[/]", spinner="dots"):
                    # 直接使用维护的 messages 列表
                    response = client.chat(messages)
                    if response:
                        final_reply = response["choices"][0]["message"]["content"]
                        messages.append({"role": "assistant", "content": final_reply})
                    else:
                        final_reply = "抱歉，我走神了..."
                        messages.append({"role": "assistant", "content": final_reply})
            
            # --- 分支 B：任务模式 ---
            else:
                console.print("[yellow]🚀 进入任务模式...[/]")
                with Status("[bold blue]🧠 规划任务路径...[/]", spinner="dots") as status:
                    
                    # 关键修正：构建包含历史的请求
                    # 这里不再只发 user_input，而是发 recent history
                    plan_messages = build_context_messages(full_system_prompt, messages, user_input)
                    
                    # 追加规划指令
                    plan_directive = {
                        "role": "system", 
                        "content": f"""
                        当前可用技能: {tool_names}

                        # 核心身份约束
                        你是一个任务规划者，你本人 **不能** 执行任何代码或访问网络。
                        你只能通过调用 "可用技能" 列表中的工具来完成任务。
                        
                        # 严禁行为
                        1. 严禁输出 XML 标签 (如 <minimax:tool_call>)。
                        2. 严禁输出代码块 (如 ```python 或 curl)。
                        3. 严禁假装已经执行了任务。
                        4.  **绝对禁止**直接回复用户说"我做不到"、"无法访问网络"或任何解释性文字。
                        
                        # 必须执行
                        你必须输出一个标准的 JSON 对象来描述计划。
                        如果现有工具无法完成任务，请务必使用 "need_new_skill" 工具请求新能力。
                        
                        正确输出示例:
                        {{"plan": [{{"step": "获取天气", "tool": "need_new_skill", "args": {{"description": "获取实时天气的能力"}}}}]}}
                        """
                    }                    

                    plan_messages.append(plan_directive)
                    
                    plan_response = client.chat(plan_messages)
                    
                    plan_data = {}
                    raw_content = ""
                    
                    if plan_response:
                        raw_content = plan_response["choices"][0]["message"]["content"]
                        
                        try:
                            # 1. 预处理：移除 XML 标签
                            import re
                            clean_content = re.sub(r'<[^>]+>', '', raw_content).strip()
                            
                            # 2. 提取 JSON
                            json_str = clean_content
                            if "```json" in json_str:
                                json_str = json_str.split("```json")[1].split("```")[0].strip()
                            elif "```" in json_str:
                                json_str = json_str.split("```")[1].split("```")[0].strip()
                            
                            # 3. 尝试解析
                            if json_str.startswith("{") and "plan" in json_str:
                                plan_data = json.loads(json_str)
                            else:
                                # 关键修正：如果不是 JSON，说明模型在“狡辩”或“拒绝”
                                # 我们不把它当闲聊处理，而是强行当作“需要新技能”处理
                                raise ValueError("模型未输出规划JSON")
                            
                        except (json.JSONDecodeError, ValueError) as e:
                            # === 核心修正：解析失败不再退化为聊天，而是触发技能请求 ===
                            
                            # 提示用户发生了什么
                            console.print(f"[yellow]⚠️ 模型未能生成有效计划，正在尝试自动构建解决方案...[/]")
                            
                            # 强制构造一个“技能缺失”的计划
                            # 把用户的原始需求直接扔给“新技能生成器”
                            plan_data = {
                                "plan": [
                                    {
                                        "step": "分析需求并安装必要工具", 
                                        "tool": "need_new_skill", 
                                        "args": {
                                            "description": f"为了完成用户任务: '{user_input}'，需要安装相关功能模块（如天气查询、短信发送等）。"
                                        }
                                    }
                                ]
                            }

                # 执行计划步骤
                # 注意：我们需要维护一个临时的执行上下文，因为任务可能有多步
                # 但为了简单，我们直接操作主 messages 或创建临时 execution_log
                
                execution_log = [] # 记录本次任务执行过程
                
                for step_item in plan_data.get("plan", []):
                    step_desc = step_item.get("step", "")
                    tool_name = step_item.get("tool")
                    tool_args = step_item.get("args", {})

                    console.print(f"[yellow]➡️ 执行:[/] {step_desc}")

                    # 1. 缺失技能
                    if tool_name == "need_new_skill":
                        missing_desc = tool_args.get("description", "未知功能")
                        console.print(f"[bold red]⚠️ 技能缺失:[/] {missing_desc}")
                        
                        if Prompt.ask("是否尝试自动编写该技能? [y/n]", choices=["y", "n"], default="y") == "y":
                            status.update("[bold magenta]💻 编写新技能...[/]")
                            new_skill_name = f"auto_skill_{int(time.time())}"
                            
                            code_prompt = f"""
                            请编写一个 Python 脚本来实现以下功能: {missing_desc}
                            
                            # 代码规范
                            1. 必须包含 run(arguments: dict) 函数作为入口。
                            2. 必须包含 get_tool_definition() 函数。
                            3. get_tool_definition 必须返回符合 OpenAI 标准的 JSON Schema：
                               即返回结构必须为 {{"type": "function", "function": {{"name": "...", "description": "...", "parameters": {{}}}}}}
                            
                            只输出代码，不要解释。
                            """
                            # 写代码也需要上下文，比如刚才读到了什么
                            code_context = build_context_messages(full_system_prompt, messages, code_prompt)
                            
                            code_response = client.chat(code_context)
                            code_content = code_response["choices"][0]["message"]["content"]
                            code_content = code_content.replace("```python", "").replace("```", "")
                            
                            filepath = skill_manager.create_skill_file(new_skill_name, code_content)
                            available_tools = skill_manager.get_all_tools_schema()
                            tool_names = [t['function']['name'] for t in available_tools]
                            
                            final_reply = f"✅ 新技能已生成 ({new_skill_name})，请再试一次。"
                            messages.append({"role": "assistant", "content": final_reply})
                            memory.record_interaction(user_input, final_reply, client)
                            break 
                        else:
                            final_reply = "任务中止。"
                            break

                    # 1.1 新增：直接输出模式 (针对模型直接给出答案的情况)
                    elif tool_name == "direct_output":
                        final_reply = tool_args.get("content", "...")
                        messages.append({"role": "assistant", "content": final_reply})

                    # 2. 普通聊天 (在任务中)
                    elif tool_name == "chat":
                        # 这里的 chat 需要知道之前工具执行的结果
                        # 我们把执行日志作为系统消息塞进去
                        temp_msgs = messages + [{"role": "system", "content": f"工具执行日志: {json.dumps(execution_log)}"}]
                        response = client.chat(temp_msgs)
                        final_reply = response["choices"][0]["message"]["content"]
                        messages.append({"role": "assistant", "content": final_reply})
                    
                    # 3. 调用工具
                    elif tool_name in skill_manager.skills:
                        func = skill_manager.get_skill(tool_name)
                        result = func(tool_args)
                        
                        # 记录结果，供后续步骤或最终回复使用
                        execution_log.append({"step": step_desc, "result": result})
                        console.print(f"[dim]   ⬅️ 结果: {result.get('message', 'done')}[/]")
                        
                        # 如果这是最后一步，或者我们需要将结果反馈给 LLM 进行下一步
                        # 这里简单处理：将结果转为文本追加到 messages 中，模拟 tool 角色
                        # 这样下一步如果调用 chat，模型就能看到这个结果了
                        messages.append({
                            "role": "system", # 使用 system 注入数据比较稳妥
                            "content": f"工具 [{tool_name}] 执行结果: {json.dumps(result, ensure_ascii=False)}"
                        })
                        
                        # 如果计划只有这一步，或者这是最后一步，生成自然语言总结
                        if step_item == plan_data["plan"][-1]:
                             # 生成最终总结
                             summary_prompt = "根据上述工具执行结果，回复用户。"
                             # 这里的 messages 已经包含了工具结果
                             temp_msgs = messages + [{"role": "user", "content": summary_prompt}]
                             res = client.chat(temp_msgs)
                             final_reply = res["choices"][0]["message"]["content"]
                             messages.append({"role": "assistant", "content": final_reply})
                    else:
                        console.print(f"[red]❌ 未知工具: {tool_name}[/]")

            # === 记忆更新 ===
            if final_reply:
                console.print("\n[bold green]🤖 Neo:[/]")
                console.print(Markdown(final_reply))
                
                # 如果在任务模式下，assistant 消息可能已经在上面的逻辑里追加过了
                # 这里做一层检查，避免重复追加
                if not (messages[-1]["role"] == "assistant" and messages[-1]["content"] == final_reply):
                    messages.append({"role": "assistant", "content": final_reply})
                
                # 记录到外部文件
                memory.record_interaction(user_input, final_reply, client)

            interaction_counter += 1
            if interaction_counter % 10 == 0:
                recent_chat = memory._read_file(memory.active_file)
                soul.reflect_and_evolve(recent_chat, client)

        except KeyboardInterrupt:
            console.print("\n[bold red]⚠️ 强制中断[/]")
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ 错误:[/] {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
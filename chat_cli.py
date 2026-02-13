import sys
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.status import Status

# 引入核心模块
from llm_client import LLMClient
from tools.notes_skill import NotesSkill
from tools.memory_skill import PersonalMemorySkill

# 初始化 Rich 控制台
console = Console()

def main():
    # 1. 初始化核心组件
    with Status("[bold green]正在初始化本地助手...[/]", spinner="dots") as status:
        client = LLMClient()
        memory = PersonalMemorySkill()
        
        available_functions = {
            "notes_operator": NotesSkill.run,
        }
        tools_schema = [NotesSkill.get_tool_definition()]

        # 构建初始 System Prompt (注入记忆)
        base_system_prompt = "你是一个运行在用户 macOS 上的本地助手。你可以操作备忘录等本地应用。"
        memory_context = memory.load_context()
        
        messages = [
            {
                "role": "system", 
                "content": base_system_prompt + memory_context
            }
        ]

    # 启动界面
    console.print(Panel.fit(
        "🤖 [bold magenta]本地助手已启动[/] (带记忆功能)\n"
        "输入 [cyan]exit[/] 或 [cyan]quit[/] 退出",
        border_style="magenta",
        title="Agent v1.0"
    ))

    # 主循环
    while True:
        try:
            # 1. 获取用户输入
            user_input = Prompt.ask("\n[bold cyan]👤 You[/]")
            
            if not user_input.strip():
                continue
            
            if user_input.lower() in ["exit", "quit", "退出"]:
                console.print("\n👋 [bold yellow]再见！[/]")
                break

            messages.append({"role": "user", "content": user_input})

            # 2. 发起请求
            with Status("[bold blue]🤖 AI 正在思考...[/]", spinner="dots") as status:
                response = client.chat(messages, tools=tools_schema)
                
                if not response or "choices" not in response:
                    console.print("[bold red]❌ 连接失败，请检查网络或 API Key。[/]")
                    messages.pop() # 移除失败的消息
                    continue

                assistant_message = response["choices"][0]["message"]
                final_reply_content = ""
                
                # 3. 处理工具调用
                if assistant_message.get("tool_calls"):
                    # 更新状态提示
                    status.update("[bold yellow]🔧 正在执行本地工具...[/]")
                    
                    messages.append(assistant_message)
                    
                    for tool_call in assistant_message["tool_calls"]:
                        func_name = tool_call["function"]["name"]
                        func_args_str = tool_call["function"]["arguments"]
                        
                        # 显示工具调用信息
                        console.print(f"[dim]➡️ 调用工具: [bold]{func_name}[/] with args: {func_args_str}[/]")
                        
                        if func_name in available_functions:
                            func_args = json.loads(func_args_str)
                            tool_result = available_functions[func_name](func_args)
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "name": func_name,
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })

                    # 再次调用 LLM 生成最终回复
                    status.update("[bold blue]📝 正在生成回复...[/]")
                    final_response = client.chat(messages, tools=tools_schema)
                    
                    if final_response:
                        final_reply_content = final_response["choices"][0]["message"]["content"]
                        messages.append({"role": "assistant", "content": final_reply_content})
                    else:
                        final_reply_content = "工具执行完毕，但生成回复失败。"
                        messages.append({"role": "assistant", "content": final_reply_content})

                else:
                    # 直接回复
                    final_reply_content = assistant_message.get("content", "...")
                    messages.append({"role": "assistant", "content": final_reply_content})

            # 4. 渲染 AI 回复 (支持 Markdown)
            console.print("\n[bold green]🤖 AI:[/]", end=" ")
            console.print(Markdown(final_reply_content))

            # 5. 记忆固化
            if final_reply_content:
                memory.record_interaction(user_input, final_reply_content, client)

        except KeyboardInterrupt:
            console.print("\n[bold red]⚠️ 强制中断[/]")
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ 发生错误:[/] {e}")

if __name__ == "__main__":
    main()





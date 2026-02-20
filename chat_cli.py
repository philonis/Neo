"""
Neo 命令行界面 - 基于 ReAct 架构

使用方法:
    python chat_cli.py
"""

import sys
import json
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.status import Status
from rich.table import Table
from rich import print as rprint

from llm_client import LLMClient
from core import SkillManager, ReActAgent, TaskPlanner, VectorMemory
from tools.soul_skill import SoulSkill

console = Console()


def print_banner(skill_names: List[str]):
    console.print(Panel.fit(
        "🧠 [bold magenta]Neo 智能助手[/]\n"
        "[dim]基于 ReAct 架构 | 原生 Function Calling | 智能记忆系统[/]\n\n"
        f"已加载技能: [cyan]{len(skill_names)}[/] 个\n"
        "[dim]输入 'help' 查看帮助，'quit' 退出[/]",
        border_style="magenta"
    ))


def print_help():
    help_table = Table(title="📖 命令帮助", show_header=False)
    help_table.add_column("命令", style="cyan")
    help_table.add_column("说明", style="white")
    
    help_table.add_row("help", "显示帮助信息")
    help_table.add_row("quit / exit", "退出程序")
    help_table.add_row("skills", "列出所有已加载的技能")
    help_table.add_row("memory", "显示记忆统计")
    help_table.add_row("clear", "清空对话历史")
    help_table.add_row("status", "显示代码保护状态")
    help_table.add_row("trace", "切换执行轨迹显示")
    help_table.add_row("logs", "切换LLM通信日志显示")
    
    console.print(help_table)
    
    console.print("\n[bold]💡 使用示例:[/]")
    console.print("  • [cyan]帮我搜索今天的新闻[/]")
    console.print("  • [cyan]打开豆包，问它今天天气[/]")
    console.print("  • [cyan]访问小红书看看热门帖子[/]")
    console.print("  • [cyan]创建一个备忘录：购物清单[/]")
    console.print()


def print_skills(skill_manager: SkillManager):
    skills = skill_manager.list_skills()
    
    table = Table(title=f"🔧 已加载技能 ({len(skills)} 个)")
    table.add_column("技能名称", style="cyan")
    table.add_column("描述", style="white")
    
    for skill_name in skills:
        info = skill_manager.get_skill_info(skill_name)
        if info:
            desc = info["schema"].get("function", {}).get("description", "")[:60]
            table.add_row(skill_name, desc + "...")
    
    console.print(table)


def print_memory_stats(memory: VectorMemory):
    stats = memory.get_stats()
    
    table = Table(title="📊 记忆统计")
    table.add_column("类型", style="cyan")
    table.add_column("数量", style="white")
    
    table.add_row("短期记忆", str(stats["short_term_count"]))
    table.add_row("长期记忆", str(stats["long_term_count"]))
    table.add_row("索引关键词", str(stats["index_keywords"]))
    
    console.print(table)


def print_code_guard_status():
    try:
        from code_guard import get_code_guard
        guard = get_code_guard()
        status = guard.get_status()
        
        table = Table(title="🔒 代码保护状态")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="white")
        
        table.add_row("保护级别", status["level"])
        table.add_row("受保护文件", str(status["protected_files_count"]))
        table.add_row("受保护目录", str(status["protected_dirs_count"]))
        table.add_row("沙盒目录", ", ".join(status["sandbox_dirs"]))
        table.add_row("修改记录数", str(status["modifications_count"]))
        
        console.print(table)
    except ImportError:
        console.print("[yellow]代码保护系统未安装[/]")


def on_progress(stage: str, message: str):
    icons = {
        "thinking": "🧠",
        "action": "⚡",
        "observation": "👁️",
        "generating": "💻"
    }
    icon = icons.get(stage, "▶️")
    console.print(f"[dim]{icon} {message}[/]")


def on_log(log_type: str, data: dict):
    if log_type == "response":
        if data.get("content"):
            console.print(f"[dim]📥 LLM响应: {data['content'][:100]}...[/]")
        if data.get("has_tool_calls"):
            console.print(f"[dim]🔧 调用 {data.get('tool_calls_count', 0)} 个工具[/]")
    elif log_type == "tool_call":
        console.print(f"[dim]🔧 工具调用: {data.get('tool')}[/]")
    elif log_type == "tool_result":
        status = "✅" if data.get("success") else "❌"
        console.print(f"[dim]{status} 工具结果: {data.get('tool')}[/]")


def render_result(result: Dict[str, Any], show_trace: bool = False, show_logs: bool = False, logs: List = None):
    if result["success"]:
        console.print()
        console.print(Markdown(result["response"]))
        
        if show_trace and result.get("trace"):
            console.print("\n[dim]📋 执行轨迹:[/]")
            for item in result["trace"]:
                console.print(f"  [dim]步骤 {item['iteration']}: 调用[/] [cyan]{item['tool']}[/]")
                if "error" in item.get("result", {}):
                    console.print(f"    [red]❌ {item['result']['error']}[/]")
                else:
                    console.print(f"    [green]✅ 执行成功[/]")
        
        if show_logs and logs:
            console.print("\n[dim]📡 LLM通信日志:[/]")
            for log in logs:
                if log["type"] == "request":
                    console.print(f"  [dim]📤 请求 #{log['data'].get('iteration')}[/]")
                elif log["type"] == "response":
                    console.print(f"  [dim]📥 响应 #{log['data'].get('iteration')}[/]")
                elif log["type"] == "tool_call":
                    console.print(f"  [dim]🔧 工具: {log['data'].get('tool')}[/]")
    else:
        console.print(f"\n[red]❌ {result['response']}[/]")


def main():
    with Status("[bold green]正在初始化核心系统...[/]", spinner="dots"):
        client = LLMClient()
        skill_manager = SkillManager()
        memory = VectorMemory()
        soul = SoulSkill()
        agent = ReActAgent(client, skill_manager, memory)
        planner = TaskPlanner(client, skill_manager)
    
    try:
        from agent_skills.telegram_bot import init_telegram_service
        telegram_service = init_telegram_service(agent)
        if telegram_service:
            console.print("[green]✅ Telegram服务已自动启动[/]")
    except Exception as e:
        pass
    
    skill_names = skill_manager.list_skills()
    print_banner(skill_names)
    
    messages: List[Dict[str, str]] = []
    interaction_count = 0
    show_trace = False
    show_logs = False
    current_logs = []
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]👤 You[/]").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit"]:
                console.print("[magenta]👋 再见！[/]")
                break
            
            if user_input.lower() == "help":
                print_help()
                continue
            
            if user_input.lower() == "skills":
                print_skills(skill_manager)
                continue
            
            if user_input.lower() == "memory":
                print_memory_stats(memory)
                continue
            
            if user_input.lower() == "clear":
                messages = []
                console.print("[green]✅ 对话历史已清空[/]")
                continue
            
            if user_input.lower() == "status":
                print_code_guard_status()
                continue
            
            if user_input.lower() == "trace":
                show_trace = not show_trace
                status = "开启" if show_trace else "关闭"
                console.print(f"[green]✅ 执行轨迹显示已{status}[/]")
                continue
            
            if user_input.lower() == "logs":
                show_logs = not show_logs
                status = "开启" if show_logs else "关闭"
                console.print(f"[green]✅ LLM日志显示已{status}[/]")
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            context = [m for m in messages[:-1] if m["role"] in ["user", "assistant"]]
            
            console.print("[dim]🧠 正在思考...[/]")
            
            current_logs = []
            
            def collect_logs(log_type: str, data: dict):
                current_logs.append({"type": log_type, "data": data})
                if show_logs:
                    on_log(log_type, data)
            
            result = agent.run(user_input, context=context, on_progress=on_progress, on_log=collect_logs)
            
            render_result(result, show_trace=show_trace, show_logs=show_logs, logs=current_logs)
            
            if result["success"]:
                messages.append({"role": "assistant", "content": result["response"]})
            else:
                messages.append({"role": "assistant", "content": f"任务执行失败: {result['response']}"})
            
            memory.add_interaction(
                user_input=user_input,
                assistant_response=result["response"],
                tool_calls=[{"name": t["tool"], "args": t["args"]} for t in result.get("trace", [])]
            )
            
            interaction_count += 1
            
            if interaction_count % 10 == 0:
                console.print("[dim]🧘 正在压缩记忆...[/]")
                memory.compress(client)
                
                recent_chat = memory.get_context_for_prompt("最近的对话")
                soul.reflect_and_evolve(recent_chat, client)
        
        except KeyboardInterrupt:
            console.print("\n[bold red]⚠️ 强制中断[/]")
            console.print("[dim]输入 'quit' 退出程序[/]")
            continue
        
        except Exception as e:
            console.print(f"\n[bold red]❌ 错误:[/] {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

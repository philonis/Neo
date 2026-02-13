import streamlit as st
import json
import time
import re
from llm_client import LLMClient
from tools.memory_skill import PersonalMemorySkill
from tools.soul_skill import SoulSkill
from core.skill_manager import SkillManager

# --- 1. 页面配置 ---
st.set_page_config(page_title="Neo 智能助手", page_icon="🧠", layout="centered")

# --- 2. 核心资源初始化 (全局单例) ---
@st.cache_resource
def init_resources():
    client = LLMClient()
    memory = PersonalMemorySkill()
    soul = SoulSkill()
    skill_manager = SkillManager()
    return client, memory, soul, skill_manager

client, memory, soul, skill_manager = init_resources()

# --- 3. 辅助函数 ---

def build_context_messages(full_system_prompt, history_messages, current_input):
    """构建带有历史上下文的完整消息列表"""
    messages = [{"role": "system", "content": full_system_prompt}]
    recent_history = history_messages[-6:] if len(history_messages) > 6 else history_messages[:-1]
    if recent_history:
        messages.extend(recent_history)
    messages.append({"role": "user", "content": current_input})
    return messages

def classify_intent(user_input, tool_names, history_context):
    """路由器：判断用户意图"""
    # 提取历史对话摘要（只取内容，不取角色）
    history_summary = "无"
    if history_context:
        last_msg = history_context[-1]
        if isinstance(last_msg, dict) and "content" in last_msg:
            history_summary = last_msg["content"]
    
    prompt = f"""
    历史对话摘要: {history_summary}
    当前用户输入: "{user_input}"
    可用功能: {tool_names}
    
    判断意图：
    1. 如果是简单的问候、闲聊、常识问题、旅行建议、生活建议等开放性问题 -> 回复 "CHAT"
    2. 如果涉及文件操作、数据查询、系统设置、或者需要调用工具的具体任务 -> 回复 "TASK"
    
    只能回复 CHAT 或 TASK。
    """
    result = client.simple_chat(prompt)
    # 确保result不为None
    if result and "TASK" in result:
        return "TASK"
    return "CHAT"

def extract_json_from_text(text):
    """健壮的 JSON 提取逻辑"""
    try:
        clean_content = re.sub(r'<[^>]+>', '', text).strip()
        json_str = clean_content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
            
        if json_str.startswith("{") and "plan" in json_str:
            return json.loads(json_str)
        else:
            return None
    except:
        return None

# --- 4. Session State 初始化 ---

if "system_prompt" not in st.session_state:
    base_system_prompt = (
        "你是一个高级本地助手 Neo。你具备规划能力。\n"
        "重要规则：当你需要回答关于用户数据的问题时，**必须先调用工具读取数据**，不要预设自己不知道。"
    )
    soul_context = soul.load_soul()
    memory_context = memory.load_context()
    st.session_state.system_prompt = base_system_prompt + soul_context + memory_context

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": st.session_state.system_prompt}]

if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0

# --- 5. 界面布局 ---

# 初始化工具列表 (每次脚本运行时获取最新的)
available_tools = skill_manager.get_all_tools_schema()
tool_names = [t['function']['name'] for t in available_tools]

st.title("🧠 Neo 规划式助手")
st.caption(f"已加载技能: `{'`, `'.join(tool_names)}` | 具备自我进化能力")

# 显示历史聊天记录
for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 6. 主逻辑处理 ---

if prompt := st.chat_input("请输入指令..."):
    # 1. 显示用户消息
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 意图路由
    with st.status("🧐 正在理解意图...", expanded=False) as status:
        intent = classify_intent(prompt, tool_names, st.session_state.messages)
        status.update(label=f"意图识别: {'🚀 任务模式' if intent == 'TASK' else '💬 闲聊模式'}", state="complete")

    final_reply = ""
    
    # --- 分支 A：闲聊模式 ---
    if intent == "CHAT":
        with st.chat_message("assistant"):
            response = client.chat(st.session_state.messages)
            if response:
                final_reply = response["choices"][0]["message"]["content"]
                st.markdown(final_reply)
            else:
                final_reply = "抱歉，我走神了..."
                st.error(final_reply)
            st.session_state.messages.append({"role": "assistant", "content": final_reply})

    # --- 分支 B：任务模式 (支持即时重规划) ---
    else:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            # 引入“重规划”循环：如果生成了新技能，循环不会退出，而是继续执行新计划
            max_attempts = 2  # 防止死循环，最多尝试规划2次
            current_attempt = 0
            
            while current_attempt < max_attempts:
                current_attempt += 1
                
                # 每次循环开始时，刷新工具列表（如果有新技能生成）
                available_tools = skill_manager.get_all_tools_schema()
                tool_names = [t['function']['name'] for t in available_tools]
                
                placeholder.markdown(f"🧠 **正在规划任务路径...** (尝试 {current_attempt})")
                
                # 1. 构建规划请求
                plan_messages = build_context_messages(st.session_state.system_prompt, st.session_state.messages, prompt)
                plan_directive = {
                    "role": "system", 
                    "content": f"""
                    当前可用技能: {tool_names}
                    
                    # 核心身份约束
                    你是一个任务规划者。请严格按照以下优先级处理任务：
                    
                    ## 优先级顺序
                    1. **优先使用现有工具**：充分利用已有的工具完成任务，即使需要组合使用多个工具
                    2. **使用通用聊天工具**：对于开放性问题、创意生成、建议提供、旅行建议、生活建议等不需要特定功能的任务，使用 "chat" 工具
                    3. **仅在必要时创建新技能**：只有当现有工具完全无法完成任务，且任务确实需要特定功能时，才使用 "need_new_skill" 工具
                    
                    ## 决策指南
                    - **使用现有工具**：当任务可以通过组合使用现有工具完成时
                    - **使用聊天工具**：当任务是开放性问题、创意讨论、建议请求、常识问答、旅行建议等
                    - **创建新技能**：当任务需要特定的功能实现，且现有工具无法满足
                    
                    ## 重要要求
                    - 无论使用哪种方式，最终都必须向用户提供一个详细、有用的回答
                    - 对于旅行、生活建议等常见问题，优先使用聊天工具直接回答
                    - 只有当需要执行具体操作（如文件处理、数据查询）时，才需要创建新技能
                    
                    ## 输出要求
                    你必须输出标准的 JSON 对象，包含详细的执行计划。
                    """
                }
                plan_messages.append(plan_directive)
                
                # 2. 获取规划响应
                plan_response = client.chat(plan_messages)
                
                if not plan_response:
                    final_reply = "规划失败，请检查网络。"
                    break

                raw_content = plan_response["choices"][0]["message"]["content"]
                plan_data = extract_json_from_text(raw_content)
                
                # 3. 处理规划解析失败
                if not plan_data:
                    plan_data = {
                        "plan": [{
                            "step": "分析需求并安装必要工具", 
                            "tool": "need_new_skill", 
                            "args": {"description": f"为了完成用户任务: '{prompt}'，需要安装相关功能模块。"}
                        }]
                    }

                # 4. 执行步骤
                execution_log = []
                should_replan = False # 标记是否需要重新规划
                
                for step_item in plan_data.get("plan", []):
                    step_desc = step_item.get("step", "")
                    tool_name = step_item.get("tool")
                    tool_args = step_item.get("args", {})

                    placeholder.markdown(f"➡️ **执行步骤**: {step_desc}")
                    time.sleep(0.3)

                    # 情况 A: 缺失技能 -> 自动生成并标记重规划
                    if tool_name == "need_new_skill":
                        missing_desc = tool_args.get("description", "未知功能")
                        
                        # 先搜索现有技能
                        matching_skills = skill_manager.search_skills(missing_desc)
                        if matching_skills:
                            best_skill = matching_skills[0]
                            placeholder.markdown(f"🔍 **发现现有技能**: `{best_skill['name']}` 可以处理此任务。正在使用该技能...")
                            # 直接使用现有技能，不需要创建新技能
                            # 将现有技能信息添加到上下文
                            st.session_state.messages.append({
                                "role": "system",
                                "content": f"已找到并使用现有技能: {best_skill['name']} - {best_skill['description']}"
                            })
                            should_replan = True
                            break
                        
                        # 如果没有找到匹配的技能，才创建新技能
                        placeholder.markdown(f"🛠️ **技能缺失**: {missing_desc} \n\n ⏳ 正在自动编写新技能...")
                        
                        new_skill_name = f"auto_skill_{int(time.time())}"
                        code_prompt = f"编写 Python 脚本实现: {missing_desc}。要求：包含 run 函数和 get_tool_definition 函数。必须返回标准 OpenAI Schema。只输出代码。"
                        
                        code_context = build_context_messages(st.session_state.system_prompt, st.session_state.messages, code_prompt)
                        code_response = client.chat(code_context)
                        
                        if code_response:
                            code_content = code_response["choices"][0]["message"]["content"]
                            code_content = code_content.replace("```python", "").replace("```", "")
                            
                            # 保存并加载
                            filepath = skill_manager.create_skill_file(new_skill_name, code_content)
                            
                            placeholder.markdown(f"✅ **新技能已生成** (`{new_skill_name}`)。正在立即重新规划任务...")
                            
                            # 关键：不退出循环，而是设置标记，让外层 while 循环继续运行
                            should_replan = True
                            break # 跳出当前 for 循环，进入下一次 while 循环
                        else:
                            final_reply = "代码生成失败。"
                            should_replan = False
                            break

                    # 情况 B: 普通聊天
                    elif tool_name == "chat":
                        temp_msgs = st.session_state.messages + [{"role": "system", "content": f"工具执行日志: {json.dumps(execution_log)}"}]
                        response = client.chat(temp_msgs)
                        final_reply = response["choices"][0]["message"]["content"]
                        # 任务完成，无需重规划
                        should_replan = False 

                    # 情况 C: 调用工具
                    elif tool_name in skill_manager.skills:
                        func = skill_manager.get_skill(tool_name)
                        result = func(tool_args)
                        execution_log.append({"step": step_desc, "result": result})
                        
                        # 将结果注入历史
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"工具 [{tool_name}] 执行结果: {json.dumps(result, ensure_ascii=False)}"
                        })
                        
                        # 如果是最后一步，生成总结
                        if step_item == plan_data["plan"][-1]:
                             summary_prompt = "根据上述工具执行结果，回复用户。"
                             temp_msgs = st.session_state.messages + [{"role": "user", "content": summary_prompt}]
                             res = client.chat(temp_msgs)
                             final_reply = res["choices"][0]["message"]["content"]
                             should_replan = False
                    else:
                        placeholder.error(f"❌ 未知工具: {tool_name}")
                        should_replan = False
                        break

                # 如果不需要重规划（任务完成或失败），退出 while 循环
                if not should_replan:
                    break
            
            # 循环结束，显示最终结果
            if final_reply:
                placeholder.markdown(final_reply)
                st.session_state.messages.append({"role": "assistant", "content": final_reply})
            else:
                placeholder.markdown("任务执行结束。")

    # --- 5. 记忆更新 ---
    if final_reply:
        memory.record_interaction(prompt, final_reply, client)
        st.session_state.interaction_count += 1
        if st.session_state.interaction_count % 10 == 0:
            recent_chat = memory._read_file(memory.active_file)
            soul.reflect_and_evolve(recent_chat, client)
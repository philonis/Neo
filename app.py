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
    # 取最近 5 轮历史 (10条消息)
    recent_history = history_messages[-6:] if len(history_messages) > 6 else history_messages[:-1]
    if recent_history:
        messages.extend(recent_history)
    messages.append({"role": "user", "content": current_input})
    return messages

def classify_intent(user_input, tool_names, history_context):
    """路由器：判断用户意图"""
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

def extract_json_from_text(text):
    """健壮的 JSON 提取逻辑"""
    try:
        # 1. 清洗 XML 标签
        clean_content = re.sub(r'<[^>]+>', '', text).strip()
        
        # 2. 提取 JSON
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

# 获取当前可用工具
available_tools = skill_manager.get_all_tools_schema()
tool_names = [t['function']['name'] for t in available_tools]

# 构建系统提示 (注入人格和记忆)
if "system_prompt" not in st.session_state:
    base_system_prompt = (
        "你是一个高级本地助手 Neo。你具备规划能力。\n"
        "重要规则：当你需要回答关于用户数据的问题时，**必须先调用工具读取数据**，不要预设自己不知道。"
    )
    soul_context = soul.load_soul()
    memory_context = memory.load_context()
    st.session_state.system_prompt = base_system_prompt + soul_context + memory_context

# 初始化消息历史
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": st.session_state.system_prompt}]

# 初始化交互计数器
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0

# --- 5. 界面布局 ---

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

    # --- 分支 B：任务模式 ---
    else:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("🧠 正在规划任务路径...")

            # 1. 构建规划请求
            plan_messages = build_context_messages(st.session_state.system_prompt, st.session_state.messages, prompt)
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
                
                # 必须执行
                你必须输出一个标准的 JSON 对象来描述计划。
                如果现有工具无法完成任务，请务必使用 "need_new_skill" 工具请求新能力。
                """
            }
            plan_messages.append(plan_directive)
            
            # 2. 获取规划响应
            plan_response = client.chat(plan_messages)
            
            if not plan_response:
                final_reply = "规划失败，请检查网络。"
                st.error(final_reply)
            else:
                raw_content = plan_response["choices"][0]["message"]["content"]
                plan_data = extract_json_from_text(raw_content)
                
                # 3. 处理规划解析失败 (自动转为技能请求)
                if not plan_data:
                    placeholder.markdown("⚠️ 模型未能生成有效计划，正在尝试自动构建解决方案...")
                    plan_data = {
                        "plan": [{
                            "step": "分析需求并安装必要工具", 
                            "tool": "need_new_skill", 
                            "args": {"description": f"为了完成用户任务: '{prompt}'，需要安装相关功能模块。"}
                        }]
                    }

                # 4. 执行步骤
                execution_log = []
                for step_item in plan_data.get("plan", []):
                    step_desc = step_item.get("step", "")
                    tool_name = step_item.get("tool")
                    tool_args = step_item.get("args", {})

                    placeholder.markdown(f"➡️ **执行步骤**: {step_desc}")
                    time.sleep(0.5) # 稍微停顿一下，让用户看到进度

                    # 情况 A: 缺失技能 -> 自动生成
                    if tool_name == "need_new_skill":
                        missing_desc = tool_args.get("description", "未知功能")
                        placeholder.markdown(f"🛠️ **技能缺失**: {missing_desc} \n\n ⏳ 正在自动编写新技能...")
                        
                        new_skill_name = f"auto_skill_{int(time.time())}"
                        code_prompt = f"编写 Python 脚本实现: {missing_desc}。要求：包含 run 函数和 get_tool_definition 函数。必须返回标准 OpenAI Schema。只输出代码。"
                        
                        # 写代码也需要上下文
                        code_context = build_context_messages(st.session_state.system_prompt, st.session_state.messages, code_prompt)
                        code_response = client.chat(code_context)
                        
                        if code_response:
                            code_content = code_response["choices"][0]["message"]["content"]
                            code_content = code_content.replace("```python", "").replace("```", "")
                            
                            # 保存并加载
                            filepath = skill_manager.create_skill_file(new_skill_name, code_content)
                            
                            # 更新当前会话的工具列表 (注意：这里更新的是局部变量，下次运行会自动从缓存读取新状态)
                            available_tools = skill_manager.get_all_tools_schema()
                            tool_names = [t['function']['name'] for t in available_tools]
                            
                            final_reply = f"✅ 新技能已生成并加载 (`{new_skill_name}`)。请**重新发送指令**以使用它。"
                            placeholder.markdown(final_reply)
                            
                            st.session_state.messages.append({"role": "assistant", "content": final_reply})
                            # 任务暂停，等待用户重试
                            break 
                        else:
                            final_reply = "代码生成失败。"
                            placeholder.error(final_reply)
                            break

                    # 情况 B: 普通聊天
                    elif tool_name == "chat":
                        temp_msgs = st.session_state.messages + [{"role": "system", "content": f"工具执行日志: {json.dumps(execution_log)}"}]
                        response = client.chat(temp_msgs)
                        final_reply = response["choices"][0]["message"]["content"]
                        placeholder.markdown(final_reply)
                        st.session_state.messages.append({"role": "assistant", "content": final_reply})

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
                             placeholder.markdown(final_reply)
                             st.session_state.messages.append({"role": "assistant", "content": final_reply})
                    else:
                        placeholder.error(f"❌ 未知工具: {tool_name}")

    # --- 5. 记忆更新 ---
    if final_reply:
        # 记录到外部文件
        memory.record_interaction(prompt, final_reply, client)
        
        # 更新灵魂
        st.session_state.interaction_count += 1
        if st.session_state.interaction_count % 10 == 0:
            recent_chat = memory._read_file(memory.active_file)
            soul.reflect_and_evolve(recent_chat, client)

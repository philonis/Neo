import streamlit as st
import json
from llm_client import LLMClient
from core import SkillManager, ReActAgent, TaskPlanner, VectorMemory
from tools.soul_skill import SoulSkill

st.set_page_config(
    page_title="Neo 智能助手", 
    page_icon="🧠", 
    layout="centered",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_resources():
    client = LLMClient()
    skill_manager = SkillManager()
    memory = VectorMemory()
    soul = SoulSkill()
    agent = ReActAgent(client, skill_manager, memory)
    planner = TaskPlanner(client, skill_manager)
    return client, skill_manager, memory, soul, agent, planner

client, skill_manager, memory, soul, agent, planner = init_resources()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0

if "show_trace" not in st.session_state:
    st.session_state.show_trace = False

with st.sidebar:
    st.header("⚙️ 设置")
    st.session_state.show_trace = st.checkbox("显示执行轨迹", value=False)
    
    st.divider()
    st.header("🔧 已加载技能")
    for skill_name in skill_manager.list_skills():
        info = skill_manager.get_skill_info(skill_name)
        if info:
            desc = info["schema"].get("function", {}).get("description", "")[:40]
            st.caption(f"**{skill_name}**: {desc}...")
    
    st.divider()
    st.header("📊 记忆统计")
    stats = memory.get_stats()
    st.metric("短期记忆", stats["short_term_count"])
    st.metric("长期记忆", stats["long_term_count"])
    st.metric("索引关键词", stats["index_keywords"])

st.title("🧠 Neo 智能助手")
st.caption("基于 ReAct 架构 | 原生 Function Calling | 智能记忆系统")

for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            if message["role"] == "assistant" and "trace" in message:
                with st.expander("📋 执行轨迹", expanded=False):
                    for item in message["trace"]:
                        st.write(f"**步骤 {item['iteration']}**: 调用 `{item['tool']}`")
                        if "error" in item.get("result", {}):
                            st.error(f"❌ {item['result']['error']}")
                        else:
                            st.success("✅ 执行成功")

if prompt := st.chat_input("请输入指令..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        progress_placeholder = st.empty()
        
        def on_progress(stage: str, message: str):
            icons = {
                "thinking": "🧠",
                "action": "⚡",
                "observation": "👁️"
            }
            icon = icons.get(stage, "▶️")
            progress_placeholder.info(f"{icon} {message}")
        
        progress_placeholder.info("🧠 正在思考...")
        
        context = [m for m in st.session_state.messages[:-1] if m["role"] in ["user", "assistant"]]
        
        result = agent.run(prompt, context=context, on_progress=on_progress)
        
        progress_placeholder.empty()
        
        if result["success"]:
            final_response = result["response"]
            st.markdown(final_response)
            
            if st.session_state.show_trace and result.get("trace"):
                with st.expander("📋 执行轨迹", expanded=False):
                    for item in result["trace"]:
                        st.write(f"**步骤 {item['iteration']}**: 调用 `{item['tool']}`")
                        st.json(item["args"])
                        if "error" in item.get("result", {}):
                            st.error(f"❌ {item['result']['error']}")
                        else:
                            st.success("✅ 执行成功")
                            with st.expander("查看结果"):
                                st.json(item["result"])
        else:
            final_response = f"抱歉，任务执行遇到问题: {result['response']}"
            st.error(final_response)
        
        message_entry = {
            "role": "assistant", 
            "content": final_response
        }
        if result.get("trace"):
            message_entry["trace"] = result["trace"]
        
        st.session_state.messages.append(message_entry)
        
        memory.add_interaction(
            user_input=prompt,
            assistant_response=final_response,
            tool_calls=[{"name": t["tool"], "args": t["args"]} for t in result.get("trace", [])]
        )
        
        st.session_state.interaction_count += 1
        
        if st.session_state.interaction_count % 10 == 0:
            with st.spinner("🧘 正在压缩记忆..."):
                memory.compress(client)
            
            recent_chat = memory.get_context_for_prompt("最近的对话")
            soul.reflect_and_evolve(recent_chat, client)

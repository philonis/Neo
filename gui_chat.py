import streamlit as st
from llm_client import LLMClient
from tools.notes_skill import NotesSkill
from tools.memory_skill import PersonalMemorySkill
import json

# 1. 页面基础配置
st.set_page_config(page_title="本地智能助手", page_icon="🤖", layout="centered")

# 2. 初始化资源 (使用 st.cache_resource 确保全局只加载一次)
@st.cache_resource
def init_resources():
    client = LLMClient()
    memory = PersonalMemorySkill()
    return client, memory

client, memory = init_resources()

# 注册工具
available_functions = {
    "notes_operator": NotesSkill.run,
}
tools_schema = [NotesSkill.get_tool_definition()]

# 3. 初始化 Session State (对话历史)
# 这里的 messages 是发送给 LLM 的完整历史
if "messages" not in st.session_state:
    # 加载记忆上下文
    base_system_prompt = "你是一个运行在用户 macOS 上的本地助手。你可以操作备忘录等本地应用。"
    memory_context = memory.load_context()
    
    st.session_state.messages = [
        {"role": "system", "content": base_system_prompt + memory_context}
    ]
    
    # 历史聊天记录 (仅用于页面显示，不包含 System Prompt)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

# 4. 页面标题
st.title("🤖 本地智能助手")
st.caption("支持备忘录操作 & 长期记忆 | Powered by Streamlit")

# 5. 显示历史聊天记录 (页面刷新时渲染)
for message in st.session_state.chat_history:
    # 过滤掉 tool 和 system 消息，只显示 user 和 assistant
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 6. 处理用户输入
if prompt := st.chat_input("请输入指令..."):
    # --- 显示用户消息 ---
    st.chat_message("user").markdown(prompt)
    
    # 添加到历史记录
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # --- 调用 LLM ---
    with st.chat_message("assistant"):
        # 创建一个空的占位符，用于流式/逐步显示内容
        message_placeholder = st.empty()
        message_placeholder.markdown("思考中...")

        # 1. 第一次调用 LLM
        response = client.chat(st.session_state.messages, tools=tools_schema)
        
        if not response or "choices" not in response:
            message_placeholder.markdown("❌ 连接失败，请检查 API Key 或网络。")
            st.stop()

        assistant_message = response["choices"][0]["message"]
        final_reply_content = ""

        # 2. 处理工具调用
        if assistant_message.get("tool_calls"):
            # 必须把 LLM 的工具调用意图加入历史，否则会断片
            st.session_state.messages.append(assistant_message)
            
            # 遍历工具调用
            for tool_call in assistant_message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args_str = tool_call["function"]["arguments"]
                
                # 显示工具调用状态 (比 CLI 更优雅的方式)
                with st.status(f"🔧 正在执行工具: {func_name}...", expanded=False) as status:
                    st.write(f"参数: {func_args_str}")
                    
                    if func_name in available_functions:
                        func_args = json.loads(func_args_str)
                        tool_result = available_functions[func_name](func_args)
                        st.write(f"结果: {tool_result}")
                        status.update(label=f"✅ 工具 {func_name} 执行完毕", state="complete")
                        
                        # 将结果回传给 LLM
                        st.session_state.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": func_name,
                            "content": json.dumps(tool_result, ensure_ascii=False)
                        })

            # 3. 第二次调用 LLM (生成最终回复)
            message_placeholder.markdown("正在组织语言...")
            final_response = client.chat(st.session_state.messages, tools=tools_schema)
            
            if final_response:
                final_reply_content = final_response["choices"][0]["message"]["content"]
            else:
                final_reply_content = "工具执行完毕，但生成回复失败。"
        
        else:
            # 直接回复
            final_reply_content = assistant_message.get("content", " ")

        # --- 最终渲染 ---
        message_placeholder.markdown(final_reply_content)
        
        # 更新历史
        st.session_state.messages.append({"role": "assistant", "content": final_reply_content})
        st.session_state.chat_history.append({"role": "assistant", "content": final_reply_content})

        # --- 记忆固化 ---
        if final_reply_content:
            memory.record_interaction(prompt, final_reply_content, client)

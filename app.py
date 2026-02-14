import streamlit as st
import json
import re
from typing import Optional, Dict, Any, List
from llm_client import LLMClient
from core import SkillManager, ReActAgent, TaskPlanner, VectorMemory
from tools.soul_skill import SoulSkill

st.set_page_config(
    page_title="Neo 智能助手", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_rich_content(content: str):
    image_patterns = [
        r'!\[([^\]]*)\]\(([^)]+)\)',
        r'(https?://[^\s<>"{}|\\^`\[\]]+\.(?:jpg|jpeg|png|gif|webp|svg|bmp))',
    ]
    images = []
    for pattern in image_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                alt, url = match
                images.append((alt, url))
            else:
                images.append(('', match))
    
    url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
    links = re.findall(url_pattern, content)
    
    st.markdown(content)
    
    show_images = st.session_state.get('show_images', True)
    if images and show_images:
        st.divider()
        st.subheader("🖼️ 相关图片")
        cols = st.columns(min(len(images), 3))
        for idx, (alt, url) in enumerate(images[:6]):
            with cols[idx % 3]:
                try:
                    st.image(url, caption=alt if alt else None, use_container_width=True)
                except Exception:
                    st.caption(f"📷 {alt}: {url}")
    
    return images, links

def render_map_if_needed(content: str, result_data: Optional[Dict] = None):
    show_maps = st.session_state.get('show_maps', True)
    if not show_maps:
        return False
    
    map_keywords = ['超市', '商店', '位置', '地址', '地点', '附近', 'supermarket', 'location', 'address']
    
    has_location_info = any(kw in content.lower() for kw in map_keywords)
    
    if result_data and isinstance(result_data, dict):
        if 'latitude' in result_data and 'longitude' in result_data:
            lat = result_data['latitude']
            lon = result_data['longitude']
            name = result_data.get('name', '目标位置')
            
            st.divider()
            st.subheader("🗺️ 位置地图")
            
            map_data = {
                'lat': [lat],
                'lon': [lon],
                'name': [name]
            }
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.map(map_data, latitude='lat', longitude='lon', size=20, color='#FF4444')
            with col2:
                st.metric("📍 纬度", f"{lat:.6f}")
                st.metric("📍 经度", f"{lon:.6f}")
                st.info(f"**{name}**")
            
            return True
        
        if 'locations' in result_data and isinstance(result_data['locations'], list):
            locations = result_data['locations']
            if locations and 'latitude' in locations[0]:
                st.divider()
                st.subheader("🗺️ 位置地图")
                
                lats = []
                lons = []
                names = []
                for loc in locations:
                    if 'latitude' in loc and 'longitude' in loc:
                        lats.append(loc['latitude'])
                        lons.append(loc['longitude'])
                        names.append(loc.get('name', '未知'))
                
                if lats:
                    map_data = {
                        'lat': lats,
                        'lon': lons,
                        'name': names
                    }
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.map(map_data, latitude='lat', longitude='lon', size=15, color='#4CAF50')
                    with col2:
                        st.caption("**📍 所有位置**")
                        for i, name in enumerate(names[:5]):
                            st.caption(f"{i+1}. {name}")
                        if len(names) > 5:
                            st.caption(f"... 还有 {len(names) - 5} 个位置")
                    
                    return True
    
    return False

def render_data_visualization(result_data: Optional[Dict] = None):
    if not result_data or not isinstance(result_data, dict):
        return False
    
    chart_data = None
    
    if 'prices' in result_data and isinstance(result_data['prices'], list):
        prices = result_data['prices']
        if prices and isinstance(prices[0], dict) and 'price' in prices[0]:
            import pandas as pd
            df = pd.DataFrame(prices)
            if 'price' in df.columns and 'name' in df.columns:
                st.divider()
                st.subheader("📊 价格对比")
                st.bar_chart(df.set_index('name')['price'])
                return True
    
    if 'items' in result_data and isinstance(result_data['items'], list):
        items = result_data['items']
        if len(items) > 3:
            st.divider()
            st.subheader("📋 数据列表")
            import pandas as pd
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True)
            return True
    
    return False

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
    st.markdown("""
    <style>
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.expander("⚙️ 设置", expanded=False):
        st.session_state.show_trace = st.checkbox("显示执行轨迹", value=False)
        st.session_state.show_images = st.checkbox("自动显示图片", value=True)
        st.session_state.show_maps = st.checkbox("显示地图", value=True)
    
    st.divider()
    with st.expander("🔧 已加载技能", expanded=False):
        skills = skill_manager.list_skills()
        st.metric("技能总数", len(skills))
        for skill_name in skills:
            info = skill_manager.get_skill_info(skill_name)
            if info:
                desc = info["schema"].get("function", {}).get("description", "")[:50]
                st.caption(f"✦ **{skill_name}**")
                st.caption(f"  {desc}...")
    
    st.divider()
    with st.expander("📊 记忆统计", expanded=True):
        stats = memory.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("短期记忆", stats["short_term_count"])
            st.metric("索引关键词", stats["index_keywords"])
        with col2:
            st.metric("长期记忆", stats["long_term_count"])
            st.metric("交互次数", st.session_state.interaction_count)
    
    st.divider()
    with st.expander("💡 使用提示", expanded=False):
        st.caption("• 询问位置信息可显示地图")
        st.caption("• 发送图片链接可自动展示")
        st.caption("• 查询价格可显示对比图表")
        st.caption("• 勾选执行轨迹查看详情")

st.title("🧠 Neo 智能助手")
st.caption("基于 ReAct 架构 | 原生 Function Calling | 智能记忆系统")

for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            render_rich_content(message["content"])
            
            if message["role"] == "assistant":
                if "result_data" in message and message["result_data"]:
                    render_map_if_needed(message["content"], message["result_data"])
                    render_data_visualization(message["result_data"])
                
                if "trace" in message:
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
            render_rich_content(final_response)
            
            result_data = None
            if result.get("trace"):
                for item in result["trace"]:
                    if "result" in item and isinstance(item["result"], dict):
                        result_data = item["result"]
                        break
            
            if result_data:
                render_map_if_needed(final_response, result_data)
                render_data_visualization(result_data)
            
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
            "content": final_response,
            "result_data": result_data if result.get("success") else None
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

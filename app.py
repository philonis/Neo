import streamlit as st
import json
import re
import time
from typing import Optional, Dict, Any, List
from llm_client import LLMClient
from core import SkillManager, ReActAgent, TaskPlanner, VectorMemory
from core.message_sync import MessageSyncService, get_sync_service
from tools.soul_skill import SoulSkill

st.set_page_config(
    page_title="Neo 智能助手", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_audio_players(content: str):
    show_audio = st.session_state.get('show_audio', True)
    if not show_audio:
        return []
    
    audio_patterns = [
        (r'(https?://[^\s<>"{}|\\^`\[\]]+\.(?:mp3|wav|ogg|m4a|aac|flac|wma))', 'direct'),
        (r'(https?://[^\s<>"{}|\\^`\[\]]+\.podbean\.com[^\s]*)', 'podbean'),
        (r'(https?://[^\s<>"{}|\\^`\[\]]+\.buzzsprout\.com[^\s]*)', 'buzzsprout'),
        (r'(https?://open\.spotify\.com/episode/([a-zA-Z0-9]+))', 'spotify'),
        (r'(https?://podcasts\.apple\.com/[^\s]+)', 'apple'),
        (r'(https?://www\.soundcloud\.com/[^\s]+)', 'soundcloud'),
    ]
    
    audio_items = []
    for pattern, audio_type in audio_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                url = match[0] if len(match) > 1 else match
                audio_id = match[1] if len(match) > 1 else None
            else:
                url = match
                audio_id = None
            audio_items.append((url, audio_type, audio_id))
    
    if audio_items:
        st.divider()
        st.subheader("🎵 音频播放器")
        
        for url, audio_type, audio_id in audio_items[:3]:
            with st.container():
                if audio_type == 'direct':
                    try:
                        st.audio(url, format="audio/mpeg")
                        st.caption(f"🎧 {url.split('/')[-1][:50]}")
                    except Exception:
                        st.caption(f"🎵 [音频文件]({url})")
                
                elif audio_type == 'spotify':
                    if audio_id:
                        st.markdown(f"""
                        <iframe src="https://open.spotify.com/embed/episode/{audio_id}" 
                                width="100%" height="152" frameborder="0" 
                                allowtransparency="true" allow="encrypted-media">
                        </iframe>
                        """, unsafe_allow_html=True)
                
                elif audio_type == 'apple':
                    st.markdown(f"""
                    <iframe allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" 
                            frameborder="0" height="175" 
                            style="width:100%;overflow:hidden;border-radius:10px;" 
                            sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation"
                            src="{url}">
                    </iframe>
                    """, unsafe_allow_html=True)
                
                elif audio_type in ['podbean', 'buzzsprout']:
                    try:
                        st.audio(url, format="audio/mpeg")
                        st.caption(f"🎙️ 播客音频")
                    except Exception:
                        st.markdown(f"🎙️ [播客链接]({url})")
                
                elif audio_type == 'soundcloud':
                    st.markdown(f"""
                    <iframe width="100%" height="166" scrolling="no" frameborder="no" 
                            src="https://w.soundcloud.com/player/?url={url}&color=%23ff5500&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false">
                    </iframe>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
    
    return audio_items

def render_weather_card(content: str, result_data: Optional[Dict] = None):
    weather_keywords = ['天气', '气温', '温度', 'weather', 'temperature', '晴', '雨', '阴', '雪', '多云']
    
    if not any(kw in content.lower() for kw in weather_keywords):
        return False
    
    if result_data and isinstance(result_data, dict):
        if 'temperature' in result_data or 'weather' in result_data:
            st.divider()
            st.subheader("🌤️ 天气信息")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'temperature' in result_data:
                    temp = result_data['temperature']
                    if isinstance(temp, (int, float)):
                        st.metric("🌡️ 温度", f"{temp}°C")
                    else:
                        st.metric("🌡️ 温度", str(temp))
                elif 'temp' in result_data:
                    st.metric("🌡️ 温度", result_data['temp'])
            
            with col2:
                if 'weather' in result_data:
                    weather = result_data['weather']
                    weather_emoji = {
                        '晴': '☀️', 'sunny': '☀️', 'clear': '☀️',
                        '雨': '🌧️', 'rain': '🌧️', 'rainy': '🌧️',
                        '阴': '☁️', 'cloudy': '☁️', 'overcast': '☁️',
                        '雪': '❄️', 'snow': '❄️', 'snowy': '❄️',
                        '多云': '⛅', 'partly cloudy': '⛅',
                    }
                    emoji = weather_emoji.get(weather.lower(), '🌤️')
                    st.metric("天气", f"{emoji} {weather}")
                elif 'condition' in result_data:
                    st.metric("天气状况", result_data['condition'])
            
            with col3:
                if 'humidity' in result_data:
                    st.metric("💧 湿度", f"{result_data['humidity']}%")
                elif 'wind' in result_data:
                    st.metric("💨 风力", result_data['wind'])
                elif 'city' in result_data:
                    st.metric("📍 城市", result_data['city'])
            
            if 'description' in result_data:
                st.info(result_data['description'])
            
            return True
    
    import re
    temp_match = re.search(r'(\d+)\s*[°度]?\s*[Cc]?', content)
    weather_match = re.search(r'(晴|雨|阴|雪|多云|sunny|rainy|cloudy|snow)', content, re.IGNORECASE)
    city_match = re.search(r'([\u4e00-\u9fa5]{2,4})\s*(?:的)?天气', content)
    
    if temp_match or weather_match:
        st.divider()
        st.subheader("🌤️ 天气信息")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if temp_match:
                temp = temp_match.group(1)
                st.metric("🌡️ 温度", f"{temp}°C")
        
        with col2:
            if weather_match:
                weather = weather_match.group(1)
                weather_emoji = {
                    '晴': '☀️', 'sunny': '☀️',
                    '雨': '🌧️', 'rainy': '🌧️',
                    '阴': '☁️', 'cloudy': '☁️',
                    '雪': '❄️', 'snow': '❄️',
                    '多云': '⛅',
                }
                emoji = weather_emoji.get(weather.lower(), '🌤️')
                st.metric("天气", f"{emoji} {weather}")
        
        if city_match:
            st.caption(f"📍 {city_match.group(1)}")
        
        return True
    
    return False


def render_news_list(content: str, result_data: Optional[Dict] = None):
    news_keywords = ['新闻', '资讯', '头条', 'news', 'headline']
    
    if not any(kw in content.lower() for kw in news_keywords):
        return False
    
    if result_data and isinstance(result_data, dict):
        items = None
        if 'news' in result_data:
            items = result_data['news']
        elif 'items' in result_data:
            items = result_data['items']
        elif 'headlines' in result_data:
            items = result_data['headlines']
        
        if items and isinstance(items, list) and len(items) > 0:
            st.divider()
            st.subheader("📰 新闻资讯")
            
            for i, item in enumerate(items[:5]):
                if isinstance(item, dict):
                    title = item.get('title', item.get('headline', ''))
                    source = item.get('source', item.get('author', ''))
                    url = item.get('url', item.get('link', ''))
                    date = item.get('date', item.get('published', ''))
                    
                    with st.container():
                        st.markdown(f"**{i+1}. {title}**")
                        if source:
                            st.caption(f"📰 {source}" + (f" | 📅 {date}" if date else ""))
                        if url:
                            st.markdown(f"[查看详情]({url})")
                        st.markdown("---")
                elif isinstance(item, str):
                    st.markdown(f"**{i+1}.** {item}")
            
            return True
    
    return False


def render_price_comparison(content: str, result_data: Optional[Dict] = None):
    price_keywords = ['价格', '多少钱', '比价', 'price', 'cost']
    
    if not any(kw in content.lower() for kw in price_keywords):
        return False
    
    if result_data and isinstance(result_data, dict):
        prices = result_data.get('prices', result_data.get('items', []))
        
        if prices and isinstance(prices, list) and len(prices) > 0:
            st.divider()
            st.subheader("💰 价格对比")
            
            for item in prices[:5]:
                if isinstance(item, dict):
                    name = item.get('name', item.get('product', ''))
                    price = item.get('price', item.get('cost', 0))
                    source = item.get('source', item.get('store', ''))
                    
                    col1, col2, col3 = st.columns([3, 2, 2])
                    with col1:
                        st.write(f"**{name}**")
                    with col2:
                        if isinstance(price, (int, float)):
                            st.metric("价格", f"¥{price}")
                        else:
                            st.write(price)
                    with col3:
                        if source:
                            st.caption(f"📍 {source}")
            
            return True
    
    return False


def render_smart_content(content: str, result_data: Optional[Dict] = None):
    rendered = False
    
    if render_weather_card(content, result_data):
        rendered = True
    
    if render_news_list(content, result_data):
        rendered = True
    
    if render_price_comparison(content, result_data):
        rendered = True
    
    if render_map_if_needed(content, result_data):
        rendered = True
    
    if render_data_visualization(result_data):
        rendered = True
    
    return rendered


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
    
    render_audio_players(content)
    
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
    
    sync_service = get_sync_service()
    sync_service.set_agent(agent)
    
    return client, skill_manager, memory, soul, agent, planner, sync_service

client, skill_manager, memory, soul, agent, planner, sync_service = init_resources()

try:
    from agent_skills.telegram_bot import init_telegram_service, TelegramService
    telegram_service = init_telegram_service(agent)
    if telegram_service:
        sync_service.set_telegram_service(telegram_service)
        
        def handle_telegram_message(chat_id: str, text: str, username: str) -> None:
            response = sync_service.process_telegram_message(chat_id, text, username)
            telegram_service.send_rich_message(response, chat_id)
        
        telegram_service.set_message_handler(handle_telegram_message)
except Exception as e:
    print(f"Telegram服务初始化跳过: {e}")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0

if "show_trace" not in st.session_state:
    st.session_state.show_trace = False

if "show_logs" not in st.session_state:
    st.session_state.show_logs = False

if "current_logs" not in st.session_state:
    st.session_state.current_logs = []

if "sync_to_telegram" not in st.session_state:
    st.session_state.sync_to_telegram = True

if "last_sync_timestamp" not in st.session_state:
    st.session_state.last_sync_timestamp = 0

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 5

if "pending_plan" not in st.session_state:
    st.session_state.pending_plan = None

if "plan_confirmed" not in st.session_state:
    st.session_state.plan_confirmed = False

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
        st.session_state.show_logs = st.checkbox("显示LLM通信日志", value=False)
        st.session_state.show_images = st.checkbox("自动显示图片", value=True)
        st.session_state.show_maps = st.checkbox("显示地图", value=True)
        st.session_state.show_audio = st.checkbox("自动渲染音频播放器", value=True)
        st.session_state.sync_to_telegram = st.checkbox("同步消息到 Telegram", value=True)
    
    st.divider()
    
    with st.expander("📱 Telegram 同步", expanded=False):
        sync_stats = sync_service.get_stats()
        if sync_stats['telegram_connected']:
            st.success("✅ Telegram 已连接")
        else:
            st.warning("⚠️ Telegram 未连接")
        
        st.metric("总消息数", sync_stats['total_messages'])
        
        source_dist = sync_stats['source_distribution']
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Web 消息", source_dist.get('web', 0))
        with col2:
            st.metric("Telegram 消息", source_dist.get('telegram', 0))
        
        if st.button("🔄 刷新同步消息"):
            st.session_state.last_sync_timestamp = 0
            st.rerun()
        
        if st.button("🗑️ 清空同步消息"):
            sync_service.clear_messages()
            st.rerun()
        
        st.divider()
        st.session_state.auto_refresh = st.checkbox("自动刷新", value=True)
        st.session_state.refresh_interval = st.slider("刷新间隔(秒)", 3, 30, st.session_state.refresh_interval)
        
        if st.session_state.auto_refresh:
            time.sleep(0.1)
            if 'refresh_counter' not in st.session_state:
                st.session_state.refresh_counter = 0
            st.session_state.refresh_counter += 1
            
            st.markdown(f"""
            <script>
            setTimeout(function() {{
                window.location.reload();
            }}, {st.session_state.refresh_interval * 1000});
            </script>
            """, unsafe_allow_html=True)
            st.caption(f"⏱️ {st.session_state.refresh_interval}秒后自动刷新")
    
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
        st.caption("• 天气查询会显示精美天气卡片")
        st.caption("• 新闻资讯会自动列表展示")
        st.caption("• 价格对比会显示对比表格")
        st.caption("• 位置信息可显示地图")
        st.caption("• 勾选LLM日志查看通信细节")

st.title("🧠 Neo 智能助手")
st.caption("基于 ReAct 架构 | 原生 Function Calling | 智能记忆系统 | Telegram 同步")

synced_messages = sync_service.get_messages(limit=20, since_timestamp=st.session_state.last_sync_timestamp)
telegram_messages = [m for m in synced_messages if m.get('source') == 'telegram']

if telegram_messages:
    with st.expander("📱 Telegram 消息同步", expanded=True):
        for msg in telegram_messages:
            source_icon = "📱" if msg['source'] == 'telegram' else "🌐"
            type_icon = "👤" if msg['type'] == 'user' else "🤖"
            
            timestamp_str = time.strftime('%H:%M:%S', time.localtime(msg['timestamp']))
            
            if msg['type'] == 'user':
                st.markdown(f"**{source_icon} {type_icon} 用户** ({timestamp_str})")
            else:
                st.markdown(f"**{source_icon} {type_icon} 助手** ({timestamp_str})")
            
            st.markdown(f"{msg['content'][:500]}{'...' if len(msg['content']) > 500 else ''}")
            st.markdown("---")
        
        if telegram_messages:
            st.session_state.last_sync_timestamp = telegram_messages[-1]['timestamp']

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
    
    sync_service.add_user_message(prompt, source="web")
    
    is_plan_mode = prompt.strip().startswith("/plan")
    is_confirm = prompt.strip().lower() in ["/confirm", "/执行", "/确认", "确认执行", "执行"]
    is_cancel = prompt.strip().lower() in ["/cancel", "/取消", "/放弃", "取消执行", "放弃"]
    
    if is_plan_mode:
        with st.chat_message("assistant"):
            st.info("📋 **规划模式** - 正在生成行动计划...")
            
            plan_prompt = prompt.strip()[5:].strip() if len(prompt.strip()) > 5 else "请描述你想要完成的任务"
            
            if plan_prompt == "请描述你想要完成的任务":
                st.warning("请在 /plan 后描述你想要完成的任务，例如：`/plan 帮我分析最近一周的科技新闻`")
            else:
                plan_result = planner.create_plan(plan_prompt)
                
                if plan_result.get("success"):
                    plan = plan_result.get("plan", {})
                    st.session_state.pending_plan = plan
                    
                    st.markdown("## 📋 行动计划")
                    st.markdown(f"**目标**: {plan.get('goal', plan_prompt)}")
                    st.markdown("---")
                    
                    steps = plan.get("steps", [])
                    for i, step in enumerate(steps):
                        with st.container():
                            st.markdown(f"### 步骤 {i+1}: {step.get('action', '未知操作')}")
                            st.markdown(f"- **工具**: `{step.get('tool', '未指定')}`")
                            st.markdown(f"- **参数**: `{step.get('args', {})}`")
                            st.markdown(f"- **说明**: {step.get('description', '无说明')}")
                            st.markdown("---")
                    
                    st.info("💡 确认执行请输入 `/confirm`，取消请输入 `/cancel`，或继续讨论修改计划")
                else:
                    st.error(f"生成计划失败: {plan_result.get('error', '未知错误')}")
    
    elif is_confirm and st.session_state.pending_plan:
        with st.chat_message("assistant"):
            st.success("✅ 开始执行计划...")
            
            plan = st.session_state.pending_plan
            steps = plan.get("steps", [])
            results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, step in enumerate(steps):
                status_text.info(f"执行步骤 {i+1}/{len(steps)}: {step.get('action', '')}")
                
                tool_name = step.get("tool")
                tool_args = step.get("args", {})
                
                if skill_manager.has_skill(tool_name):
                    try:
                        step_result = skill_manager.execute_skill(tool_name, tool_args)
                        results.append({
                            "step": i + 1,
                            "tool": tool_name,
                            "success": step_result.get("success", False),
                            "result": step_result
                        })
                    except Exception as e:
                        results.append({
                            "step": i + 1,
                            "tool": tool_name,
                            "success": False,
                            "error": str(e)
                        })
                else:
                    results.append({
                        "step": i + 1,
                        "tool": tool_name,
                        "success": False,
                        "error": f"工具 {tool_name} 不存在"
                    })
                
                progress_bar.progress((i + 1) / len(steps))
            
            status_text.empty()
            progress_bar.empty()
            
            st.markdown("## 📊 执行结果")
            for r in results:
                if r["success"]:
                    st.success(f"✅ 步骤 {r['step']}: `{r['tool']}` 执行成功")
                else:
                    st.error(f"❌ 步骤 {r['step']}: `{r['tool']}` 执行失败 - {r.get('error', '未知错误')}")
            
            st.session_state.pending_plan = None
            st.session_state.plan_confirmed = False
    
    elif is_cancel:
        with st.chat_message("assistant"):
            if st.session_state.pending_plan:
                st.warning("🚫 已取消执行计划")
                st.session_state.pending_plan = None
            else:
                st.info("没有待执行的计划")
    
    elif st.session_state.pending_plan and not is_plan_mode:
        with st.chat_message("assistant"):
            st.info("📝 正在根据您的反馈修改计划...")
            
            current_plan = st.session_state.pending_plan
            modify_result = planner.modify_plan(current_plan, prompt)
            
            if modify_result.get("success"):
                st.session_state.pending_plan = modify_result.get("plan")
                plan = st.session_state.pending_plan
                
                st.markdown("## 📋 修改后的行动计划")
                st.markdown(f"**目标**: {plan.get('goal', '')}")
                st.markdown("---")
                
                steps = plan.get("steps", [])
                for i, step in enumerate(steps):
                    with st.container():
                        st.markdown(f"### 步骤 {i+1}: {step.get('action', '未知操作')}")
                        st.markdown(f"- **工具**: `{step.get('tool', '未指定')}`")
                        st.markdown(f"- **参数**: `{step.get('args', {})}`")
                        st.markdown(f"- **说明**: {step.get('description', '无说明')}")
                        st.markdown("---")
                
                st.info("💡 确认执行请输入 `/confirm`，取消请输入 `/cancel`，或继续讨论修改计划")
            else:
                st.error(f"修改计划失败: {modify_result.get('error', '未知错误')}")
    
    else:
        with st.chat_message("assistant"):
            progress_placeholder = st.empty()
            logs_placeholder = st.empty() if st.session_state.show_logs else None
            
            st.session_state.current_logs = []
            
            def on_progress(stage: str, message: str):
                icons = {
                    "thinking": "🧠",
                    "action": "⚡",
                    "observation": "👁️"
                }
                icon = icons.get(stage, "▶️")
                progress_placeholder.info(f"{icon} {message}")
            
            def on_log(log_type: str, data: dict):
                log_entry = {"type": log_type, "data": data}
                st.session_state.current_logs.append(log_entry)
                
                if logs_placeholder and st.session_state.show_logs:
                    with logs_placeholder.container():
                        st.caption(f"📝 **{log_type}**")
                        st.json(data)
            
            progress_placeholder.info("🧠 正在思考...")
            
            context = [m for m in st.session_state.messages[:-1] if m["role"] in ["user", "assistant"]]
            
            result = agent.run(prompt, context=context, on_progress=on_progress, on_log=on_log)
        
        progress_placeholder.empty()
        if logs_placeholder:
            logs_placeholder.empty()
        
        if result["success"]:
            final_response = result["response"]
            render_rich_content(final_response)
            
            result_data = None
            if result.get("trace"):
                for item in result["trace"]:
                    if "result" in item and isinstance(item["result"], dict):
                        result_data = item["result"]
                        break
            
            render_smart_content(final_response, result_data)
            
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
            
            if st.session_state.show_logs and st.session_state.current_logs:
                with st.expander("📡 LLM通信日志", expanded=False):
                    for i, log in enumerate(st.session_state.current_logs):
                        if log["type"] == "request":
                            st.markdown(f"### 📤 请求 #{log['data'].get('iteration', i+1)}")
                            
                            st.markdown("**消息列表:**")
                            messages = log['data'].get('messages', [])
                            for j, msg in enumerate(messages):
                                role = msg.get('role', 'unknown')
                                role_icon = {'system': '⚙️', 'user': '👤', 'assistant': '🤖', 'tool': '🔧'}.get(role, '📄')
                                with st.container():
                                    st.caption(f"{role_icon} **{role}**")
                                    if msg.get('content_preview'):
                                        st.text(msg['content_preview'][:500])
                                    if msg.get('tool_calls'):
                                        st.caption(f"工具调用: {', '.join([tc['name'] for tc in msg['tool_calls']])}")
                                    if msg.get('tool_name'):
                                        st.caption(f"工具: {msg['tool_name']}")
                            
                            st.caption(f"**可用工具数:** {len(log['data'].get('tools_available', []))}")
                            
                        elif log["type"] == "response":
                            st.markdown(f"### 📥 响应 #{log['data'].get('iteration', i+1)}")
                            if log["data"].get("content"):
                                st.markdown("**LLM思考:**")
                                st.info(log["data"]["content"])
                            if log["data"].get("has_tool_calls"):
                                st.success(f"🔧 决定调用 {log['data'].get('tool_calls_count', 0)} 个工具")
                        
                        elif log["type"] == "tool_call":
                            st.markdown(f"### 🔧 工具调用")
                            st.markdown(f"**工具:** `{log['data'].get('tool')}`")
                            st.json(log['data'].get('args', {}))
                        
                        elif log["type"] == "tool_result":
                            status = "✅ 成功" if log["data"].get("success") else "❌ 失败"
                            st.markdown(f"### {status} 工具结果")
                            st.caption(f"**工具:** {log['data'].get('tool')}")
                            with st.expander("查看结果详情"):
                                st.json(log["data"])
                        
                        st.divider()
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
        
        sync_service.add_assistant_message(final_response, source="web")
        
        if st.session_state.sync_to_telegram and sync_service.telegram_service:
            try:
                sync_service.telegram_service.send_rich_message(
                    f"💬 [Web] 用户: {prompt}\n\n🤖 助手: {final_response}"
                )
            except Exception as e:
                print(f"同步到 Telegram 失败: {e}")
        
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

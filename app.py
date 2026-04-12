# app.py
import streamlit as st
import pandas as pd
from agent import TravelAgent
import time

# 页面基础配置
st.set_page_config(page_title="AI智能旅游平台", layout="wide")

# === 初始化Session State ===
if "agent" not in st.session_state:
    st.session_state.agent = TravelAgent()  # 现在Agent自带上下文
if "messages" not in st.session_state:
    st.session_state.messages = []
if "guide_expanded" not in st.session_state:
    st.session_state.guide_expanded = []
if "page" not in st.session_state:
    st.session_state.page = "chat"  # 默认进入聊天页

# 自定义样式
st.markdown("""
<style>
[data-testid="stHeader"], #MainMenu, header, footer { visibility: hidden; }
.user-msg { background: #f0f2f6; padding: 12px; border-radius: 8px; margin-bottom: 8px; }
.ai-msg { background: white; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #4b6cb7; }
.guide-card { background: white; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)


# 顶部Banner（所有页面都显示）
st.markdown("""
<div style="background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%); padding: 20px; border-radius: 12px; color: white; text-align: center; margin-bottom: 24px;">
    <h1>🧳 AI旅行规划师</h1>
    <p>智能行程规划 · 精选景点攻略</p>
</div>
""", unsafe_allow_html=True)

# ========== 顶部导航栏 ==========
col1, col2= st.columns(2)
with col1:
    if st.button("💬 智能对话", use_container_width=True, key="nav_chat"):
        st.session_state.page = "chat"
with col2:
    if st.button("📍 旅游攻略", use_container_width=True, key="nav_spots"):
        st.session_state.page = "spots"

st.divider() # 添加一条分隔线，让布局更清晰


# ========== 页面1：智能对话 ==========
if st.session_state.page == "chat":
    st.subheader("💬 与AI旅行助手对话")
    
    # 聊天容器
    chat_container = st.container(height=600, border=True)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"].replace("\n", "<br>"), unsafe_allow_html=True)
    
    # 用户输入
    if prompt := st.chat_input("例如：苏州三天游 / 杭州美食推荐"):
        # 添加用户消息到展示列表
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        chat_history_for_agent = st.session_state.messages[:-1] # 排除最后一条（即刚添加的用户消息）
        
        # 流式生成AI回复
        with chat_container:
            with st.chat_message("assistant"):
                thinking_placeholder = st.empty()
                thinking_placeholder.markdown("🤔 正在为您规划行程...")
                response_placeholder = st.empty()
                full_response = ""
                ctrip_link = None  # 用于存储解析出的链接
                try:
                    # 调用带上下文的流式接口
                    stream_generator = st.session_state.agent.chat_stream(prompt, chat_history_for_agent)
                    for chunk in stream_generator:
                        # ===== 新增：检查并处理特殊标记 =====
                        if chunk.startswith("__CTIP_LINK__"):
                            import json
                            payload_str = chunk[len("__CTIP_LINK__"):]
                            try:
                                payload = json.loads(payload_str)
                                ctrip_link = payload.get("link")
                            except json.JSONDecodeError:
                                pass # 如果解析失败，忽略
                            continue # 不将标记本身显示给用户
                        # ===================================
                        
                        full_response += chunk
                        response_placeholder.markdown(
                            full_response.replace("\n", "<br>"),
                            unsafe_allow_html=True
                        )
                        time.sleep(0.03)  # 控制打字速度
                except Exception as e:
                    error_msg = f"生成出错: {str(e)}"
                    response_placeholder.markdown(error_msg)
                    full_response = error_msg
                
                # ===== 新增：如果检测到链接，则渲染按钮 =====
                if ctrip_link:
                    st.markdown(f'<a href="{ctrip_link}" target="_blank" style="display: inline-block; background-color: #ff6700; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold;">✅ 立即前往携程预订</a>', unsafe_allow_html=True)
                # =========================================
                
                # 保存完整回复到展示列表（不包含链接标记）
                st.session_state.messages.append({"role": "assistant", "content": full_response})
    # 清空聊天（同时清空Agent的上下文）
    if st.button("🗑️ 清空聊天", key="clear_chat"):
        st.session_state.messages = []
        st.session_state.agent.clear_history()  # 清空Agent的上下文记忆
        st.rerun()

# ========== 页面2：景点信息 ==========
elif st.session_state.page == "spots":
    st.subheader("📖 精选旅行攻略（点击展开）")
    
    # 加载攻略数据
    try:
        guides_df = pd.read_csv("travel_guides.csv", encoding="utf-8")
    except FileNotFoundError:
        guides_df = pd.DataFrame(columns=["title", "location", "content"])
    except Exception as e:
        guides_df = pd.DataFrame(columns=["title", "location", "content"])
        st.error(f"加载攻略失败：{str(e)}")
    
    # 展示攻略
    guide_container = st.container(height=600, border=True)
    with guide_container:
        if guides_df.empty:
            st.info("暂无精选攻略数据")
        else:
            if len(st.session_state.guide_expanded) != len(guides_df):
                st.session_state.guide_expanded = [False] * len(guides_df)
            
            for idx, row in guides_df.iterrows():
                title = row.get("title", "未命名攻略")
                location = row.get("location", "未知地点")
                content = row.get("content", "暂无内容")
                
                if st.button(f"📍 {location} | {title}", key=f"guide_btn_{idx}", use_container_width=True):
                    st.session_state.guide_expanded[idx] = not st.session_state.guide_expanded[idx]
                
                if st.session_state.guide_expanded[idx]:
                    st.markdown(f"""
                    <div class="guide-card">
                        <div style="font-size:14px; line-height:1.6;">{content.replace("\n", "<br>")}</div>
                    </div>
                    """, unsafe_allow_html=True)
  
# 底部说明（所有页面都显示）
st.markdown("""
<div style="text-align:center; font-size:12px; color:#888; margin-top:20px;">
AI基于本地CSV行程库生成 | 攻略由人工整理维护
</div>
""", unsafe_allow_html=True)
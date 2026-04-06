import time
import os
import streamlit as st
from dotenv import load_dotenv

from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent

# --- PAGE CONFIG ---
st.set_page_config(page_title="👟 Tư Vấn Giày - Chatbot Mode", layout="wide")

# --- INITIALIZATION ---
@st.cache_resource
def load_components():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, None
    provider = OpenAIProvider(
        model_name=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        api_key=api_key
    )
    tools = [
        {"name": "search_shoes_by_brand", "description": "Tìm kiếm tất cả giày trong kho bằng tên hãng. Đầu vào: brand (str). Đầu ra: string danh sách SKU và tên giày."},
        {"name": "check_shoe_availability", "description": "Kiểm tra tồn kho thực tế. Đầu vào: sku (str). Đầu ra: số lượng đang có."},
        {"name": "check_price", "description": "Lấy giá tiền chính xác của giày. Đầu vào: sku (str). Đầu ra: Giá tiền (USD)."}
    ]
    agent = ReActAgent(llm=provider, tools=tools, max_steps=7)
    return provider, agent

provider, agent = load_components()

# --- UI STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- UI HEADER ---
st.sidebar.title("⚙️ Cấu hình Hệ thống")
max_loops = st.sidebar.slider("Cấu hình ReAct Loops (Max Steps)", min_value=2, max_value=10, value=5)
agent.max_steps = max_loops

st.title("👟 Shoe Consultant: Chatbot vs Agent")
st.markdown("Web Chatbot kết hợp tính năng so sánh (A/B Testing).")

if not provider:
    st.error("Missing OPENAI_API_KEY in .env file.")
    st.stop()

# --- RENDER CHAT HISTORY ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown("**Kết quả so sánh:**")
            col1, col2 = st.columns(2)
            with col1:
                st.info("🤖 **Baseline Chatbot**")
                st.markdown(msg["baseline_content"])
                st.caption(f"⚡ Latency: {msg['baseline_latency']}ms | 🪙 Tokens: {msg['baseline_tokens']}")
            with col2:
                status = "success" if "thất bại" not in msg["agent_content"].lower() else "error"
                if status == "success":
                    st.success("🧠 **ReAct Agent**")
                else:
                    st.error("🧠 **ReAct Agent** (Thất bại)")
                    
                st.markdown(msg["agent_content"])
                st.caption(f"⚡ Latency: {msg['agent_latency']}ms | 🔄 Steps: {msg['agent_steps']}")
                with st.expander("Logs logic nội bộ"):
                    st.code("\n".join(msg["agent_history"]))

# --- CHAT INPUT ---
if prompt := st.chat_input("Hãy hỏi tôi về giày Nike, Adidas, hoặc Puma..."):
    
    # 1. Hiển thị ngay câu hỏi của người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Xử lý câu trả lời song song trong Chat Message UI
    with st.chat_message("assistant"):
        col1, col2 = st.columns(2)
        system_prompt = "Bạn là chuyên gia tư vấn bán hàng. Hãy trả lời câu hỏi chuyên nghiệp."
        
        # === BASELINE CHATBOT ===
        with col1:
            st.info("🤖 **Baseline Chatbot**")
            with st.spinner("Đang sinh câu trả lời nhanh..."):
                try:
                    base_result = provider.generate(prompt=prompt, system_prompt=system_prompt)
                    st.markdown(base_result["content"])
                    st.caption(f"⚡ Latency: {base_result['latency_ms']}ms | 🪙 Tokens: {base_result['usage']['total_tokens']}")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
                    base_result = {"content": str(e), "latency_ms": 0, "usage": {"total_tokens": 0}}
                    
        # === REACT AGENT ===
        with col2:
            st.success("🧠 **ReAct Agent**")
            with st.spinner("Đang kích hoạt ReAct Loop & Tools..."):
                try:
                    # Clear history so context window is fresh for new chat turn
                    agent.history = [f"User Request: {prompt}"]
                    
                    start_time = time.time()
                    agent_answer = agent.run(prompt)
                    latency = int((time.time() - start_time) * 1000)
                    steps = max(0, len(agent.history) // 2)
                    
                    st.markdown(agent_answer)
                    st.caption(f"⚡ Latency: {latency}ms | 🔄 Steps: {steps}")
                    
                    with st.expander("Logs logic nội bộ"):
                        st.code("\n".join(agent.history))
                except Exception as e:
                    st.error(f"Lỗi: {e}")
                    agent_answer = str(e)
                    latency = 0
                    steps = 0

        # 3. Lưu vào lịch sử phiên (State)
        st.session_state.messages.append({
            "role": "assistant",
            "baseline_content": base_result["content"],
            "baseline_latency": base_result["latency_ms"],
            "baseline_tokens": base_result["usage"]["total_tokens"],
            "agent_content": agent_answer,
            "agent_latency": latency,
            "agent_steps": steps,
            "agent_history": list(agent.history)
        })

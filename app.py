import streamlit as st
import ollama
import json
import base64
import os
from history_manager import HistoryManager
from streamlit_mic_recorder import mic_recorder, speech_to_text
from rag_engine import RAGEngine

# Initialize History Manager
history_mgr = HistoryManager()

# Initialize RAG Engine
@st.cache_resource
def get_rag_engine():
    return RAGEngine()

rag_engine = get_rag_engine()

# Page configuration
st.set_page_config(page_title="Ollama", page_icon="🌌", layout="wide")

# Custom CSS for a high-end Premium feel
st.markdown("""
    <style>
    /* Global Styles */
    :root {
        --bg-main: #0B0E14;
        --accent-primary: #6366f1;
        --accent-secondary: #a855f7;
        --glass-bg: rgba(23, 28, 41, 0.4);
        --glass-border: rgba(255, 255, 255, 0.08);
        --text-main: #F1F5F9;
        --text-dim: #94A3B8;
    }

    .stApp {
        background-color: var(--bg-main);
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.1) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.1) 0px, transparent 50%);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    }

    h1, h2, h3, .stTitle {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-weight: 700 !important;
        background: linear-gradient(to right, #fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }

    /* Premium Chat Bubbles */
    .stChatMessage {
        border-radius: 20px !important;
        padding: 1.2rem !important;
        margin-bottom: 1rem !important;
        border: 1px solid var(--glass-border) !important;
        background: var(--glass-bg) !important;
        backdrop-filter: blur(15px) !important;
        max-width: 85%;
        transition: all 0.3s ease;
    }

    /* User Bubble: Right Aligned-ish feel */
    [data-testid="stChatMessageUser"] {
        background: rgba(99, 102, 241, 0.15) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
        margin-left: auto !important;
    }

    /* Assistant Bubble: Left Aligned feel */
    [data-testid="stChatMessageAssistant"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border-color: rgba(255, 255, 255, 0.05) !important;
        margin-right: auto !important;
    }

    .stChatMessage:hover {
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-2px);
    }

    /* Message Icons */
    [data-testid="stChatMessageAvatarAssistant"], [data-testid="stChatMessageAvatarUser"] {
        border-radius: 12px;
        border: 2px solid var(--glass-border);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(11, 14, 20, 0.95);
        border-right: 1px solid var(--glass-border);
        backdrop-filter: blur(10px);
    }

    /* Global Button Style (Text Buttons) */
    .stButton>button {
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid var(--glass-border) !important;
        color: var(--text-main) !important;
        padding: 0.6rem 1.2rem !important;
        width: 100% !important; /* Default to full width for sidebar/new conv */
        transition: all 0.3s ease;
    }

    /* Icon Buttons (Inside Columns) */
    [data-testid="column"] .stButton>button {
        width: 44px !important;
        height: 44px !important;
        min-width: 44px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 10px !important;
    }

    .stButton>button div p {
        margin: 0 !important;
        font-size: 1.2rem !important;
        line-height: 1 !important;
    }

    .stButton>button:hover {
        background: rgba(99, 102, 241, 0.1);
        border-color: var(--accent-primary);
        color: #fff;
        transform: translateY(-1px);
    }

    .stButton>button:active {
        transform: translateY(0px);
    }

    /* Input Area Styling */
    .stChatInputContainer {
        border-radius: 20px !important;
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid var(--glass-border) !important;
        backdrop-filter: blur(10px);
        padding: 4px !important;
    }

    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: var(--text-main) !important;
        padding-right: 110px !important;
        font-size: 1rem !important;
    }

    /* Ensure Streamlit Header/Toggle is visible but styled */
    /* Force Sidebar Toggle Visibility */
    [data-testid="stHeader"] {
        background: transparent !important;
        z-index: 1000 !important;
        display: block !important;
    }

    button[data-testid="stSidebarCollapseButton"], 
    button[aria-label="Open sidebar"], 
    button[aria-label="Close sidebar"],
    header button {
        background: #6366f1 !important;
        color: white !important;
        border-radius: 12px !important;
        width: 48px !important;
        height: 48px !important;
        min-width: 48px !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 10001 !important;
        opacity: 1 !important;
        visibility: visible !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* Target the SVG icon inside the toggle */
    header button svg, button[data-testid="stSidebarCollapseButton"] svg {
        fill: white !important;
        color: white !important;
        width: 28px !important;
        height: 28px !important;
    }

    /* Custom Mic Injection Styling */
    .mic-container {
        display: none;
        z-index: 10000;
    }
    
    .mic-container button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 1.6rem !important;
        cursor: pointer;
        opacity: 1.0;
        transition: all 0.3s ease;
    }
    
    .mic-container button:hover {
        opacity: 1;
        transform: scale(1.1);
        filter: drop-shadow(0 0 8px var(--accent-primary));
    }

    .injected-mic {
        position: absolute;
        right: 65px;
        bottom: 14px;
        z-index: 10001;
    }

    /* Animations */
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stChatMessage {
        animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Action bar styling */
    .chat-actions {
        display: flex;
        gap: 12px;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--glass-border);
    }
    </style>
""", unsafe_allow_html=True)

# Helper: Speak function
def speak_text_js(text, stop=False):
    if stop:
        st.components.v1.html("""
            <script>if(window.speechSynthesis){window.speechSynthesis.cancel();}</script>
        """, height=0)
    elif text:
        text_json = json.dumps(text)
        st.components.v1.html(f"""
            <script>
                if (window.speechSynthesis) {{
                    window.speechSynthesis.cancel();
                    var msg = new SpeechSynthesisUtterance({text_json});
                    msg.rate = 1.4;
                    msg.volume = 1.0;
                    var voices = window.speechSynthesis.getVoices();
                    var preferred = voices.find(v => v.name.includes("Google") || v.name.includes("Natural"));
                    if(preferred) msg.voice = preferred;
                    window.speechSynthesis.speak(msg);
                }}
            </script>
        """, height=0)

# Helper: Copy function
def copy_text(text):
    text_b64 = base64.b64encode(text.encode()).decode()
    st.components.v1.html(f"""
        <script>
            const text = atob("{text_b64}");
            navigator.clipboard.writeText(text);
        </script>
    """, height=0)

# ---------------------------------------------------------
# INITIALIZE STATE
# ---------------------------------------------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "session_id" not in st.session_state: st.session_state.session_id = history_mgr.generate_session_id()
if "voice_text" not in st.session_state: st.session_state.voice_text = ""
if "speaking_idx" not in st.session_state: st.session_state.speaking_idx = -1
if "text_to_speak" not in st.session_state: st.session_state.text_to_speak = None
if "rag_enabled" not in st.session_state: st.session_state.rag_enabled = False

# Sidebar Content
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 2.2rem; margin-bottom: 2rem;'>🤖 Ollama AI</h1>", unsafe_allow_html=True)
    
    if st.button("✨ New Conversation", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.session_id = history_mgr.generate_session_id()
        st.session_state.voice_text = ""
        st.session_state.speaking_idx = -1
        st.rerun()

    st.markdown("<p style='color: var(--text-dim); font-size: 0.8rem; margin-top: 2rem; margin-bottom: 0.5rem; font-weight: 600;'>HISTORY</p>", unsafe_allow_html=True)
    
    # Load and display sessions
    try:
        current_sessions = history_mgr.list_sessions()
    except Exception:
        current_sessions = []

    for s in current_sessions:
        s_id = s['id']
        col_n, col_d = st.columns([0.75, 0.25])
        with col_n:
            label = s_id[:15] + "..." if len(s_id) > 15 else s_id
            if st.button(f"💬 {label}", key=f"s_{s_id}", use_container_width=True):
                st.session_state.messages = history_mgr.load_session(s_id)
                st.session_state.session_id = s_id
                st.session_state.voice_text = ""
                st.rerun()
        with col_d:
            if st.button("🗑️", key=f"d_{s_id}", help="Delete"):
                history_mgr.delete_session(s_id)
                if st.session_state.session_id == s_id:
                    st.session_state.messages = []
                    st.session_state.session_id = history_mgr.generate_session_id()
                st.rerun()

    st.divider()
    
    # Model Selection
    try:
        available_models = [m['name'] for m in ollama.list()['models']]
        if not available_models: available_models = ["llama3.2"]
    except:
        available_models = ["llama3.2"]
    
    selected_model = st.selectbox("🧠 Model", available_models, index=0)

    # Export Feature
    if st.session_state.messages:
        st.markdown("<p style='color: var(--text-dim); font-size: 0.8rem; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 600;'>💾 EXPORT</p>", unsafe_allow_html=True)
        ex1, ex2 = st.columns(2)
        js_data = json.dumps(st.session_state.messages, indent=2)
        tx_data = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        with ex1:
            st.download_button("JSON", js_data, file_name=f"chat_{st.session_state.session_id}.json", use_container_width=True)
        with ex2:
            st.download_button("Text", tx_data, file_name=f"chat_{st.session_state.session_id}.txt", use_container_width=True)

    st.markdown("<p style='text-align: center; color: var(--text-dim); font-size: 0.7rem; margin-top: 3rem;'>Ollama AI v2.3</p>", unsafe_allow_html=True)

    st.divider()
    
    # Knowledge Base Section
    st.markdown("<p style='color: var(--text-dim); font-size: 0.8rem; margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 600;'>📚 KNOWLEDGE BASE</p>", unsafe_allow_html=True)
    
    st.session_state.rag_enabled = st.toggle("Enable RAG", value=st.session_state.rag_enabled)
    
    uploaded_files = st.file_uploader("Upload Docs (PDF/TXT)", type=["pdf", "txt"], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("📥 Process Knowledge"):
            with st.status("Processing documents...", expanded=True) as status:
                temp_paths = []
                for uploaded_file in uploaded_files:
                    # Save to a temporary file because LangChain loaders need paths
                    temp_dir = "temp_uploads"
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    
                    temp_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_paths.append(temp_path)
                    st.write(f"Reading {uploaded_file.name}...")

                num_splits = rag_engine.add_documents(temp_paths)
                
                # Cleanup temp files
                for p in temp_paths:
                    if os.path.exists(p):
                        os.remove(p)
                
                status.update(label=f"Done! Created {num_splits} text chunks.", state="complete")
                st.toast(f"Knowledge Base updated with {len(uploaded_files)} files!")

    if rag_engine.has_knowledge():
        if st.button("🗑️ Clear Knowledge Base", type="secondary"):
            rag_engine.clear_database()
            st.toast("Knowledge Base cleared!")
            st.rerun()

# ---------------------------------------------------------
# MAIN CHAT AREA
# ---------------------------------------------------------
# Logo / Toggle Backup Trigger
st.markdown("""
<div id="logo-trigger" style="position: fixed; top: 12px; left: 60px; z-index: 10002; cursor: pointer; transition: transform 0.2s;">
    <div style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));">
        <span style="font-size: 1.6rem;">🤖</span>
        <span style="background: linear-gradient(to right, #fff, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Ollama API</span>
    </div>
</div>
<script>
    const trigger = window.parent.document.getElementById('logo-trigger');
    trigger.onclick = function() {
        const btn = window.parent.document.querySelector('button[data-testid="stSidebarCollapseButton"]') || 
                    window.parent.document.querySelector('button[aria-label="Open sidebar"]') ||
                    window.parent.document.querySelector('button[aria-label="Close sidebar"]');
        if (btn) btn.click();
    };
    trigger.onmouseover = function() { trigger.style.transform = 'scale(1.05)'; };
    trigger.onmouseout = function() { trigger.style.transform = 'scale(1)'; };
</script>
""", unsafe_allow_html=True)

st.title("🤖 Ollama")
st.markdown(f"<p style='color: var(--text-dim); margin-top: -1rem; font-size: 0.9rem;'>Session: {st.session_state.session_id} | {selected_model}</p>", unsafe_allow_html=True)

# Message Container
chat_box = st.container()
with chat_box:
    for i, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])
            if role == "assistant":
                a_col1, a_col2, _ = st.columns([0.15, 0.15, 0.7])
                with a_col1:
                    if st.button("📋", key=f"cp_{i}", help="Copy"):
                        copy_text(msg["content"])
                        st.toast("Copied!")
                with a_col2:
                    is_active = st.session_state.speaking_idx == i
                    spk_icon = "⏹️" if is_active else "🔊"
                    if st.button(spk_icon, key=f"sp_{i}", help="Speak"):
                        if is_active:
                            st.session_state.speaking_idx = -1
                            st.session_state.text_to_speak = "STOP"
                        else:
                            st.session_state.speaking_idx = i
                            st.session_state.text_to_speak = msg["content"]
                        st.rerun()

# Mic Integration
with st.container():
    st.markdown('<div class="mic-container" id="mic-wrapper">', unsafe_allow_html=True)
    voice_key = f"voice_{st.session_state.session_id}_{len(st.session_state.messages)}"
    stt_res = speech_to_text(language='en', start_prompt="🎙️", stop_prompt="⏹️", just_once=True, key=voice_key)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.components.v1.html("""
        <script>
            function moveMic() {
                var mic = window.parent.document.getElementById('mic-wrapper');
                var input = window.parent.document.querySelector('[data-testid="stChatInput"]');
                if (mic && input) {
                    mic.style.display = 'block';
                    mic.classList.add('injected-mic');
                    input.appendChild(mic);
                }
            }
            setInterval(moveMic, 350);
        </script>
    """, height=0)

    if stt_res:
        st.session_state.voice_text = stt_res
        st.rerun()

# User Input Handling
prompt = ""
if st.session_state.voice_text:
    st.markdown("---")
    rev = st.text_area("Review your voice message:", value=st.session_state.voice_text, key="voice_review")
    b_col1, b_col2 = st.columns([0.2, 0.8])
    with b_col1:
        if st.button("🚀 Send", type="primary", use_container_width=True):
            prompt = rev
            st.session_state.voice_text = ""
    with b_col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.voice_text = ""
            st.rerun()
else:
    prompt = st.chat_input("Message Ollama...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    history_mgr.save_session(st.session_state.session_id, st.session_state.messages)
    
    with chat_box:
        with st.chat_message("user"): st.markdown(prompt)

    with chat_box:
        with st.chat_message("assistant"):
            thought = st.empty()
            thought.markdown("🤖 *Thinking...*")
            try:
                full_resp = ""
                
                # If RAG is enabled, get context
                context_prefix = ""
                if st.session_state.rag_enabled and rag_engine.has_knowledge():
                    with st.spinner("Searching knowledge base..."):
                        context = rag_engine.query(prompt)
                        if context:
                            context_str = "\n".join(context)
                            context_prefix = f"Using the following context from the knowledge base to answer the user's question:\n\n{context_str}\n\nUser Question: "
                
                # Prepare messages for Ollama (injecting context into the latest user message content)
                ollama_messages = []
                for m in st.session_state.messages[:-1]:
                    ollama_messages.append(m)
                
                # Update the last message with context for Ollama only
                last_msg = st.session_state.messages[-1].copy()
                if context_prefix:
                    last_msg["content"] = context_prefix + last_msg["content"]
                ollama_messages.append(last_msg)

                for chunk in ollama.chat(model=selected_model, messages=ollama_messages, stream=True):
                    full_resp += chunk['message']['content']
                    thought.markdown(full_resp + "▌")
                thought.markdown(full_resp)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
                st.session_state.speaking_idx = -1
                history_mgr.save_session(st.session_state.session_id, st.session_state.messages)
                st.rerun()
            except Exception as e:
                thought.error(f"Error: {e}")

# Apply Voice
if st.session_state.text_to_speak == "STOP":
    speak_text_js("", stop=True)
    st.session_state.text_to_speak = None
elif st.session_state.text_to_speak:
    speak_text_js(st.session_state.text_to_speak)
    st.session_state.text_to_speak = None

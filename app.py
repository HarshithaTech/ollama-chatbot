import streamlit as st
import ollama

# Page configuration
st.set_page_config(page_title="Ollama Premium Chat", page_icon="🤖", layout="wide")

# Custom CSS for a premium feel
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #1e1e2f 0%, #121212 100%);
        color: #ffffff;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .stChatInputContainer {
        border-top: 1px solid #333;
        padding-top: 20px;
    }
    .sidebar .sidebar-content {
        background-color: #1e1e2f;
    }
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        background: -webkit-linear-gradient(#eee, #333);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.title("⚙️ Settings")
    selected_model = st.selectbox("Select Model", ["llama3.2", "mistral", "phi3"], index=0)
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    st.info("💡 **Tip:** Ensure Ollama is running locally if you are on your machine.")

# Main Title
st.title("🤖 Ollama Premium Chat")
st.caption(f"Currently using: {selected_model}")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Ask me anything...")

if user_input:
    # Store and display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Bot response logic
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 *Thinking...*")
        
        try:
            response = ollama.chat(
                model=selected_model,
                messages=st.session_state.messages
            )
            bot_reply = response["message"]["content"]
            message_placeholder.markdown(bot_reply)
            
            # Store bot response
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
        except Exception as e:
            message_placeholder.error("🚨 **Connection Error**")
            st.warning("""
                **Could not connect to Ollama.**
                
                If you are running this on **Streamlit Cloud**, please note that it cannot connect to your local Ollama instance. 
                To fix this:
                1. Run the app **locally** using: `streamlit run app.py`
                2. Make sure Ollama is running on your computer.
                
                *Technical details:* """ + str(e))

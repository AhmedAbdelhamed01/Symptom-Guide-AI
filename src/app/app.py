"""
SymptoGuide AI: Smart Router + Category Search
Main Streamlit UI application.
"""

import streamlit as st
import os
import logging

from config import MedicalConfig
from llm_utils import set_mode, build_chain
from medical_logic import fast_emergency_check, classify_intent, enhance_query
from vector_db import load_vector_db, smart_category_search
from config import DIAGNOSIS_PROMPT

# ============================================================================
# 📝 LOGGING SETUP
# ============================================================================

def setup_logging():
    """Initialize logging to file and console."""
    os.makedirs(MedicalConfig.LOG_DIR, exist_ok=True)
    log_file_path = os.path.join(MedicalConfig.LOG_DIR, "session.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("SymptoGuide")


logger = setup_logging()

# ============================================================================
# 🖥️ PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title=MedicalConfig.PAGE_TITLE,
    page_icon=MedicalConfig.PAGE_ICON,
    layout="wide"
)

# Dark theme styling
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .stChatMessage { background-color: #161B22; border: 1px solid #30363D; border-radius: 10px; }
    h1, h2, h3 { color: #58A6FF !important; }
    p, li { color: #C9D1D9 !important; }
    .emergency-alert {
        background-color: #381315; color: #FF7B72; padding: 15px;
        border-radius: 8px; border: 1px solid #FFA198; border-left: 5px solid #FF7B72;
        font-weight: bold; margin-bottom: 20px;
    }
    .router-box {
        background-color: #0D1117; color: #79C0FF; padding: 8px;
        border-radius: 6px; border: 1px solid #1F6FEB; font-family: monospace; font-size: 0.85rem;
    }
    .source-box {
        background-color: #161B22; color: #8B949E; padding: 10px;
        border-radius: 6px; border-left: 3px solid #238636; margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title(f"{MedicalConfig.PAGE_ICON} {MedicalConfig.PAGE_TITLE}")
st.caption("Enterprise Medical Assistant | Intent-Aware RAG System")

# ============================================================================
# ⚙️ SIDEBAR SETTINGS
# ============================================================================

with st.sidebar:
    st.title("⚙️ Settings")
    mode = st.radio("AI Model:", ["Local (Ollama)", "Cloud (HuggingFace)"])
    set_mode(mode)
    
    if mode == "Cloud (HuggingFace)":
        hf_token = st.text_input("HF Token:", type="password")
        if hf_token:
            os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token
    
    st.divider()
    show_debug = st.checkbox("Show Logic (Router/Search)", value=True)
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# ============================================================================
# 📦 LOAD RESOURCES
# ============================================================================

try:
    vector_db = load_vector_db()
except Exception as e:
    st.error(f"Error loading resources: {e}")
    logger.error(f"Resource loading failed: {e}")
    st.stop()

# ============================================================================
# 💬 CHAT INTERFACE
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am SymptoGuide. How can I help you today?"}
    ]

# Display message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Chat input & processing
if user_input := st.chat_input("Describe your symptoms..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # --- STEP 1: EMERGENCY CHECK ---
            emergency_alert = fast_emergency_check(user_input)
            if emergency_alert:
                full_response = f"""
                <div class='emergency-alert'>
                    🚨 <b>EMERGENCY DETECTED: {emergency_alert}</b><br>
                    Please call 999 or go to the nearest Emergency Room immediately.<br>
                    Do not wait for an AI response.
                </div>
                """
                message_placeholder.markdown(full_response, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": "🚨 EMERGENCY ALERT TRIGGERED"})
                logger.critical(f"Emergency Triggered: {user_input}")
                st.stop()
            
            # --- STEP 2: INTENT CLASSIFICATION ---
            with st.spinner("🤔 Thinking..."):
                intent = classify_intent(user_input)
                if show_debug:
                    st.markdown(
                        f"<div class='router-box'>⚡ <b>Detected Intent:</b> {intent}</div>",
                        unsafe_allow_html=True
                    )
            
            # --- STEP 3: HANDLE BY INTENT ---
            if intent == "GREETING":
                full_response = "Hello! 👋 I am ready to help. Please tell me what symptoms you are experiencing (e.g., 'I have a headache')."
                message_placeholder.markdown(full_response)
            
            elif intent == "OFF_TOPIC":
                full_response = "I am a medical AI assistant. I cannot discuss that topic. Please ask me about medical symptoms."
                message_placeholder.markdown(full_response)
            
            elif intent == "VAGUE":
                full_response = "I understand you aren't feeling well, but I need more details. \n\n**Please tell me:**\n1. Where is the pain?\n2. How long have you had it?\n3. Are there other symptoms (fever, nausea)?"
                message_placeholder.markdown(full_response)
            
            elif intent == "SYMPTOM":
                # 1. Enhance Query
                with st.spinner("🔬 Analyzing medical terms..."):
                    enhanced_query = enhance_query(user_input)
                    if show_debug:
                        st.markdown(
                            f"<div class='router-box'>🔍 <b>Searching for:</b> {enhanced_query}</div>",
                            unsafe_allow_html=True
                        )
                
                # 2. Smart Search
                with st.spinner("📚 Retrieving Conditions, Medicines & Tests..."):
                    retrieved_docs = smart_category_search(vector_db, enhanced_query)
                    
                    if not retrieved_docs:
                        full_response = "I searched my database but found no matching records. Please describe your symptoms differently."
                        message_placeholder.markdown(full_response)
                        st.stop()
                    
                    context_text = ""
                    for doc in retrieved_docs:
                        category = doc.metadata.get('entity_type', 'General').upper()
                        name = doc.metadata.get('name', 'Unknown')
                        context_text += f"--- {category}: {name} ---\n{doc.page_content}\n\n"
                
                # 3. Generate Diagnosis
                with st.spinner("🩺 Generating advice..."):
                    diagnosis_chain = build_chain(DIAGNOSIS_PROMPT, temperature=0.2)
                    
                    for chunk in diagnosis_chain.stream({"input": user_input, "context": context_text}):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                    
                    # Display sources
                    with st.expander("📚 Referenced Medical Sources"):
                        for doc in retrieved_docs:
                            cat = doc.metadata.get('entity_type', 'Doc').upper()
                            name = doc.metadata.get('name', 'Unknown')
                            url = doc.metadata.get('url', '#')
                            snippet = doc.page_content[:200].replace('\n', ' ') + "..."
                            
                            html_content = f"""
                            <div class='source-box'>
                                <b>[{cat}] <a href='{url}' target='_blank' style='color: #58A6FF; text-decoration: none;'>{name} ↗</a></b><br>
                                <i>{snippet}</i>
                            </div>
                            """
                            st.markdown(html_content, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"System Error: {e}")
            logger.error(f"Error: {e}")
        
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})

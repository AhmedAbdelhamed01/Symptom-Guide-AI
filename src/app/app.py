"""
SymptoGuide AI: Smart Router + Category Search
Main Streamlit UI application.
"""

import streamlit as st
import os
import sys
import logging
from pathlib import Path
import json
from datetime import datetime

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.app.config import MedicalConfig, DIAGNOSIS_PROMPT
from src.app.llm_utils import set_mode, build_chain
from src.app.medical_logic import fast_emergency_check, classify_intent, enhance_query, detect_context_request, extract_symptoms_from_history
from src.app.vector_db import load_vector_db, smart_category_search

# ============================================================================
#  CHAT PERSISTENCE
# ============================================================================

CHAT_HISTORY_FILE = Path(MedicalConfig.LOG_DIR) / "chat_history.json"

def load_chat_history():
    """Load chat history from disk."""
    if CHAT_HISTORY_FILE.exists():
        try:
            with open(CHAT_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load chat history: {e}")
    return []

def save_chat_history(messages):
    """Save chat history to disk."""
    try:
        with open(CHAT_HISTORY_FILE, 'w') as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save chat history: {e}")

def format_chat_context(messages):
    """Format recent chat history as context for the LLM."""
    recent = messages[-6:] if len(messages) > 6 else messages  # last 3 exchanges
    context_lines = []
    for msg in recent:
        role = "User" if msg['role'] == "user" else "Assistant"
        content = msg['content'][:200] if len(msg['content']) > 200 else msg['content']
        context_lines.append(f"{role}: {content}")
    return "\n".join(context_lines)


def extract_all_symptoms(messages):
    """Extract all symptoms mentioned throughout the conversation."""
    return extract_symptoms_from_history(messages)

# ============================================================================
#  LOGGING SETUP
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
#  PAGE CONFIG
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
st.caption("Medical Assistant | Intent-Aware RAG System")

# ============================================================================
#  SIDEBAR SETTINGS
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
    show_debug = st.checkbox("Show Logic (Router/Search)", value=False)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            save_chat_history([])
            st.session_state['last_context'] = ""
            st.rerun()
    
    with col2:
        if st.button("💾 Save Chat"):
            save_chat_history(st.session_state.messages)
            st.success("Chat saved!")

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
#  CHAT INTERFACE
# ============================================================================

# Initialize session state
if "messages" not in st.session_state:
    # Load persisted chat history
    persisted = load_chat_history()
    if persisted:
        st.session_state.messages = persisted
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am SymptoGuide. How can I help you today?"}
        ]

if "last_context" not in st.session_state:
    st.session_state['last_context'] = ""

# Display message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Chat input - simple text input only
user_input = st.chat_input("Describe your symptoms or ask a question...")

if user_input:
    # Validate and clean input
    user_input = user_input.strip()
    if not user_input:
        st.warning("Please enter something.")
        st.stop()
    
    # Limit input length
    if len(user_input) > 500:
        st.warning("Input too long. Please use fewer than 500 characters.")
        st.stop()
    
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
                save_chat_history(st.session_state.messages)
                logger.critical(f"Emergency Triggered: {user_input}")
                st.stop()
            
            # --- STEP 2: INTENT CLASSIFICATION ---
            with st.spinner("🤔 Thinking..."):
                try:
                    intent = classify_intent(user_input)
                except Exception as e:
                    logger.warning(f"Intent classification failed: {e}")
                    intent = "SYMPTOM"  # default to symptom
                    
                if show_debug:
                    st.markdown(
                        f"<div class='router-box'>⚡ <b>Detected Intent:</b> {intent}</div>",
                        unsafe_allow_html=True
                    )
            
            # --- STEP 3: HANDLE BY INTENT ---
            
            # Check if user is asking about their chat history/previous symptoms
            is_context_request = detect_context_request(user_input)
            
            if intent == "GREETING":
                full_response = "Hello! 👋 I am ready to help. Please tell me what symptoms you are experiencing (e.g., 'I have a headache')."
                message_placeholder.markdown(full_response)
            
            elif intent == "OFF_TOPIC":
                full_response = "I am a medical AI assistant. I cannot discuss that topic. Please ask me about medical symptoms."
                message_placeholder.markdown(full_response)
            
            elif intent == "VAGUE":
                full_response = "I understand you aren't feeling well, but I need more details. 

**Please tell me:**\n1. Where is the pain/symptom?\n2. How long have you had it?\n3. Are there other symptoms (fever, nausea, etc.)?"
                message_placeholder.markdown(full_response)
            
            elif is_context_request:
                # User is asking to recap/summarize their previous symptoms
                st.info("📋 Reviewing your conversation history...")
                all_symptoms = extract_all_symptoms(st.session_state.messages)
                
                if "(No specific symptoms recorded" not in all_symptoms:
                    # Generate comprehensive response with all symptoms
                    with st.spinner("🩺 Analyzing all your symptoms..."):
                        try:
                            recent_chat = format_chat_context(st.session_state.messages[:-1])
                            context_aware_prompt = DIAGNOSIS_PROMPT + f"

IMPORTANT: User is asking you to summarize/recap all their symptoms from the conversation.\nAll symptoms found: {all_symptoms}"
                            diagnosis_chain = build_chain(context_aware_prompt, temperature=0.2)
                            
                            for chunk in diagnosis_chain.stream({"input": user_input, "context": all_symptoms, "recent_chat": recent_chat}):\n                                full_response += chunk\n                                message_placeholder.markdown(full_response + "▌")\n                            message_placeholder.markdown(full_response)\n                        except Exception as e:\n                            logger.error(f"Recap generation failed: {e}")\n                            full_response = f"Based on our conversation, I found: {all_symptoms}\\n\\nPlease consult a real healthcare provider for an accurate diagnosis."\n                            message_placeholder.markdown(full_response)\n                else:\n                    full_response = f"I don't have any symptom records from our conversation yet. {all_symptoms}\\n\\nPlease tell me what symptoms you're experiencing, and I'll help you."\n                    message_placeholder.markdown(full_response)\n            
            elif intent == "SYMPTOM":
                # 1. Enhance Query
                with st.spinner("🔬 Analyzing medical terms..."):
                    try:
                        enhanced_query = enhance_query(user_input)
                    except Exception as e:
                        logger.warning(f"Query enhancement failed: {e}")
                        enhanced_query = user_input  # fallback
                        
                    if show_debug:
                        st.markdown(
                            f"<div class='router-box'>🔍 <b>Searching for:</b> {enhanced_query}</div>",
                            unsafe_allow_html=True
                        )
                
                # 2. Smart Search
                with st.spinner("📚 Retrieving Medical Information..."):
                    try:
                        retrieved_with_scores = smart_category_search(vector_db, enhanced_query)
                    except Exception as e:
                        logger.error(f"Vector search failed: {e}")
                        retrieved_with_scores = []
                    
                    if not retrieved_with_scores:
                        full_response = "I searched my database but found no matching records. Could you describe your symptoms more specifically?"
                        message_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        save_chat_history(st.session_state.messages)
                        st.stop()
                    
                    # unpack docs and scores
                    docs, scores = zip(*retrieved_with_scores)
                    avg_score = sum(scores) / len(scores)
                    confidence = 1 / (1 + avg_score)
                    confidence_pct = int(confidence * 100)
                    
                    context_text = ""
                    for doc in docs:
                        category = doc.metadata.get('entity_type', 'General').upper()
                        name = doc.metadata.get('name', 'Unknown')
                        context_text += f"--- {category}: {name} ---\n{doc.page_content}

"
                
                # Display confidence
                st.info(f"🔎 Search confidence: {confidence_pct}%")
                
                # 3. Generate Diagnosis with chat history context
                with st.spinner("🩺 Generating advice..."):
                    try:
                        # Include recent chat history in the prompt
                        recent_chat = format_chat_context(st.session_state.messages[:-1])  # exclude current message
                        
                        diagnosis_chain = build_chain(DIAGNOSIS_PROMPT, temperature=0.2)
                        
                        for chunk in diagnosis_chain.stream({"input": user_input, "context": context_text, "recent_chat": recent_chat}):
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)
                    except Exception as e:
                        logger.error(f"Diagnosis generation failed: {e}")
                        full_response = "I encountered an error generating a response. Please try again or rephrase your question."
                        message_placeholder.markdown(full_response)
                    
                    # Display sources
                    with st.expander("📚 Referenced Medical Sources"):
                        for doc in docs:
                            try:
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
                                logger.warning(f"Could not display source: {e}")
        
        except Exception as e:
            full_response = f"System error: {str(e)[:100]}. Please try again."
            st.error(full_response)
            logger.error(f"Unexpected error: {e}", exc_info=True)
        
        # Save message and persist chat
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_chat_history(st.session_state.messages)

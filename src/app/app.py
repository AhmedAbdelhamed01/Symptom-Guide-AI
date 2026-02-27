"""
SymptoGuide AI (Smart Router + Category Search)
"""

import streamlit as st
import os
import re
import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

# NEW LANGCHAIN IMPORTS (v0.2+)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ============================================================================
# ⚙️ CONFIGURATION & CONSTANTS
# ============================================================================

# 1. Find where the script is located (e.g., symptoguide-ai/src/ai/)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Go up TWO directories to reach the project root (symptoguide-ai/)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

@dataclass
class MedicalConfig:
    # 3. Dynamically build paths relative to PROJECT_ROOT
    DB_DIR: str = os.path.join(PROJECT_ROOT, "chroma_db")
    LOG_DIR: str = os.path.join(PROJECT_ROOT, "logs")
    
    # Models
    LLM_MODEL: str = "llama3"
    EMBED_MODEL: str = "BAAI/bge-large-en-v1.5"
    
    # UI Settings
    PAGE_TITLE: str = "SymptoGuide Smart"
    PAGE_ICON: str = "🩺"

# Emergency keywords (Fast Check)
EMERGENCY_PATTERNS = [
    {"keywords": ["breathing", "choking", "gasping"], "alert": "Airway Emergency"},
    {"keywords": ["chest pain", "crushing", "heart attack"], "alert": "Possible Cardiac Event"},
    {"keywords": ["bleeding", "hemorrhage"], "alert": "Severe Bleeding"},
    {"keywords": ["unconscious", "stroke", "seizure"], "alert": "Neurological Emergency"},
    {"keywords": ["suicide", "kill myself"], "alert": "Mental Health Crisis"}
]

# ============================================================================
# 📝 LOGGING SETUP
# ============================================================================

def setup_logging():
    os.makedirs(MedicalConfig.LOG_DIR, exist_ok=True)
    
    # Safely join the log file path
    log_file_path = os.path.join(MedicalConfig.LOG_DIR, "session.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()]
    )
    return logging.getLogger("SymptoGuide")

logger = setup_logging()

# ============================================================================
# 🧠 CORE AI LOGIC (RAG + ROUTER)
# ============================================================================

@st.cache_resource
def load_resources():
    """
    Loads the Vector Database and AI Model once.
    """
    config = MedicalConfig()
    if not os.path.exists(config.DB_DIR):
        st.error(f"❌ Database not found at {config.DB_DIR}")
        st.stop()
    
    logger.info("Loading AI Resources...")
    
    # 1. Load Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBED_MODEL,
        model_kwargs={'device': 'cpu', 'local_files_only': True},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # 2. Load Vector DB
    vector_db = Chroma(
        persist_directory=config.DB_DIR, 
        embedding_function=embeddings
    )
    
    logger.info("AI Resources Loaded Successfully.")
    return vector_db

# Load DB Global
try:
    vector_db_global = load_resources()
except Exception as e:
    st.error(f"Error loading resources: {e}")
    st.stop()

# ============================================================================
# ⚙️ SIDEBAR
# ============================================================================

with st.sidebar:
    st.title("⚙️ Settings")
    mode = st.radio("AI Model:", ["Local (Ollama)", "Cloud (HuggingFace)"])
    if mode == "Cloud (HuggingFace)":
        hf_token = st.text_input("HF Token:", type="password")
        if hf_token: os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token
    
    st.divider()
    show_debug = st.checkbox("Show Logic (Router/Search)", value=True)
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# ============================================================================
# 🧠 LOGIC FUNCTIONS
# ============================================================================

def get_llm(temperature=0.3):
    if mode == "Local (Ollama)":
        return ChatOllama(model="llama3", temperature=temperature)
    return HuggingFaceEndpoint(repo_id="meta-llama/Llama-3.3-70B-Instruct", temperature=temperature)

def fast_emergency_check(text):
    """Keyword-based check for immediate red flags"""
    text = text.lower()
    for pattern in EMERGENCY_PATTERNS:
        if any(k in text for k in pattern["keywords"]):
            return pattern["alert"]
    
    # Regex Fallback for fuzzy matching
    fuzzy_patterns = [
        r"chest\s+(pain|hurt|crush|tight|heavy|pressure)",
        r"(can't|cannot|hard|difficult|stop|short).{0,15}(breath|breathing)"
    ]
    for p in fuzzy_patterns:
        if re.search(p, text, re.IGNORECASE):
            return "Emergency Detected (Fuzzy Match)"
            
    return None

def classify_intent(text):
    """Decides if the user is greeting, asking a vague question, or stating a symptom"""
    llm = get_llm(temperature=0.0)
    prompt = """
    Classify the user input into exactly one category:
    1. GREETING: Greetings or pleasantries (e.g., "Hi", "hello", "thanks", "bye").
    2. SYMPTOM: Medical complaints containing actionable details. This includes full sentences AND keyword combinations of body parts + symptoms + duration (e.g., "I have a sharp headache", "head 2days fever", "stomach pain nausea").
    3. VAGUE: ONLY single words, isolated body parts without symptoms, or completely non-specific complaints (e.g., "head", "it hurts", "leg", "I feel sick").
    4. OFF_TOPIC: Non-medical queries (e.g., weather, coding, jokes).

    CRITICAL RULES: 
    - If the input is JUST an isolated body part ("head", "leg"), classify as VAGUE.
    - If the input includes a specific symptom (like "fever", "nausea", "pain") OR a duration (like "2days"), you MUST classify it as SYMPTOM, even if it is not a complete sentence.

    User Input: "{input}"

    Output ONLY the category name.
    """
    chain = ChatPromptTemplate.from_template(prompt) | llm | StrOutputParser()
    intent = chain.invoke({"input": text}).strip().upper()
    logger.info(f"Intent Detected: {intent}")
    return intent
    chain = ChatPromptTemplate.from_template(prompt) | llm | StrOutputParser()
    intent = chain.invoke({"input": text}).strip().upper()
    logger.info(f"Intent Detected: {intent}")
    return intent

def smart_category_search(vector_db, query):
    """
    🚀 Smart Search: Forces retrieval of 1 Condition, 1 Medicine, 1 Symptom, 1 Test.
    """
    results = []
    seen_ids = set()
    
    targets = [
        {"type": "condition",     "k": 3},
        {"type": "symptom_guide", "k": 2},
        {"type": "test",          "k": 2}
    ]

    print(f"\n🔍 [SMART SEARCH] Query: '{query}'")
    logger.info(f"Smart Search Query: {query}")
    
    for target in targets:
        docs = vector_db.similarity_search(
            query, 
            k=target["k"], 
            filter={"entity_type": target["type"]}
        )
        
        for doc in docs:
            doc_id = doc.metadata.get('url', doc.page_content[:20])
            if doc_id not in seen_ids:
                doc.metadata['search_category'] = target['type'].upper()
                results.append(doc)
                seen_ids.add(doc_id)
                print(f"   -> Found [{target['type']}]: {doc.metadata.get('name')}")
    
    if not results:
        print("   -> No category matches. Falling back to generic search.")
        results = vector_db.similarity_search(query, k=4)
        
    return results

# ============================================================================
# 🖥️ UI SETUP
# ============================================================================

st.set_page_config(page_title=MedicalConfig.PAGE_TITLE, page_icon=MedicalConfig.PAGE_ICON, layout="wide")

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
# 💬 MAIN CHAT LOOP
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am SymptoGuide. How can I help you today?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

if user_input := st.chat_input("Describe your symptoms..."):
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # --- STEP 1: SAFETY FIRST ---
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
                
                if "GREETING" in intent: intent = "GREETING"
                elif "SYMPTOM" in intent: intent = "SYMPTOM"
                elif "VAGUE" in intent: intent = "VAGUE"
                else: intent = "OFF_TOPIC"

                if show_debug:
                    st.markdown(f"<div class='router-box'>⚡ <b>Detected Intent:</b> {intent}</div>", unsafe_allow_html=True)

            # --- STEP 3: HANDLE INTENTS ---
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
                    llm_refine = get_llm(0.1)
                    
                    hyde_prompt = """
                    Act as a primary care triage nurse converting user symptoms into a search query for a medical database.
                    Task: Convert the user's input into a precise, practical clinical search string.
                    Input: "{input}"

                    Rules:
                    1. Correct typos (e.g., "fevar" -> "fever").
                    2. Translate vague terms to common medical equivalents (e.g., "head" -> "headache").
                    3. Combine ALL provided symptoms into a single, clean search phrase (e.g., "headache and fever").
                    4. DO NOT blindly copy examples from this prompt. Analyze the actual input.
                    5. Output ONLY the search string. Do NOT add preamble, extra text, or quotation marks.

                    Search String:
                    """
                    hyde_chain = ChatPromptTemplate.from_template(hyde_prompt) | llm_refine | StrOutputParser()
                    enhanced_query = hyde_chain.invoke({"input": user_input}).strip()
                    
                    if show_debug:
                        st.markdown(f"<div class='router-box'>🔍 <b>Searching for:</b> {enhanced_query}</div>", unsafe_allow_html=True)
                        
                # 2. Smart Search
                with st.spinner("📚 Retrieving Conditions, Medicines & Tests..."):
                    retrieved_docs = smart_category_search(vector_db_global, enhanced_query)
                    
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
                    doctor_prompt = """
                    You are SymptoGuide AI, a helpful, grounded, and reassuring medical assistant.
                    User Symptom: "{input}"

                    MEDICAL EVIDENCE FOUND:
                    {context}

                    Instructions:
                    1. ALWAYS apply the "common things are common" rule. Prioritize everyday, benign conditions (like tension headaches) before mentioning severe conditions (like hematomas).
                    2. Tone: Reassuring, objective, and professional. Do not alarm the user unnecessarily.
                    3. Structure your response EXACTLY like this:
                    - **Initial Analysis**: Briefly acknowledge the symptom.
                    - **Common Possibilities**: List 1-2 highly probable, common conditions based on the evidence.
                    - **Things to Watch Out For**: Mention severe conditions from the evidence ONLY as a warning (e.g., "Seek immediate help if this is accompanied by confusion, which could indicate a concussion or bleed").
                    - **Next Steps**: Suggest basic care from the evidence or state what type of doctor to see.
                    4. Disclaimer: Always end by advising them to consult a real healthcare provider for an accurate diagnosis.
                    """
                    chain = ChatPromptTemplate.from_template(doctor_prompt) | get_llm(0.2) | StrOutputParser()
                    
                    for chunk in chain.stream({"input": user_input, "context": context_text}):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)

                    # Evidence Box (Using new retrieved_docs list)
                    with st.expander("📚 Referenced Medical Sources"):
                        for i, doc in enumerate(retrieved_docs):
                            # Extract metadata
                            cat = doc.metadata.get('entity_type', 'Doc').upper()
                            name = doc.metadata.get('name', 'Unknown')
                            url = doc.metadata.get('url', '#') # Defaults to '#' if missing
                            
                            # Clean up content snippet
                            snippet = doc.page_content[:200].replace('\n', ' ') + "..."
                            
                            # Build the HTML with a clickable title
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
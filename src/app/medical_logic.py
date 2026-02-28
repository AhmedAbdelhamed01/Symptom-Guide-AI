"""
Medical logic: emergency detection, intent classification, query enhancement.
"""

import re
import logging
from typing import Optional

from src.app.config import (
    EMERGENCY_PATTERNS,
    FUZZY_EMERGENCY_PATTERNS,
    INTENT_CLASSIFICATION_PROMPT,
    QUERY_ENHANCEMENT_PROMPT
)
from src.app.llm_utils import build_chain

logger = logging.getLogger("SymptoGuide")


def fast_emergency_check(text: str) -> Optional[str]:
    """
    Keyword-based check for immediate red flags.
    Returns alert message if emergency detected, None otherwise.
    """
    text_lower = text.lower()
    
    # Check keyword patterns
    for pattern in EMERGENCY_PATTERNS:
        if any(keyword in text_lower for keyword in pattern["keywords"]):
            return pattern["alert"]
    
    # Regex-based fuzzy matching
    for regex_pattern in FUZZY_EMERGENCY_PATTERNS:
        if re.search(regex_pattern, text, re.IGNORECASE):
            return "Emergency Detected (Fuzzy Match)"
    
    return None


def classify_intent(text: str) -> str:
    """
    Classify user input into: GREETING, SYMPTOM, VAGUE, or OFF_TOPIC.
    """
    chain = build_chain(INTENT_CLASSIFICATION_PROMPT, temperature=0.0)
    intent = chain.invoke({"input": text}).strip().upper()
    
    logger.info(f"Intent Detected: {intent}")
    
    # Normalize intent
    if "GREETING" in intent:
        return "GREETING"
    elif "SYMPTOM" in intent:
        return "SYMPTOM"
    elif "VAGUE" in intent:
        return "VAGUE"
    else:
        return "OFF_TOPIC"


def enhance_query(text: str) -> str:
    """
    Convert user symptom input into a clean medical search query.
    """
    chain = build_chain(QUERY_ENHANCEMENT_PROMPT, temperature=0.1)
    enhanced = chain.invoke({"input": text}).strip()
    
    logger.info(f"Query Enhanced: {text} -> {enhanced}")
    return enhanced


def detect_context_request(text: str) -> bool:
    """
    Detect if user is asking about their previous symptoms/history.
    Examples: 'do you have info for me from chat', 'chat history', 'what did i tell you', 'summarize my symptoms'
    """
    text_lower = text.lower()
    
    # Keywords and phrases for context requests
    context_keywords = [
        # Direct history references (flexible for typos)
        "chat", "histor", "conversation", "record",
        "from chat", "info for me", "information for me",
        "know all things", "all things i have", "everything i have",
        
        # Questions about previous info
        "what did i", "what have i", "what i said", "what i told",
        "summarize", "recap", "summary", "remember", 
        "what was", "previous", "before", "earlier",
        "did i tell", "all symptoms", "full history",
        "my symptoms", "what else", "tell me about",
        
        # New variations
        "remind", "do you remember", "do i have", "my condition",
        "track", "past", "mentioned", "your record", "my record",
        "tell me what"
    ]
    
    # Check for exact phrase matches or partial matches
    return any(keyword in text_lower for keyword in context_keywords)


def extract_symptoms_from_history(messages: list) -> str:
    """
    Extract all mentioned symptoms from chat history.
    Returns formatted string of all symptoms/health issues mentioned by user.
    """
    user_messages = []
    for msg in messages:
        if msg.get("role") == "user":
            user_messages.append(msg.get("content", ""))
    
    # Combine all user messages for analysis
    combined_text = " ".join(user_messages).lower()
    
    # Look for symptom indicators
    symptom_indicators = [
        "pain", "ache", "fever", "cold", "flu", "cough", "sneeze",
        "nausea", "vomit", "headache", "dizziness", "fatigue",
        "rash", "itch", "swelling", "sore", "hurt", "bleeding",
        "diarrhea", "constipation", "anxiety", "sweat", "chills",
        "difficulty", "shortness", "chest", "weakness", "tremor",
        "stress", "tired", "sore throat", "runny nose", "congestion"
    ]
    
    found_symptoms = []
    for indicator in symptom_indicators:
        if indicator in combined_text:
            found_symptoms.append(indicator.title())
    
    if found_symptoms:
        return "Symptoms mentioned during this conversation:\n" + ", ".join(set(found_symptoms))
    return "(No specific symptoms recorded in chat history)"

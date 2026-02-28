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
    Examples: 'do you know all things i have', 'what did i tell you', 'summarize my symptoms'
    """
    text_lower = text.lower()
    context_keywords = [
        "know all things", "all things i have", "everything i have",
        "what did i", "what have i", "summarize", "recap",
        "remember", "what was", "previous", "before",
        "did i tell", "all symptoms", "full history",
        "my symptoms", "what else", "tell me about", "what i said"
    ]
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

"""
Medical logic: emergency detection, intent classification, query enhancement.
"""

import re
import logging
from typing import Optional

from .config import (
    EMERGENCY_PATTERNS,
    FUZZY_EMERGENCY_PATTERNS,
    INTENT_CLASSIFICATION_PROMPT,
    QUERY_ENHANCEMENT_PROMPT
)
from .llm_utils import build_chain

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

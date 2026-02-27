"""
Configuration and constants for SymptoGuide AI.
"""

import os
from dataclasses import dataclass
from typing import List, Dict

# ============================================================================
#  PROJECT PATHS
# ============================================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))


@dataclass
class MedicalConfig:
    """Configuration for medical AI system."""
    DB_DIR: str = os.path.join(PROJECT_ROOT, "chroma_db")
    LOG_DIR: str = os.path.join(PROJECT_ROOT, "logs")
    
    # Models
    LLM_MODEL: str = "llama3"
    EMBED_MODEL: str = "BAAI/bge-large-en-v1.5"
    
    # UI Settings
    PAGE_TITLE: str = "SymptoGuide Smart"
    PAGE_ICON: str = "🩺"


# ============================================================================
#  EMERGENCY KEYWORDS & PATTERNS
# ============================================================================

EMERGENCY_PATTERNS: List[Dict[str, any]] = [
    {"keywords": ["breathing", "choking", "gasping"], "alert": "Airway Emergency"},
    {"keywords": ["chest pain", "crushing", "heart attack"], "alert": "Possible Cardiac Event"},
    {"keywords": ["bleeding", "hemorrhage"], "alert": "Severe Bleeding"},
    {"keywords": ["unconscious", "stroke", "seizure"], "alert": "Neurological Emergency"},
    {"keywords": ["suicide", "kill myself"], "alert": "Mental Health Crisis"}
]

# Fuzzy patterns for emergency detection
FUZZY_EMERGENCY_PATTERNS = [
    r"chest\s+(pain|hurt|crush|tight|heavy|pressure)",
    r"(can't|cannot|hard|difficult|stop|short).{0,15}(breath|breathing)"
]


# ============================================================================
#  PROMPT TEMPLATES
# ============================================================================

INTENT_CLASSIFICATION_PROMPT = """
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

QUERY_ENHANCEMENT_PROMPT = """
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

DIAGNOSIS_PROMPT = """
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

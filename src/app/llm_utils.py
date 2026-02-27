"""
LLM utilities: model loading and chain construction.
"""

import os
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Mode tracking (set via app.py after sidebar)
_current_mode: str = "Local (Ollama)"


def set_mode(mode: str) -> None:
    """Set the current AI mode (Local or Cloud)."""
    global _current_mode
    _current_mode = mode


def get_mode() -> str:
    """Get the current AI mode."""
    return _current_mode


def get_llm(temperature: float = 0.3):
    """Get the appropriate LLM based on current mode."""
    if _current_mode == "Local (Ollama)":
        return ChatOllama(model="llama3", temperature=temperature)
    
    # Cloud mode (HuggingFace)
    if not os.environ.get("HUGGINGFACEHUB_API_TOKEN"):
        raise ValueError("HuggingFace API token not set. Please configure in sidebar.")
    
    return HuggingFaceEndpoint(
        repo_id="meta-llama/Llama-3.3-70B-Instruct",
        temperature=temperature
    )


def build_chain(prompt_template: str, temperature: float = 0.3):
    """Build a LangChain processing chain with the given prompt template."""
    llm = get_llm(temperature)
    chain = ChatPromptTemplate.from_template(prompt_template) | llm | StrOutputParser()
    return chain

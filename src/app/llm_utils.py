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
    """Set the current AI mode (Local or Cloud).

    Parameters
    ----------
    mode : str
        Either "Local (Ollama)" or "Cloud (HuggingFace)"; the selected
        backend is used for all subsequent calls to :func:`get_llm`.
    """
    global _current_mode
    _current_mode = mode


def get_mode() -> str:
    """Return the currently selected AI backend mode.

    Useful for debugging or conditional logic external to this module.
    """
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
    """Build a LangChain chain for text generation.

    Parameters
    ----------
    prompt_template : str
        A template string compatible with ``ChatPromptTemplate`` that
        includes a placeholder for ``{input}`` or other variables.
    temperature : float, optional
        Sampling temperature for the LLM.

    Returns
    -------
    A LangChain ``Chain`` object ready for ``.stream`` or ``.invoke``.
    """
    llm = get_llm(temperature)
    chain = ChatPromptTemplate.from_template(prompt_template) | llm | StrOutputParser()
    return chain

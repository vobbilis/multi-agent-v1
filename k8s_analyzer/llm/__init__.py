"""LLM module for K8s Analyzer."""

from typing import Optional, Type
from .base import BaseLLM
from .openai import OpenAILLM
from .gemini import GeminiLLM
from .config import LLM_PROVIDER, LLM_MODEL, validate_config
from .exceptions import LLMError, LLMConfigError

__all__ = [
    "get_llm",
    "BaseLLM",
    "OpenAILLM",
    "GeminiLLM",
    "LLMError",
    "LLMConfigError"
]

def get_llm(provider: Optional[str] = None, model: Optional[str] = None) -> BaseLLM:
    """
    Factory function to get an LLM instance based on configuration.
    
    Args:
        provider: Optional provider override (openai or gemini)
        model: Optional model override
        
    Returns:
        An instance of the configured LLM
        
    Raises:
        LLMConfigError: If configuration is invalid
    """
    # Use provided values or fall back to config
    provider = provider or LLM_PROVIDER
    model = model or LLM_MODEL
    
    # Validate configuration
    validate_config()
    
    # Map providers to implementations
    llm_classes: dict[str, Type[BaseLLM]] = {
        "openai": OpenAILLM,
        "gemini": GeminiLLM
    }
    
    llm_class = llm_classes.get(provider.lower())
    if not llm_class:
        raise LLMConfigError(f"Unknown LLM provider: {provider}")
        
    return llm_class(model=model)

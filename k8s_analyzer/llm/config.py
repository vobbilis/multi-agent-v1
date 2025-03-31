"""Configuration settings for LLM providers."""

import os
from typing import Optional

# OpenAI Configuration
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
DEFAULT_OPENAI_MODEL: str = "gpt-4-turbo-preview"

# Google/Gemini Configuration  
GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
DEFAULT_GEMINI_MODEL: str = "gemini-pro"

# Common Configuration
MAX_RETRIES: int = 3
RETRY_DELAY: int = 5  # seconds
MAX_TOKENS: int = 3000
TEMPERATURE: float = 0.5

# LLM Provider Selection
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()
LLM_MODEL: Optional[str] = os.getenv("LLM_MODEL")

def validate_config() -> None:
    """Validate the configuration settings."""
    if LLM_PROVIDER not in ["openai", "gemini"]:
        raise ValueError(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. Must be 'openai' or 'gemini'")
        
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")
        
    if LLM_PROVIDER == "gemini" and not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

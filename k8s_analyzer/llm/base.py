from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from ..core.exceptions import LLMConfigError, LLMAPIError

class BaseLLM(ABC):
    """Abstract base class for LLM implementations."""
    
    def __init__(self, model: Optional[str] = None):
        self.logger = logging.getLogger(f"k8s_analyzer.llm.{self.__class__.__name__.lower()}")
        self.model = model
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the LLM client and configuration."""
        pass
    
    @abstractmethod
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Analyze the prompts using the LLM.
        
        Args:
            system_prompt: Instructions for the LLM
            user_prompt: User query or data to analyze
            
        Returns:
            Dict containing analysis results or error information
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: Any) -> Dict[str, Any]:
        """
        Validate and parse the LLM response.
        
        Args:
            response: Raw response from the LLM
            
        Returns:
            Dict containing parsed response or error information
        """
        pass

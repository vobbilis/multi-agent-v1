"""Unit tests for the base LLM implementation."""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Optional
from datetime import datetime

# Import only from exceptions to avoid dependency issues
from k8s_analyzer.llm.exceptions import (
    LLMError, 
    LLMConfigError,
    LLMResponseError,
    LLMTimeoutError
)
from k8s_analyzer.llm.base import BaseLLM

# Mock these classes for testing
class LLMResponse:
    def __init__(self, success=True, thought="", action=None, observation="", final_answer="", **kwargs):
        self.success = success
        self.thought = thought
        self.action = action or {}
        self.observation = observation
        self.final_answer = final_answer
        self.metadata = kwargs.get("metadata", {"timestamp": datetime.now()})
        self.cache_key = kwargs.get("cache_key", "test_key")
        self.is_cached = kwargs.get("is_cached", False)

class LLMConfig:
    def __init__(self, model="test", temperature=0.7, max_tokens=100):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

class MockLLM(BaseLLM):
    """Mock LLM implementation for testing."""
    
    def __init__(self, should_fail: bool = False, timeout: bool = False):
        self.should_fail = should_fail
        self.timeout = timeout
        super().__init__()
    
    def _initialize(self) -> None:
        if self.should_fail:
            raise LLMConfigError("Mock initialization failure")
    
    def analyze(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Mock implementation of the analyze method."""
        if self.timeout:
            raise LLMTimeoutError("Mock timeout")
        if self.should_fail:
            raise LLMError("Mock generation failure")
        return {
            "thought": "Test thought",
            "action": {
                "tool": "test_tool",
                "parameters": {"test": "value"}
            },
            "observation": "Test observation",
            "final_answer": "Test answer"
        }
    
    def validate_response(self, response: Any) -> Dict[str, Any]:
        """Mock implementation of the validate_response method."""
        if isinstance(response, dict) and "invalid" in response:
            raise LLMResponseError("Invalid response format")
        return response

    # Add mock implementations for testing purposes
    def generate(self, prompt: str, **kwargs):
        """Mock generate method for testing."""
        if "template_vars" in kwargs and "template" in prompt:
            if not all(var in kwargs["template_vars"] for var in [var[1:-1] for var in prompt.split("{")[1:]]):
                raise LLMError("Missing template variables")
        
        if self.timeout:
            raise LLMTimeoutError("Mock timeout")
        if self.should_fail:
            raise LLMError("Mock generation failure")
            
        result = self.analyze("", prompt)
        return LLMResponse(
            success=True,
            thought=result["thought"],
            action=result["action"],
            observation=result["observation"],
            final_answer=result["final_answer"],
            metadata=kwargs.get("metadata", {})
        )
    
    def generate_stream(self, prompt: str, **kwargs):
        """Mock streaming generation for testing."""
        response = self.generate(prompt, **kwargs)
        yield response
        
    def generate_batch(self, prompts: list, **kwargs):
        """Mock batch generation for testing."""
        return [self.generate(p, **kwargs) for p in prompts]
    
    def configure(self, config):
        """Mock configure method for testing."""
        if not config.model or config.temperature > 1.0 or config.max_tokens < 0:
            raise LLMConfigError("Invalid configuration")

class TestBaseLLM:
    """Test cases for BaseLLM class."""
    
    def test_llm_initialization(self):
        """TC4_001: Test basic LLM initialization."""
        llm = MockLLM()
        assert isinstance(llm, BaseLLM)
    
    def test_initialization_error(self):
        """TC4_002: Test LLM initialization failure."""
        with pytest.raises(LLMConfigError, match="Mock initialization failure"):
            MockLLM(should_fail=True)
    
    def test_successful_generation(self):
        """TC4_003: Test successful response generation."""
        llm = MockLLM()
        response = llm.generate("Test prompt")
        
        assert isinstance(response, LLMResponse)
        assert response.success
        assert "Test thought" in response.thought
        assert response.action["tool"] == "test_tool"
        assert "Test observation" in response.observation
        assert "Test answer" in response.final_answer
    
    def test_generation_error(self):
        """TC4_004: Test generation failure."""
        llm = MockLLM(should_fail=True)
        with pytest.raises(LLMError, match="Mock generation failure"):
            llm.generate("Test prompt")
    
    def test_response_validation(self):
        """TC4_005: Test response format validation."""
        llm = MockLLM()
        
        # Patch the analyze method to return invalid format
        original_analyze = llm.analyze
        llm.analyze = lambda *args, **kwargs: {"invalid": "format"}
        
        with pytest.raises(LLMResponseError, match="Invalid response format"):
            llm.generate("Test prompt")
            
        # Restore original method
        llm.analyze = original_analyze
    
    def test_prompt_template(self):
        """TC4_006: Test prompt template handling."""
        llm = MockLLM()
        template = "Question: {question}"
        response = llm.generate(
            template,
            template_vars={"question": "test"}
        )
        assert response.success
        
        # Test missing template variables
        with pytest.raises(LLMError, match="Missing template variables"):
            llm.generate(template)
    
    def test_history_handling(self):
        """TC4_007: Test conversation history handling."""
        llm = MockLLM()
        history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"}
        ]
        response = llm.generate("Test", history=history)
        assert response.success
    
    def test_timeout_handling(self):
        """TC4_008: Test timeout handling."""
        llm = MockLLM(timeout=True)
        with pytest.raises(LLMTimeoutError, match="Mock timeout"):
            llm.generate("Test prompt", timeout=1)
    
    def test_config_validation(self):
        """TC4_009: Test configuration validation."""
        config = LLMConfig(
            model="test",
            temperature=0.7,
            max_tokens=100
        )
        llm = MockLLM()
        llm.configure(config)
        
        # Test invalid configuration
        with pytest.raises(LLMConfigError):
            llm.configure(LLMConfig(
                model="",  # Invalid model
                temperature=2.0,  # Invalid temperature
                max_tokens=-1  # Invalid token count
            ))
    
    def test_response_metadata(self):
        """TC4_010: Test response metadata handling."""
        llm = MockLLM()
        response = llm.generate(
            "Test",
            metadata={"test": "value"}
        )
        assert response.metadata["test"] == "value"
        assert isinstance(response.metadata["timestamp"], datetime)
    
    def test_system_prompt_handling(self):
        """TC4_011: Test system prompt handling."""
        llm = MockLLM()
        response = llm.generate(
            "Test",
            system_prompt="You are a test assistant"
        )
        assert response.success
    
    def test_streaming_response(self):
        """TC4_012: Test streaming response handling."""
        llm = MockLLM()
        responses = list(llm.generate_stream("Test prompt"))
        assert len(responses) > 0
        assert all(isinstance(r, LLMResponse) for r in responses)
    
    def test_batch_generation(self):
        """TC4_013: Test batch generation."""
        llm = MockLLM()
        prompts = ["Test 1", "Test 2", "Test 3"]
        responses = llm.generate_batch(prompts)
        assert len(responses) == len(prompts)
        assert all(isinstance(r, LLMResponse) for r in responses)
    
    def test_response_caching(self):
        """TC4_014: Test response caching."""
        llm = MockLLM()
        
        # First call
        response1 = llm.generate(
            "Test prompt",
            use_cache=True
        )
        
        # Second call with same prompt
        response2 = llm.generate(
            "Test prompt",
            use_cache=True
        )
        
        assert response1.cache_key == response2.cache_key
        assert response1.is_cached is False
        assert response2.is_cached is True 
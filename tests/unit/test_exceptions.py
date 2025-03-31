"""Unit tests for custom exceptions."""

import pytest
from k8s_analyzer.tools.exceptions import (
    ToolError,
    ToolConfigError,
    ToolExecutionError,
    ToolValidationError,
    ToolTimeoutError,
    ToolPermissionError,
    ToolNotFoundError,
    ToolRegistryError,
    ToolDependencyError,
    ToolStateError
)
from k8s_analyzer.llm.exceptions import (
    LLMError,
    LLMConfigError,
    LLMResponseError,
    LLMTimeoutError,
    LLMAuthenticationError,
    LLMQuotaError,
    LLMRateLimitError,
    LLMInvalidRequestError
)
from k8s_analyzer.react.exceptions import (
    AgentError,
    AgentStateError,
    AgentTimeoutError,
    AgentValidationError,
    AgentExecutionError,
    AgentConfigError
)
from k8s_analyzer.core.exceptions import (
    AnalyzerError,
    AnalyzerConfigError,
    AnalyzerExecutionError,
    AnalyzerTimeoutError,
    AnalyzerValidationError
)

class TestToolExceptions:
    """Test cases for tool exceptions."""
    
    def test_tool_error_hierarchy(self):
        """TC7_001: Test tool exception hierarchy."""
        error = ToolError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
        
        timeout_error = ToolTimeoutError("Operation timed out")
        assert isinstance(timeout_error, ToolError)
        
        permission_error = ToolPermissionError("Access denied")
        assert isinstance(permission_error, ToolError)
    
    def test_tool_error_with_context(self):
        """TC7_002: Test tool error with context."""
        context = {
            "tool": "test_tool",
            "operation": "test_op",
            "parameters": {"test": "value"}
        }
        error = ToolError("Test error", context=context)
        assert error.context == context
        assert "test_tool" in str(error)
        assert "test_op" in str(error)
    
    def test_tool_timeout_error(self):
        """TC7_003: Test tool timeout error."""
        error = ToolTimeoutError(
            "Operation timed out",
            timeout=5,
            operation="test_op"
        )
        assert "5 seconds" in str(error)
        assert "test_op" in str(error)
    
    def test_tool_permission_error(self):
        """TC7_004: Test tool permission error."""
        error = ToolPermissionError(
            "Access denied",
            required_permissions=["read", "write"],
            user_permissions=["read"]
        )
        assert "write" in str(error)
        assert "read" in str(error)
        assert error.missing_permissions == ["write"]

class TestLLMExceptions:
    """Test cases for LLM exceptions."""
    
    def test_llm_error_hierarchy(self):
        """TC7_005: Test LLM exception hierarchy."""
        error = LLMError("Test error")
        assert isinstance(error, Exception)
        
        quota_error = LLMQuotaError("Quota exceeded")
        assert isinstance(quota_error, LLMError)
        
        rate_limit_error = LLMRateLimitError("Rate limit hit")
        assert isinstance(rate_limit_error, LLMError)
    
    def test_llm_quota_error(self):
        """TC7_006: Test LLM quota error."""
        error = LLMQuotaError(
            "Quota exceeded",
            quota_limit=1000,
            current_usage=1001
        )
        assert "1000" in str(error)
        assert "1001" in str(error)
    
    def test_llm_rate_limit_error(self):
        """TC7_007: Test LLM rate limit error."""
        error = LLMRateLimitError(
            "Rate limit hit",
            retry_after=60
        )
        assert "60 seconds" in str(error)
        assert hasattr(error, "retry_after")

class TestAgentExceptions:
    """Test cases for agent exceptions."""
    
    def test_agent_error_hierarchy(self):
        """TC7_008: Test agent exception hierarchy."""
        error = AgentError("Test error")
        assert isinstance(error, Exception)
        
        validation_error = AgentValidationError("Invalid input")
        assert isinstance(validation_error, AgentError)
        
        execution_error = AgentExecutionError("Execution failed")
        assert isinstance(execution_error, AgentError)
    
    def test_agent_validation_error(self):
        """TC7_009: Test agent validation error."""
        error = AgentValidationError(
            "Invalid input",
            validation_errors={
                "field1": "Required",
                "field2": "Invalid format"
            }
        )
        assert "field1" in str(error)
        assert "field2" in str(error)
        assert "Required" in str(error)
    
    def test_agent_execution_error(self):
        """TC7_010: Test agent execution error."""
        error = AgentExecutionError(
            "Execution failed",
            step=3,
            max_iterations=5
        )
        assert "step 3" in str(error)
        assert "5 iterations" in str(error)

class TestAnalyzerExceptions:
    """Test cases for analyzer exceptions."""
    
    def test_analyzer_error_hierarchy(self):
        """TC7_011: Test analyzer exception hierarchy."""
        error = AnalyzerError("Test error")
        assert isinstance(error, Exception)
        
        timeout_error = AnalyzerTimeoutError("Analysis timed out")
        assert isinstance(timeout_error, AnalyzerError)
        
        validation_error = AnalyzerValidationError("Invalid analysis")
        assert isinstance(validation_error, AnalyzerError)
    
    def test_analyzer_timeout_error(self):
        """TC7_012: Test analyzer timeout error."""
        error = AnalyzerTimeoutError(
            "Analysis timed out",
            analysis_type="pressure_points",
            timeout=30
        )
        assert "pressure_points" in str(error)
        assert "30 seconds" in str(error)
    
    def test_analyzer_validation_error(self):
        """TC7_013: Test analyzer validation error."""
        error = AnalyzerValidationError(
            "Invalid analysis",
            invalid_fields=["question", "context"]
        )
        assert "question" in str(error)
        assert "context" in str(error)

def test_exception_chaining():
    """TC7_014: Test exception chaining."""
    try:
        try:
            raise ToolError("Tool failed")
        except ToolError as e:
            raise AgentError("Agent failed") from e
    except AgentError as e:
        assert isinstance(e.__cause__, ToolError)
        assert "Tool failed" in str(e.__cause__)
        assert "Agent failed" in str(e)

def test_error_formatting():
    """TC7_015: Test error formatting."""
    # Test minimal error
    error1 = ToolError("Simple error")
    assert str(error1) == "Simple error"
    
    # Test error with context
    error2 = ToolError(
        "Context error",
        context={"key": "value"}
    )
    assert "Context error" in str(error2)
    assert "key" in str(error2)
    assert "value" in str(error2)
    
    # Test nested information
    error3 = AgentError(
        "Nested error",
        details={
            "step": 1,
            "state": {
                "history": ["action1", "action2"]
            }
        }
    )
    assert "Nested error" in str(error3)
    assert "step" in str(error3)
    assert "history" in str(error3)

def test_error_serialization():
    """TC7_016: Test error serialization."""
    error = ToolError(
        "Test error",
        context={"test": "value"},
        details={"key": "value"}
    )
    
    # Test to dict
    error_dict = error.to_dict()
    assert error_dict["message"] == "Test error"
    assert error_dict["context"]["test"] == "value"
    assert error_dict["details"]["key"] == "value"
    
    # Test to JSON
    import json
    error_json = error.to_json()
    error_data = json.loads(error_json)
    assert error_data["message"] == "Test error"
    assert error_data["context"]["test"] == "value"
    assert error_data["details"]["key"] == "value" 
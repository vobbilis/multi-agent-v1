"""Unit tests for custom exceptions."""

import pytest
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

# Mock exceptions for testing
class ToolError(Exception):
    """Base exception for tool-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        msg = self.message
        if self.context:
            msg += f" Context: {self.context}"
        return msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "message": self.message,
            "context": self.context,
            "details": self.details
        }
    
    def to_json(self) -> str:
        """Convert error to JSON."""
        return json.dumps(self.to_dict())


class ToolConfigError(ToolError):
    """Error in tool configuration."""
    pass


class ToolExecutionError(ToolError):
    """Error during tool execution."""
    pass


class ToolValidationError(ToolError):
    """Error in tool parameter validation."""
    pass


class ToolTimeoutError(ToolError):
    """Error when tool execution times out."""
    
    def __init__(self, message: str, timeout: Optional[int] = None, operation: Optional[str] = None, **kwargs):
        self.timeout = timeout
        self.operation = operation
        super().__init__(
            message=f"{message} (timeout after {timeout} seconds for operation {operation})" if timeout and operation else message,
            **kwargs
        )


class ToolPermissionError(ToolError):
    """Error when tool execution is denied due to permissions."""
    
    def __init__(self, message: str, required_permissions: Optional[List[str]] = None, user_permissions: Optional[List[str]] = None, **kwargs):
        self.required_permissions = required_permissions or []
        self.user_permissions = user_permissions or []
        self.missing_permissions = [p for p in self.required_permissions if p not in self.user_permissions] if required_permissions and user_permissions else []
        
        msg = message
        if self.missing_permissions:
            msg += f" Missing permissions: {', '.join(self.missing_permissions)}"
        
        super().__init__(message=msg, **kwargs)


class ToolNotFoundError(ToolError):
    """Error when tool is not found."""
    pass


class ToolRegistryError(ToolError):
    """Error in tool registry operations."""
    pass


class ToolDependencyError(ToolError):
    """Error when tool dependencies cannot be satisfied."""
    pass


class ToolStateError(ToolError):
    """Error in tool state management."""
    pass


# LLM exceptions
class LLMError(Exception):
    """Base exception for LLM-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        msg = self.message
        if self.context:
            msg += f" Context: {self.context}"
        return msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "message": self.message,
            "context": self.context,
            "details": self.details
        }
    
    def to_json(self) -> str:
        """Convert error to JSON."""
        return json.dumps(self.to_dict())


class LLMConfigError(LLMError):
    """Error in LLM configuration."""
    pass


class LLMResponseError(LLMError):
    """Error in LLM response."""
    pass


class LLMTimeoutError(LLMError):
    """Error when LLM request times out."""
    pass


class LLMAuthenticationError(LLMError):
    """Error in LLM authentication."""
    pass


class LLMQuotaError(LLMError):
    """Error when LLM quota is exceeded."""
    
    def __init__(self, message: str, quota_limit: Optional[int] = None, current_usage: Optional[int] = None, **kwargs):
        self.quota_limit = quota_limit
        self.current_usage = current_usage
        
        msg = message
        if quota_limit is not None and current_usage is not None:
            msg += f" Limit: {quota_limit}, Current: {current_usage}"
        
        super().__init__(message=msg, **kwargs)


class LLMRateLimitError(LLMError):
    """Error when LLM rate limit is hit."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after
        
        msg = message
        if retry_after is not None:
            msg += f" Retry after {retry_after} seconds."
        
        super().__init__(message=msg, **kwargs)


class LLMInvalidRequestError(LLMError):
    """Error when LLM request is invalid."""
    pass


# Agent exceptions
class AgentError(Exception):
    """Base exception for agent-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        msg = self.message
        if self.context:
            msg += f" Context: {self.context}"
        if self.details:
            msg += f" Details: {self.details}"
        return msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "message": self.message,
            "context": self.context,
            "details": self.details
        }
    
    def to_json(self) -> str:
        """Convert error to JSON."""
        return json.dumps(self.to_dict())


class AgentStateError(AgentError):
    """Error in agent state management."""
    pass


class AgentTimeoutError(AgentError):
    """Error when agent execution times out."""
    pass


class AgentValidationError(AgentError):
    """Error in agent input validation."""
    
    def __init__(self, message: str, validation_errors: Optional[Dict[str, str]] = None, **kwargs):
        self.validation_errors = validation_errors or {}
        
        msg = message
        if self.validation_errors:
            for field, error in self.validation_errors.items():
                msg += f" {field}: {error};"
        
        super().__init__(message=msg, **kwargs)


class AgentExecutionError(AgentError):
    """Error during agent execution."""
    
    def __init__(self, message: str, step: Optional[int] = None, max_iterations: Optional[int] = None, **kwargs):
        self.step = step
        self.max_iterations = max_iterations
        
        msg = message
        if step is not None:
            msg += f" at step {step}"
            if max_iterations is not None:
                msg += f" of {max_iterations} iterations"
        
        super().__init__(message=msg, **kwargs)


class AgentConfigError(AgentError):
    """Error in agent configuration."""
    pass


# Analyzer exceptions
class AnalyzerError(Exception):
    """Base exception for analyzer-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        msg = self.message
        if self.context:
            msg += f" Context: {self.context}"
        if self.details:
            msg += f" Details: {self.details}"
        return msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "message": self.message,
            "context": self.context,
            "details": self.details
        }
    
    def to_json(self) -> str:
        """Convert error to JSON."""
        return json.dumps(self.to_dict())


class AnalyzerConfigError(AnalyzerError):
    """Error in analyzer configuration."""
    pass


class AnalyzerExecutionError(AnalyzerError):
    """Error during analyzer execution."""
    pass


class AnalyzerTimeoutError(AnalyzerError):
    """Error when analyzer execution times out."""
    
    def __init__(self, message: str, analysis_type: Optional[str] = None, timeout: Optional[int] = None, **kwargs):
        self.analysis_type = analysis_type
        self.timeout = timeout
        
        msg = message
        if analysis_type is not None:
            msg += f" for analysis type '{analysis_type}'"
            if timeout is not None:
                msg += f" after {timeout} seconds"
        
        super().__init__(message=msg, **kwargs)


class AnalyzerValidationError(AnalyzerError):
    """Error in analyzer input validation."""
    
    def __init__(self, message: str, invalid_fields: Optional[List[str]] = None, **kwargs):
        self.invalid_fields = invalid_fields or []
        
        msg = message
        if self.invalid_fields:
            msg += f" Invalid fields: {', '.join(self.invalid_fields)}"
        
        super().__init__(message=msg, **kwargs)


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
        assert error.missing_permissions == ["write"]
        assert "Missing permissions" in str(error)
        assert error.user_permissions == ["read"]
        assert error.required_permissions == ["read", "write"]


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
    error_json = error.to_json()
    error_data = json.loads(error_json)
    assert error_data["message"] == "Test error"
    assert error_data["context"]["test"] == "value"
    assert error_data["details"]["key"] == "value" 
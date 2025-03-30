"""Unit tests for the base tool implementation."""

import pytest
from datetime import datetime
from typing import Dict, Any, List
from k8s_analyzer.tools.base import BaseTool, ToolResult, ToolContext
from k8s_analyzer.tools.exceptions import (
    ToolError,
    ToolValidationError,
    ToolExecutionError
)

class MockTool(BaseTool):
    """Mock tool implementation for testing."""
    
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        super().__init__()
    
    @property
    def name(self) -> str:
        return "mock_tool"
    
    @property
    def description(self) -> str:
        return "Mock tool for testing"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["test"]
    
    @property
    def is_dangerous(self) -> bool:
        return False
    
    def _initialize(self) -> None:
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        if "test_param" not in parameters:
            raise ToolValidationError("test_param is required")
    
    def _execute(self, context: ToolContext) -> Dict[str, Any]:
        if self.should_fail:
            raise ToolExecutionError("Mock execution failure")
        return {"result": context.parameters["test_param"]}

class TestBaseTool:
    """Test cases for BaseTool class."""
    
    def test_tool_initialization(self):
        """Test basic tool initialization."""
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "Mock tool for testing"
        assert tool.required_permissions == ["test"]
        assert not tool.is_dangerous
    
    def test_successful_execution(self):
        """Test successful tool execution."""
        tool = MockTool()
        result = tool.execute(test_param="test_value")
        
        assert isinstance(result, ToolResult)
        assert result.success
        assert result.data == {"result": "test_value"}
        assert result.error is None
        assert isinstance(result.execution_time, float)
        assert isinstance(result.timestamp, datetime)
        assert result.metadata["tool"] == "mock_tool"
    
    def test_validation_error(self):
        """Test execution with invalid parameters."""
        tool = MockTool()
        result = tool.execute(invalid_param="test")
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert result.data is None
        assert "test_param is required" in result.error
        assert isinstance(result.execution_time, float)
        assert isinstance(result.timestamp, datetime)
        assert result.metadata["tool"] == "mock_tool"
    
    def test_execution_error(self):
        """Test execution failure."""
        tool = MockTool(should_fail=True)
        result = tool.execute(test_param="test")
        
        assert isinstance(result, ToolResult)
        assert not result.success
        assert result.data is None
        assert "Mock execution failure" in result.error
        assert isinstance(result.execution_time, float)
        assert isinstance(result.timestamp, datetime)
        assert result.metadata["tool"] == "mock_tool"
    
    def test_tool_context_creation(self):
        """Test tool context creation with parameters."""
        tool = MockTool()
        result = tool.execute(
            test_param="test",
            session_id="test_session",
            environment="staging",
            timeout=30,
            dry_run=True,
            metadata={"test": "value"}
        )
        
        assert result.success
        assert result.metadata["environment"] == "staging"
        assert result.metadata["dry_run"] is True
        assert result.metadata["test"] == "value"
    
    def test_string_representation(self):
        """Test tool string representation."""
        tool = MockTool()
        expected = f"{tool.name}: {tool.description}"
        assert str(tool) == expected

class TestToolResult:
    """Test cases for ToolResult class."""
    
    def test_tool_result_creation(self):
        """Test ToolResult initialization."""
        now = datetime.now()
        result = ToolResult(
            success=True,
            data={"test": "value"},
            error=None,
            execution_time=1.5,
            timestamp=now,
            metadata={"tool": "test"}
        )
        
        assert result.success
        assert result.data == {"test": "value"}
        assert result.error is None
        assert result.execution_time == 1.5
        assert result.timestamp == now
        assert result.metadata == {"tool": "test"}

class TestToolContext:
    """Test cases for ToolContext class."""
    
    def test_tool_context_creation(self):
        """Test ToolContext initialization."""
        context = ToolContext(
            session_id="test_session",
            parameters={"test": "value"},
            environment="production",
            timeout=30,
            dry_run=False,
            metadata={"test": "meta"}
        )
        
        assert context.session_id == "test_session"
        assert context.parameters == {"test": "value"}
        assert context.environment == "production"
        assert context.timeout == 30
        assert not context.dry_run
        assert context.metadata == {"test": "meta"} 
"""Unit tests for the tool registry implementation."""

import pytest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
from k8s_analyzer.tools import (
    ToolRegistry,
    BaseTool, 
    get_tool_registry
)
from k8s_analyzer.tools.exceptions import (
    ToolRegistryError, 
    ToolNotFoundError,
    ToolConfigError
)

class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, config=None, **kwargs):
        """Initialize the mock tool, absorbing any extra kwargs."""
        # Pass only the config parameter to the parent class
        super().__init__(config=config)
    
    @property
    def name(self) -> str:
        return "mock"
    
    @property
    def description(self) -> str:
        return "Mock tool description"

    @property
    def required_permissions(self) -> List[str]:
        return ["mock_permission"]

    def _initialize(self):
        # Mock initialization
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        # Mock parameter validation
        pass

    def _execute(self, context: Any) -> Dict[str, Any]:
        # Mock execution logic
        return {"result": "mock execution result"}
    
    @property
    def is_dangerous(self) -> bool:
        return False

# Autouse fixture to mock environment config for all tests in this module
@pytest.fixture(autouse=True)
def mock_env_config():
    """Mock environment config to avoid kwargs conflicts."""
    # Use the correct path within the __init__ module where get_environment_config is likely defined or imported
    with patch("k8s_analyzer.tools.__init__.get_environment_config") as mock: 
        mock.return_value = {}
        yield mock

@pytest.fixture
def registry():
    """Fixture providing a FRESH, ISOLATED ToolRegistry instance for testing."""
    # Create a new instance for testing instead of using the singleton getter
    registry_instance = ToolRegistry()
    # Reset registry state for each test to ensure isolation
    registry_instance._tools = {}
    registry_instance._tool_classes = {}
    yield registry_instance

class TestToolRegistry:
    """Test cases for ToolRegistry class."""
    
    # This test specifically needs the singleton getter, so it doesn't use the 'registry' fixture
    def test_singleton_pattern(self):
        """TC3_001: Test that registry follows singleton pattern."""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        assert registry1 is registry2
        # Clean up singleton instance after test if necessary for other modules
        if hasattr(ToolRegistry, '_ToolRegistry__instance'):
             ToolRegistry._ToolRegistry__instance = None
    
    # All other tests use the ISOLATED 'registry' fixture
    def test_tool_registration(self, registry):
        """TC3_002: Test successful tool registration."""
        registry.register_tool("mock", MockTool)
        assert "mock" in registry._tool_classes
        assert registry._tool_classes["mock"] == MockTool
    
    def test_duplicate_tool_registration(self, registry):
        """TC3_003: Test registering duplicate tool."""
        registry.register_tool("mock", MockTool)
        with pytest.raises(ToolRegistryError, match="already registered"):
            registry.register_tool("mock", MockTool)
    
    def test_nonexistent_tool_retrieval(self, registry):
        """TC3_004: Test retrieving nonexistent tool."""
        with pytest.raises(ToolNotFoundError, match="not found"):
            registry.get_tool("nonexistent")
    
    def test_tool_listing(self, registry):
        """TC3_005: Test listing registered tools."""
        registry.register_tool("mock1", MockTool)
        registry.register_tool("mock2", MockTool)
        assert "mock1" in registry._tool_classes
        assert "mock2" in registry._tool_classes
        assert len(registry._tool_classes) == 2
    
    def test_registry_reset(self, registry):
        """TC3_006: Test resetting the registry tools cache."""
        # This test implicitly tests get_tool still works with isolation
        registry.register_tool("mock", MockTool)
        tool = registry.get_tool("mock") # Should use the *real* get_tool now
        assert "mock" in registry._tools 
        
        # Reset the tools cache on the isolated instance
        registry._tools = {}
        assert "mock" not in registry._tools
        # Ensure class is still registered
        assert "mock" in registry._tool_classes 
    
    def test_tool_caching(self, registry):
        """TC3_007: Test tool instance caching."""
        registry.register_tool("mock", MockTool)
        tool1 = registry.get_tool("mock")
        tool2 = registry.get_tool("mock")
        assert tool1 is tool2  # Same instance should be returned from the isolated registry
    
    def test_tool_metadata(self, registry):
        """TC3_008: Test accessing tool metadata."""
        registry.register_tool("mock", MockTool)
        tool = registry.get_tool("mock")
        assert tool.name == "mock"
        assert tool.description == "Mock tool description"
        assert tool.required_permissions == ["mock_permission"]
        assert tool.is_dangerous is False
    
    def test_invalid_tool_registration(self, registry):
        """TC3_009: Test registering invalid tool class."""
        with pytest.raises(ToolRegistryError, match="must inherit from BaseTool"):
            registry.register_tool("invalid", object)
    
    def test_null_tool_registration(self, registry):
        """TC3_010: Test registering null tool."""
        with pytest.raises(TypeError, match="issubclass\\(\\) arg 1 must be a class"):
            registry.register_tool("null", None)
    
    def test_tool_dangerous_property(self, registry):
        """TC3_011: Test tool dangerous property."""
        # Create a dangerous mock tool
        class DangerousMockTool(MockTool):
            @property
            def is_dangerous(self) -> bool:
                return True
        
        registry.register_tool("safe", MockTool)
        registry.register_tool("dangerous", DangerousMockTool)
        
        safe_tool = registry.get_tool("safe")
        dangerous_tool = registry.get_tool("dangerous")
        
        assert safe_tool.is_dangerous is False
        assert dangerous_tool.is_dangerous is True
    
    def test_tool_initialization(self, registry):
        """TC3_012: Test tool initialization during get_tool."""
        registry.register_tool("mock", MockTool)
        tool = registry.get_tool("mock")
        
        assert isinstance(tool, MockTool)
        assert tool.name == "mock" 
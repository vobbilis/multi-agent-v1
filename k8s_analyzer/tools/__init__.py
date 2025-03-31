"""Tools module for K8s Analyzer."""

from typing import Dict, Type, Optional, List, Any
from .base import BaseTool, ToolContext
from .kubectl import KubectlTool
from .result import ToolResult
from .config import validate_config, get_environment_config
from .exceptions import (
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

__all__ = [
    "get_tool_registry",
    "BaseTool",
    "ToolResult",
    "ToolContext",
    "KubectlTool",
    "ToolError",
    "ToolConfigError",
    "ToolExecutionError",
    "ToolValidationError",
    "ToolTimeoutError",
    "ToolPermissionError",
    "ToolNotFoundError",
    "ToolRegistryError",
    "ToolDependencyError",
    "ToolStateError"
]

class ToolRegistry:
    """Registry for managing and accessing tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {
            "kubectl": KubectlTool
        }
        validate_config()
    
    def register_tool(self, name: str, tool_class: Type[BaseTool]) -> None:
        """
        Register a new tool class.
        
        Args:
            name: Unique name for the tool
            tool_class: Tool class to register
            
        Raises:
            ToolRegistryError: If registration fails
        """
        if name in self._tool_classes:
            raise ToolRegistryError(f"Tool {name} is already registered")
            
        if not issubclass(tool_class, BaseTool):
            raise ToolRegistryError(
                f"Tool class {tool_class.__name__} must inherit from BaseTool"
            )
            
        self._tool_classes[name] = tool_class
    
    def get_tool(self, name: str, **kwargs) -> BaseTool:
        """
        Get a tool instance by name.
        
        Args:
            name: Name of the tool to get
            **kwargs: Additional configuration for the tool
            
        Returns:
            Instance of the requested tool
            
        Raises:
            ToolNotFoundError: If tool is not found
            ToolConfigError: If tool configuration fails
        """
        # Return cached instance if available
        if name in self._tools:
            return self._tools[name]
            
        # Create new instance
        tool_class = self._tool_classes.get(name)
        if not tool_class:
            raise ToolNotFoundError(f"Tool {name} not found")
            
        try:
            # Add environment config to kwargs
            kwargs.update(get_environment_config())
            tool = tool_class(**kwargs)
            self._tools[name] = tool
            return tool
        except Exception as e:
            raise ToolConfigError(f"Failed to initialize tool {name}: {e}")
    
    def list_tools(self) -> List[BaseTool]:
        """
        Get list of all available tools.
        
        Returns:
            List of tool instances
        """
        return [
            self.get_tool(name)
            for name in self._tool_classes.keys()
        ]
    
    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names."""
        return list(self._tool_classes.keys())
    
    def get_tool_descriptions(self) -> Dict[str, Dict[str, Any]]:
        """Get descriptions of all registered tools."""
        descriptions = {}
        for name in self._tool_classes.keys():
            try:
                # Get tool instance (creates if needed)
                tool = self.get_tool(name)
                descriptions[name] = {
                    "description": getattr(tool, 'description', 'No description available.'),
                    "parameters": getattr(tool, 'parameters', {}), # Assuming parameters schema is an attribute
                    # Add more details if needed, e.g., expected input/output
                }
            except Exception as e:
                 # Log or handle error if a tool fails to initialize during description retrieval
                 print(f"Warning: Could not get description for tool '{name}': {e}") # Basic warning
                 descriptions[name] = {
                     "description": f"Error retrieving description: {e}",
                     "parameters": {}
                 }
        return descriptions
        
    def execute_tool(self, name: str, **parameters) -> ToolResult:
        """
        Execute a tool by name with given parameters.
        
        Args:
            name: Name of the tool to execute
            **parameters: Parameters for the tool's execute method
            
        Returns:
            ToolResult object containing the execution outcome
            
        Raises:
            ToolNotFoundError: If the tool is not registered
            ToolExecutionError: If the tool execution fails
        """
        try:
            tool = self.get_tool(name) # Raises ToolNotFoundError if not found
            # Assuming the tool instance has an 'execute' method
            if not hasattr(tool, 'execute') or not callable(getattr(tool, 'execute')):
                 raise ToolExecutionError(f"Tool '{name}' does not have a callable 'execute' method.")
                 
            # Execute the tool
            result = tool.execute(**parameters)
            
            # Ensure the result is a ToolResult object
            if isinstance(result, ToolResult):
                 return result
            else:
                 # Wrap non-ToolResult outputs for consistency
                 return ToolResult(success=True, data=result)
                 
        except ToolNotFoundError: # Re-raise specific error
             raise
        except Exception as e:
             # Wrap other exceptions in ToolExecutionError
             raise ToolExecutionError(f"Error executing tool '{name}': {e}") from e
    
    def clear_cache(self) -> None:
        """Clear the tool instance cache."""
        self._tools.clear()

# Global registry instance
_registry: Optional[ToolRegistry] = None

def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.
    
    Returns:
        ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

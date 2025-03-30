"""Custom exceptions for K8s Analyzer tools."""

class ToolError(Exception):
    """Base exception for all tool-related errors."""
    pass

class ToolConfigError(ToolError):
    """Raised when there is a configuration error in a tool."""
    pass

class ToolExecutionError(ToolError):
    """Raised when a tool fails during execution."""
    pass

class ToolValidationError(ToolError):
    """Raised when tool parameters or state validation fails."""
    pass

class ToolTimeoutError(ToolError):
    """Raised when a tool execution times out."""
    pass

class ToolPermissionError(ToolError):
    """Raised when there are insufficient permissions to execute a tool."""
    pass

class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found."""
    pass

class ToolRegistryError(ToolError):
    """Raised when there is an error with the tool registry."""
    pass

class ToolDependencyError(ToolError):
    """Raised when a tool's dependencies are not met."""
    pass

class ToolStateError(ToolError):
    """Raised when a tool is in an invalid state."""
    pass

"""
Core module exceptions for the Kubernetes Analyzer.
"""

class K8sAnalyzerError(Exception):
    """Base exception for all k8s analyzer errors."""
    pass

class LLMConfigError(K8sAnalyzerError):
    """Raised when there are issues with LLM configuration."""
    pass

class LLMAPIError(K8sAnalyzerError):
    """Raised when there are issues with LLM API calls."""
    pass

class ToolExecutionError(K8sAnalyzerError):
    """Raised when a tool execution fails."""
    pass

class ContextCollectionError(K8sAnalyzerError):
    """Raised when context collection fails."""
    pass

class PromptLoadError(K8sAnalyzerError):
    """Raised when prompt loading fails."""
    pass

class InvalidToolError(K8sAnalyzerError):
    """Raised when an invalid tool is requested."""
    pass

class HITLError(K8sAnalyzerError):
    """Raised when there are issues with human-in-the-loop interaction."""
    pass

class AnalyzerError(Exception):
    """Base error class for analyzer-related errors."""
    pass

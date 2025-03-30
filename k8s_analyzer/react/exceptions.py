"""Custom exceptions for ReAct agents."""

class ReActError(Exception):
    """Base exception for all ReAct-related errors."""
    pass

class ReActConfigError(ReActError):
    """Raised when there is a configuration error in the ReAct agent."""
    pass

class ReActStateError(ReActError):
    """Raised when there is an error with the agent's state."""
    pass

class ReActToolError(ReActError):
    """Raised when there is an error with a tool execution."""
    pass

class ReActValidationError(ReActError):
    """Raised when there is an error validating actions or responses."""
    pass

class ReActTimeoutError(ReActError):
    """Raised when an operation times out."""
    pass

class ReActMaxIterationsError(ReActError):
    """Raised when the agent reaches maximum iterations without resolution."""
    pass

class ReActHITLError(ReActError):
    """Raised when there is an error in human-in-the-loop interaction."""
    pass

class ReActPromptError(ReActError):
    """Raised when there is an error processing or formatting prompts."""
    pass

class ReActParsingError(ReActError):
    """Raised when there is an error parsing LLM responses or tool outputs."""
    pass

class ReActAbortError(ReActError):
    """Raised when the user aborts the execution."""
    pass

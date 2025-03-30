"""Custom exceptions for LLM-related errors."""

class LLMError(Exception):
    """Base exception for all LLM-related errors."""
    pass

class LLMConfigError(LLMError):
    """Raised when there is a configuration error with the LLM provider."""
    pass

class LLMAPIError(LLMError):
    """Raised when there is an error interacting with the LLM API."""
    pass

class LLMResponseError(LLMError):
    """Raised when there is an error processing the LLM response."""
    pass

class LLMValidationError(LLMError):
    """Raised when there is an error validating LLM input or output."""
    pass

class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""
    pass

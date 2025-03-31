"""ReAct module for K8s Analyzer."""

from typing import Type, Optional
from .base import BaseReActAgent, AgentState
from .agent import ReActAgent
from .config import (
    MAX_ITERATIONS,
    HITL_ENABLED,
    SAFE_ACTIONS,
    DANGEROUS_ACTIONS,
    get_prompt_template
)
from .exceptions import (
    ReActError,
    ReActConfigError,
    ReActStateError,
    ReActToolError,
    ReActValidationError,
    ReActTimeoutError,
    ReActMaxIterationsError,
    ReActHITLError,
    ReActPromptError,
    ReActParsingError
)

__all__ = [
    "get_agent",
    "BaseReActAgent",
    "ReActAgent",
    "AgentState",
    "ReActError",
    "ReActConfigError",
    "ReActStateError",
    "ReActToolError",
    "ReActValidationError",
    "ReActTimeoutError",
    "ReActMaxIterationsError",
    "ReActHITLError",
    "ReActPromptError",
    "ReActParsingError",
    "MAX_ITERATIONS",
    "HITL_ENABLED",
    "SAFE_ACTIONS",
    "DANGEROUS_ACTIONS",
    "get_prompt_template"
]

def get_agent(
    agent_class: Optional[Type[BaseReActAgent]] = None,
    **kwargs
) -> BaseReActAgent:
    """
    Factory function to get a ReAct agent instance.
    
    Args:
        agent_class: Optional agent class override
        **kwargs: Additional configuration for the agent
        
    Returns:
        An instance of the ReAct agent
        
    Raises:
        ReActConfigError: If configuration is invalid
    """
    agent_class = agent_class or ReActAgent
    if not issubclass(agent_class, BaseReActAgent):
        raise ReActConfigError(
            f"Agent class {agent_class.__name__} must inherit from BaseReActAgent"
        )
    return agent_class(**kwargs)

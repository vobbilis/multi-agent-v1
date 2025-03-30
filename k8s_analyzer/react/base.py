"""Base interface for ReAct agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AgentState:
    """State of the ReAct agent during analysis."""
    session_id: str
    history: List[Dict[str, Any]]
    context: Dict[str, Any]
    max_iterations: int
    current_iteration: int = 0
    last_tool_result: Optional[Any] = None
    start_time: datetime = field(default_factory=datetime.now)
    last_llm_reasoning: Optional[str] = None
    
    @property
    def has_reached_max_iterations(self) -> bool:
        """Check if the agent has reached maximum iterations."""
        return self.current_iteration >= self.max_iterations

    def add_interaction(self, role: str, content: Any, action: Optional[Dict] = None):
        """Adds an interaction step to the history."""
        interaction = {
            "role": role,       # e.g., 'llm', 'tool', 'user_feedback'
            "content": content,   # The response text, tool result dict, etc.
            "timestamp": datetime.now().isoformat()
        }
        if action: # Include the action that led to a tool result
             interaction["action"] = action
             
        # Ensure history exists before appending
        if self.history is None:
             self.history = []
             
        self.history.append(interaction)

    # Example method (if needed later)
    # def get_last_observation(self) -> Optional[Any]:

class BaseReActAgent(ABC):
    """Base class for ReAct agents."""
    
    @abstractmethod
    def initialize_state(self, session_id: str, **kwargs) -> None:
        """Initialize or reset the agent state."""
        pass
    
    @abstractmethod
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze a question using the ReAct loop.
        
        Args:
            question: The user's question to analyze
            
        Returns:
            Dict containing analysis results and history
        """
        pass
    
    @abstractmethod
    def propose_actions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Propose next actions based on current context.
        
        Args:
            context: Current analysis context
            
        Returns:
            List of proposed actions with their details
        """
        pass
    
    @abstractmethod
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a chosen action.
        
        Args:
            action: Action details to execute
            
        Returns:
            Results of the action execution
        """
        pass
    
    @abstractmethod
    def get_final_answer(self) -> Dict[str, Any]:
        """Get the final analysis answer."""
        pass
    
    @abstractmethod
    def validate_action(self, action: Dict[str, Any]) -> bool:
        """
        Validate a proposed action.
        
        Args:
            action: Action details to validate
            
        Returns:
            True if action is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def format_history(self) -> List[Dict[str, Any]]:
        """Format the analysis history for presentation."""
        pass

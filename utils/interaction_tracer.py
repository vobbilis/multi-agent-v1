"""
Interaction Tracer for Agent Collaborations

This module provides utilities for tracing and logging interactions
between the master agent and specialist agents during investigations.
"""

import os
import logging
import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InteractionTracer:
    """
    Traces and logs interactions between agents during an investigation.
    """
    
    def __init__(self, log_dir: str = "output/logs"):
        """
        Initialize the interaction tracer.
        
        Args:
            log_dir: Directory to store interaction logs
        """
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize interaction log
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"agent_interactions_{current_time}.log")
        self.interactions = []
        
        logger.info(f"Interaction tracing initialized, logs will be saved to {self.log_file}")
    
    def record_interaction(self, 
                           from_agent: str, 
                           to_agent: str, 
                           message: str,
                           timestamp: Optional[str] = None) -> None:
        """
        Record an interaction between agents.
        
        Args:
            from_agent: The agent initiating the interaction
            to_agent: The agent receiving the interaction
            message: The content of the interaction
            timestamp: Optional timestamp (if not provided, current time will be used)
        """
        if not timestamp:
            timestamp = datetime.datetime.now().isoformat()
        
        interaction = {
            "timestamp": timestamp,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message": message
        }
        
        self.interactions.append(interaction)
        
        # Log to file
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {from_agent} → {to_agent} | {message}\n\n")
        
        logger.debug(f"Recorded interaction: {from_agent} → {to_agent}: {message}")
    
    def record_action(self, 
                     agent: str, 
                     action_type: str,
                     action_description: str,
                     timestamp: Optional[str] = None) -> None:
        """
        Record an action taken by an agent.
        
        Args:
            agent: The agent performing the action
            action_type: Type of action (e.g., "analyzing", "collecting", "deciding")
            action_description: Description of the action
            timestamp: Optional timestamp (if not provided, current time will be used)
        """
        if not timestamp:
            timestamp = datetime.datetime.now().isoformat()
        
        action = {
            "timestamp": timestamp,
            "agent": agent,
            "action_type": action_type,
            "action_description": action_description
        }
        
        # Log to file
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {agent} | {action_type}: {action_description}\n\n")
        
        logger.debug(f"Recorded action: {agent} - {action_type}: {action_description}")
    
    def get_interactions(self) -> List[Dict[str, Any]]:
        """
        Get all recorded interactions.
        
        Returns:
            List of interaction dictionaries
        """
        return self.interactions
    
    def get_log_file_path(self) -> str:
        """
        Get the path to the current log file.
        
        Returns:
            Path to the log file
        """
        return self.log_file

# Global tracer instance for use across modules
_tracer = None

def get_tracer() -> InteractionTracer:
    """
    Get the global interaction tracer instance.
    
    Returns:
        InteractionTracer instance
    """
    global _tracer
    if _tracer is None:
        _tracer = InteractionTracer()
    return _tracer 
"""
Agent Interaction Tracer for Kubernetes Root Cause Analysis
"""
import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional

# Setup dedicated logging for agent interactions
# Create a specific formatter for agent interactions
agent_formatter = logging.Formatter('%(message)s')

# Create a file handler for agent interactions
os.makedirs("output/logs", exist_ok=True)
agent_handler = logging.FileHandler("output/logs/agent_interactions.log", mode='w')
agent_handler.setFormatter(agent_formatter)

# Create a dedicated logger for agent interactions
agent_logger = logging.getLogger("agent_interactions")
agent_logger.setLevel(logging.INFO)
agent_logger.addHandler(agent_handler)
agent_logger.propagate = False  # Don't propagate to root logger

# Setup regular logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentInteractionTracer:
    """
    Tracer for logging interactions between agents in the workflow.
    Keeps a record of all agent interactions and can output to logs and files.
    """
    
    def __init__(self, 
                 log_to_file: bool = True, 
                 log_dir: str = "output/logs",
                 include_state: bool = False):
        """
        Initialize the tracer
        
        Args:
            log_to_file: Whether to log interactions to a file
            log_dir: Directory to save log files
            include_state: Whether to include the full state in logs
        """
        self.interactions = []
        self.log_to_file = log_to_file
        self.log_dir = log_dir
        self.include_state = include_state
        self.investigation_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.log_to_file:
            os.makedirs(log_dir, exist_ok=True)
            self.log_file = os.path.join(log_dir, f"agent_interactions_{self.investigation_id}.log")
            self.json_file = os.path.join(log_dir, f"agent_interactions_{self.investigation_id}.json")
            
            # Update file handler to point to this specific log file
            for handler in agent_logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    agent_logger.removeHandler(handler)
            
            # Add new file handler for this investigation
            file_handler = logging.FileHandler(self.log_file, mode='w')
            file_handler.setFormatter(agent_formatter)
            agent_logger.addHandler(file_handler)
            
            # Initialize log file with header
            with open(self.log_file, 'w') as f:
                f.write(f"=== Kubernetes RCA Agent Interactions (Investigation: {self.investigation_id}) ===\n\n")
    
    def log_interaction(self, 
                        from_agent: str, 
                        to_agent: str, 
                        message: str, 
                        state: Optional[Dict[str, Any]] = None,
                        data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an interaction between agents
        
        Args:
            from_agent: Source agent identifier
            to_agent: Destination agent identifier
            message: Description of the interaction
            state: Current workflow state (optional)
            data: Additional data about the interaction (optional)
        """
        timestamp = datetime.datetime.now().isoformat()
        
        interaction = {
            "timestamp": timestamp,
            "from": from_agent,
            "to": to_agent,
            "message": message
        }
        
        if data:
            interaction["data"] = data
            
        if state and self.include_state:
            interaction["state"] = state
        
        self.interactions.append(interaction)
        
        # Log to console and agent interactions logger
        formatted_message = f"AGENT INTERACTION: {from_agent} → {to_agent} | {message}"
        agent_logger.info(formatted_message)
        logger.info(formatted_message)
        
        # Log to file if enabled
        if self.log_to_file:
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] {from_agent} → {to_agent} | {message}\n")
                if data:
                    f.write(f"    Data: {json.dumps(data, indent=2)}\n")
                f.write("\n")
    
    def log_agent_action(self,
                         agent: str,
                         action: str,
                         details: str = "",
                         state: Optional[Dict[str, Any]] = None,
                         data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an action taken by an agent
        
        Args:
            agent: Agent identifier
            action: Action description
            details: Additional details about the action
            state: Current workflow state (optional)
            data: Additional data about the action (optional)
        """
        timestamp = datetime.datetime.now().isoformat()
        
        interaction = {
            "timestamp": timestamp,
            "agent": agent,
            "action": action,
            "details": details
        }
        
        if data:
            interaction["data"] = data
            
        if state and self.include_state:
            interaction["state"] = state
        
        self.interactions.append(interaction)
        
        # Log to console and agent interactions logger
        formatted_message = f"AGENT ACTION: {agent} | {action}{': ' + details if details else ''}"
        agent_logger.info(formatted_message)
        logger.info(formatted_message)
        
        # Log to file if enabled
        if self.log_to_file:
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] {agent} | {action}{': ' + details if details else ''}\n")
                if data:
                    f.write(f"    Data: {json.dumps(data, indent=2)}\n")
                f.write("\n")
    
    def save_interactions(self) -> None:
        """Save all interactions to a JSON file"""
        if self.log_to_file:
            with open(self.json_file, 'w') as f:
                json.dump(self.interactions, f, indent=2)
            logger.info(f"Saved {len(self.interactions)} interactions to {self.json_file}")
    
    def get_interactions(self) -> List[Dict[str, Any]]:
        """Get all recorded interactions"""
        return self.interactions
    
    def get_agent_interactions(self, agent: str) -> List[Dict[str, Any]]:
        """
        Get all interactions involving a specific agent
        
        Args:
            agent: Agent identifier
            
        Returns:
            List of interactions involving the agent
        """
        return [
            interaction for interaction in self.interactions 
            if (interaction.get("from") == agent or 
                interaction.get("to") == agent or 
                interaction.get("agent") == agent)
        ]
    
    def get_phase_transitions(self) -> List[Dict[str, Any]]:
        """Get all phase transition interactions"""
        return [
            interaction for interaction in self.interactions
            if interaction.get("message", "").startswith("Investigation advancing from")
        ]
    
    def summarize_interactions(self) -> Dict[str, Any]:
        """Generate a summary of all interactions"""
        agents_involved = set()
        phases = []
        actions_by_agent = {}
        
        for interaction in self.interactions:
            if "from" in interaction and "to" in interaction:
                agents_involved.add(interaction["from"])
                agents_involved.add(interaction["to"])
                
                # Count agent interactions
                from_agent = interaction["from"]
                if from_agent not in actions_by_agent:
                    actions_by_agent[from_agent] = 0
                actions_by_agent[from_agent] += 1
                
            elif "agent" in interaction:
                agents_involved.add(interaction["agent"])
                
                # Count agent actions
                agent = interaction["agent"]
                if agent not in actions_by_agent:
                    actions_by_agent[agent] = 0
                actions_by_agent[agent] += 1
            
            # Track phase transitions
            if interaction.get("message", "").startswith("Investigation advancing from"):
                phase_info = interaction["message"].replace("Investigation advancing from ", "").split(" to ")
                if len(phase_info) == 2:
                    phases.append({
                        "from": phase_info[0],
                        "to": phase_info[1],
                        "timestamp": interaction["timestamp"]
                    })
        
        return {
            "investigation_id": self.investigation_id,
            "total_interactions": len(self.interactions),
            "agents_involved": list(agents_involved),
            "phase_transitions": phases,
            "actions_by_agent": actions_by_agent
        }
    
    def print_summary(self) -> None:
        """Print a summary of the interactions"""
        summary = self.summarize_interactions()
        
        print("\n=== AGENT INTERACTION SUMMARY ===")
        print(f"Investigation ID: {summary['investigation_id']}")
        print(f"Total Interactions: {summary['total_interactions']}")
        
        print("\nAgents Involved:")
        for agent in summary['agents_involved']:
            print(f"- {agent}")
        
        print("\nPhase Transitions:")
        for phase in summary['phase_transitions']:
            print(f"- {phase['from']} → {phase['to']} ({phase['timestamp']})")
        
        print("\nActions by Agent:")
        for agent, count in summary['actions_by_agent'].items():
            print(f"- {agent}: {count} actions")
        
        if self.log_to_file:
            print(f"\nDetailed logs saved to: {self.log_file}")
            print(f"JSON data saved to: {self.json_file}") 
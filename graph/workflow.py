"""
LangGraph workflow for Kubernetes Root Cause Analysis
"""
import os
import json
import logging
import datetime
from typing import Dict, List, Any, Annotated, TypedDict, Union

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END

# Import agents
# In a real implementation, these would be imported from the agents package
from agents.master_agent import MasterAgent
from agents.network_agent import NetworkAgent
from agents.metrics_agent import MetricsAgent
from agents.cluster_agent import ClusterAgent

# Import interaction tracer
from utils.interaction import tracer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the state type
class AgentState(TypedDict):
    """State maintained and passed between agents in the workflow"""
    # Core investigation data
    initial_symptoms: str
    investigation_phase: str
    evidence: List[Dict[str, Any]]
    findings: Dict[str, Dict[str, Any]]
    
    # Reasoning data
    current_hypothesis: Dict[str, Any]
    confidence_scores: Dict[str, float]
    specialist_agents_to_activate: List[str]
    
    # Results
    root_causes: List[Dict[str, Any]]
    next_actions: List[str]
    recommendations: List[Dict[str, Any]]
    prevention_measures: List[str]
    
    # Metadata
    timestamp: str
    confidence_history: Dict[str, Dict[str, float]]

def create_k8s_rca_workflow() -> StateGraph:
    """
    Create a LangGraph workflow for Kubernetes root cause analysis
    
    Returns:
        StateGraph: Compiled workflow graph
    """
    # Create master and specialist agents
    master_agent = MasterAgent(explain_reasoning=True)
    network_agent = NetworkAgent()
    metrics_agent = MetricsAgent()
    cluster_agent = ClusterAgent()
    # Add other specialist agents here
    # workload_agent = WorkloadAgent()
    # config_agent = ConfigAgent()
    # state_agent = StateAgent()
    # logs_agent = LogsAgent()
    # security_agent = SecurityAgent()
    
    # Define augmented versions of agents that include interaction tracing
    def master_with_tracing(state: Dict[str, Any]) -> Dict[str, Any]:
        """Master agent with interaction tracing"""
        # Log the entry to master agent
        tracer.log_agent_action(
            agent="master",
            action="processing",
            details=f"Phase: {state.get('investigation_phase', 'unknown')}",
            data={"symptoms": state.get("initial_symptoms", "")[:100] + "..."}
        )
        
        # Process state with master agent
        result = master_agent(state)
        
        # Log the interactions with specialist agents
        for specialist in result.get("specialist_agents_to_activate", []):
            tracer.log_interaction(
                from_agent="master",
                to_agent=specialist,
                message=f"Activating specialist agent for {result.get('investigation_phase', 'investigation')}"
            )
        
        # Save a snapshot of interactions so far
        tracer.save_interactions()
        
        return result
    
    def network_with_tracing(state: Dict[str, Any]) -> Dict[str, Any]:
        """Network agent with interaction tracing"""
        # Log the entry to network agent
        tracer.log_agent_action(
            agent="network",
            action="investigating",
            details="Analyzing network configurations and connectivity"
        )
        
        # Process state with network agent
        result = network_agent(state)
        
        # Log the completion
        findings = result.get("findings", {})
        evidence_count = len(result.get("evidence", []))
        confidence = result.get("confidence_scores", {}).get("network", 0)
        
        tracer.log_interaction(
            from_agent="network",
            to_agent="master",
            message=f"Completed network analysis with {evidence_count} evidence items ({int(confidence*100)}% confidence)",
            data={"findings_keys": list(findings.keys())}
        )
        
        # Save a snapshot of interactions
        tracer.save_interactions()
        
        return result
    
    def metrics_with_tracing(state: Dict[str, Any]) -> Dict[str, Any]:
        """Metrics agent with interaction tracing"""
        # Log the entry to metrics agent
        tracer.log_agent_action(
            agent="metrics",
            action="investigating",
            details="Analyzing resource utilization and performance metrics"
        )
        
        # Process state with metrics agent
        result = metrics_agent(state)
        
        # Log the completion
        findings = result.get("findings", {})
        evidence_count = len(result.get("evidence", []))
        confidence = result.get("confidence_scores", {}).get("metrics", 0)
        
        tracer.log_interaction(
            from_agent="metrics",
            to_agent="master",
            message=f"Completed metrics analysis with {evidence_count} evidence items ({int(confidence*100)}% confidence)",
            data={"findings_keys": list(findings.keys())}
        )
        
        # Save a snapshot of interactions
        tracer.save_interactions()
        
        return result
    
    def cluster_with_tracing(state: Dict[str, Any]) -> Dict[str, Any]:
        """Cluster agent with interaction tracing"""
        # Log the entry to cluster agent
        tracer.log_agent_action(
            agent="cluster",
            action="investigating",
            details="Analyzing cluster state and node conditions"
        )
        
        # Process state with cluster agent
        result = cluster_agent(state)
        
        # Log the completion
        findings = result.get("findings", {})
        evidence_count = len(result.get("evidence", []))
        confidence = result.get("confidence_scores", {}).get("cluster", 0)
        
        tracer.log_interaction(
            from_agent="cluster",
            to_agent="master",
            message=f"Completed cluster analysis with {evidence_count} evidence items ({int(confidence*100)}% confidence)",
            data={"findings_keys": list(findings.keys())}
        )
        
        # Save a snapshot of interactions
        tracer.save_interactions()
        
        return result
    
    # Define the workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph with tracing wrappers
    workflow.add_node("master", master_with_tracing)
    workflow.add_node("network_analysis", network_with_tracing)
    workflow.add_node("metrics_analysis", metrics_with_tracing)
    workflow.add_node("cluster_analysis", cluster_with_tracing)
    # Add other specialist agent nodes
    # workflow.add_node("workload_analysis", workload_agent)
    # workflow.add_node("config_analysis", config_agent)
    # workflow.add_node("state_analysis", state_agent)
    # workflow.add_node("logs_analysis", logs_agent)
    # workflow.add_node("security_analysis", security_agent)
    
    # Define conditional routing based on investigation phase and specialist agent activation
    def route_by_master_decision(state: AgentState) -> Union[List[str], str]:
        """
        Route to the next node(s) based on master agent decision
        
        Args:
            state: Current workflow state
            
        Returns:
            Union[List[str], str]: Next node(s) to execute
        """
        # Check if investigation is complete
        if state.get("investigation_phase") == "complete":
            tracer.log_agent_action(
                agent="workflow",
                action="completing",
                details="Investigation complete, ending workflow"
            )
            logger.info("Investigation complete, ending workflow")
            return END
        
        # Get specialist agents to activate
        agents_to_activate = state.get("specialist_agents_to_activate", [])
        
        if not agents_to_activate:
            # If no specialists to activate, return to master
            tracer.log_agent_action(
                agent="workflow",
                action="routing",
                details="No specialist agents to activate, returning to master"
            )
            logger.info("No specialist agents to activate, returning to master")
            return "master"
        
        # Map agent types to node names
        agent_map = {
            "network": "network_analysis",
            "metrics": "metrics_analysis",
            "cluster": "cluster_analysis",
            # Add mappings for other agent types
            # "workload": "workload_analysis",
            # "config": "config_analysis",
            # "state": "state_analysis",
            # "logs": "logs_analysis",
            # "security": "security_analysis"
        }
        
        # Get node names for agents to activate
        nodes_to_activate = [agent_map.get(agent_type) for agent_type in agents_to_activate 
                           if agent_type in agent_map]
        
        if not nodes_to_activate:
            # If no valid specialist nodes, return to master
            tracer.log_agent_action(
                agent="workflow",
                action="routing",
                details="No valid specialist nodes to activate, returning to master"
            )
            logger.info("No valid specialist nodes to activate, returning to master")
            return "master"
        
        # Log the routing decision
        tracer.log_agent_action(
            agent="workflow",
            action="routing",
            details=f"Routing to specialist agent(s): {nodes_to_activate}"
        )
        logger.info(f"Routing to specialist agent(s): {nodes_to_activate}")
        
        # If only one node, return it as string, otherwise as list
        if len(nodes_to_activate) == 1:
            return nodes_to_activate[0]
        return nodes_to_activate
    
    # Add conditional edges from master to specialist agents
    workflow.add_conditional_edges(
        "master",
        route_by_master_decision
    )
    
    # Add edges from specialist agents back to master
    workflow.add_edge("network_analysis", "master")
    workflow.add_edge("metrics_analysis", "master")
    workflow.add_edge("cluster_analysis", "master")
    # Add edges for other specialist agents
    # workflow.add_edge("workload_analysis", "master")
    # workflow.add_edge("config_analysis", "master")
    # workflow.add_edge("state_analysis", "master")
    # workflow.add_edge("logs_analysis", "master")
    # workflow.add_edge("security_analysis", "master")
    
    # Set entry point
    workflow.set_entry_point("master")
    
    return workflow

# Create and compile the workflow
k8s_rca_app = create_k8s_rca_workflow().compile()

def run_investigation(symptoms: str) -> Dict[str, Any]:
    """
    Run a Kubernetes root cause analysis investigation
    
    Args:
        symptoms: Description of the symptoms or issues
        
    Returns:
        Dict: Investigation results
    """
    # Start a new investigation in the tracer
    tracer.log_agent_action(
        agent="workflow",
        action="starting",
        details=f"Starting investigation with symptoms: {symptoms[:100]}..."
    )
    
    # Create initial state with symptoms
    initial_state = {
        "investigation_phase": "initial_assessment",
        "initial_symptoms": symptoms,
        "evidence": [],
        "findings": {},
        "current_hypothesis": {},
        "confidence_scores": {},
        "specialist_agents_to_activate": [],
        "root_causes": [],
        "next_actions": [],
        "recommendations": [],
        "prevention_measures": [],
        "timestamp": datetime.datetime.now().isoformat(),
        "confidence_history": {}
    }
    
    # Run the investigation
    logger.info(f"Starting investigation with symptoms: {symptoms}")
    result = k8s_rca_app.invoke(initial_state)
    
    # Log completion and save final interactions
    tracer.log_agent_action(
        agent="workflow",
        action="completed",
        details=f"Investigation completed with phase: {result.get('investigation_phase', 'unknown')}"
    )
    tracer.save_interactions()
    
    # Print interaction summary
    tracer.print_summary()
    
    return result

# Example usage
if __name__ == "__main__":
    # Define symptoms
    symptoms = """
    Several pods in the production namespace keep restarting with CrashLoopBackOff status.
    The application logs show connection timeouts when trying to reach the database service.
    This started approximately 30 minutes after a network policy update was applied.
    Some pods are also showing high CPU utilization and memory pressure.
    Control plane nodes are reporting disk pressure warnings.
    """
    
    # Run the investigation
    result = run_investigation(symptoms)
    
    # Print key results
    print("\n=== Investigation Results ===\n")
    print(f"Investigation Phase: {result.get('investigation_phase')}")
    
    print("\nRoot Causes:")
    for cause in result.get("root_causes", []):
        print(f"- {cause.get('category')}: {cause.get('description')} (Confidence: {cause.get('confidence', 0)*100:.1f}%)")
    
    print("\nRecommended Actions:")
    for i, action in enumerate(result.get("next_actions", []), 1):
        print(f"{i}. {action}")
        
    print("\nConfidence Scores:")
    for area, score in result.get("confidence_scores", {}).items():
        print(f"- {area}: {score*100:.1f}%") 
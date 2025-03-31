#!/usr/bin/env python3
"""
Test script for a complete K8s root cause analysis workflow.

This script simulates a full investigation with all specialist agents,
including the newly added logs and events agents.
"""

import logging
import json
import datetime
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

from agents.master_agent import MasterAgent
from agents.logs_agent import LogsAgent, Task as LogsTask
from agents.events_agent import EventsAgent, Task as EventsTask
from utils.interaction_tracer import get_tracer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Mock responses for master agent
MOCK_INITIAL_ASSESSMENT = {
    "reasoning": "The symptoms describe a web pod that is constantly crashing with CrashLoopBackOff status and showing connection timeout errors in the logs. This indicates several potential issues: application errors, connectivity problems, resource constraints, or configuration issues.",
    "investigation_phase": "initial_assessment",
    "initial_hypothesis": "The pod is crashing due to connection timeout errors when trying to reach a dependent service or database. This may be caused by network connectivity issues, service unavailability, resource constraints, or incorrect configuration.",
    "specialist_agents_to_activate": ["logs", "events", "network"],
    "confidence_scores": {
        "application_error": 0.75,
        "connectivity_issue": 0.85,
        "resource_constraints": 0.60,
        "configuration_error": 0.72
    }
}

MOCK_HYPOTHESIS_TESTING = {
    "reasoning": "Based on the findings from the specialist agents, we can see that both logs and events data indicate connectivity problems. The logs show connection timeout errors and the events show network policy issues affecting communication between services. The network analysis confirms traffic blocking between certain services.",
    "investigation_phase": "root_cause_determination",
    "root_causes": [
        {
            "category": "network_configuration",
            "component": "network_policy",
            "description": "Restrictive network policies are blocking communication between the web pod and its dependent services, causing connection timeouts and pod crashes.",
            "confidence": 0.90
        },
        {
            "category": "service_dependency",
            "component": "backend_service",
            "description": "The backend service that the web pod depends on is unreachable, possibly due to incorrect service configuration or being in a different namespace with restricted access.",
            "confidence": 0.85
        }
    ],
    "next_actions": [
        "Review network policies affecting the web pod namespace",
        "Check if the dependent service is running and healthy",
        "Verify service DNS resolution is working correctly",
        "Check for namespace isolation preventing cross-namespace communication",
        "Examine pod security policies that might restrict network access"
    ],
    "confidence_scores": {
        "network_configuration": 0.90,
        "service_dependency": 0.85,
        "application_error": 0.45,
        "resource_constraints": 0.30
    }
}

def simulate_workflow(symptoms: str):
    """
    Simulate a full investigation workflow with all specialist agents.
    
    Args:
        symptoms: The symptoms to investigate
    """
    logger.info(f"Starting investigation with symptoms: {symptoms}")
    
    # Get the interaction tracer
    tracer = get_tracer()
    tracer.record_action("workflow", "starting", f"Investigation for: {symptoms}")
    
    # Initialize the master agent (with mocking)
    master_agent = MasterAgent(explain_reasoning=True)
    
    # Initial state with symptoms
    initial_state = {
        "investigation_phase": "initial_assessment",
        "initial_symptoms": symptoms
    }
    
    # Process initial state - this would trigger specialist agent activation
    tracer.record_action("workflow", "processing", "Initial assessment phase")
    
    # Mock the master agent's call to avoid API usage
    with patch.object(master_agent, '__call__', return_value=MOCK_INITIAL_ASSESSMENT):
        result = master_agent(initial_state)
    
    # Record the master agent's reasoning
    tracer.record_action("master", "reasoning", result.get("reasoning", "No reasoning provided"))
    
    # Get the specialist agents to activate
    specialist_agents = result.get("specialist_agents_to_activate", [])
    tracer.record_action("master", "activating", f"Specialist agents: {', '.join(specialist_agents)}")
    
    # Simulate findings from specialist agents
    findings = {}
    
    # For each specialist agent, simulate their investigation
    for agent_type in specialist_agents:
        if agent_type == "logs":
            # Simulate logs agent
            tracer.record_interaction("master", "logs", "Requesting logs analysis")
            logs_agent = LogsAgent(use_mock=True)
            logs_task = LogsTask(
                description=f"Investigate logs related to: {symptoms}",
                type="logs_analysis",
                priority="high"
            )
            
            tracer.record_action("logs", "collecting", "Gathering container logs")
            
            # Mock the logs agent's investigate method
            with patch.object(logs_agent, 'analyze_evidence') as mock_analyze:
                evidence = logs_agent.collect_logs_evidence(logs_task)
                mock_finding = logs_agent.Finding(
                    agent_type="logs",
                    evidence=evidence,
                    analysis="Logs show connection timeout errors when attempting to reach backend services. Multiple retries failing.",
                    confidence=0.88,
                    potential_issues=[
                        "Connection timeout to dependent services",
                        "Network policies blocking communication",
                        "Service DNS resolution failures",
                        "Backend service unavailable or misconfigured"
                    ]
                )
                mock_analyze.return_value = mock_finding
                logs_finding = logs_agent.investigate(logs_task)
            
            # Convert finding to dictionary for the master agent
            findings["logs"] = logs_finding.to_dict()
            tracer.record_interaction("logs", "master", "Logs analysis complete")
            
        elif agent_type == "events":
            # Simulate events agent
            tracer.record_interaction("master", "events", "Requesting events analysis")
            events_agent = EventsAgent(use_mock=True)
            events_task = EventsTask(
                description=f"Investigate Kubernetes events related to: {symptoms}",
                type="events_analysis",
                priority="high"
            )
            
            tracer.record_action("events", "collecting", "Gathering Kubernetes events")
            
            # Mock the events agent's investigate method
            with patch.object(events_agent, 'analyze_evidence') as mock_analyze:
                evidence = events_agent.collect_events_evidence(events_task)
                mock_finding = events_agent.Finding(
                    agent_type="events",
                    evidence=evidence,
                    analysis="Kubernetes events show multiple pod restarts and network policy events affecting pod connectivity.",
                    confidence=0.85,
                    potential_issues=[
                        "Pod restarts due to application failures",
                        "NetworkPolicy application events coinciding with failures",
                        "Container terminations due to health check failures",
                        "Service endpoint changes during the crash period"
                    ]
                )
                mock_analyze.return_value = mock_finding
                events_finding = events_agent.investigate(events_task)
            
            # Convert finding to dictionary for the master agent
            findings["events"] = events_finding.to_dict()
            tracer.record_interaction("events", "master", "Events analysis complete")
            
        elif agent_type == "network":
            # Simulate network agent
            tracer.record_interaction("master", "network", "Requesting network analysis")
            tracer.record_action("network", "analyzing", "Checking network policies")
            
            # Mock network agent finding
            findings["network"] = {
                "agent_type": "network",
                "analysis": "Network analysis shows restrictive network policies blocking connectivity between the web pod and backend services.",
                "confidence": 0.92,
                "potential_issues": [
                    "NetworkPolicy restricting egress traffic",
                    "Service connection failing due to namespace isolation",
                    "DNS resolution working but connection blocked",
                    "Ingress/egress rules mismatch between namespaces"
                ]
            }
            tracer.record_interaction("network", "master", "Network analysis complete")
            
        elif agent_type == "metrics":
            # Simulate metrics agent
            tracer.record_interaction("master", "metrics", "Requesting metrics analysis")
            tracer.record_action("metrics", "collecting", "Gathering pod resource usage")
            
            # Mock metrics agent finding
            findings["metrics"] = {
                "agent_type": "metrics",
                "analysis": "Metrics show resource constraints affecting pods.",
                "confidence": 0.78,
                "potential_issues": [
                    "Memory usage exceeding limits",
                    "CPU throttling detected",
                    "High disk IO wait times",
                    "Network bandwidth saturation"
                ]
            }
            tracer.record_interaction("metrics", "master", "Metrics analysis complete")
            
        elif agent_type == "cluster":
            # Simulate cluster agent
            tracer.record_interaction("master", "cluster", "Requesting cluster analysis")
            tracer.record_action("cluster", "analyzing", "Examining node and cluster state")
            
            # Mock cluster agent finding
            findings["cluster"] = {
                "agent_type": "cluster",
                "analysis": "Cluster analysis shows node pressure affecting pod scheduling.",
                "confidence": 0.82,
                "potential_issues": [
                    "Node memory pressure",
                    "Insufficient resources for scheduling",
                    "Taint/toleration preventing scheduling",
                    "Node selector constraints"
                ]
            }
            tracer.record_interaction("cluster", "master", "Cluster analysis complete")
    
    # Update state with findings from specialist agents
    updated_state = result.copy()
    updated_state["findings"] = findings
    
    # Proceed to hypothesis testing phase
    updated_state["investigation_phase"] = "hypothesis_testing"
    tracer.record_action("workflow", "processing", "Hypothesis testing phase")
    
    # Process updated state with findings - using mock response
    with patch.object(master_agent, '__call__', return_value=MOCK_HYPOTHESIS_TESTING):
        final_result = master_agent(updated_state)
    
    # Record the master agent's final determination
    tracer.record_action("master", "determining", "Finalizing root cause analysis")
    
    # Generate output files
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/investigations/test_workflow_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(final_result, f, indent=2)
    
    logger.info(f"Investigation complete, results saved to {output_file}")
    logger.info(f"Interaction log saved to {tracer.get_log_file_path()}")
    
    return final_result, tracer.get_log_file_path()

if __name__ == "__main__":
    # Test with different scenarios that would engage different specialist agents
    
    # Scenario 1: Pod crashing - logs and events agents
    symptoms1 = "My web pod is constantly crashing with CrashLoopBackOff and the logs show connection timeout errors"
    
    # Scenario 2: Service connectivity - network agent
    symptoms2 = "My service is not accessible from outside the cluster, but pods are running fine"
    
    # Scenario 3: Image pull error - events agent
    symptoms3 = "My deployment is stuck with ImagePullBackOff errors"
    
    # Run the scenario
    result, log_path = simulate_workflow(symptoms1)
    
    # Print results
    print("\n=== Investigation Results ===")
    print(f"Symptoms: {symptoms1}")
    print(f"Root Causes:")
    for cause in result.get("root_causes", []):
        print(f"- {cause.get('category')}: {cause.get('component')} - {cause.get('description')}")
    print(f"\nConfidence: {max(result.get('confidence_scores', {}).values()) * 100:.1f}%")
    print(f"\nLog file: {log_path}")
    print("\nSpecialist agents activated:")
    for agent in result.get("specialist_agents_to_activate", []):
        print(f"- {agent}") 
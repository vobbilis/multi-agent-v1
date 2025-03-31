#!/usr/bin/env python3
"""
Test script for the Logs and Events specialist agents
"""
import sys
import logging
import json
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from agents.logs_agent import LogsAgent, Task as LogsTask, Finding, Evidence
from agents.events_agent import EventsAgent, Task as EventsTask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Mock LLM responses
MOCK_LOGS_RESPONSE = {
    "analysis": "The logs indicate a database connection failure leading to container crashes. The primary issue appears to be the database container failing with 'out of memory' errors and connection issues.",
    "confidence": 0.85,
    "potential_issues": [
        "Out of memory condition in the database container",
        "Database connection failures",
        "Resource constraints leading to container termination",
        "Possible configuration issue with database parameters",
        "Potential memory leak in the database process"
    ],
    "error_patterns": [
        {
            "pattern": "ERROR: out of memory",
            "frequency": "Multiple occurrences",
            "severity": "High",
            "description": "The database container is experiencing memory pressure"
        },
        {
            "pattern": "ERROR: connection refused",
            "frequency": "Repeated",
            "severity": "High",
            "description": "Connection attempts to the database are being rejected"
        }
    ],
    "related_components": ["database", "backend"]
}

MOCK_EVENTS_RESPONSE = {
    "analysis": "Kubernetes events show that the chaos-dashboard pod in the chaos-testing namespace is experiencing image pull failures. The container runtime cannot pull the specified image 'ghcr.io/chaos-mesh/chaos-dashboard:v2.6.1'.",
    "confidence": 0.92,
    "potential_issues": [
        "Image pull failures for chaos-dashboard pod",
        "Registry connectivity issues",
        "Invalid image reference",
        "Missing or invalid registry credentials",
        "Network issues preventing image downloads"
    ],
    "significant_events": [
        {
            "type": "Warning",
            "reason": "Failed",
            "description": "Pod cannot start due to image pull failures",
            "impact": "The chaos-dashboard pod cannot become ready, preventing access to the UI",
            "related_resources": ["chaos-dashboard pod", "container registry"]
        }
    ],
    "timeline": "Multiple image pull failures over the last 10 minutes with the latest attempt 2 minutes ago",
    "affected_components": ["chaos-dashboard pod", "image registry connectivity"]
}

def test_logs_agent():
    """Test the Logs specialist agent with a sample task"""
    logger.info("Testing Logs specialist agent...")
    
    # Create a logs agent with mock data
    logs_agent = LogsAgent(use_mock=True)
    
    # Create a sample task for investigation
    task = LogsTask(
        description="Investigate logs for pod database in namespace default that's showing CrashLoopBackOff",
        type="logs_analysis",
        priority="high"
    )
    
    # Mock the LLM response to avoid API calls
    with patch('agents.logs_agent.LogsAgent.analyze_evidence', autospec=True) as mock_analyze:
        # Create a mock finding to return
        mock_finding = Finding(
            agent_type="logs",
            evidence=logs_agent.collect_logs_evidence(task),
            analysis=MOCK_LOGS_RESPONSE["analysis"],
            confidence=MOCK_LOGS_RESPONSE["confidence"],
            potential_issues=MOCK_LOGS_RESPONSE["potential_issues"]
        )
        
        # Configure the mock to return our predefined response
        mock_analyze.return_value = mock_finding
        
        # Run the investigation
        finding = logs_agent.investigate(task)
    
    # Print the results
    print("\n=== Logs Agent Finding ===")
    print(f"Analysis: {finding.analysis}")
    print(f"Confidence: {finding.confidence * 100:.1f}%")
    print("Potential issues:")
    for issue in finding.potential_issues:
        print(f"- {issue}")
    print()
    
    # Return the finding for further use if needed
    return finding

def test_events_agent():
    """Test the Events specialist agent with a sample task"""
    logger.info("Testing Events specialist agent...")
    
    # Create an events agent with mock data
    events_agent = EventsAgent(use_mock=True)
    
    # Create a sample task for investigation
    task = EventsTask(
        description="Investigate Kubernetes events for pod chaos-dashboard in namespace chaos-testing that's not starting",
        type="events_analysis",
        priority="high"
    )
    
    # Mock the LLM response to avoid API calls
    with patch('agents.events_agent.EventsAgent.analyze_evidence', autospec=True) as mock_analyze:
        # Create a mock finding to return
        mock_finding = Finding(
            agent_type="events",
            evidence=events_agent.collect_events_evidence(task),
            analysis=MOCK_EVENTS_RESPONSE["analysis"],
            confidence=MOCK_EVENTS_RESPONSE["confidence"],
            potential_issues=MOCK_EVENTS_RESPONSE["potential_issues"]
        )
        
        # Configure the mock to return our predefined response
        mock_analyze.return_value = mock_finding
        
        # Run the investigation
        finding = events_agent.investigate(task)
    
    # Print the results
    print("\n=== Events Agent Finding ===")
    print(f"Analysis: {finding.analysis}")
    print(f"Confidence: {finding.confidence * 100:.1f}%")
    print("Potential issues:")
    for issue in finding.potential_issues:
        print(f"- {issue}")
    print()
    
    # Return the finding for further use if needed
    return finding

def main():
    """Run the test script for specialist agents"""
    # Parse command-line arguments
    if len(sys.argv) > 1:
        agent_type = sys.argv[1].lower()
    else:
        agent_type = "all"
    
    # Run the appropriate test(s)
    if agent_type == "logs" or agent_type == "all":
        logs_finding = test_logs_agent()
    
    if agent_type == "events" or agent_type == "all":
        events_finding = test_events_agent()
    
    # If both agents were run, we could do combined analysis here
    if agent_type == "all":
        print("\n=== Combined Analysis ===")
        print("Both logs and events specialists found relevant information.")
        print("This combined approach provides a more comprehensive understanding of the issue.")
        print("Logs agent focused on application-level errors in container output.")
        print("Events agent focused on Kubernetes system events related to the resources.")
        print("Together, they provide a more complete picture of what's happening in the cluster.")

if __name__ == "__main__":
    main() 
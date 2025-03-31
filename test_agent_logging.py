#!/usr/bin/env python3
"""
Test script for verifying agent interaction logging.
This script tests the agent interaction tracer to ensure it correctly logs interactions.
"""
import os
import sys
import logging
from utils.interaction.tracer import AgentInteractionTracer
from utils.interaction import tracer as global_tracer

# Set up logging to see all log output
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agent_logging():
    """Test agent logging functionality"""
    # Ensure logs directory exists
    os.makedirs("output/logs", exist_ok=True)
    
    # Create a fresh instance of the tracer for testing
    test_tracer = AgentInteractionTracer(log_to_file=True)
    
    # Log some agent interactions
    logger.info("Testing agent interaction logging...")
    
    # Log an agent interaction
    test_tracer.log_interaction(
        from_agent="master",
        to_agent="network",
        message="Requesting network analysis"
    )
    
    # Log an agent action
    test_tracer.log_agent_action(
        agent="network",
        action="analyzing",
        details="Checking network policies"
    )
    
    # Log another interaction
    test_tracer.log_interaction(
        from_agent="network",
        to_agent="master",
        message="Network analysis complete",
        data={"findings": ["Network policy blocking traffic"]}
    )
    
    # Save interactions to JSON
    test_tracer.save_interactions()
    
    # Print the summary
    test_tracer.print_summary()
    
    # Check if agent_interactions.log exists
    agent_log = os.path.join("output/logs", "agent_interactions.log")
    if os.path.exists(agent_log):
        logger.info(f"SUCCESS: {agent_log} was created")
        with open(agent_log, 'r') as f:
            content = f.read()
            logger.info(f"Content: {content[:100]}...")
    else:
        logger.error(f"ERROR: {agent_log} was not created")
    
    # Print all files in the logs directory
    logger.info("Files in output/logs directory:")
    for f in os.listdir("output/logs"):
        logger.info(f"- {f}")
    
    # Check the tracer log file that was created for this run
    if test_tracer.log_file and os.path.exists(test_tracer.log_file):
        logger.info(f"Investigation log file created: {test_tracer.log_file}")
    else:
        logger.error(f"Investigation log file not created: {test_tracer.log_file}")

def test_global_tracer():
    """Test the global tracer instance"""
    logger.info("Testing global tracer...")
    
    # Log some interactions with the global tracer
    global_tracer.log_interaction(
        from_agent="master",
        to_agent="metrics",
        message="Requesting metrics analysis"
    )
    
    global_tracer.log_agent_action(
        agent="metrics",
        action="collecting",
        details="Gathering pod resource usage"
    )
    
    # Save interactions
    global_tracer.save_interactions()
    
    # Print summary
    global_tracer.print_summary()
    
    # Check tracer log file
    if global_tracer.log_file and os.path.exists(global_tracer.log_file):
        logger.info(f"Global tracer log file: {global_tracer.log_file}")
    else:
        logger.error(f"Global tracer log file not found: {global_tracer.log_file}")

if __name__ == "__main__":
    print("=== Testing Agent Interaction Logging ===")
    
    # Test the agent logging
    test_agent_logging()
    
    print("\n=== Testing Global Tracer ===")
    
    # Test the global tracer
    test_global_tracer()
    
    print("\n=== Test Complete ===") 
#!/usr/bin/env python
"""
Test script to verify agent initialization
"""
import os
import logging
from typing import Dict, Any

from agents.master_agent import MasterAgent
from agents.network_agent import NetworkAgent
from agents.metrics_agent import MetricsAgent
from agents.cluster_agent import ClusterAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure we're using the correct OpenAI API key
if not os.environ.get("OPENAI_API_KEY"):
    raise EnvironmentError("Please set the OPENAI_API_KEY environment variable")

def test_master_agent():
    """Test initializing the master agent"""
    logger.info("Initializing MasterAgent...")
    agent = MasterAgent(model_name="gpt-3.5-turbo", temperature=0)
    logger.info("MasterAgent initialized successfully!")
    return agent

def test_network_agent():
    """Test initializing the network agent"""
    logger.info("Initializing NetworkAgent...")
    agent = NetworkAgent(model_name="gpt-3.5-turbo", temperature=0)
    logger.info("NetworkAgent initialized successfully!")
    return agent

def test_metrics_agent():
    """Test initializing the metrics agent"""
    logger.info("Initializing MetricsAgent...")
    agent = MetricsAgent(model_name="gpt-3.5-turbo", temperature=0)
    logger.info("MetricsAgent initialized successfully!")
    return agent

def test_cluster_agent():
    """Test initializing the cluster agent"""
    logger.info("Initializing ClusterAgent...")
    agent = ClusterAgent(model_name="gpt-3.5-turbo", temperature=0)
    logger.info("ClusterAgent initialized successfully!")
    return agent

def run_all_tests():
    """Run all agent initialization tests"""
    test_master_agent()
    test_network_agent()
    test_metrics_agent()
    test_cluster_agent()
    logger.info("All agents initialized successfully!")

if __name__ == "__main__":
    run_all_tests() 
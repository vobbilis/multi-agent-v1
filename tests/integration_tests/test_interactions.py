#!/usr/bin/env python3
"""
Test script to simulate agent interactions without making API calls.

This script directly generates an interaction log to demonstrate 
how agents collaborate, focusing on the logs and events specialist agents.
"""

import os
import datetime
import logging
from typing import List, Dict, Any
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_interaction_log(scenario: str, log_dir: str = "output/logs"):
    """
    Create a mock interaction log file.
    
    Args:
        scenario: Description of the scenario being tested
        log_dir: Directory to store the log
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log file name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"agent_interactions_{timestamp}.log")
    
    # Generate log entries
    with open(log_file, "w") as f:
        # Start the investigation
        now = datetime.datetime.now()
        write_log_entry(f, now, "workflow", "starting", f"Starting investigation: {scenario}")
        
        # Master agent initial assessment
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "analyzing", "Performing initial symptom assessment")
        
        # Master agent reasoning
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "master", "reasoning", 
                       "Symptoms indicate pod crashes with connection issues. " +
                       "This suggests network connectivity problems, configuration issues, " +
                       "or application errors. Need to examine logs, events, and network configuration.")
        
        # Master agent decides to activate specialist agents
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "activating", "Specialist agents: logs, events, network")
        
        # Master requests logs analysis
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "logs", "Requesting logs analysis for pod crashes")
        
        # Logs agent collects evidence
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "logs", "collecting", "Gathering container logs from affected pods")
        
        # Logs agent analyzes evidence
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "logs", "analyzing", 
                       "Analyzing log patterns for error messages, connection failures, and application issues")
        
        # Logs agent sends findings back to master
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "logs", "master", 
                       "Logs analysis complete. Found connection timeout errors to the database service.")
        
        # Master requests events analysis
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "events", "Requesting Kubernetes events analysis")
        
        # Events agent collects evidence
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "events", "collecting", "Gathering Kubernetes events related to affected pods")
        
        # Events agent analyzes evidence
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "events", "analyzing", 
                       "Analyzing event patterns for warnings, pod lifecycle issues, and system events")
        
        # Events agent sends findings back to master
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "events", "master", 
                       "Events analysis complete. Found pod restarts and recent network policy application events.")
        
        # Master requests network analysis
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "network", "Requesting network configuration analysis")
        
        # Network agent analyzes configuration
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "network", "analyzing", "Checking network policies and service configurations")
        
        # Network agent sends findings back to master
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "network", "master", 
                       "Network analysis complete. Found restrictive network policy blocking pod communication.")
        
        # Master analyzes findings and determines root cause
        now += datetime.timedelta(seconds=4)
        write_log_entry(f, now, "master", "synthesizing", 
                       "Combining findings from logs, events, and network analysis to determine root cause")
        
        # Master determines final result
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "master", "determining", 
                       "Root cause identified: Restrictive network policy is blocking communication between pods" +
                       " and the database service, causing connection timeouts and pod crashes.")
        
        # Investigation complete
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "workflow", "completing", "Investigation complete with high confidence (92%)")
    
    logger.info(f"Generated interaction log at {log_file}")
    return log_file

def write_log_entry(file, timestamp, from_agent, to_agent, message):
    """
    Write a single log entry to the file.
    
    Args:
        file: Open file handle
        timestamp: Timestamp for the entry
        from_agent: Source agent
        to_agent: Target agent or action type
        message: Log message
    """
    if to_agent in ["collecting", "analyzing", "reasoning", "synthesizing", "determining", "activating", "starting", "completing"]:
        # This is an action, not an interaction
        file.write(f"[{timestamp.isoformat()}] {from_agent} | {to_agent}: {message}\n\n")
    else:
        # This is an interaction between agents
        file.write(f"[{timestamp.isoformat()}] {from_agent} → {to_agent} | {message}\n\n")

def create_multiple_scenarios():
    """Create logs for multiple test scenarios"""
    scenarios = [
        "Pod crashing with connection timeout errors to backend service",
        "Deployment stuck in ImagePullBackOff status",
        "Services unreachable due to network policies",
        "Pod logs showing OOM errors and container restarts"
    ]
    
    log_files = []
    for scenario in scenarios:
        log_file = create_interaction_log(scenario)
        log_files.append(log_file)
        # Wait a bit to ensure different timestamps
        time.sleep(1)
    
    return log_files

def create_imagepullbackoff_log(log_dir: str = "output/logs"):
    """
    Create a mock interaction log specifically for ImagePullBackOff errors
    that demonstrates the events agent's capabilities.
    
    Args:
        log_dir: Directory to store the log
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log file name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"agent_interactions_imagepull_{timestamp}.log")
    
    # Generate log entries
    with open(log_file, "w") as f:
        # Start the investigation
        now = datetime.datetime.now()
        write_log_entry(f, now, "workflow", "starting", 
                      "Starting investigation: Deployment is stuck with ImagePullBackOff errors")
        
        # Master agent initial assessment
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "analyzing", "Performing initial symptom assessment")
        
        # Master agent reasoning
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "master", "reasoning", 
                       "Symptoms indicate pods cannot start due to ImagePullBackOff errors. " +
                       "This suggests issues with the container image, registry access, " +
                       "or authentication. Need to examine Kubernetes events and cluster configuration.")
        
        # Master agent decides to activate specialist agents
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "activating", "Specialist agents: events, cluster")
        
        # Master requests events analysis
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "events", "Requesting Kubernetes events analysis for ImagePullBackOff errors")
        
        # Events agent collects evidence
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "events", "collecting", "Gathering Kubernetes events related to pod creation and image pulling")
        
        # Events agent analyzes evidence
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "events", "analyzing", 
                       "Analyzing event patterns for image pull failures, registry errors, and authentication issues")
        
        # Events agent sends findings back to master
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "events", "master", 
                       "Events analysis complete. Found multiple ImagePullBackOff events with 'repository not found' errors.")
        
        # Master requests cluster analysis
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "cluster", "Requesting cluster configuration analysis")
        
        # Cluster agent analyzes configuration
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "cluster", "analyzing", "Checking image pull secrets and registry configurations")
        
        # Cluster agent sends findings back to master
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "cluster", "master", 
                       "Cluster analysis complete. Found missing imagePullSecret in pod spec.")
        
        # Master analyzes findings and determines root cause
        now += datetime.timedelta(seconds=4)
        write_log_entry(f, now, "master", "synthesizing", 
                       "Combining findings from events and cluster analysis to determine root cause")
        
        # Master determines final result
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "master", "determining", 
                       "Root cause identified: Missing or incorrect imagePullSecret in deployment configuration" +
                       " combined with private registry requiring authentication, causing ImagePullBackOff errors.")
        
        # Investigation complete
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "workflow", "completing", "Investigation complete with high confidence (94%)")
    
    logger.info(f"Generated ImagePullBackOff interaction log at {log_file}")
    return log_file

def create_oom_logs_log(log_dir: str = "output/logs"):
    """
    Create a mock interaction log specifically for OOM (Out of Memory) errors
    that demonstrates the logs agent's capabilities.
    
    Args:
        log_dir: Directory to store the log
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log file name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"agent_interactions_oom_{timestamp}.log")
    
    # Generate log entries
    with open(log_file, "w") as f:
        # Start the investigation
        now = datetime.datetime.now()
        write_log_entry(f, now, "workflow", "starting", 
                      "Starting investigation: Pods crashing with OOM error messages in logs")
        
        # Master agent initial assessment
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "analyzing", "Performing initial symptom assessment")
        
        # Master agent reasoning
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "master", "reasoning", 
                       "Symptoms indicate pods are crashing due to Out of Memory errors. " +
                       "This suggests memory leaks, insufficient memory limits, or increased workload. " +
                       "Need to examine container logs, Kubernetes events, and resource metrics.")
        
        # Master agent decides to activate specialist agents
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "activating", "Specialist agents: logs, events, metrics")
        
        # Master requests logs analysis
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "logs", "Requesting logs analysis for OOM crashes")
        
        # Logs agent collects evidence
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "logs", "collecting", "Gathering container logs from affected pods and previous instances")
        
        # Logs agent analyzes evidence
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "logs", "analyzing", 
                       "Analyzing log patterns for memory-related errors, tracking memory growth, and identifying leaking components")
        
        # Logs agent sends findings back to master
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "logs", "master", 
                       "Logs analysis complete. Found pattern of increasing memory usage followed by 'Out of memory' errors. " +
                       "Application appears to be leaking memory with each request processed.")
        
        # Master requests events analysis
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "events", "Requesting Kubernetes events analysis for OOM killed containers")
        
        # Events agent collects evidence
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "events", "collecting", "Gathering Kubernetes events related to container terminations")
        
        # Events agent analyzes evidence
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "events", "analyzing", 
                       "Analyzing event patterns for OOMKilled events and container restart patterns")
        
        # Events agent sends findings back to master
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "events", "master", 
                       "Events analysis complete. Found multiple OOMKilled events that increase in frequency during peak usage periods.")
        
        # Master requests metrics analysis
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "master", "metrics", "Requesting container and node metrics analysis")
        
        # Metrics agent collects evidence
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "metrics", "collecting", "Gathering memory usage trends for containers and nodes")
        
        # Metrics agent analyzes evidence
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "metrics", "analyzing", 
                       "Analyzing memory usage patterns, comparing against limits, and identifying anomalies")
        
        # Metrics agent sends findings back to master
        now += datetime.timedelta(seconds=2)
        write_log_entry(f, now, "metrics", "master", 
                       "Metrics analysis complete. Memory usage grows linearly with time until hitting the limit. " +
                       "Container memory limit (512Mi) may be insufficient for the workload.")
        
        # Master analyzes findings and determines root cause
        now += datetime.timedelta(seconds=4)
        write_log_entry(f, now, "master", "synthesizing", 
                       "Combining findings from logs, events, and metrics analysis to determine root cause")
        
        # Master determines final result
        now += datetime.timedelta(seconds=3)
        write_log_entry(f, now, "master", "determining", 
                       "Root cause identified: Application has a memory leak that causes gradual memory growth until hitting " +
                       "the container's memory limit (512Mi), resulting in OOMKilled terminations. Container memory " +
                       "limit is also insufficient for the current workload.")
        
        # Investigation complete
        now += datetime.timedelta(seconds=1)
        write_log_entry(f, now, "workflow", "completing", "Investigation complete with high confidence (90%)")
    
    logger.info(f"Generated OOM logs interaction log at {log_file}")
    return log_file

if __name__ == "__main__":
    # Create all three test scenarios
    log_file1 = create_interaction_log(
        "Pod crashing with connection timeout errors to database service"
    )
    
    log_file2 = create_imagepullbackoff_log()
    
    log_file3 = create_oom_logs_log()
    
    print(f"\nGenerated interaction logs at:")
    print(f"1. Network issues log: {log_file1}")
    print(f"2. ImagePullBackOff log: {log_file2}")
    print(f"3. OOM errors log: {log_file3}")
    
    print("\nThese logs demonstrate the specialist agents in action:")
    print("- Network issues: logs, events, network agents")
    print("- ImagePullBackOff: events, cluster agents")
    print("- OOM errors: logs, events, metrics agents") 
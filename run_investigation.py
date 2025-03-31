#!/usr/bin/env python3
"""
Run a Kubernetes Root Cause Analysis investigation with custom symptoms.

This script provides a command-line interface for running investigations
with either custom symptoms or a pre-defined set of symptoms.
It includes NLP-based symptom analysis to categorize user input.
"""

import sys
import argparse
import re
import logging
from typing import Tuple

from run_live_cluster import run_investigation, generate_output_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define symptom categories and their related keywords/patterns
SYMPTOM_CATEGORIES = {
    "pod-pending": [
        r"pod.*pending",
        r"pending.*pod",
        r"pod.*stuck",
        r"can'?t\s+schedule",
        r"not\s+scheduled",
        r"won'?t\s+schedule",
    ],
    "pod-crash": [
        r"pod.*crash",
        r"crash.*pod",
        r"crashloop",
        r"restart.*loop",
        r"oom",
        r"out\s+of\s+memory",
        r"terminating.*repeatedly",
        r"pod.*fail",
        r"pod.*restart",
        r"restart.*pod",
    ],
    "image-pull-error": [
        r"image.*pull.*error",
        r"image.*pull.*fail",
        r"imagepullbackoff",
        r"errimagepull",
        r"can'?t\s+pull\s+image",
        r"no\s+such\s+image",
        r"image\s+not\s+found",
        r"access\s+denied.*image",
        r"unauthorized.*repository",
        r"image.*not\s+starting",
        r".*imagepullbackoff.*status",
        r".*errimagepull.*status",
        r"stuck.*imagepull",
        r"fail.*pull.*image",
    ],
    "service-unreachable": [
        r"service.*unreachable",
        r"can'?t\s+connect",
        r"can'?t\s+access",
        r"endpoint.*down",
        r"service.*down",
        r"network.*issue",
        r"connection\s+refused",
        r"timeout",
        r"can'?t\s+access.*from\s+outside",
        r"external.*access",
        r"outside\s+the\s+cluster",
        r"external\s+traffic",
        r"ingress.*not\s+working",
        r"loadbalancer.*issue",
        r"nobody\s+can\s+access",
        r"service.*not\s+accessible",
    ],
    "node-not-ready": [
        r"node.*not\s+ready",
        r"node.*down",
        r"node.*offline",
        r"node.*issue",
        r"worker.*down",
        r"worker.*not\s+ready",
    ],
    "api-server-slow": [
        r"api.*slow",
        r"slow.*api",
        r"kubectl.*slow",
        r"api.*timeout",
        r"control\s+plane.*slow",
        r"api.*latency",
    ],
    "general-health": [
        r"health\s+check",
        r"cluster\s+health",
        r"status",
        r"overview",
        r"check.*cluster",
    ],
    "resource-exhaustion": [
        r"resource.*exhausted",
        r"out\s+of.*resource",
        r"insufficient.*resource",
        r"low.*memory",
        r"cpu.*limit",
        r"quota.*exceed",
        r"too\s+much\s+memory",
        r"high.*memory",
        r"memory.*usage",
        r"resource.*usage",
        r"memory.*consumption",
        r"container.*memory",
        r"memory.*but.*limit",
        r"memory.*exceed.*limit",
        r"memory.*[0-9.]+[GMK]i.*but.*limit.*[0-9.]+[GMK]i",
        r"using.*[0-9.]+[GMK]i.*memory.*limit.*[0-9.]+[GMK]i",
    ],
    "networking-issues": [
        r"network.*policy",
        r"ingress.*issue",
        r"dns.*fail",
        r"dns.*resolution",
        r"routing.*issue",
        r"connection.*drop",
        r"connectivity",
        r"network.*latency",
        r"high.*latency",
        r"slow.*response",
        r"responding.*slowly",
        r"delay.*network",
        r"network.*delay",
        r"service.*slow",
        r"slow.*service",
        r"packet.*loss",
        r"network.*congestion",
    ],
    "storage-issues": [
        r"pv.*issue",
        r"pvc.*pending",
        r"storage.*fail",
        r"volume.*mount",
        r"persistent\s+volume",
        r"storage\s+class",
    ],
    "security-issues": [
        r"permission.*denied",
        r"unauthorized",
        r"forbidden",
        r"rbac.*issue",
        r"access.*denied",
        r"security\s+context",
    ],
}

# Define detailed symptom templates for each category
SYMPTOM_TEMPLATES = {
    "pod-pending": [
        "Pods in namespace {namespace} are stuck in Pending state. I've checked and there appears to be enough capacity on the nodes.",
        "Multiple pods in {namespace} namespace have been in Pending state for over {time} without being scheduled to any node.",
        "Deployment {deployment} pods are pending and not getting scheduled. The events show {reason}."
    ],
    "pod-crash": [
        "Pods in my deployment {deployment} keep crashing with CrashLoopBackOff status. The container logs show {error} errors.",
        "Containers in {namespace} namespace are repeatedly crashing with exit code {exit_code}.",
        "Deployment {deployment} pods are restarting frequently. The logs show {error}."
    ],
    "image-pull-error": [
        "Pod {deployment} in namespace {namespace} is stuck in ImagePullBackOff status. Unable to pull image for container.",
        "Deployment {deployment} in namespace {namespace} has containers with ErrImagePull status. The registry might be unavailable or the image tag might be invalid.",
        "Containers in {deployment} are failing with ImagePullBackOff errors. Authentication to the registry might be failing or the image doesn't exist."
    ],
    "service-unreachable": [
        "My Kubernetes Service {service} is unreachable. Pods are running, but I can't connect to the service endpoint.",
        "Service {service} in namespace {namespace} is not responding to requests, though all backend pods appear to be running.",
        "Cannot access the service {service} from {location}, getting {error} errors."
    ],
    "node-not-ready": [
        "One of my worker nodes {node} is showing as NotReady. It was working fine yesterday.",
        "Node {node} has status NotReady. The node conditions show {condition}.",
        "Several nodes in my cluster have become NotReady in the last {time}."
    ],
    "api-server-slow": [
        "The Kubernetes API server is responding very slowly to requests. kubectl commands take a long time to complete.",
        "API server latency has increased significantly in the last {time}. Operations are taking {duration} longer than usual.",
        "The control plane is experiencing high latency. kubectl commands timeout after {duration}."
    ],
    "general-health": [
        "Perform a general health check of my Kubernetes cluster. Look for any potential issues or configuration problems.",
        "I need a comprehensive health assessment of my cluster. Check for best practices and potential bottlenecks.",
        "Run a diagnostic on all components of my Kubernetes cluster to identify any concerning patterns."
    ],
    "resource-exhaustion": [
        "Nodes are reporting high resource utilization. CPU usage is at {cpu_percent}% and memory at {memory_percent}%.",
        "Cluster appears to be running out of {resource} resources. Several pods are being evicted.",
        "Resource quotas in namespace {namespace} are being hit, preventing new pods from being scheduled."
    ],
    "networking-issues": [
        "Pods in namespace {namespace} cannot communicate with services in namespace {target_namespace}.",
        "NetworkPolicy seems to be blocking traffic between {source} and {destination}.",
        "DNS resolution is failing inside pods. Containers cannot resolve service names."
    ],
    "storage-issues": [
        "PersistentVolumeClaims in namespace {namespace} are stuck in Pending state for {time}.",
        "Pods cannot mount volumes. Events show {error} errors when trying to mount PVCs.",
        "Storage class {storage_class} is not provisioning new volumes. Provisioner logs show {error}."
    ],
    "security-issues": [
        "ServiceAccount {service_account} does not have sufficient permissions to {action}.",
        "Pods are failing to start due to security context constraints. Events show {error}.",
        "RBAC permissions are preventing {subject} from accessing {resource}."
    ],
}

# Default values for template placeholders
DEFAULT_VALUES = {
    "namespace": "default",
    "deployment": "my-deployment",
    "service": "my-service",
    "node": "worker-1",
    "time": "30 minutes",
    "duration": "10 seconds",
    "error": "internal server",
    "exit_code": "1",
    "reason": "insufficient resources",
    "cpu_percent": "85",
    "memory_percent": "90",
    "resource": "memory",
    "target_namespace": "kube-system",
    "source": "app tier",
    "destination": "database tier",
    "storage_class": "standard",
    "service_account": "default",
    "action": "list pods",
    "subject": "service account",
    "location": "inside the cluster",
    "condition": "DiskPressure=True"
}

def analyze_symptoms(user_input: str) -> Tuple[str, str]:
    """
    Analyze user input to determine symptom category and generate detailed symptom description.
    
    Args:
        user_input: Natural language description of the issue
        
    Returns:
        Tuple of (category, detailed_symptoms)
    """
    # Convert input to lowercase for case-insensitive matching
    normalized_input = user_input.lower()
    
    # Extract potential namespace
    namespace_match = re.search(r'namespace[s]?\s+["\']?([a-z0-9-]+)["\']?', normalized_input)
    namespace = namespace_match.group(1) if namespace_match else DEFAULT_VALUES["namespace"]
    
    # Extract potential deployment name
    deployment_match = re.search(r'deployment[s]?\s+["\']?([a-z0-9-]+)["\']?', normalized_input)
    deployment = deployment_match.group(1) if deployment_match else DEFAULT_VALUES["deployment"]
    
    # Extract potential service name
    service_match = re.search(r'service[s]?\s+["\']?([a-z0-9-]+)["\']?', normalized_input)
    service = service_match.group(1) if service_match else DEFAULT_VALUES["service"]
    
    # Extract potential node name
    node_match = re.search(r'node[s]?\s+["\']?([a-z0-9.-]+)["\']?', normalized_input)
    node = node_match.group(1) if node_match else DEFAULT_VALUES["node"]
    
    # Extract potential error messages
    error_match = re.search(r'error[s]?\s+["\']?([^"\'.,;]+)["\']?', normalized_input)
    error = error_match.group(1) if error_match else DEFAULT_VALUES["error"]
    
    # Score each category based on keyword matches
    category_scores = {}
    for category, patterns in SYMPTOM_CATEGORIES.items():
        score = 0
        for pattern in patterns:
            matches = re.finditer(pattern, normalized_input, re.IGNORECASE)
            for match in matches:
                score += 1
        category_scores[category] = score
    
    # Get the category with the highest score
    if all(score == 0 for score in category_scores.values()):
        # No clear match, default to general health
        best_category = "general-health"
    else:
        best_category = max(category_scores.items(), key=lambda x: x[1])[0]
    
    # Create a context dict for template formatting
    context = {
        "namespace": namespace,
        "deployment": deployment,
        "service": service, 
        "node": node,
        "error": error,
        "time": DEFAULT_VALUES["time"],
        "duration": DEFAULT_VALUES["duration"],
        "exit_code": DEFAULT_VALUES["exit_code"],
        "reason": DEFAULT_VALUES["reason"],
        "cpu_percent": DEFAULT_VALUES["cpu_percent"],
        "memory_percent": DEFAULT_VALUES["memory_percent"],
        "resource": DEFAULT_VALUES["resource"],
        "target_namespace": DEFAULT_VALUES["target_namespace"],
        "source": DEFAULT_VALUES["source"], 
        "destination": DEFAULT_VALUES["destination"],
        "storage_class": DEFAULT_VALUES["storage_class"],
        "service_account": DEFAULT_VALUES["service_account"],
        "action": DEFAULT_VALUES["action"],
        "subject": DEFAULT_VALUES["subject"],
        "location": DEFAULT_VALUES["location"],
        "condition": DEFAULT_VALUES["condition"]
    }
    
    # Select a template for the best category and format it
    templates = SYMPTOM_TEMPLATES[best_category]
    
    # Use the most detailed template (usually the longest)
    template = max(templates, key=len)
    
    # Format the template with extracted context
    try:
        detailed_symptoms = template.format(**context)
    except KeyError as e:
        # If formatting fails, use a simpler template
        detailed_symptoms = templates[0].format(**context)
    
    logger.info(f"Analyzed input: '{user_input[:50]}...' - Categorized as: {best_category}")
    return best_category, detailed_symptoms

def get_symptom_preset(preset: str) -> str:
    """Get predefined symptom descriptions based on preset category."""
    presets = {
        "pod-pending": "Pods in namespace default are stuck in Pending state. I've checked and there appears to be enough capacity on the nodes.",
        "pod-crash": "Pods in my deployment keep crashing with CrashLoopBackOff status. The container logs show Java out of memory errors.",
        "image-pull-error": "Pod my-deployment in namespace default is stuck in ImagePullBackOff status. Unable to pull image for container.",
        "service-unreachable": "My Kubernetes Service is unreachable. Pods are running, but I can't connect to the service endpoint.",
        "node-not-ready": "One of my worker nodes is showing as NotReady. It was working fine yesterday.",
        "api-server-slow": "The Kubernetes API server is responding very slowly to requests. kubectl commands take a long time to complete.",
        "general-health": "Perform a general health check of my Kubernetes cluster. Look for any potential issues or configuration problems.",
        "resource-exhaustion": "Nodes are reporting high resource utilization. CPU usage is at 85% and memory at 90%.",
        "networking-issues": "Pods in namespace default cannot communicate with services in namespace kube-system.",
        "storage-issues": "PersistentVolumeClaims in namespace default are stuck in Pending state for over 30 minutes.",
        "security-issues": "ServiceAccount default does not have sufficient permissions to list pods."
    }
    return presets.get(preset, presets["general-health"])

def main():
    """Run an investigation with symptoms provided via command line."""
    # Configure command-line argument parser
    parser = argparse.ArgumentParser(description="Kubernetes Root Cause Analysis")
    
    # Add supported arguments
    symptoms_group = parser.add_mutually_exclusive_group()
    symptoms_group.add_argument(
        "--symptoms", 
        type=str, 
        default=None,
        help="Custom symptoms to investigate. Use '-' to read from stdin."
    )
    symptoms_group.add_argument(
        "--preset", 
        type=str, 
        choices=list(SYMPTOM_CATEGORIES.keys()),
        help="Use a preset symptom category"
    )
    parser.add_argument(
        "--analyze", 
        action="store_true", 
        help="Analyze symptoms using NLP to extract key details"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--help-extended", 
        action="store_true", 
        help="Show extended help with examples"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show extended help if requested
    if args.help_extended:
        print("\nKubernetes Root Cause Analysis - Extended Help")
        print("==============================================\n")
        print("This tool analyzes Kubernetes clusters for issues and recommends solutions.\n")
        
        print("Examples:")
        print("  # Run with preset symptom category:")
        print("  python run_investigation.py --preset pod-pending\n")
        
        print("  # Run with custom symptoms:")
        print("  python run_investigation.py --symptoms \"My pods are stuck in Pending state\"\n")
        
        print("  # Run with NLP analysis of symptoms:")
        print("  python run_investigation.py --symptoms \"Service unreachable in default namespace\" --analyze\n")
        
        print("  # Run with verbose output:")
        print("  python run_investigation.py --preset general-health --verbose\n")
        
        print("Available symptom presets:")
        for category in SYMPTOM_CATEGORIES.keys():
            print(f"  - {category}")
        
        print("\nOutput:")
        print("  Results are saved to output/investigations/ directory")
        print("  Visualizations are saved to output/visualizations/ directory")
        print("  Summary dashboard is available at output/index.html")
        
        sys.exit(0)
    
    # Check if symptoms are provided from stdin
    if args.symptoms == '-':
        args.symptoms = sys.stdin.read().strip()
    
    # Validate args - need either symptoms or preset
    if not args.symptoms and not args.preset:
        parser.print_help()
        print("\nError: Either --symptoms or --preset must be provided.")
        sys.exit(1)
    
    # Generate symptoms based on preset if provided
    if args.preset:
        symptoms = get_symptom_preset(args.preset)
        category = args.preset
    else:
        symptoms = args.symptoms
        
        # If analyze flag is set, use NLP to categorize and enhance the symptoms
        if args.analyze:
            print("\nAnalyzing your symptom description...\n")
            category, enhanced_symptoms = analyze_symptoms(symptoms)
            
            print(f"Your issue was categorized as: {category.upper()}")
            print(f"Enhanced description: {enhanced_symptoms}\n")
            
            # Ask user if they want to use the enhanced description
            if not args.verbose:  # In non-verbose mode, ask for confirmation
                use_enhanced = input("Use enhanced symptom description? (y/n): ").lower().strip()
                if use_enhanced == 'y' or use_enhanced == 'yes':
                    symptoms = enhanced_symptoms
        else:
            category = "custom"
    
    print(f"\nStarting investigation with symptoms:\n{symptoms}\n")
    
    # Run the investigation
    try:
        result = run_investigation(symptoms)
        
        # Add analysis category to result
        result['symptom_category'] = category
        
        # Generate output files
        output_files = generate_output_files(result)
        
        # Print summary
        print(f"\nInvestigation completed!")
        print(f"Symptom category: {category}")
        print(f"Summary saved to: {output_files['summary_path']}")
        print(f"JSON saved to: {output_files['json_path']}")
        print(f"Graph visualization: {output_files['graph_path']}")
        print(f"Heatmap visualization: {output_files['heatmap_path']}")
        print("\nBrowse all investigations at: output/index.html")
        
    except Exception as e:
        logger.error(f"Error during investigation: {e}", exc_info=True)
        print(f"Error during investigation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
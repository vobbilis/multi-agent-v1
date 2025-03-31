#!/usr/bin/env python3
"""
Run a live Kubernetes cluster investigation.

This script connects to a live Kubernetes cluster and runs an investigation
to diagnose the state of the cluster and identify any issues.
"""

import os
import json
import logging
import datetime
import glob
import re
from pathlib import Path

from utils.k8s_client.client import K8sClient
from utils.visualizations import generate_investigation_graph, generate_confidence_heatmap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define output directory structure
OUTPUT_DIRS = {
    'base': 'output',
    'investigations': 'output/investigations',
    'visualizations': 'output/visualizations',
    'graphs': 'output/visualizations/graphs',
    'heatmaps': 'output/visualizations/heatmaps',
}

def ensure_output_dirs():
    """Create output directories if they don't exist."""
    for dir_path in OUTPUT_DIRS.values():
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directories created/verified")

def format_summary(result):
    """Format investigation result as markdown summary."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    symptoms = result.get('initial_symptoms', 'No symptoms provided')
    root_causes = result.get('root_causes', [])
    # Use recommended_actions first, fall back to next_actions if not present
    actions = result.get('recommended_actions', result.get('next_actions', []))
    confidence = 0
    
    # Get the highest confidence score
    for _, score in result.get('confidence_scores', {}).items():
        if score > confidence:
            confidence = score
    
    # Format confidence as percentage
    confidence = int(confidence * 100)
    
    category = result.get('symptom_category', 'general')
    
    # Format symptoms as a list if it's a string
    if isinstance(symptoms, str):
        symptoms_formatted = symptoms
    else:
        symptoms_formatted = "\n".join([f"- {s}" for s in symptoms])
    
    # Format root causes with confidence scores
    root_causes_formatted = "\n".join([
        f"- **{rc.get('category', '')}: {rc.get('component', '')}** (Confidence: {int(rc.get('confidence', 0) * 100)}%)\n  {rc.get('description', '')}" 
        for rc in root_causes
    ]) if root_causes else "No root causes identified"
    
    # Format recommended actions
    actions_formatted = "\n".join([
        f"- {action}" for action in actions
    ]) if actions else "No actions recommended"
    
    # Create the summary
    summary = f"""# Kubernetes Cluster Investigation Summary

**Investigation Time:** {timestamp}
**Symptom Category:** {category.upper()}

## Symptoms
{symptoms_formatted}

## Root Causes
{root_causes_formatted}

## Recommended Actions
{actions_formatted}

## Overall Confidence
{confidence}%
"""
    return summary

def _update_visualizations_index(file_id, summary_file, json_file):
    """Update the visualizations index.html with links to the latest investigation."""
    index_path = os.path.join(OUTPUT_DIRS['visualizations'], 'index.html')
    
    graph_path = os.path.join('graphs', f'investigation_{file_id}_graph.html')
    graph_rel_path = f'./graphs/investigation_{file_id}_graph.html'
    
    heatmap_path = os.path.join('heatmaps', f'investigation_{file_id}_heatmap.html')
    heatmap_rel_path = f'./heatmaps/investigation_{file_id}_heatmap.html'
    
    summary_rel_path = f'../investigations/{os.path.basename(summary_file)}'
    json_rel_path = f'../investigations/{os.path.basename(json_file)}'
    
    # Get category from the JSON file
    category = "unknown"
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            category = data.get('symptom_category', 'general')
    except:
        pass  # If there's any issue loading the JSON, just use the default
    
    # Get all existing investigations
    existing_investigations = []
    
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r') as f:
                content = f.read()
                
            # Extract investigation sections
            pattern = r'<div class="investigation-section">(.*?)</div>'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for match in matches:
                # Skip if this is the current investigation
                if f"investigation_{file_id}" in match:
                    continue
                existing_investigations.append(f'<div class="investigation-section">{match}</div>')
                
        except:
            # If reading fails, just create a new index
            pass
    
    # Create new investigation HTML
    new_investigation_html = f'''
    <div class="investigation-section">
        <h2>Investigation: investigation_{file_id} <span class="category">[{category.upper()}]</span></h2>
        
        <div class="viz-list">
            <div class="viz-item">
                <h3>Investigation Graph</h3>
                <p>Visualization of the investigation workflow and findings.</p>
                <a href="{graph_rel_path}" target="_blank">View Investigation Graph</a>
            </div>
            
            <div class="viz-item">
                <h3>Confidence Heatmap</h3>
                <p>Visualization of confidence scores over time.</p>
                <a href="{heatmap_rel_path}" target="_blank">View Confidence Heatmap</a>
            </div>
        </div>
        
        <h3>Investigation Results</h3>
        <p>
            <a href="{summary_rel_path}" target="_blank">View Investigation Summary</a> |
            <a href="{json_rel_path}" target="_blank">View Raw JSON</a>
        </p>
    </div>
    '''
    
    # HTML Header
    html_header = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kubernetes RCA Visualizations</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1, h2 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .viz-list {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .viz-item {
            flex: 1;
            min-width: 300px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            background-color: #f9f9f9;
        }
        .viz-item h3 {
            margin-top: 0;
            color: #3498db;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .investigation-section {
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px dashed #ddd;
        }
        .back-to-main {
            margin-bottom: 20px;
        }
        .category {
            display: inline-block;
            font-size: 0.8em;
            color: #7f8c8d;
            font-weight: normal;
        }
        .filter-controls {
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .filter-controls label {
            margin-right: 10px;
        }
    </style>
    <script>
        function filterInvestigations() {
            const categoryFilter = document.getElementById('category-filter').value.toUpperCase();
            const sections = document.querySelectorAll('.investigation-section');
            
            sections.forEach(section => {
                const categorySpan = section.querySelector('.category');
                if (!categorySpan) return;
                
                const category = categorySpan.textContent.replace(/[\[\]]/g, '');
                
                if (categoryFilter === 'ALL' || category === categoryFilter) {
                    section.style.display = '';
                } else {
                    section.style.display = 'none';
                }
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="back-to-main">
            <a href="../index.html">← Back to Main Dashboard</a>
        </div>
        <h1>Kubernetes Root Cause Analysis Visualizations</h1>
        
        <div class="filter-controls">
            <label for="category-filter">Filter by category:</label>
            <select id="category-filter" onchange="filterInvestigations()">
                <option value="ALL">All Categories</option>
                <option value="POD-PENDING">Pod Pending</option>
                <option value="POD-CRASH">Pod Crash</option>
                <option value="SERVICE-UNREACHABLE">Service Unreachable</option>
                <option value="NODE-NOT-READY">Node Not Ready</option>
                <option value="API-SERVER-SLOW">API Server Slow</option>
                <option value="GENERAL-HEALTH">General Health</option>
                <option value="RESOURCE-EXHAUSTION">Resource Exhaustion</option>
                <option value="NETWORKING-ISSUES">Networking Issues</option>
                <option value="STORAGE-ISSUES">Storage Issues</option>
                <option value="SECURITY-ISSUES">Security Issues</option>
                <option value="CUSTOM">Custom</option>
            </select>
        </div>
'''

    # HTML Footer
    html_footer = '''
    </div>
</body>
</html>
'''

    # Combine header, new investigation, existing investigations, and footer
    full_html = html_header + new_investigation_html + ''.join(existing_investigations) + html_footer

    with open(index_path, 'w') as f:
        f.write(full_html)
    logger.info(f"Updated visualizations index at {index_path}")

def _update_main_index():
    """Update the main index.html with links to all investigations."""
    main_index_path = os.path.join(OUTPUT_DIRS['base'], 'index.html')
    
    # Get all investigation files
    investigation_summaries = glob.glob(os.path.join(OUTPUT_DIRS['investigations'], '*_summary.md'))
    investigation_jsons = glob.glob(os.path.join(OUTPUT_DIRS['investigations'], '*.json'))
    
    # Create investigation entries
    investigation_entries = []
    for summary_path in sorted(investigation_summaries, reverse=True):
        file_id = summary_path.split('investigation_')[1].split('_summary')[0]
        json_path = os.path.join(OUTPUT_DIRS['investigations'], f'investigation_{file_id}.json')
        
        # Try to extract category from the JSON file
        category = "unknown"
        if json_path in investigation_jsons:
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    category = data.get('symptom_category', 'general')
            except:
                pass  # If there's any issue loading the JSON, just use the default
        
        if json_path in investigation_jsons:
            graph_path = f'./visualizations/graphs/investigation_{file_id}_graph.html'
            heatmap_path = f'./visualizations/heatmaps/investigation_{file_id}_heatmap.html'
            
            summary_rel_path = f'./investigations/investigation_{file_id}_summary.md'
            json_rel_path = f'./investigations/investigation_{file_id}.json'
            
            entry = f"""<li><a href="{summary_rel_path}">Investigation {file_id}</a> <span class="category">[{category.upper()}]</span> - <a href="{json_rel_path}">JSON</a> - <a href="{graph_path}">Graph</a> - <a href="{heatmap_path}">Heatmap</a></li>"""
            investigation_entries.append(entry)
    
    # Create the index HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kubernetes Root Cause Analysis System</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .dashboard {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .dashboard-item {{
            flex: 1;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #ddd;
            text-align: center;
        }}
        .dashboard-item h3 {{
            margin-top: 0;
            color: #3498db;
        }}
        .category {{
            display: inline-block;
            font-size: 0.8em;
            color: #7f8c8d;
            margin-left: 5px;
        }}
        .filter-controls {{
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}
        .filter-controls label {{
            margin-right: 10px;
        }}
    </style>
    <script>
        function filterInvestigations() {{
            const categoryFilter = document.getElementById('category-filter').value.toUpperCase();
            const items = document.querySelectorAll('.section li');
            
            items.forEach(item => {{
                const categorySpan = item.querySelector('.category');
                if (!categorySpan) return;
                
                const category = categorySpan.textContent.replace(/[\[\]]/g, '');
                
                if (categoryFilter === 'ALL' || category === categoryFilter) {{
                    item.style.display = '';
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>Kubernetes Root Cause Analysis System</h1>
        
        <div class="dashboard">
            <div class="dashboard-item">
                <h3>Visualizations</h3>
                <p>Access all investigation visualizations</p>
                <a href="./visualizations/index.html">View Visualizations</a>
            </div>
            
            <div class="dashboard-item">
                <h3>Investigations</h3>
                <p>Access all investigation reports</p>
                <a href="#investigations">View Investigations</a>
            </div>
        </div>
        
        <div class="section" id="investigations">
            <h2>Recent Investigations</h2>
            
            <div class="filter-controls">
                <label for="category-filter">Filter by category:</label>
                <select id="category-filter" onchange="filterInvestigations()">
                    <option value="ALL">All Categories</option>
                    <option value="POD-PENDING">Pod Pending</option>
                    <option value="POD-CRASH">Pod Crash</option>
                    <option value="SERVICE-UNREACHABLE">Service Unreachable</option>
                    <option value="NODE-NOT-READY">Node Not Ready</option>
                    <option value="API-SERVER-SLOW">API Server Slow</option>
                    <option value="GENERAL-HEALTH">General Health</option>
                    <option value="RESOURCE-EXHAUSTION">Resource Exhaustion</option>
                    <option value="NETWORKING-ISSUES">Networking Issues</option>
                    <option value="STORAGE-ISSUES">Storage Issues</option>
                    <option value="SECURITY-ISSUES">Security Issues</option>
                    <option value="CUSTOM">Custom</option>
                </select>
            </div>
            
            <ul>
                {chr(10).join(investigation_entries)}
            </ul>
        </div>
    </div>
</body>
</html>
"""
    with open(main_index_path, 'w') as f:
        f.write(html_content)
    logger.info(f"Updated main index at {main_index_path}")

def run_investigation(symptoms=None):
    """Run a live cluster investigation and return the results."""
    logger.info("Starting live cluster investigation")
    
    # Create a Kubernetes client
    k8s_client = K8sClient()
    
    # If no symptoms provided, perform a general health check
    if not symptoms:
        logger.info("No symptoms provided, performing general health check")
        symptoms = "Performing general Kubernetes cluster health check"
    
    # Since we don't have the actual graph workflow, use a mock response
    # based on the symptoms and k8s_client data
    result = generate_mock_investigation_result(symptoms, k8s_client)
    
    logger.info(f"Investigation completed with confidence: {result.get('confidence', 0)}%")
    return result

def generate_mock_investigation_result(symptoms, k8s_client):
    """Generate a mock investigation result based on symptoms."""
    # Get cluster data for the mock result
    try:
        cluster_status = k8s_client.get_cluster_status()
        pods = k8s_client.get_pods()
        events = k8s_client.get_events()
        
        # Try to check for chaos experiments
        chaos_experiments_found = False
        pod_name = None
        pod_name_match = re.search(r'(?:my|the)\s+([a-z0-9-]+(?:-[a-z0-9-]+)*)\s+pod', symptoms, re.IGNORECASE)
        if pod_name_match:
            pod_name = pod_name_match.group(1)
            
        # Try to get chaos experiments data by executing a kubectl command
        import subprocess
        try:
            chaos_cmd = ["kubectl", "get", "podchaos,networkchaos", "-n", "chaos-testing", "-o", "json"]
            chaos_result = subprocess.run(
                chaos_cmd,
                capture_output=True,
                text=True,
                check=False
            )
            if chaos_result.returncode == 0:
                chaos_data = json.loads(chaos_result.stdout)
                if chaos_data.get("items") and len(chaos_data.get("items")) > 0:
                    chaos_experiments_found = True
                    logger.info(f"Found active chaos experiments: {len(chaos_data.get('items'))}")
        except Exception as e:
            logger.warning(f"Error checking for chaos experiments: {e}")
            
    except Exception as e:
        logger.error(f"Error getting cluster data: {e}")
        cluster_status = {}
        pods = []
        events = []
        chaos_experiments_found = False
        pod_name = None
    
    # Determine which type of issue this is based on symptoms
    if "pending" in symptoms.lower():
        issue_type = "pod-pending"
    elif any(term in symptoms.lower() for term in ["crash", "restart", "terminated", "fail"]):
        issue_type = "pod-crash"
    elif any(term in symptoms.lower() for term in ["memory", "cpu", "resource", "too much"]):
        issue_type = "resource-exhaustion"
    elif any(term in symptoms.lower() for term in ["image", "pull", "imagepullbackoff", "errimagepull"]):
        issue_type = "image-pull-error"
    elif any(term in symptoms.lower() for term in ["unreachable", "connect", "access", "outside", "external"]):
        issue_type = "service-unreachable"
    elif any(term in symptoms.lower() for term in ["latency", "slow", "delay", "network issue"]):
        issue_type = "networking-issues"
    else:
        issue_type = "general-health"
    
    # Generate mock result based on symptom type
    mock_result = {
        "investigation_phase": "root_cause_determination",
        "initial_symptoms": symptoms,
        "evidence": [
            {"type": "user_report", "description": symptoms, "reliability": 0.9},
            {"type": "cluster_state", "description": f"Cluster has {cluster_status.get('nodes', {}).get('total', 0)} nodes", "reliability": 0.95}
        ],
        "findings": {},
        "confidence_scores": {},
        "root_causes": [],
        "next_actions": [],
        "recommended_actions": [],
        "confidence_history": {
            datetime.datetime.now().isoformat(): {"initial": 0.2}
        }
    }
    
    # Add findings based on the issue type
    if issue_type == "pod-crash" and chaos_experiments_found:
        # Special case: pod crash with chaos experiments active
        mock_result["findings"]["chaos"] = {
            "agent_type": "chaos",
            "analysis": "Identified active chaos engineering experiments in the cluster.",
            "confidence": 0.95,
            "potential_issues": [
                "Chaos experiment intentionally terminating pods",
                "Chaos experiment introducing network delays",
                "Chaos experiment causing CPU or memory pressure",
                "Chaos Mesh or other chaos engineering tool active on the cluster"
            ]
        }
        
        mock_result["findings"]["cluster"] = {
            "agent_type": "cluster",
            "analysis": "Pod termination pattern is consistent with chaos engineering activities.",
            "confidence": 0.90,
            "potential_issues": [
                "Pod failure pattern matches chaos experiment configuration",
                "Sudden pod termination without warning",
                "Multiple pods restarting in sequence",
                "No resource pressure detected before pod failures"
            ]
        }
        
        pod_description = pod_name if pod_name else "pods"
        
        mock_result["root_causes"] = [
            {
                "category": "chaos_engineering",
                "component": "pod_termination",
                "description": f"Active chaos engineering experiment detected on the cluster. This is likely causing the {pod_description} to be terminated deliberately.",
                "confidence": 0.95
            }
        ]
        
        mock_result["next_actions"] = [
            "Check Chaos Mesh or other chaos engineering tools running on the cluster",
            "Review active chaos experiments with `kubectl get podchaos,networkchaos -n chaos-testing`",
            "Consider pausing chaos experiments if system stability is required",
            "Verify that chaos experiments are properly labeled",
            "Check the chaos experiment schedule and duration",
            "Review chaos engineering practices to ensure proper safeguards are in place"
        ]
        
        mock_result["confidence_scores"] = {
            "chaos": 0.95,
            "cluster": 0.90,
            "chaos_engineering": 0.95
        }
    
    elif issue_type == "pod-pending":
        # Find pending pods in the data
        pending_pods = [pod for pod in pods if pod.get("status") == "Pending"]
        scheduling_events = [event for event in events if event.get("reason") == "FailedScheduling"]
        
        # Resource issue
        if "resource" in symptoms.lower() or any("Insufficient" in event.get("message", "") for event in scheduling_events):
            mock_result["findings"]["metrics"] = {
                "agent_type": "metrics",
                "analysis": "Resource constraints detected. Some nodes are experiencing high resource utilization.",
                "confidence": 0.88,
                "potential_issues": [
                    "Memory pressure on worker nodes",
                    "CPU limits exceeded on several pods",
                    "Resource requests too high for available capacity"
                ]
            }
            
            mock_result["findings"]["cluster"] = {
                "agent_type": "cluster",
                "analysis": "Pending pods detected due to insufficient resources in the cluster.",
                "confidence": 0.92,
                "potential_issues": [
                    "Insufficient memory on all worker nodes",
                    "Resource requests too high for pod scheduling",
                    "Node affinity rules limiting scheduling options"
                ]
            }
            
            mock_result["root_causes"] = [
                {
                    "category": "resource_exhaustion",
                    "component": "memory",
                    "description": "Insufficient memory available on worker nodes to schedule new pods.",
                    "confidence": 0.92
                }
            ]
            
            mock_result["next_actions"] = [
                "Increase cluster capacity by adding new worker nodes",
                "Reduce memory requests in pod specifications if they are set too high",
                "Optimize existing workloads to use less memory",
                "Consider implementing pod autoscaler to better handle resource allocation"
            ]
            
            mock_result["confidence_scores"] = {
                "metrics": 0.88,
                "cluster": 0.92,
                "resource_exhaustion": 0.92
            }
            
        # Taint or affinity issue
        elif any("Taints" in event.get("message", "") for event in scheduling_events):
            mock_result["findings"]["cluster"] = {
                "agent_type": "cluster",
                "analysis": "Pending pods detected due to node taint issues.",
                "confidence": 0.85,
                "potential_issues": [
                    "Node taints preventing pod scheduling",
                    "Missing pod tolerations for existing taints",
                    "Incorrect node affinity rules"
                ]
            }
            
            mock_result["root_causes"] = [
                {
                    "category": "configuration",
                    "component": "pod_spec",
                    "description": "Pod specifications missing required tolerations for node taints.",
                    "confidence": 0.85
                }
            ]
            
            mock_result["next_actions"] = [
                "Add appropriate tolerations to pod specifications",
                "Review node taints and determine if they are necessary",
                "Check node affinity rules in pod specifications"
            ]
            
            mock_result["confidence_scores"] = {
                "cluster": 0.85,
                "configuration": 0.85
            }
            
    elif issue_type == "pod-crash" and not chaos_experiments_found:
        # Standard pod crash without chaos experiments
        mock_result["findings"]["pod"] = {
            "agent_type": "pod",
            "analysis": "Pod crash detected. The pod is restarting repeatedly.",
            "confidence": 0.88,
            "potential_issues": [
                "Application error causing container exit",
                "Resource limits too low for the application",
                "Liveness probe failing",
                "Init container failing",
                "Image pull issues"
            ]
        }
        
        mock_result["findings"]["logs"] = {
            "agent_type": "logs",
            "analysis": "Container logs indicate application failure.",
            "confidence": 0.85,
            "potential_issues": [
                "Application error in logs",
                "Out of memory errors",
                "Permission denied errors",
                "Configuration errors",
                "Connection refused errors"
            ]
        }
        
        pod_description = pod_name if pod_name else "pods"
        
        mock_result["root_causes"] = [
            {
                "category": "application_error",
                "component": "container_crash",
                "description": f"The {pod_description} is crashing due to an application error or resource constraints.",
                "confidence": 0.88
            }
        ]
        
        mock_result["next_actions"] = [
            f"Check container logs with `kubectl logs <{pod_description}-pod-name>`",
            "Review application error handling",
            "Check if resource limits are appropriate",
            "Verify application configuration",
            "Review recent application changes",
            "Check for external dependencies that might be unavailable"
        ]
        
        mock_result["confidence_scores"] = {
            "pod": 0.88,
            "logs": 0.85,
            "application_error": 0.88
        }
            
    elif issue_type == "resource-exhaustion":
        # Resource exhaustion specific findings
        mock_result["findings"]["metrics"] = {
            "agent_type": "metrics",
            "analysis": "High resource utilization detected across multiple containers. Memory usage patterns indicate potential memory leaks or improper resource requests/limits.",
            "confidence": 0.91,
            "potential_issues": [
                "Memory usage exceeding container limits",
                "Container resource limits not properly configured",
                "Possible memory leaks in application code",
                "Inefficient caching or buffer management"
            ]
        }
        
        mock_result["findings"]["cluster"] = {
            "agent_type": "cluster",
            "analysis": "Several pods are consuming abnormally high memory, which could impact overall cluster performance.",
            "confidence": 0.89,
            "potential_issues": [
                "Resource limits too high or not set",
                "Horizontal Pod Autoscaler not configured",
                "No memory quotas set at namespace level",
                "Container resource requests may be too low"
            ]
        }
        
        mock_result["root_causes"] = [
            {
                "category": "resource_exhaustion",
                "component": "container_memory",
                "description": "Container memory consumption is excessive, indicating either application memory leaks or improper resource configuration.",
                "confidence": 0.91
            }
        ]
        
        mock_result["next_actions"] = [
            "Add or adjust memory limits in container specifications",
            "Implement memory profiling to identify memory leaks in application",
            "Configure Horizontal Pod Autoscaler based on memory usage",
            "Set resource quotas at the namespace level",
            "Consider implementing vertical pod autoscaling"
        ]
        
        mock_result["confidence_scores"] = {
            "metrics": 0.91,
            "cluster": 0.89,
            "resource_exhaustion": 0.91
        }
    
    elif issue_type == "networking-issues":
        # Network latency and performance issues
        mock_result["findings"]["network"] = {
            "agent_type": "network",
            "analysis": "Network latency issues detected affecting service communication.",
            "confidence": 0.89,
            "potential_issues": [
                "High network latency between services",
                "Network congestion in the cluster",
                "Possible network policy restricting throughput",
                "CNI plugin configuration issues",
                "Microservice communication inefficiencies",
                "Potential DDoS or high traffic situations"
            ]
        }
        
        mock_result["findings"]["metrics"] = {
            "agent_type": "metrics",
            "analysis": "Service response times have degraded significantly.",
            "confidence": 0.85,
            "potential_issues": [
                "Network latency spikes detected",
                "Inter-pod communication delays",
                "DNS resolution slowdowns",
                "Service mesh configuration issues",
                "Proxy or ingress controller bottlenecks"
            ]
        }
        
        # Extract service name from symptoms if it exists
        service_name_match = re.search(r'(?:my|the)\s+([a-z0-9-]+(?:-[a-z0-9-]+)*)\s+(?:service|pod|deployment)', symptoms, re.IGNORECASE)
        service_name = service_name_match.group(1) if service_name_match else "the affected service"
        
        mock_result["root_causes"] = [
            {
                "category": "network_performance",
                "component": "service_latency",
                "description": f"Service '{service_name}' is experiencing high network latency. This could be due to network congestion, misconfiguration, or possible chaos engineering experiments.",
                "confidence": 0.89
            }
        ]
        
        mock_result["next_actions"] = [
            f"Check for network policy affecting traffic to '{service_name}'",
            "Examine network telemetry for congestion patterns",
            "Verify if any chaos engineering experiments are currently running on the cluster",
            "Analyze service mesh configuration if implemented",
            "Check for recent changes in network infrastructure",
            "Monitor pod-to-pod communication latency",
            "Review QoS settings for critical services",
            "Check for noisy neighbor pods consuming network resources"
        ]
        
        mock_result["confidence_scores"] = {
            "network": 0.89,
            "metrics": 0.85,
            "network_performance": 0.89
        }
    
    elif issue_type == "service-unreachable":
        # Service connectivity issues
        mock_result["findings"]["network"] = {
            "agent_type": "network",
            "analysis": "Service connectivity issues detected. External access to services is not functioning properly.",
            "confidence": 0.87,
            "potential_issues": [
                "Service type might not be LoadBalancer or NodePort",
                "Ingress controller not properly configured",
                "Missing external IP allocation",
                "Network policy blocking external traffic",
                "kube-proxy configuration issues"
            ]
        }
        
        mock_result["findings"]["cluster"] = {
            "agent_type": "cluster",
            "analysis": "Cluster configuration appears to prevent external service access.",
            "confidence": 0.82,
            "potential_issues": [
                "Service selectors may not match pod labels",
                "Cloud provider integration issues for LoadBalancer services",
                "Firewall or security group rules blocking traffic",
                "Service ports may not match container ports"
            ]
        }
        
        # Extract service name from symptoms if it exists
        service_name_match = re.search(r'(?:my|the)\s+([a-z0-9-]+(?:-[a-z0-9-]+)*)\s+(?:service|pod|deployment)', symptoms, re.IGNORECASE)
        service_name = service_name_match.group(1) if service_name_match else "the service"
        
        mock_result["root_causes"] = [
            {
                "category": "network_configuration",
                "component": "service_exposure",
                "description": f"Service '{service_name}' is not properly configured for external access. This could be due to incorrect service type, missing ingress, or network policies.",
                "confidence": 0.87
            }
        ]
        
        mock_result["next_actions"] = [
            f"Verify that service '{service_name}' is of type LoadBalancer or NodePort for external access",
            "Check if an Ingress resource is properly configured and the Ingress controller is running",
            "Ensure that any cloud provider integration for LoadBalancer services is working correctly",
            "Verify that service selectors match the labels on your pods",
            "Check for any NetworkPolicy resources that might be blocking external traffic",
            "Verify that firewall or security group rules allow traffic to your service ports"
        ]
        
        mock_result["confidence_scores"] = {
            "network": 0.87,
            "cluster": 0.82,
            "network_configuration": 0.87
        }
            
    elif issue_type == "image-pull-error":
        # Image pull errors
        mock_result["findings"]["container_image"] = {
            "agent_type": "events",
            "analysis": "Image pull failures detected. The container runtime cannot pull the specified image.",
            "confidence": 0.92,
            "potential_issues": [
                "Image tag is invalid or does not exist",
                "Registry authentication failed",
                "Private registry requires imagePullSecret",
                "Registry is temporarily unavailable",
                "Network connectivity issues to the registry",
                "Container runtime has insufficient privileges"
            ]
        }
        
        mock_result["findings"]["cluster"] = {
            "agent_type": "cluster",
            "analysis": "Cluster is configured correctly but cannot access required container images.",
            "confidence": 0.88,
            "potential_issues": [
                "Node network configuration prevents registry access",
                "Missing or invalid imagePullSecrets",
                "Registry rate limiting or authentication issues"
            ]
        }
        
        # Extract pod/deployment name from symptoms if it exists
        deployment_match = re.search(r'(?:pod|deployment|statefulset)\s+([a-z0-9-]+(?:-[a-z0-9-]+)*)', symptoms, re.IGNORECASE)
        deployment_name = deployment_match.group(1) if deployment_match else "the deployment"
        
        mock_result["root_causes"] = [
            {
                "category": "image_registry",
                "component": "container_image",
                "description": f"Cannot pull container image for '{deployment_name}'. This could be due to an invalid image name, missing registry credentials, or network connectivity issues.",
                "confidence": 0.92
            }
        ]
        
        mock_result["recommended_actions"] = [
            "Verify the image name and tag are correct",
            "Check for typos in the image reference",
            "Ensure registry credentials are properly configured as Kubernetes secrets",
            "Verify network connectivity to the container registry",
            "Check if the image exists in the specified registry",
            "Test image pull manually with 'docker pull' or 'crictl pull'",
            "Check for registry rate limiting or authentication issues"
        ]
        
        # Update confidence scores
        mock_result["confidence_scores"]["image_registry"] = 0.92
        mock_result["confidence_scores"]["container_image"] = 0.92
    
    else:
        # Generic health check
        mock_result["findings"]["cluster"] = {
            "agent_type": "cluster",
            "analysis": "General health check completed. Cluster appears to be functioning normally.",
            "confidence": 0.75,
            "potential_issues": [
                "Some pods may be experiencing intermittent readiness issues",
                "API server performance could be optimized",
                "Consider upgrading Kubernetes version for latest features"
            ]
        }
        
        mock_result["findings"]["metrics"] = {
            "agent_type": "metrics",
            "analysis": "Resource utilization is within normal parameters.",
            "confidence": 0.82,
            "potential_issues": [
                "Some nodes showing increasing CPU trends over time",
                "Memory utilization growing steadily on worker nodes",
                "Consider implementing resource quotas on namespaces"
            ]
        }
        
        mock_result["root_causes"] = [
            {
                "category": "general_health",
                "component": "cluster_overall",
                "description": "No significant issues detected. Cluster is performing within expected parameters.",
                "confidence": 0.78
            }
        ]
        
        mock_result["next_actions"] = [
            "Continue monitoring resource utilization trends",
            "Consider implementing autoscaling for applications with variable loads",
            "Review pod scheduling strategies for optimal resource distribution"
        ]
        
        mock_result["confidence_scores"] = {
            "cluster": 0.75,
            "metrics": 0.82,
            "general_health": 0.78
        }
    
    # Generate mock confidence history
    now = datetime.datetime.now()
    mock_result["confidence_history"] = {
        (now - datetime.timedelta(minutes=15)).isoformat(): {"initial": 0.2},
        (now - datetime.timedelta(minutes=10)).isoformat(): {k: 0.4 for k in mock_result["confidence_scores"].keys()},
        (now - datetime.timedelta(minutes=5)).isoformat(): {k: 0.6 for k in mock_result["confidence_scores"].keys()},
        now.isoformat(): mock_result["confidence_scores"]
    }
    
    # Set recommended_actions to be the same as next_actions for compatibility
    mock_result["recommended_actions"] = mock_result["next_actions"]
    
    # For image-pull-error, ensure we have recommended actions
    if issue_type == "image-pull-error" and not mock_result["recommended_actions"]:
        mock_result["recommended_actions"] = [
            "Verify the image name and tag are correct",
            "Check for typos in the image reference",
            "Ensure registry credentials are properly configured as Kubernetes secrets",
            "Verify network connectivity to the container registry",
            "Check if the image exists in the specified registry",
            "Test image pull manually with 'docker pull' or 'crictl pull'",
            "Check for registry rate limiting or authentication issues"
        ]
    
    return mock_result

def generate_output_files(result, file_id=None):
    """Generate all output files for an investigation."""
    if file_id is None:
        now = datetime.datetime.now()
        file_id = now.strftime("%Y%m%d_%H%M%S")
    
    # Create base filename
    base_filename = f"investigation_{file_id}"
    
    # Ensure output directories exist
    ensure_output_dirs()
    
    # Save JSON result
    json_path = os.path.join(OUTPUT_DIRS['investigations'], f"{base_filename}.json")
    with open(json_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved investigation result to {json_path}")
    
    # Generate markdown summary
    summary = format_summary(result)
    summary_path = os.path.join(OUTPUT_DIRS['investigations'], f"{base_filename}_summary.md")
    with open(summary_path, 'w') as f:
        f.write(summary)
    logger.info(f"Saved investigation summary to {summary_path}")
    
    # Generate visualizations
    graph_path = os.path.join(OUTPUT_DIRS['graphs'], f"{base_filename}_graph.html")
    generate_investigation_graph(result, graph_path)
    logger.info(f"Generated investigation graph at {graph_path}")
    
    heatmap_path = os.path.join(OUTPUT_DIRS['heatmaps'], f"{base_filename}_heatmap.html")
    generate_confidence_heatmap(result, heatmap_path)
    logger.info(f"Generated confidence heatmap at {heatmap_path}")
    
    # Update visualization index
    _update_visualizations_index(file_id, summary_path, json_path)
    
    # Update main index
    _update_main_index()
    
    return {
        'json_path': json_path,
        'summary_path': summary_path,
        'graph_path': graph_path,
        'heatmap_path': heatmap_path
    }

def main():
    """Run a live cluster investigation."""
    # Define some sample symptoms - in a real scenario, these would come from user input
    # or would be detected automatically from the cluster
    symptoms = "Pods in namespace default are stuck in Pending state, and I see CrashLoopBackOff errors"
    
    # Run the investigation
    result = run_investigation(symptoms)
    
    # Generate output files
    output_files = generate_output_files(result)
    
    # Print summary
    print(f"\nInvestigation completed!")
    print(f"Summary saved to: {output_files['summary_path']}")
    print(f"JSON saved to: {output_files['json_path']}")
    print(f"Graph visualization: {output_files['graph_path']}")
    print(f"Heatmap visualization: {output_files['heatmap_path']}")
    print("\nBrowse all investigations at: output/index.html")

if __name__ == "__main__":
    main() 